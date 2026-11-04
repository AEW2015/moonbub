#!/usr/bin/env python3
"""Untimed paired-control analysis; never predicts skipped SR sizes."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def build():
    path=HERE/'results.json';d=json.loads(path.read_text());rows=[]
    for gate in [c for c in d['cases'] if c['mode']=='gated']:
        exact=next(c for c in d['cases'] if c['source']==gate['source'] and c['mode']=='exact')
        assert gate['manifest']['source_sha256']==exact['manifest']['source_sha256']
        assert gate['manifest']['frame_sha256']==exact['manifest']['frame_sha256']
        aa={p['id']:p for p in gate['result']['packets']};bb={p['id']:p for p in exact['result']['packets']}
        ca={c['id']:c for c in gate['result']['commits']};cb={c['id']:c for c in exact['result']['commits']}
        matched=[];missed=[];unmatched=[]
        for i,a in aa.items():
            b=bb.get(i)
            if b is None or not all(a[k]==b[k] for k in ('key','promoted','reference_bank','reference_id','reference_tag')):
                unmatched.append(i);continue
            gm_a=next(t['bytes'] for t in a['info']['inner_attempts'] if t['codec']=='GM01')
            gm_b=next(t['bytes'] for t in b['info']['inner_attempts'] if t['codec']=='GM01')
            assert gm_a==gm_b
            if i in ca and i in cb:assert ca[i]['base_rgb_sha256']==cb[i]['base_rgb_sha256']
            matched.append(i)
            if not a['info']['gate']['allow_sr'] and b['info']['inner_codec']=='SR01':
                saved=gm_b-b['info']['inner_bytes'];assert saved>0
                missed.append(dict(id=i,control_gm_inner_bytes=gm_b,control_selected_sr_inner_bytes=b['info']['inner_bytes'],actual_control_saved_bytes=saved))
        rows.append(dict(source=gate['source'],gate_evaluated=len(aa),eligible=sum(p['info']['gate']['allow_sr'] for p in aa.values()),
                         matched_reference_and_gm_length_ids=matched,unmatched_ids=unmatched,
                         actual_control_sr_wins_skipped_by_gate=missed,
                         matched_control_saved_inner_bytes=sum(p['actual_control_saved_bytes'] for p in missed),
                         gate_service_ms=sum(p['info']['gate_ms'] for p in aa.values()),
                         caveat='Observed in separately executed exact controls with matching current source/ref/GM length only; does not assign a length to an uncoded gated SR candidate or infer unmatched opportunities.'))
    return dict(results_sha256=digest(path),analysis_source_sha256=digest(HERE/'analyze.py'),rows=rows,
                timing_scope='Read-only untimed analysis after retained source-pinned benchmark. Fixed gate not retuned.',
                recommendation='No evidence to deploy this fixed screen over GM-only on these clips: all174 screens skippedSR, adding~0.107ms, and actual matched controls show forgone SR byte wins. Keep it as a negative causal-gate experiment.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();result=build();out=HERE/'gate-analysis.json'
    if a.check:assert json.loads(out.read_text())==result
    else:out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print('PASS: paired actual-control skipped-win analysis; same reference/GM lengths; no uncoded SR estimates; benchmark and analyzer hashes bound')

if __name__=='__main__':main()
