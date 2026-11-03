#!/usr/bin/env python3
"""Compact source-bound summaries; common source IDs are explicit."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    path=HERE/'results.json';doc=json.loads(path.read_text());cases=[]
    for case in doc['cases']:
        r=case['result']
        cases.append(dict(name=case['name'],kind=case['kind'],controller=r['config']['controller'],
                          decoder_service=r['config']['decoder_service'],captures=r['capture_count'],prepared=r['prepared'],
                          strict=r['presented_strict'],eventual=r['presented_eventual'],
                          diagnostic_ids_per_second=r['metrics']['steady_fps'],age_p95_ms=r['metrics']['age_p95_ms'],
                          encode_services=r['service_summary'],drops=r['drops_by_reason'],
                          forward_bytes=r['forward_ipv4_udp_bytes'],feedback_bytes=r['feedback_ipv4_udp_bytes']))
    comparisons=[]
    for label in sorted({c['name'] for c in doc['cases'] if c['kind']=='baseline'}):
        for decoder in ('assumed','python_wall'):
            pair={c['result']['config']['controller']:c for c in doc['cases'] if c['name']==label and c['kind']=='baseline' and c['result']['config']['decoder_service']==decoder}
            a,b=pair['normal']['result'],pair['gate']['result']
            left={r['id'] for r in a['presented']};right={r['id'] for r in b['presented']};common=sorted(left&right)
            qa={r['id']:r['active_rgb565_mse'] for r in a['commits']};qb={r['id']:r['active_rgb565_mse'] for r in b['commits']}
            comparisons.append(dict(name=label,decoder_service=decoder,common_presented_ids=common,
                                    normal_only_ids=sorted(left-right),gate_only_ids=sorted(right-left),
                                    same_presented_ids=left==right,
                                    common_active_mse_delta_gate_minus_normal_mean=sum(qb[i]-qa[i] for i in common)/len(common) if common else None,
                                    scope='Different endogenous services/reference histories can change selected IDs/pixels; no equal-quality rate claim.'))
    result={'evidence':'Derived stored finite-pipeline summaries, not another timing or hardware run',
            'source_sha256':{str(HERE/'analysis.py'):hashlib.sha256((HERE/'analysis.py').read_bytes()).hexdigest()},
            'results_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cases':cases,'normal_gate_comparisons':comparisons}
    (HERE/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    for c in cases:print(c['name'],c['kind'],c['controller'],c['decoder_service'],c['strict'],c['eventual'],c['diagnostic_ids_per_second'],c['age_p95_ms'])


if __name__=='__main__':main()
