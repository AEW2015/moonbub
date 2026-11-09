#!/usr/bin/env python3
"""Retain a source-bound index of actual campaign failures, including pre-RTL errors."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];A=R/'experiments/python-gamebub-v120'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
negative_routes=[]
for p in sorted(set(A.rglob('receipt.json')) | {q for name in ('report.json','results.json') for q in A.rglob(name) if q.parent.parent.name=='attempts'}):
 if any(x in p.parts for x in ('sources','source-snapshot')):continue
 d=json.loads(p.read_text())
 if d.get('status')=='FAIL' and 'wall_seconds' not in d:continue  # initialized pessimistically; not a terminal failure
 if d.get('component_route_finished') and d.get('result',{}).get('component_internal_target_pass') is False:
  negative_routes.append(dict(path=str(p.relative_to(R)),sha256=sha(p),clock_period_ns=d['clock_period_ns'],timing=d['result']['timing']))
 if not (d.get('status')=='FAIL' or d.get('status','').endswith('FAILED')):continue
 rows.append(dict(path=str(p.relative_to(R)),sha256=sha(p),status=d['status'],actual_RTL_run=d.get('actual_RTL_run',False),error=d.get('error'),failed_commands=[dict(argv=c['argv'],exit_code=c['exit_code'])for c in d.get('commands',[])if isinstance(c,dict)and c.get('exit_code',0)!=0]))
(A/'orchestration').mkdir(exist_ok=True)
(A/'orchestration/failures.json').write_text(json.dumps(dict(schema='v120-preserved-failed-campaign-index-v1',failures=rows,negative_completed_native_routes=negative_routes),indent=2,sort_keys=True)+'\n')
print('Preserved failed campaigns',len(rows))
