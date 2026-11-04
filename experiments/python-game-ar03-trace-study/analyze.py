#!/usr/bin/env python3
"""Untimed exact stripe-refill demand analysis of retained token cursors."""
import argparse,hashlib,json
from pathlib import Path
import importlib.util,sys
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('ar03_trace_object_reader',HERE/'verify.py')
v=importlib.util.module_from_spec(s);sys.modules[s.name]=v;s.loader.exec_module(v)

def size(r):return 0 if r is None else r[1]-r[0]
def reads(rec):
    if rec['storage']=='raw':return size(rec['raw_range'])
    if rec['storage']=='rice':return size(rec['dc_read_range'])+size(rec['ac_read_range'])
    return size(rec['mode_read_range'])+size(rec.get('dc_value_range'))+(reads(rec['compact_cp02']) if 'compact_cp02' in rec else 0)
def build():
    path=HERE/'results.json';d=json.loads(path.read_text());rows=[]
    for c in d['cohorts']:
        for row in c['rows']:
            trace=json.loads(v.raw(row['trace']))
            for p in trace['planes']:
                stripes=[sum(reads(b) for b in stripe['blocks']) for stripe in p['stripes']]
                info=p['selected_entropy'];cp=info.get('cp02')
                cp_payload=0 if cp is None else size(cp['dc_range'])+size(cp['ac_range'])-cp['dc_parameter_bytes']-cp['ac_parameter_bytes']
                expected=cp_payload+(info.get('mode_bytes',0)+info.get('dc_value_bytes',0))
                assert sum(stripes)==expected,(c['name'],row['id'],p['plane'],sum(stripes),expected)
                # Exclude headers/parameters/CRC from both sides of this comparison.
                mean=sum(stripes)/len(stripes)
                rows.append(dict(cohort=c['name'],id=row['id'],plane=p['plane'],storage=info['storage'],stripe_refill_bytes=stripes,
                    selected_payload_refill_bytes=sum(stripes),uniform_block_count_apportion_bytes_per_stripe=mean,
                    peak_stripe_refill_bytes=max(stripes),peak_to_uniform_ratio=None if not mean else max(stripes)/mean,
                    max_absolute_deviation_from_uniform_bytes=max(abs(x-mean) for x in stripes)))
    native=[r for r in rows if r['cohort'].startswith('native')]
    return dict(results_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),analyzer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        plane_traces=len(rows),rows=rows,
        native_max_peak_to_uniform_ratio=max(r['peak_to_uniform_ratio'] for r in native if r['peak_to_uniform_ratio'] is not None),
        native_max_absolute_deviation_bytes=max(r['max_absolute_deviation_from_uniform_bytes'] for r in native),
        scope='Logical selected-payload cursor refills, not all CRC/preflight/header/map rescans or physical cache/SDRAM bursts. Uniform comparison excludes all headers/params/CRC from both sides. Exact per-stream byte offsets remain in trace. Not native memory timing or 30fps proof.')
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();d=build();path=HERE/'stripe-demand.json'
    if a.check:assert json.loads(path.read_text())==d
    else:path.write_text(json.dumps(d,indent=2)+'\n')
    print('PASS:48actual-plane exact cursor refill conservation; byte-demand peaks measured from tokens, not proportional apportion; no timing claim')
if __name__=='__main__':main()
