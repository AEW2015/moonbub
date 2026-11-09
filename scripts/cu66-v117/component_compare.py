#!/usr/bin/env python3
"""Report actual body cycles; malformed partial-output counts are schedule-dependent."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v117'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(area,seed):
    p=AREA/area/'spatial/results.json';d=json.loads(p.read_text())
    assert d['status']=='PASS_V117_FINAL_SPATIAL_CANONICAL'
    raw=ROOT/d['selected_receipt'];assert json.loads(raw.read_text())=={k:v for k,v in d.items()if k!='selected_receipt'}
    p=raw.parent/f'candidate-{seed}-simulation.jsonl';assert sha(p)==d['artifact_sha256'][p.name]
    rows=[json.loads(x)for x in p.read_text().splitlines()]
    return {(x['id'],x['memory_profile']):x for x in rows if x.get('type')=='case'},dict(path=str(raw.relative_to(ROOT)),sha256=sha(raw))
def main():
    out=[];pins={}
    for seed in [107601,107602]:
        a,pins['A']=load('read-study',seed);b,pins['B']=load('throughput-study',seed);assert a.keys()==b.keys()
        for k,x in a.items():
            y=b[k];assert x['status']==y['status']and x['error']==y['error']
            if x['error']==0:assert x['canonical']['samples']==y['canonical']['samples']==518400
            out.append(dict(seed=seed,id=k[0],memory_profile=k[1],A_component_cycles=x['cycles'],B_component_cycles=y['cycles'],saved_cycles=x['cycles']-y['cycles'],percent_saved=100*(x['cycles']-y['cycles'])/x['cycles'],status=y['status'],error=y['error'],A_partial_or_complete_samples=x['canonical']['samples'],B_partial_or_complete_samples=y['canonical']['samples']))
    good=[x for x in out if x['error']==0]
    d=dict(schema='v117-observed-body-throughput-comparison-v1',status='PASS_SOURCE_BOUND_COMPONENT_CYCLE_COMPARISON',receipts=pins,rows=out,range_successful_component_cycle_savings_percent=[min(x['percent_saved']for x in good),max(x['percent_saved']for x in good)],scope='Actual component Bench cycles; no LIVE validation/wholeparent/nativeclock/hardwarefps/latency claim. Canonical byte equality independently bound by spatial receipts. Malformed partial-output count may differ under the declared schedule; it is not a successful frame or an exact partial-cycle claim.')
    (AREA/'component-cycle-comparison.json').write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
    print(d['status'],d['range_successful_component_cycle_savings_percent'],len(out))
if __name__=='__main__':main()
