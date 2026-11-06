#!/usr/bin/env python3
"""Independent retained-row/source audit for a complete coupled-model session."""
from __future__ import annotations
import argparse,gzip,hashlib,importlib.util,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(values):return dict(min=min(values),median=statistics.median(values),max=max(values),total=sum(values))

def verify(session):
 session=Path(session);session=session if session.is_absolute() else ROOT/session
 run=json.loads((session/'results.json').read_text());assert run['status']=='PASS'
 assert len(run['cohorts'])==4 and {r['cohort'] for r in run['cohorts']}==set(range(4))
 wirepath=ROOT/'experiments/python-gamebub-v86/wire-attempts/20261106T135235884295Z-2a73a26a/frames.jsonl'
 wire={(r['cohort'],r['fid']):r for r in map(json.loads,wirepath.read_text().splitlines()) if r['configuration']=='copy_group_cap65536'}
 ctxpath=ROOT/'experiments/python-gamebub-v86/contexts/index.json'
 contexts={(r['cohort'],r['fid']):r for r in json.loads(ctxpath.read_text())['frames'] if r['cap']==65536}
 oldpath=ROOT/'experiments/python-gamebub-v84/summary.json'
 oldsummary=json.loads(oldpath.read_text());frozen={};oldbindings={str(oldpath.relative_to(ROOT)):sha(oldpath)}
 for name,digest in oldsummary['evidence_sha256'].items():
  if name.endswith('/results.json'):
   reportpath=ROOT/name;assert sha(reportpath)==digest
   oldreport=json.loads(reportpath.read_text());assert oldreport['status']=='PASS_CONDITIONAL_COHORT_SCHEDULES'
   path=reportpath.with_name('frames.jsonl');assert sha(path)==oldreport['artifacts_sha256']['frames.jsonl']
   oldbindings[str(reportpath.relative_to(ROOT))]=digest;oldbindings[str(path.relative_to(ROOT))]=sha(path)
   for row in map(json.loads,path.read_text().splitlines()):
    if row['configuration']=='credits8_zero_arrival':
     key=row['cohort'],row['fid'];assert key not in frozen;frozen[key]=row['finish_cycles']
 assert len(frozen)==457
 assert len(wire)==len(contexts)==457 and set(wire)==set(contexts)==set(frozen)
 rows=[];bindings={str((session/'results.json').relative_to(ROOT)):sha(session/'results.json'),str(wirepath.relative_to(ROOT)):sha(wirepath),str(ctxpath.relative_to(ROOT)):sha(ctxpath)}
 bindings.update(oldbindings)
 sources={};configs=None
 for child in run['cohorts']:
  assert child['exit_code']==0
  log=ROOT/child['log'];assert sha(log)==child['log_sha256'];bindings[str(log.relative_to(ROOT))]=sha(log)
  path=ROOT/child['report'];report=json.loads(path.read_text());assert report['status']=='PASS_CONDITIONAL_COHORT_COUPLING' and report['smoke_limit']==0
  assert report['native_sources']==(119,119,119,100)[child['cohort']]
  configs=report['configurations'] if configs is None else configs;assert configs==report['configurations']
  bindings[str(path.relative_to(ROOT))]=sha(path)
  for name,digest in report['source_sha256'].items():assert sha(ROOT/name)==digest;sources[name]=digest
  for name,digest in report['artifacts_sha256'].items():
   artifact=path.parent/name;assert sha(artifact)==digest;bindings[str(artifact.relative_to(ROOT))]=digest
  selected=list(map(json.loads,path.with_name('rows.jsonl').read_text().splitlines()));assert len(selected)==report['schedules']==report['native_sources']*6
  assert len({(r['configuration'],r['cohort'],r['fid']) for r in selected})==len(selected)
  assert {r['cohort'] for r in selected}=={child['cohort']}
  for c in configs:
   group=[r for r in selected if r['configuration']==c['name']];entry=next(r for r in report['summaries'] if r['configuration']==c['name'])
   assert entry['sources']==len(group)==report['native_sources']
   assert entry['model_ms']==stats([r['model_ms'] for r in group])
  rows+=selected
 assert len(rows)==2742 and run['schedules']==2742 and run['native_sources']==457
 by_id={(r['configuration'],r['cohort'],r['fid']):r for r in rows};configuration_names={c['name'] for c in configs}
 assert {r['configuration'] for r in rows}==configuration_names
 for row in rows:
  key=row['cohort'],row['fid'];w=wire[key];obs=contexts[key];config=next(c for c in configs if c['name']==row['configuration'])
  assert row['context_work_sha256']==obs['work_sha256'] and row['CS86_packet_sha256']==w['packet_sha256']
  assert row['wire_bytes']==w['wire_bytes']
  assert row['metadata_bytes']==sum(w['components'][k] for k in ('header','mode_body','qmap','chunk_directory'))
  for name in ('canonical_sha256','hud_sha256','display_sha256','root','seal'):assert row[name]==w['decoded'][name]
  assert row['ordinal']==obs['ordinal'] and row['key']==obs['key']
  assert row['model_ms']==row['finish_cycles']*1e-5
  assert row['finish_cycles']==row['audit']['finish_cycles']
  assert row['frontend']['all_tasks_in_completion_fence'] is True
  assert row['frontend']['coefficient_peak_slots']==row['credits']['coefficients']['peak_reserved_slots']<=8
  for stage in ('reference','inverse','coefficients'):assert row['credits'][stage]['peak_reserved_slots']<=8
  assert row['audit']['group_peak']<=4
  assert row['audit']['resource_work_cycles']['memory']==row['memory_work_cycles']
  for resource,work in row['frontend']['frontend_work_cycles'].items():assert row['audit']['resource_work_cycles'].get(resource,0)==work
  fetch_fields={'stream_bytes','raw_bytes','header_bytes','crc_bytes'}
  weights=config['weights'];expected_fetch=row['wire_bytes']*weights['crc_bytes']+row['metadata_bytes']*weights['header_bytes']
  expected_fetch+=sum(v*weights[k] for k,v in obs['shared_totals'].items() if k!='emits')
  expected_fetch+=sum(v*weights[k] for context in obs['context_totals'] for k,v in context.items() if k in fetch_fields)
  expected_arithmetic=sum(v*weights[k] for context in obs['context_totals'] for k,v in context.items() if k not in fetch_fields)
  expected_emit=obs['shared_totals']['emits']*weights['emits']
  assert row['frontend']['frontend_work_cycles']==dict(fetch=expected_fetch,arithmetic=expected_arithmetic,emit=expected_emit)
  residuals=row['credits']['inverse']['reservations']
  assert row['audit']['resource_work_cycles'].get('dequant',0)==residuals*config['dequant']
  assert row['audit']['resource_work_cycles'].get('inverse',0)==row['audit']['resource_work_cycles'].get('reconstruct',0)==residuals*64
  assert row['audit']['resource_peak'].get('arithmetic',0)<=config['lanes']
  if row['configuration']=='zero_front_control':assert row['finish_cycles']==frozen[key]
  else:assert row['memory_work_cycles']==by_id['zero_front_control',*key]['memory_work_cycles']
 summaries=[]
 for config in configs:
  group=[r for r in rows if r['configuration']==config['name']]
  entry=dict(configuration=config['name'],sources=len(group),model_ms=stats([r['model_ms'] for r in group]),conditional_under10ms=sum(r['finish_cycles']<1000000 for r in group),conditional_within30fps_period=sum(r['finish_cycles']*30<=100000000 for r in group))
  assert entry==next(r for r in run['summaries'] if r['configuration']==config['name']);summaries.append(entry)
 comparison={}
 for cost in ('low','high'):
  gains=[by_id[f'{cost}_lanes1',*key]['finish_cycles']-by_id[f'{cost}_lanes2',*key]['finish_cycles'] for key in wire]
  comparison[cost]=dict(saved_cycles=stats(gains),improved=sum(v>0 for v in gains),equal=sum(v==0 for v in gains),regressed=sum(v<0 for v in gains))
 probe_path=AREA/'memory-probe.json';probe=json.loads(probe_path.read_text())
 assert probe['status']=='PASS_FOUR_CONDITIONAL_WITNESS_REPLAYS' and probe['unique_sources']==1 and probe['schedules']==4
 bindings[str(probe_path.relative_to(ROOT))]=sha(probe_path)
 assert sha(ROOT/probe['selected_attempt'])==probe['selected_attempt_sha256'];bindings[probe['selected_attempt']]=probe['selected_attempt_sha256']
 for name,digest in probe['source_sha256'].items():assert sha(ROOT/name)==digest;sources[name]=digest
 audit_path=ROOT/'scripts/cu66-v87/audit_coupled.py';spec=importlib.util.spec_from_file_location('cu87_probe_independent_audit',audit_path);auditor=importlib.util.module_from_spec(spec);sys.modules[spec.name]=auditor;spec.loader.exec_module(auditor)
 probe_checks=[]
 for row in probe['rows']:
  witness=ROOT/row['witness'];assert sha(witness)==row['witness_sha256'];bindings[row['witness']]=row['witness_sha256']
  with gzip.open(witness,'rt') as f:data=json.load(f)
  assert (row['cohort'],row['fid'],row['lanes'],row['read_service'],row['write_service'])==(3,50,2,12,12)
  assert data['read_service']==data['write_service']==12
  expected_window=dict(period=10000,blocked=[(0,2000)]) if row['reserved20'] else None
  assert data['windows']==expected_window
  originalpath=ROOT/data['source_witness'];assert str(originalpath.relative_to(ROOT)) in probe['source_sha256']
  with gzip.open(originalpath,'rt') as f:original=json.load(f)
  assert data['capacities']==original['capacities']
  assert original['config']['name']==row['cost'].lower()+'_lanes2'
  jobs=data['workload']['jobs'];oldjobs=original['workload']['jobs'];assert len(jobs)==len(oldjobs)
  for job,old in zip(jobs,oldjobs,strict=True):
   changed=dict(old)
   if old['resource']=='memory':changed['duration']=old['BL8']*12
   assert job==changed,'probe changed more than memory interval'
  assert hashlib.sha256(json.dumps(data['workload'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==row['mutated_workload_sha256']
  timeline=data['result']['timeline'];assert hashlib.sha256(json.dumps(timeline,sort_keys=True,separators=(',',':')).encode()).hexdigest()==row['timeline_sha256']
  checked=auditor.verify(data['workload'],timeline,data['capacities'],data['windows'])
  assert checked==row['independent_audit']==data['audit']
  assert row['finish_cycles']==data['result']['finish_cycles'] and row['model_ms']==row['finish_cycles']*1e-5
  probe_checks.append(dict(cost=row['cost'],reserved20=row['reserved20'],model_ms=row['model_ms']))
 return dict(schema='cu66-v87-coupled-results-audit-v1',status='PASS_RETAINED_ROWS_AND_FROZEN_ZERO_CONTROL',native_sources=457,schedules=2742,
  frozen_zero_front_exact_matches=457,memory_probe_unique_sources=1,memory_probe_schedules=4,memory_probe_reaudits=probe_checks,summaries=summaries,two_lane_paired_comparison=comparison,artifact_sha256=bindings,source_sha256=sources,
  audit_script_sha256=sha(Path(__file__)),scope='Source/row/summary/identity audit; each schedule has in-process timeline and credit checks. Representative full DAGs have separate independent timeline audits. No physical timing proof.')

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--session',required=True);parser.add_argument('--output',default=str(AREA/'verification.json'));args=parser.parse_args()
 result=verify(args.session);path=Path(args.output)
 if path.exists():assert json.loads(path.read_text())==result,'retained verification differs'
 else:path.write_text(json.dumps(result,indent=2)+'\n')
 print('COUPLED_RESULTS_AUDIT_PASS',result['native_sources'],result['schedules'])
if __name__=='__main__':main()
