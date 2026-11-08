#!/usr/bin/env python3
"""Summarize actual RTL counters; do not call these calibrated hardware latency."""
import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v109'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(xs):
    xs=sorted(xs)
    return dict(n=len(xs),min=xs[0],median=statistics.median(xs),p95=xs[math.ceil(.95*len(xs))-1],p99=xs[math.ceil(.99*len(xs))-1],max=xs[-1],strictly_below_1000000=sum(x<1000000 for x in xs))

def main():
    rows=[];inputs={}
    cases=[('fault','canonical/fault'),('combined','canonical/combined'),
           ('fault-fetch','canonical-fetch/fault'),('combined-fetch','canonical-fetch/combined'),
           ('fault-request','canonical-request/fault'),('combined-request','canonical-request/combined')]
    for variant,directory in cases:
        p=AREA/directory/'results.json'
        if not p.exists():continue
        q=json.loads(p.read_text())
        assert q['status']=='PASS_EXACT_V109_CANONICAL' and q['actual_RTL_run']
        receipt=ROOT/q['selected_receipt'];inputs[str(p.relative_to(ROOT))]=sha(p)
        for run in q['runs']:
            transcript=receipt.parent/('candidate-'+str(run['seed'])+'-simulation.jsonl')
            assert q['artifact_sha256'][transcript.name]==sha(transcript)
            for line in transcript.read_text().splitlines():
                x=json.loads(line)
                if x['type']!='case' or x['error']!=0:continue
                assert x['status']=='PASS' and x['done_cycle']>=x['last_input'] and not x['full_frame_publication']
                rows.append(dict(variant=variant,seed=run['seed'],id=x['id'],memory_profile=x['memory_profile'],start_to_case_finish_cycles=x['cycles'],post_last_input_to_done_cycles=x['done_cycle']-x['last_input'],cache_preload_cycles=x['cache_cycles'],canonical_samples=x['canonical']['samples']))
    assert rows
    groups={}
    for variant in sorted({x['variant'] for x in rows}):
        groups[variant]={}
        for profile in (0,1):
            subset=[r for r in rows if r['variant']==variant and r['memory_profile']==profile]
            groups[variant][str(profile)]={key:stats([x[key] for x in subset]) for key in ('start_to_case_finish_cycles','post_last_input_to_done_cycles')}
    routes=[json.loads(p.read_text()) for p in (AREA/'native').glob('*/receipt.json')]
    qualified=[]
    for d in routes:
        if (d.get('result') or {}).get('component_internal_100MHz_pass') and d.get('clean_repeat_of'):
            prior=ROOT/d['clean_repeat_of']['path']
            assert sha(prior)==d['clean_repeat_of']['sha256']
            parent=json.loads(prior.read_text())
            if parent['result']['component_internal_100MHz_pass'] and parent['source_sha256']==d['source_sha256']:
                qualified.append(d['source_contract']['canonical_qualification'])
    data=dict(schema='v109-actual-RTL-cycle-budget-v1',status='RTL_COUNTER_SUMMARY_NOT_HARDWARE_CALIBRATION',inputs=inputs,rows=rows,groups=groups,
              assumed_budget_clock_Hz=100000000,strict_10ms_budget_cycles=1000000,component_100MHz_qualified=bool(qualified),component_100MHz_repeated_qualification_sources=qualified,hardware_30fps=False,validated_decode_latency_qualified=False,
              limits=['Case cycles start at start assertion and end after finish/drain; preload counted separately.',
                      'Last-input to component done is a counter proxy, not validated framebuffer publication.',
                      'Testbench CRC/hash/pixel comparisons and reference-memory helpers do not model full production service costs.',
                      'No achieved frequency, hardware FPS or hardware milliseconds are inferred.',
                      'Current zero-added-cycle variants intentionally preserve baseline counters.'])
    (AREA/'cycle-budget.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps(groups,sort_keys=True))

if __name__=='__main__':main()
