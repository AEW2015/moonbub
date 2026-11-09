#!/usr/bin/env python3
"""Recover only the resource-interrupted optimized transport seed, with explicit provenance."""
import argparse,copy,datetime,gzip,hashlib,importlib.util,json,pathlib,shutil,subprocess,time
R=pathlib.Path(__file__).resolve().parents[2];A=R/'experiments/python-gamebub-v114/optimized/spatial';P=A/'attempts/20261108T230004120722Z/receipt.json';P_SHA='50abb09cc1c0e631234a6d9fef79f7a859ab19c57faf8d8a15168c22f961ae01';B=pathlib.Path('/home/lori/gamebub-build/cu66-v69/v114-optimized-spatial-20261108T230004120722Z');IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(pathlib.Path(p).read_text())
def write(p,j):pathlib.Path(p).write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def rel(p):return str(pathlib.Path(p).resolve().relative_to(R))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');a=ap.parse_args();assert sha(P)==P_SHA;p=load(P)
 assert p['status']=='FAIL'and p['error']=="AssertionError('transport-107602-simulation.jsonl')"and p['actual_RTL_run']
 assert len(p['runs'])==2 and len(p['transport_runs'])==1 and p['transport_runs'][0]['seed']==107601
 assert p['newly_executed_candidate_case_profiles']==44 and p['newly_executed_candidate_directed_checks']==42
 stop=p['commands'][-1];assert stop['exit_code']==143 and stop['resource_stop']['psi_full_avg10']>=5 and stop['resource_stop']['available_bytes']>=4*1024**3
 assert len(p['rtl_source_order'])==18 and len(p['replacements'])==2
 for n,h in p['source_sha256'].items():assert sha(R/n)==h,n
 for n,h in p['artifact_sha256'].items():assert sha(P.parent/n)==h,n
 baseline=load(R/p['baseline_reference']['path']);assert sha(R/p['baseline_reference']['path'])==p['baseline_reference']['sha256']
 for row in p['runs']:
  assert row['verdict']['status']=='TEST_PASS'and row['verdict']['cases']==22 and row['verdict']['directed_checks']==21 and row['canonical_exact']
  stdout=[json.loads(s)for s in(P.parent/f"candidate-{row['seed']}-simulation.jsonl").read_text().splitlines()];assert [x for x in stdout if x.get('type')=='verdict']==[row['verdict']]
  ref=next(x for x in baseline['runs']if x['seed']==row['seed']);assert row['artifacts']['canonical_actual']['raw_sha256']==ref['artifacts']['canonical_actual']['raw_sha256']
 first=p['transport_runs'][0];assert first['canonical_exact']and first['verdict']['status']=='TEST_PASS'and first['verdict']['successful_case_profiles']==12 and first['verdict']['abort_reset_retries']==2
 assert first['verdict']['public_command_accepts']==first['verdict']['registered_child_deliveries']==first['verdict']['poisoned_command_tuples']==16
 assert first['artifacts']['canonical_actual']['raw_sha256']==p['runs'][0]['artifacts']['canonical_actual']['raw_sha256']
 assert [x for x in map(json.loads,(P.parent/'transport-107601-simulation.jsonl').read_text().splitlines())if x.get('type')=='transport_verdict']==[first['verdict']]
 assert sha(B/'custom_transport')==p['transport_binary_sha256']
 for name,v in p['inputs'].items():assert sha(B/name)==v['expanded_sha256']
 for row in p['runs']+p['transport_runs']:
  for v in row['artifacts'].values():assert sha(P.parent/v['path'])==v['sha256'] and hashlib.sha256(gzip.decompress((P.parent/v['path']).read_bytes())).hexdigest()==v['raw_sha256']
 spec=importlib.util.spec_from_file_location('frozen_optimized_recipe',R/'scripts/cu66-v114/optimized_spatial.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.prepare(True)
 if not a.run:print('V114_OPTIMIZED_RECOVERY_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=A/'attempts'/stamp;out.mkdir(parents=True);build=pathlib.Path('/home/lori/gamebub-build/cu66-v69')/('v114-optimized-recovery-'+stamp);build.mkdir();mapped='/build/'+build.name;started=time.monotonic()
 pointer=dict(path=rel(P),sha256=P_SHA,sha=P_SHA);q=copy.deepcopy(p);q.update(schema='v114-optimized-resource-recovery-with-partial-parent-certificates-v1',status='FAIL',actual_RTL_run=False,canonical_parent_receipt=pointer,reused_model_compile_parent_reference=pointer,canonical_reused_actual_RTL=True,candidate_model_reused=True,fresh_candidate_model_required=False,canonical_qualified_case_profiles=44,canonical_qualified_directed_checks=42,newly_executed_candidate_case_profiles=0,newly_executed_candidate_directed_checks=0,newly_executed_transport_case_profiles=0,newly_executed_transport_abort_reset_retries=0,transport_qualified_case_profiles=12,transport_qualified_abort_reset_retries=2,transport_reused_seeds=[107601],commands=[],memory_samples=[],source_sha256={**p['source_sha256'],rel(P):P_SHA,rel(pathlib.Path(__file__).resolve()):sha(pathlib.Path(__file__).resolve())},parent_remains_FAIL=True,completed_parent_artifacts_copied={},recovery_assets={},transport_runs=copy.deepcopy(p['transport_runs']))
 for key in ['error','artifact_sha256','wall_seconds']:q.pop(key,None)
 def command(argv,name,cap):
  gate=m.memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate;container='gamebub-v114-optimized-recovery-'+stamp.lower();cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={out},dst={out},readonly','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv];c=dict(argv=cmd,timeout_seconds=cap,resource_before=gate);q['commands'].append(c);t=time.monotonic()
  with(out/name).open('w')as log:
   child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);hi=0
   while child.poll()is None:
    sample=dict(command=name,elapsed_seconds=time.monotonic()-t,**m.memory());q['memory_samples'].append(sample);hi=hi+1 if sample['psi_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or hi>=2 or sample['elapsed_seconds']>cap+20:subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);c['resource_stop']=sample;break
    time.sleep(2)
   c.update(exit_code=child.wait(timeout=20),wall_seconds=time.monotonic()-t)
  assert c['exit_code']==0 and 'resource_stop'not in c,name
 def pack(path):
  target=out/(path.name+'.gz');target.write_bytes(gzip.compress(path.read_bytes(),mtime=0));return dict(path=target.name,sha256=sha(target),raw_sha256=sha(path))
 try:
  for n,h in p['artifact_sha256'].items():
   if n.startswith('transport-107602-'):continue
   target=out/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P.parent/n,target);assert sha(target)==h;q['completed_parent_artifacts_copied'][n]=h
  for path in [P,pathlib.Path(__file__).resolve()]:
   target=out/'sources'/path.relative_to(R);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
  assets=out/'recovery-assets';assets.mkdir()
  for name in ['custom_transport',*p['inputs']]:
   target=assets/name;shutil.copyfile(B/name,target);assert sha(target)==sha(B/name);q['recovery_assets'][name]=dict(path=str(target.relative_to(out)),sha256=sha(target),parent_build_path=str(B/name))
  (assets/'custom_transport').chmod(0o755)
  prefix='transport-107602';command([str(assets/'custom_transport'),str(assets/'cases.tsv'),str(assets/'transform_tiles.tsv'),str(assets/'canonical_goldens.tsv'),'107602',mapped+'/'+prefix+'-events.jsonl',mapped+'/'+prefix+'-canonical.tsv'],prefix+'-simulation.jsonl',900)
  lines=[json.loads(s)for s in(out/(prefix+'-simulation.jsonl')).read_text().splitlines()];v=[x for x in lines if x.get('type')=='transport_verdict'];assert len(v)==1 and v[0]['status']=='TEST_PASS'and v[0]['successful_case_profiles']==12 and v[0]['abort_reset_retries']==2 and v[0]['public_command_accepts']==16 and v[0]['registered_child_deliveries']==16 and v[0]['poisoned_command_tuples']==16
  path=build/(prefix+'-canonical.tsv');reference=next(x for x in baseline['runs']if x['seed']==107602);assert sha(path)==reference['artifacts']['canonical_actual']['raw_sha256']
  q['transport_runs'].append(dict(seed=107602,verdict=v[0],canonical_exact=True,artifacts=dict(events=pack(build/(prefix+'-events.jsonl')),canonical_actual=pack(path)),fences=[x for x in lines if x.get('type')=='custom_transport']))
  assert q['runs']==p['runs']and q['transport_runs'][0]==p['transport_runs'][0]
  for n,h in q['source_sha256'].items():assert sha(R/n)==h,n
  for n,v in q['recovery_assets'].items():assert sha(out/v['path'])==v['sha256']
  q.update(status='PASS_V114_OPTIMIZED_SPATIAL_CANONICAL',actual_RTL_run=True,custom_transport_status='PASS_ACTUAL_V97_TO_CUSTOM_DECODER_CANONICAL',newly_executed_transport_case_profiles=12,newly_executed_transport_abort_reset_retries=2,transport_qualified_case_profiles=24,transport_qualified_abort_reset_retries=4)
 except BaseException as e:q['error']=repr(e);raise
 finally:
  for path in build.glob('*'):
   if path.is_file()and path.name.endswith(('-events.jsonl','-canonical.tsv'))and not(out/(path.name+'.gz')).exists():pack(path)
  q['wall_seconds']=time.monotonic()-started;q['artifact_sha256']={str(path.relative_to(out)):sha(path)for path in sorted(out.rglob('*'))if path.is_file()};write(out/'receipt.json',q);write(A/'results.json',dict(q,selected_receipt=rel(out/'receipt.json')));print('V114_OPTIMIZED_RECOVERY',q['status'],out,flush=True)
if __name__=='__main__':main()
