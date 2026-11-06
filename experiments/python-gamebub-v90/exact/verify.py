#!/usr/bin/env python3
"""Independent actual-work, row/oracle and retained-DAG audit for V90."""
import gzip,hashlib,importlib.util,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
SELECTED={(0,0),(0,1),(0,3),(3,50)}
FETCH={'stream_bytes','raw_bytes','header_bytes','crc_bytes'}
LOW=dict(decisions=2,renorm=2,stream_bytes=2,rice_values=1,events=1,raw_bytes=2,header_bytes=2,crc_bytes=2,emits=1,raw_bits=1,prob_init=1,plain_bits=1)
HIGH=dict(decisions=4,renorm=4,stream_bytes=4,rice_values=1,events=1,raw_bytes=4,header_bytes=4,crc_bytes=4,emits=1,raw_bits=2,prob_init=1,plain_bits=2)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def stats(v):return dict(min=min(v),median=statistics.median(v),max=max(v),total=sum(v))


def main():
    selected=AREA/'results.json';report=json.loads(selected.read_text());attempt=ROOT/report['selected_report']
    assert report==dict(json.loads(attempt.read_text()),selected_report=report['selected_report'])
    assert report['status']=='PASS_EXHAUSTIVE_SELECTED_CAUSAL_TIMING'
    assert (report['unique_sources'],report['schedules'])==(4,64)
    bindings={str(p.relative_to(ROOT)):sha(p)for p in (selected,attempt,Path(__file__).resolve())}
    for name,digest in report['source_sha256'].items():assert sha(ROOT/name)==digest;bindings[name]=digest
    for name,digest in report['artifacts_sha256'].items():
        p=attempt.parent/name;assert sha(p)==digest;bindings[str(p.relative_to(ROOT))]=digest
    rows=list(map(json.loads,attempt.with_name('rows.jsonl').read_text().splitlines()))
    keyed={(r['cohort'],r['fid'],r['mask'],r['cost']):r for r in rows}
    assert len(rows)==len(keyed)==64
    assert set(keyed)=={(*source,mask,cost)for source in SELECTED for mask in range(8)for cost in ('LOW','HIGH')}
    data=load('v90_independent_observations',ROOT/'experiments/python-gamebub-v90/policy/data.py')
    observed={(r['cohort'],r['fid'],r['mask']):r for group in data.iter_masks(masks=range(8),only=SELECTED)for r in group}
    assert len(observed)==32
    auditor=load('v90_independent_stored_dags',ROOT/'scripts/cu66-v87/audit_coupled.py')
    witnesses=[]
    for r in rows:
        frame=observed[r['cohort'],r['fid'],r['mask']]
        assert r['packet_sha256']==frame['packet_sha256'] and r['wire_bytes']==frame['wire_bytes'] and r['metadata_bytes']==frame['metadata_bytes']
        assert r['observation_work_sha256']==frame['work_sha256'] and r['fits_49152']==(r['wire_bytes']<=49152)
        weights=LOW if r['cost']=='LOW' else HIGH
        fetch=frame['wire_bytes']*weights['crc_bytes']+frame['metadata_bytes']*weights['header_bytes']
        fetch+=sum(v*weights[k]for work in frame['shared_work']for k,v in work.items()if k!='emits')
        arithmetic=0
        for tile in frame['context_work']:
            for ctx in tile:
                for k,v in ctx.items():
                    if k in FETCH:fetch+=v*weights[k]
                    else:arithmetic+=v*weights[k]
        emit=sum(work.get('emits',0)*weights['emits']for work in frame['shared_work'])
        assert r['producer_work_cycles']==dict(fetch=fetch,arithmetic=arithmetic,emit=emit)
        assert r['decode_cycles']/100000==r['conditional_decode_ms']
        assert r['full_gather_cycles']/100000==r['conditional_base_gather_complete_ms']
        assert r['decode_cycles']<=r['full_gather_cycles']
        a=r['independent_audit'];assert a['finish_cycles']==r['full_gather_cycles'] and a['timeline_sha256']==r['timeline_sha256']
        assert a['resource_work_cycles']['memory']==r['memory_work_cycles']
        assert {k:a['resource_work_cycles'][k]for k in ('fetch','arithmetic','emit')}==r['producer_work_cycles']
        assert a['complete_fence_covers_all_jobs'] and a['context_order_and_consumer_release']
        for stage in ('reference','inverse','coefficients'):assert r['credit_peaks'][stage]['peak_reserved_slots']<=8
        if 'witness'in r:
            p=ROOT/r['witness'];assert sha(p)==r['witness_sha256']
            with gzip.open(p,'rt')as f:w=json.load(f)
            checked=auditor.verify(w['workload'],w['result']['timeline'],w['capacities'],w['windows'])
            assert checked==a
            witnesses.append(dict(path=r['witness'],sha256=sha(p),timeline_sha256=checked['timeline_sha256'],finish_cycles=checked['finish_cycles']))
    assert len(witnesses)==16
    old=json.loads((ROOT/'experiments/python-gamebub-v89/joint/results.json').read_text())
    oldrows=list(map(json.loads,(ROOT/old['selected_report']).with_name('rows.jsonl').read_text().splitlines()))
    matches=0
    for oldrow in oldrows:
        if not oldrow['alias']:continue
        r=keyed[oldrow['cohort'],oldrow['fid'],oldrow['mask'],oldrow['cost']]
        for field in ('decode_cycles','full_gather_cycles','packet_sha256','wire_bytes','observation_work_sha256','timeline_sha256'):assert r[field]==oldrow[field]
        matches+=1
    assert matches==len(report['unchanged_V89_control_matches'])==32
    unique_controls=len({(r['cohort'],r['fid'],r['mask'],r['cost'])for r in oldrows if r['alias']})
    oracle=[]
    for source in sorted(SELECTED):
        for cost in ('LOW','HIGH'):
            feasible=[r for r in rows if (r['cohort'],r['fid'],r['cost'])==(*source,cost)and r['wire_bytes']<=49152]
            best=min(feasible,key=lambda r:(r['decode_cycles'],r['wire_bytes'],r['mask']))
            saved=next(r for r in report['exact_oracles']if(r['cohort'],r['fid'],r['cost'])==(*source,cost))
            assert (best['mask'],best['decode_cycles'],best['wire_bytes'],best['packet_sha256'])==(saved['best_mask'],saved['decode_cycles'],saved['wire_bytes'],saved['packet_sha256'])
            assert saved['conditional_under10ms']==(best['decode_cycles']<1000000)
            oracle.append(saved)
    for s in report['summary_by_cost']:
        selected_oracles=[r for r in oracle if r['cost']==s['cost']]
        assert s['best_conditional_decode_ms']==stats([r['conditional_decode_ms']for r in selected_oracles])
        assert s['best_under10ms']==sum(r['conditional_under10ms']for r in selected_oracles)
    result=dict(schema='cu66-v90-exact-independent-audit-v1',status='PASS_ALL_MASK_WORK_ORACLES_AND_RETAINED_DAGS',unique_sources=4,schedules=64,
        actual_masks_observed=32,unchanged_V89_matches=32,unchanged_V89_unique_cases=unique_controls,independent_retained_witnesses=16,exact_oracles=oracle,
        source_sha256=bindings,scope='Offline selected-source exhaustive model. Costs are assumptions, and current timing fences omit qualified physical/HUD/display/ESP32 work.')
    (AREA/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('V90_EXACT_AUDIT_PASS sources=4 schedules=64 witnesses=16 controls=32')


if __name__=='__main__':main()
