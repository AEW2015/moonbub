#!/usr/bin/env python3
"""Read stored operating points; distinguish matched IDs from matched bases."""
import hashlib
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent


def stats(values):
    return {'n':len(values),'mean':float(np.mean(values)) if values else None,
            'p95':float(np.percentile(values,95)) if values else None,'max':max(values) if values else None}


def main():
    path=HERE/'results.json';probe=HERE/'refresh-results.json'
    d=json.loads(path.read_text());p=json.loads(probe.read_text());rows=[]
    for origin,data in (('main',d),('refresh_probe',p)):
        for c in data['cases']:
            r=c['result'];packets=r['packets'];commits=r['commits']
            rows.append({'origin':origin,'source':c['source'],'kind':c['kind'],'width':c['coded_width'],
                'height':c['coded_height'],'target_ids_per_second':c['target_ids_per_second'],'mode':c['mode'],
                'strict':r['presented_strict'],'eventual':r['presented_eventual'],'diagnostic':r['metrics']['steady_fps'],
                'prepared':r['prepared'],'decodes':len(commits),'key_ids':[p['id'] for p in packets if p.get('key')],
                'packet_bytes':stats([p['bytes'] for p in packets]),'encode_ms':stats([p['encode_wall_ms'] for p in packets]),
                'decode_ms':stats([p['decode_wall_ms'] for p in packets if 'decode_wall_ms' in p]),
                'active_mse':stats([p['active_rgb565_mse'] for p in commits]),
                'selected_exact_pixels':stats([p['selected_pixels'] for p in commits]),
                'age_p95_ms':r['metrics']['age_p95_ms'],'forward_bytes_including_drain':r['forward_ipv4_udp_bytes'],
                'feedback_bytes_including_drain':r['feedback_ipv4_udp_bytes'],'drops':r['drops_by_reason']})
    comparisons=[]
    for c in p['cases']:
        base=next(x for x in d['cases'] if x['source']==c['source'] and x['kind']=='baseline' and x['coded_width']==512
                  and x['mode']=='adaptive_ui' and x['target_ids_per_second']==30)
        aa={r['id']:r for r in base['result']['commits']};bb={r['id']:r for r in c['result']['commits']};common=sorted(aa.keys()&bb.keys())
        ap={r['id']:r for r in base['result']['packets']};bp={r['id']:r for r in c['result']['packets']}
        comparisons.append({'source':c['source'],'common_decoded_ids':common,
            'same_inner_base_packet_ids':[i for i in common if aa[i]['inner_base_sha256']==bb[i]['inner_base_sha256']],
            'baseline_common_mean_bytes':float(np.mean([ap[i]['bytes'] for i in common])),
            'probe_common_mean_bytes':float(np.mean([bp[i]['bytes'] for i in common])),
            'baseline_common_mean_active_mse':float(np.mean([aa[i]['active_rgb565_mse'] for i in common])),
            'probe_common_mean_active_mse':float(np.mean([bb[i]['active_rgb565_mse'] for i in common])),
            'scope':'SamecapturedIDs, notnecessarilythesamereconstructedreference; keypolicy+remeasuredtimingconfound.'})
    out={'source_sha256':{str(HERE/'analyze.py'):hashlib.sha256((HERE/'analyze.py').read_bytes()).hexdigest()},
         'main_results_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'probe_results_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),
         'operating_points':rows,'refresh_comparisons':comparisons,
         'scope':'Derivedstoredoperatingpoints, notanothercodec/timing/hardwaremeasurement. Per-canvasqualityonly; no crossresolutionPSNRequivalence.'}
    (HERE/'comparison.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    for r in rows:print(r['source'],r['width'],r['target_ids_per_second'],r['mode'],r['kind'],r['strict'],r['eventual'],r['diagnostic'])


if __name__=='__main__':main()
