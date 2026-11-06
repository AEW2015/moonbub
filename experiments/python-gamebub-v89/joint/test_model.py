#!/usr/bin/env python3
"""Frozen-control equivalence and causal producer-cost sensitivity checks."""
import copy,gzip,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent

def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 model=load('v89_test_model',AREA/'model.py');old=load('v89_test_old_obs',ROOT/'experiments/python-gamebub-v86/contexts/data.py')
 scheduler=load('v89_test_scheduler',ROOT/'experiments/python-gamebub-v83/scheduler.py')
 audit=load('v89_test_audit',ROOT/'scripts/cu66-v87/audit_coupled.py')
 manifest=json.loads((ROOT/'experiments/python-gamebub-v87/coupled/verification.json').read_text())
 source=next(ROOT/p for p in manifest['artifact_sha256'] if p.endswith('witness-c0-f0-low_lanes2.json.gz') and '/attempts/'in p)
 with gzip.open(source,'rt')as f:original=json.load(f)
 observation=next(f for f in old.iter_frames() if f['cap']==65536 and(f['cohort'],f['fid'])==(0,0))
 base=original['workload'];front=base['frontend'];shared=observation['shared_work'];contexts=observation['context_work']
 priced=model.reprice(base,shared,contexts,model.LOW,wire_bytes=front['wire_bytes'],metadata_bytes=front['metadata_bytes'])
 assert priced['jobs']==base['jobs'],'zero-change repricing changed a task or its dependencies'
 assert priced['credits']==base['credits']
 assert priced['frontend']['work_cycles']==base['frontend']['work_cycles']
 checks=[dict(name='actual_frozen_control_every_job_and_credit_equal',status='PASS',jobs=len(base['jobs']))]
 modified=copy.deepcopy(contexts);modified[0][0]['decisions']=modified[0][0]['renorm']=0;modified[0][0]['plain_bits']=1000000
 slowed=model.reprice(base,shared,modified,model.LOW,wire_bytes=front['wire_bytes'],metadata_bytes=front['metadata_bytes'])
 result=scheduler.schedule(slowed['jobs'],original['capacities'],retain_timeline=True)
 independent=audit.verify(slowed,result['timeline'],original['capacities'])
 assert result['finish_cycles']>original['result']['finish_cycles'] and result['finish_cycles']>=1000000
 checks.append(dict(name='actual_new_plain_bits_are_causal_producer_work',status='PASS',control_finish=original['result']['finish_cycles'],changed_finish=result['finish_cycles'],coefficient_peak=independent['stages']['coefficients']['peak']))
 invalid=[]
 bad=copy.deepcopy(shared);bad[0]['plain_bits']=1;invalid.append(('shared_compute_not_silently_ignored',bad,contexts,model.LOW))
 bad=copy.deepcopy(contexts);bad[0][0]['plain_bits']=-1;invalid.append(('negative_primitive',shared,bad,model.LOW))
 bad=copy.deepcopy(contexts);bad[0][0]['surprise']=1;invalid.append(('unknown_primitive',shared,bad,model.LOW))
 bad=dict(model.LOW);del bad['plain_bits'];invalid.append(('missing_explicit_plain_cost',shared,contexts,bad))
 for name,a,b,w in invalid:
  try:model.reprice(base,a,b,w,wire_bytes=front['wire_bytes'],metadata_bytes=front['metadata_bytes'])
  except ValueError:checks.append(dict(name=name,status='PASS_REJECT'))
  else:raise AssertionError(name)
 report=dict(schema='cu66-v89-joint-tests-v1',status='PASS',checks=checks,source_sha256={str(p.relative_to(ROOT)):sha(p)for p in [Path(__file__).resolve(),AREA/'model.py',source,ROOT/'experiments/python-gamebub-v86/contexts/data.py',ROOT/'experiments/python-gamebub-v83/scheduler.py',ROOT/'scripts/cu66-v87/audit_coupled.py']},scope='Frozen workload equivalence and synthetic causal cost injection, not physical latency or new content coverage.')
 (AREA/'tests.json').write_text(json.dumps(report,indent=2)+'\n');print('V89_JOINT_TESTS_PASS',len(checks))
if __name__=='__main__':main()
