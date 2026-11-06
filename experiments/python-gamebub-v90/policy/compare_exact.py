#!/usr/bin/env python3
"""Prospective frozen proxy versus exhaustive selected-source timing oracles."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(v):return dict(min=min(v),median=statistics.median(v),max=max(v),total=sum(v))


def main():
    selected=AREA/'results.json';p=json.loads(selected.read_text());pr=ROOT/p['selected_report']
    exact_path=ROOT/'experiments/python-gamebub-v90/exact/results.json';e=json.loads(exact_path.read_text());er=ROOT/e['selected_report']
    assert e['status']=='PASS_EXHAUSTIVE_SELECTED_CAUSAL_TIMING' and e['schedules']==64
    candidates=[json.loads(l)for l in pr.with_name('candidates.jsonl').read_text().splitlines()]
    decisions=[json.loads(l)for l in pr.with_name('selections.jsonl').read_text().splitlines()]
    rows=[json.loads(l)for l in er.with_name('rows.jsonl').read_text().splitlines()]
    feature={(r['cohort'],r['fid'],r['mask']):r for r in candidates}
    decision={(r['cohort'],r['fid'],r['cost']):r for r in decisions}
    actual={(r['cohort'],r['fid'],r['mask'],r['cost']):r for r in rows}
    assert len(actual)==64
    floor_slack=[];all_score_errors=[];floor_pass_actual_not=score_pass_actual_not=0
    for row in rows:
        r=feature[row['cohort'],row['fid'],row['mask']];f=r['costs'][row['cost']]
        assert r['packet_sha256']==row['packet_sha256'] and r['wire_bytes']==row['wire_bytes']
        assert f['necessary_work_floor_cycles']<=row['decode_cycles'],'necessary work floor is not conservative for the assumed graph'
        floor_slack.append(row['decode_cycles']-f['necessary_work_floor_cycles'])
        all_score_errors.append(f['resource_score_cycles']-row['decode_cycles'])
        floor_pass_actual_not+=int(f['necessary_work_floor_cycles']<1000000 and row['decode_cycles']>=1000000)
        score_pass_actual_not+=int(f['resource_score_cycles']<1000000 and row['decode_cycles']>=1000000)
    comparisons=[]
    for oracle in e['exact_oracles']:
        key=oracle['cohort'],oracle['fid'],oracle['cost'];d=decision[key]
        ar=actual[key[0],key[1],d['mask'],key[2]]
        assert ar['fits_49152'] and d['packet_sha256']==ar['packet_sha256']
        regret=ar['decode_cycles']-oracle['decode_cycles'];assert regret>=0
        comparisons.append(dict(cohort=key[0],fid=key[1],cost=key[2],proxy_mask=d['mask'],oracle_mask=oracle['best_mask'],
                                proxy_packet_sha256=d['packet_sha256'],oracle_packet_sha256=oracle['packet_sha256'],
                                proxy_actual_decode_cycles=ar['decode_cycles'],oracle_decode_cycles=oracle['decode_cycles'],regret_cycles=regret,
                                proxy_actual_ms=ar['conditional_decode_ms'],oracle_ms=oracle['conditional_decode_ms'],
                                resource_score_cycles=d['resource_score_cycles'],necessary_floor_cycles=d['necessary_work_floor_cycles'],
                                score_under10ms=d['resource_score_cycles']<1000000,necessary_floor_under10ms=d['necessary_work_floor_cycles']<1000000,
                                proxy_actual_under10ms=ar['decode_cycles']<1000000,oracle_actual_under10ms=oracle['decode_cycles']<1000000))
    summaries=[]
    for cost in ('LOW','HIGH'):
        group=[r for r in comparisons if r['cost']==cost]
        summaries.append(dict(cost=cost,sources=4,regret_cycles=stats([r['regret_cycles']for r in group]),
                              proxy_matches_oracle=sum(r['regret_cycles']==0 for r in group),
                              proxy_actual_under10ms=sum(r['proxy_actual_under10ms']for r in group),
                              oracle_actual_under10ms=sum(r['oracle_actual_under10ms']for r in group),
                              score_under10_actual_not=sum(r['score_under10ms']and not r['proxy_actual_under10ms']for r in group),
                              necessary_floor_pass_actual_not=sum(r['necessary_floor_under10ms']and not r['proxy_actual_under10ms']for r in group)))
    sources=[Path(__file__).resolve(),AREA/'model.py',selected,pr,pr.with_name('candidates.jsonl'),pr.with_name('selections.jsonl'),exact_path,er,er.with_name('rows.jsonl')]
    output=dict(schema='cu66-v90-frozen-proxy-exact-comparison-v1',status='PASS_EXHAUSTIVE_COMPARISON_NOT_A_DEADLINE_PROOF',
                source_sha256={str(p.relative_to(ROOT)):sha(p)for p in sources},exact_candidate_rows=64,source_cost_pairs=8,comparisons=comparisons,summaries=summaries,
                necessary_floor_slack_cycles=stats(floor_slack),serial_score_error_cycles=stats(all_score_errors),
                all64_necessary_floor_pass_actual_not=floor_pass_actual_not,all64_score_pass_actual_not=score_pass_actual_not,
                scope=['Proxy model frozen before these exact results. No parameters or choices fitted afterward.',
                       'Exact oracle is exhaustive only over8masks on4selectedsources and hypotheticalcosts, not a livehostpolicy orfullcorpus timing proof.',
                       'Necessary-floor passing is not a classification of deadline success; score may under- or over-estimate completion.',
                       'Absolute49152cap enforced independently of relativeoverhead; hardware30fps/fullvalidatedunder10ms remainopen.'])
    (AREA/'exact-comparison.json').write_text(json.dumps(output,indent=2)+'\n');print(output['status'],summaries)


if __name__=='__main__':main()
