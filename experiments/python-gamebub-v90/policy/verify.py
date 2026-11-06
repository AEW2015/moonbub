#!/usr/bin/env python3
"""Independent saved-row policy arithmetic and endpoint-observation audit."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
FETCH={'stream_bytes','raw_bytes','header_bytes','crc_bytes'}
LOW=dict(decisions=2,renorm=2,stream_bytes=2,rice_values=1,events=1,raw_bytes=2,header_bytes=2,crc_bytes=2,emits=1,raw_bits=1,prob_init=1,plain_bits=1)
HIGH=dict(decisions=4,renorm=4,stream_bytes=4,rice_values=1,events=1,raw_bytes=4,header_bytes=4,crc_bytes=4,emits=1,raw_bits=2,prob_init=1,plain_bits=2)


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(values):return dict(min=min(values),median=statistics.median(values),max=max(values),total=sum(values))


def main():
    root=AREA/'results.json';report=json.loads(root.read_text());path=ROOT/report['selected_report'];original=json.loads(path.read_text());assert report==dict(original,selected_report=report['selected_report'])
    assert report['status']=='PASS_ACTUAL_WORK_RESOURCE_SCORE_SELECTION'
    pins={str(root.relative_to(ROOT)):sha(root),str(path.relative_to(ROOT)):sha(path),str(Path(__file__).resolve().relative_to(ROOT)):sha(Path(__file__).resolve())}
    for name,digest in report['source_sha256'].items():assert sha(ROOT/name)==digest;pins[name]=digest
    for name,digest in report['artifacts_sha256'].items():
        p=path.parent/name;assert sha(p)==digest;pins[str(p.relative_to(ROOT))]=digest
    candidates=[json.loads(line)for line in path.with_name('candidates.jsonl').read_text().splitlines()]
    selections=[json.loads(line)for line in path.with_name('selections.jsonl').read_text().splitlines()]
    keyed={(r['cohort'],r['fid'],r['mask']):r for r in candidates};assert len(candidates)==len(keyed)==3656
    keys={(c,f)for c,f,m in keyed};assert len(keys)==457
    sel={(r['cohort'],r['fid'],r['cost']):r for r in selections};assert len(sel)==len(selections)==914
    obs={}
    for area,cap in [('experiments/python-gamebub-v86/contexts',65536),('experiments/python-gamebub-v89/observations',65536)]:
        index_path=ROOT/area/'index.json';index=json.loads(index_path.read_text());pins[str(index_path.relative_to(ROOT))]=sha(index_path)
        obs[area]={(r['cohort'],r['fid']):r for r in index['frames']if r['cap']==cap}
        assert len(obs[area])==457
    exact_endpoints=0
    for key in keys:
        assert {m for c,f,m in keyed if(c,f)==key}==set(range(8))
        for mask,source in [(0,obs['experiments/python-gamebub-v86/contexts'][key]),(7,obs['experiments/python-gamebub-v89/observations'][key])]:
            row=keyed[*key,mask]
            expected_shared=dict(source['shared_totals']);expected_shared.setdefault('plain_bits',0)
            expected_contexts=[dict(r,plain_bits=r.get('plain_bits',0))for r in source['context_totals']]
            assert row['shared_totals']==expected_shared and row['context_totals']==expected_contexts
            exact_endpoints+=1
    for row in candidates:
        for cost,w in [('LOW',LOW),('HIGH',HIGH)]:
            f=row['costs'][cost];shared=row['shared_totals'];contexts=row['context_totals']
            prefix=row['wire_bytes']*w['crc_bytes']+row['metadata_bytes']*w['header_bytes']
            inner=sum(v*w[k]for k,v in shared.items()if k!='emits')+sum(v*w[k]for c in contexts for k,v in c.items()if k in FETCH)
            compute=[sum(v*w[k]for k,v in c.items()if k not in FETCH)for c in contexts]
            parallel=max(max(compute),(sum(compute)+1)//2);emit=shared['emits']*w['emits']
            assert (f['prefix_cycles'],f['inner_fetch_cycles'],f['context_compute_cycles'],f['parallel_compute_cycles'],f['emission_cycles'])==(prefix,inner,compute,parallel,emit)
            assert f['resource_score_cycles']==prefix+f['decoder_memory_busy_cycles']+inner+parallel+emit
            assert f['necessary_work_floor_cycles']==max(prefix+max(f['decoder_memory_busy_cycles'],inner,parallel,emit,f['nominal_stage_work_cycles']),f['hash_work_cycles'])
    for c,f in keys:
        options=[keyed[c,f,m]for m in range(8)]
        for cost in ('LOW','HIGH'):
            feasible=[r for r in options if r['wire_bytes']<=49152];assert feasible
            winner=sorted(feasible,key=lambda r:(r['costs'][cost]['resource_score_cycles'],r['wire_bytes'],r['mask']))[0]
            chosen=sel[c,f,cost]
            assert (chosen['mask'],chosen['packet_sha256'],chosen['wire_bytes'])==(winner['mask'],winner['packet_sha256'],winner['wire_bytes'])
            assert all(chosen[k]==v for k,v in winner['costs'][cost].items())
    for cost in ('LOW','HIGH'):
        rr=[r for r in selections if r['cost']==cost];summary=next(s for s in report['summaries']if s['cost']==cost)
        assert summary['wire_bytes']==stats([r['wire_bytes']for r in rr])
        assert summary['resource_score_cycles']==stats([r['resource_score_cycles']for r in rr])
        assert summary['necessary_work_floor_cycles']==stats([r['necessary_work_floor_cycles']for r in rr])
        assert summary['selected_masks']=={str(m):sum(r['mask']==m for r in rr)for m in range(8)}
        assert summary['necessary_floor_strictly_under10ms']==sum(r['necessary_work_floor_cycles']<1000000 for r in rr)
    output=dict(schema='cu66-v90-policy-independent-audit-v1',status='PASS_SAVED_SCORE_SELECTION_AND_NATIVE_ENDPOINT_COUNTS',native_sources=457,candidate_records=3656,selected_records=914,endpoint_observation_records=exact_endpoints,
                source_sha256=pins,scope='Independent feature arithmetic, all cap/tie decisions and raw native endpoint totals; intermediate mixtures use producer plane extraction backed by layout tests. No completion-time accuracy claim.')
    (AREA/'verification.json').write_text(json.dumps(output,indent=2)+'\n');print(output['status'])


if __name__=='__main__':main()
