#!/usr/bin/env python3
"""Collect source-bound V116 observations; keep physical milestone gates explicit."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v116'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def pin(p):return dict(path=str(p.relative_to(ROOT)),sha256=sha(p))
def selector(p):
 q=load(p);name=q.get('selected_receipt',q.get('selected_report',q.get('path')))
 assert name
 raw=ROOT/name;r=load(raw)
 expected=q.get('selected_report_sha256',q.get('sha256'))
 if expected:assert sha(raw)==expected
 else:assert r=={k:v for k,v in q.items()if k!='selected_receipt'}
 return dict(selector=pin(p),receipt=pin(raw)),r
answer=dict(schema='v116-source-bound-measurements-v1',base_revision='c83718fa0f62c55f948bcc34b32481791d1859e6',policy=pin(AREA/'study-policy.json'),focused={},native=[],live=[],milestones=dict(sustained_hardware_30fps=False,hardware_validated_decode_under10ms=False,full_parent_routed_clock_qualified=False,production_Sunshine_ESP32_endpoint_integrated=False))
for name in ['rice','admission','rowjoin','control-b','domain-b','record-c','spatial','control-peer','live-parent']:
 p=AREA/name/'results.json'
 if not p.exists():continue
 pins,r=selector(p);entry=dict(pins,status=r['status'],actual_RTL_run=r.get('actual_RTL_run',False))
 if name in ('rice','admission','rowjoin'):entry['runs']=r.get('runs',r.get('parser_runs',[]));entry['ingress_runs']=r.get('ingress_runs',[])
 if name=='spatial':entry.update(case_profiles=r.get('newly_executed_candidate_case_profiles'),directed_checks=r.get('newly_executed_candidate_directed_checks'),transport_runs=len(r.get('transport_runs',[])))
 answer['focused'][name]=entry
 if name=='live-parent':
  for run in r.get('runs',[]):
   c=run['live_case'];row=dict(variant=run['variant'],profile=run['profile'],seed=run['seed'],source_receipt=pins['receipt'],live_case=c,fences=run.get('fences',{}),service=run['service'],conditional_only=True)
   row['conditional125_last_input_to_commit_ms']=c['last_outer_to_commit_cycles']/125000
   row['strict125_cycle_budget_only']=c['last_outer_to_commit_cycles']<1250000
   row['scope']='Actual RTL simulation with abstract bounded memory/publication; complete parent achieved frequency and hardware remain unqualified.'
   answer['live'].append(row)
answer['additional_compositions']={}
for label,base in [('B',AREA/'control-b-study'),('C',AREA/'control-c-study')]:
 entries={}
 for name in ['spatial','control-peer','live-parent']:
  path=base/name/'results.json'
  if not path.exists():continue
  pins,raw=selector(path);entries[name]=dict(pins,status=raw['status'],actual_RTL_run=raw.get('actual_RTL_run',False),source_origins=raw.get('source_origins'))
  if name=='live-parent':
   entries[name]['initial_A_exact_parent_control']=raw.get('initial_A_exact_parent_control')
   for run in raw.get('runs',[]):
    c=run['live_case'];answer['live'].append(dict(composition=label,variant=run['variant'],profile=run['profile'],seed=run['seed'],source_receipt=pins['receipt'],live_case=c,fences=run.get('fences',{}),service=run['service'],conditional_only=True,conditional125_last_input_to_commit_ms=c['last_outer_to_commit_cycles']/125000,strict125_cycle_budget_only=c['last_outer_to_commit_cycles']<1250000,full_parent_achieved_clock_validated=False))
 if entries:answer['additional_compositions'][label]=entries
for p in sorted(AREA.glob('*/native/*/receipt.json')):
 q=load(p);answer['native'].append(dict(receipt=pin(p),status=q['status'],clock_period_ns=q['clock_period_ns'],result=q.get('result'),clean_repeat_of=q.get('clean_repeat_of'),source_sha256=q['source_contract']['source_sha256']))
answer['component_internal_positive_runs']=[x['receipt']for x in answer['native']if (x.get('result')or{}).get('component_internal_target_pass')]
answer['status']='V116_MEASURED_RESULTS_SEPARATE_OPEN_MILESTONES'
(AREA/'results.json').write_text(json.dumps(answer,sort_keys=True,indent=2)+'\n')
print(answer['status'],len(answer['native']),'native runs',len(answer['live']),'live cases')
