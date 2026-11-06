#!/usr/bin/env python3
"""Independent row, actual-work and retained-timeline audit for V89 joint data."""
import gzip,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
FETCH={'stream_bytes','raw_bytes','header_bytes','crc_bytes'}
LOW=dict(decisions=2,renorm=2,stream_bytes=2,rice_values=1,events=1,raw_bytes=2,header_bytes=2,crc_bytes=2,emits=1,raw_bits=1,prob_init=1,plain_bits=1)
HIGH=dict(decisions=4,renorm=4,stream_bytes=4,rice_values=1,events=1,raw_bytes=4,header_bytes=4,crc_bytes=4,emits=1,raw_bits=2,prob_init=1,plain_bits=2)
POLICIES=('AB38_control','feedback_overhead5','feedback_overhead15','all_BR88')
SELECTED={(0,0),(0,1),(0,3),(3,50)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def main():
 selected=AREA/'results.json';report=json.loads(selected.read_text());p=ROOT/report['selected_report'];original=json.loads(p.read_text())
 assert report==dict(original,selected_report=report['selected_report'])
 assert report['status']=='PASS_SELECTED_ACTUAL_JOINT_SCHEDULES' and report['unique_sources']==4 and report['schedules']==64
 bindings={str(selected.relative_to(ROOT)):sha(selected),str(p.relative_to(ROOT)):sha(p),str(Path(__file__).resolve().relative_to(ROOT)):sha(Path(__file__).resolve())}
 for name,digest in report['source_sha256'].items():assert sha(ROOT/name)==digest;bindings[name]=digest
 for name,digest in report['artifacts_sha256'].items():
  artifact=p.parent/name;assert sha(artifact)==digest;bindings[str(artifact.relative_to(ROOT))]=digest
 rows=list(map(json.loads,p.with_name('rows.jsonl').read_text().splitlines()));assert len(rows)==64
 keyed={(r['cohort'],r['fid'],r['policy'],r['cost'],r['alias']):r for r in rows}
 assert len(keyed)==64 and set(keyed)=={(*source,policy,cost,enabled)for source in SELECTED for policy in POLICIES for cost in ('LOW','HIGH')for enabled in (False,True)}
 data=load('v89_verify_actual_obs',ROOT/'experiments/python-gamebub-v89/observations/data.py')
 observations={(f['cohort'],f['fid'],f['policy']):f for group in data.iter_policies(POLICIES,only=SELECTED) for f in group}
 assert len(observations)==16
 witness_audit=load('v89_verify_independent_graph',ROOT/'scripts/cu66-v87/audit_coupled.py')
 bindings['scripts/cu66-v87/audit_coupled.py']=sha(ROOT/'scripts/cu66-v87/audit_coupled.py')
 fitted=[];witnesses=[]
 for row in rows:
  frame=observations[row['cohort'],row['fid'],row['policy']]
  assert row['packet_sha256']==frame['packet_sha256'] and row['wire_bytes']==frame['wire_bytes'] and row['metadata_bytes']==frame['metadata_bytes']
  assert row['mask']==frame['mask'] and row['observation_work_sha256']==frame['work_sha256']
  weights=LOW if row['cost']=='LOW' else HIGH
  fetch=frame['wire_bytes']*weights['crc_bytes']+frame['metadata_bytes']*weights['header_bytes']
  fetch+=sum(v*weights[k]for work in frame['shared_work']for k,v in work.items()if k!='emits')
  arithmetic=emission=0
  for tile in frame['context_work']:
   for context in tile:
    for k,v in context.items():
     if k in FETCH:fetch+=v*weights[k]
     else:arithmetic+=v*weights[k]
  emission=sum(work.get('emits',0)*weights['emits']for work in frame['shared_work'])
  assert row['producer_work_cycles']==dict(fetch=fetch,arithmetic=arithmetic,emit=emission)
  assert row['decode_cycles']/100000==row['conditional_decode_ms']
  assert row['full_gather_cycles']/100000==row['conditional_base_gather_complete_ms']
  assert row['decode_cycles']<=row['full_gather_cycles']
  audit=row['independent_audit'];assert audit['finish_cycles']==row['full_gather_cycles'] and audit['timeline_sha256']==row['timeline_sha256']
  assert audit['complete_fence_covers_all_jobs'] and audit['context_order_and_consumer_release']
  assert audit['resource_work_cycles']['memory']==row['memory_work_cycles']
  assert audit['resource_work_cycles']['fetch']==fetch and audit['resource_work_cycles']['arithmetic']==arithmetic and audit['resource_work_cycles']['emit']==emission
  for stage in ('reference','inverse','coefficients'):assert row['credit_peaks'][stage]['peak_reserved_slots']<=8
  fitted.append(dict(cohort=row['cohort'],fid=row['fid'],policy=row['policy'],cost=row['cost'],alias=row['alias'],wire_bytes=row['wire_bytes'],fits_49152=row['wire_bytes']<=49152,conditional_under10ms=row['decode_cycles']<1000000))
  if 'witness'in row:
   wp=ROOT/row['witness'];assert sha(wp)==row['witness_sha256']
   with gzip.open(wp,'rt')as f:w=json.load(f)
   check=witness_audit.verify(w['workload'],w['result']['timeline'],w['capacities'],w['windows'])
   assert check==audit
   witnesses.append(dict(path=row['witness'],sha256=sha(wp),timeline_sha256=check['timeline_sha256'],finish_cycles=check['finish_cycles']))
 old=json.loads((ROOT/'experiments/python-gamebub-v88/alias/probe.json').read_text())
 baseline={(r['cohort'],r['fid'],r['configuration'],r['alias']):r for r in report['frozen_CS86_control_matches']}
 assert len(baseline)==10
 for expected in old['rows']:
  r=baseline[expected['cohort'],expected['fid'],expected['configuration'],expected['alias']]
  assert r['decode_cycles']/100000==expected['conditional_decode_ms'] and r['complete_cycles']/100000==expected['conditional_base_gather_complete_ms']
 result=dict(schema='cu66-v89-joint-independent-audit-v1',status='PASS_ACTUAL_WORK_ROWS_AND_RETAINED_DAGS',unique_sources=4,schedules=64,
             actual_mixed_observations=16,frozen_CS86_control_matches=10,independent_retained_witnesses=len(witnesses),
             row_budget_and_deadline_checks=fitted,witnesses=witnesses,evidence_sha256=bindings,
             scope='Actual observed producer totals, identity/byte and complete DAG/credit audits. Selected-source conditional costs; no sustained hardware or fully validated latency proof.')
 (AREA/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('V89_JOINT_VERIFY_PASS sources=4 schedules=64 witnesses='+str(len(witnesses)))
if __name__=='__main__':main()
