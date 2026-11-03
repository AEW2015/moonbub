#!/usr/bin/env python3
"""Small derived summary of stored GM01 controller results, no codec rerun."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    path=HERE/'results.json';doc=json.loads(path.read_text())
    sequence=[];captures=admitted=dropped=attempts=0
    for scene in doc['scenes']:
        policy_rows={}
        for policy,case in scene['cases'].items():
            rows=case['rows'];captures+=len(rows);admitted+=case['admitted'];dropped+=case['dropped']
            attempts+=sum(len(r['attempts']) for r in rows)
            policy_rows[policy]={key:case[key] for key in ('admitted','dropped','fallback_count','two_attempt_calls','service_ms','packet_bytes','accepted_calls_over_33_333_ms')}
        a,b=scene['cases']['uniform'],scene['cases']['priority']
        sequence.append({'name':scene['name'],'policies':policy_rows,
                         'priority_byte_ratio_to_uniform':None if not a['packet_bytes'] else b['packet_bytes']/a['packet_bytes'],
                         'common_ids':scene['comparison']['common_admitted_ids'],
                         'priority_minus_uniform_psnr_db':scene['comparison']['priority_minus_uniform_psnr_db']})
    pairs=[]
    for case in doc['paired_keys']:
        a,b=case['naive_ms']['mean'],case['shared_ms']['mean']
        pairs.append({'name':case['name'],'paired_keys':case['checks'],
                      'naive_mean_ms':a,'shared_mean_ms':b,'fraction_lower_service':1-b/a,
                      'two_attempt_pairs':case['two_attempt_pairs'],
                      'admitted_pairs':case['admitted_pairs'],
                      'shared_over_33_333_ms':sum(r['shared_service_ms']>1000/30 for r in case['records']),
                      'naive_over_33_333_ms':sum(r['naive_service_ms']>1000/30 for r in case['records']),
                      'shared_p95_ms':case['shared_ms']['p95'],'shared_max_ms':case['shared_ms']['max']})
    result={'evidence':'Derived stored controller summary, not another encode or real-time run',
            'source_sha256':{str(HERE/'analysis.py'):hashlib.sha256((HERE/'analysis.py').read_bytes()).hexdigest()},
            'results_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'sequence_cases':len(sequence)*2,'capture_policy_evaluations':captures,'admitted':admitted,'rejected':dropped,
            'actual_sequence_candidate_evaluations':attempts,'scenes':sequence,'paired_keys':pairs,
            'scope':'Equalcap does not mean equalrate/quality; sourceIDs and every attempt/drop remain explicit. Pressurekey fixtureisnotnominal48KiBstream.'}
    (HERE/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('sequence_cases','capture_policy_evaluations','admitted','rejected','actual_sequence_candidate_evaluations')},indent=2))
    for case in pairs:print(case)


if __name__=='__main__':main()
