#!/usr/bin/env python3
"""Separate actual-full-top peer-kill/physical-debt/replay proof (Verilator)."""
import argparse,datetime,gzip,hashlib,importlib.util,json,pathlib,shutil,subprocess,time,sys
sys.dont_write_bytecode=True
R=pathlib.Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v118-peer';A=R/'experiments/python-gamebub-v124/integrated-study/control-peer';P=R/'scripts/cu66-v124/integration/spatial.py'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write(p,j):pathlib.Path(p).write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');a=ap.parse_args()
 spec=importlib.util.spec_from_file_location('frozen_optimized_recipe',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 pending=[name for name in m.FOCUSED if not (R/name).is_file() or json.loads((R/name).read_text()).get('status')!='PASS']
 if pending:raise SystemExit('PREREQUISITES_NOT_READY: '+', '.join(pending))
 recipe=json.loads((S/'derivation.json').read_text());text=(R/recipe['original']).read_text();assert sha(R/recipe['original'])==recipe['original_sha256']
 for edit in recipe['edits']:assert text.count(edit['before'])==1;text=text.replace(edit['before'],edit['after'],1)
 assert text==(R/recipe['candidate']).read_text() and sha(R/recipe['candidate'])==recipe['candidate_sha256']
 for edit in reversed(recipe['edits']):assert text.count(edit['after'])==1;text=text.replace(edit['after'],edit['before'],1)
 assert text==(R/recipe['original']).read_text() and recipe['old_need_checks_removed']==0
 assert sha(R/recipe['header']['original'])==sha(R/recipe['header']['candidate'])==recipe['header']['sha256']
 contract=json.loads((S/'fault-injection-contract.json').read_text());candidate=(S/'tb_peer.cpp').read_text()
 assert contract['cpp']==str((S/'tb_peer.cpp').relative_to(R)) and contract['cpp_sha256']==sha(S/'tb_peer.cpp')
 assert hashlib.sha256(candidate[candidate.index('static void inject('):candidate.index('static void masked(')].encode()).hexdigest()==contract['injection_body_sha256']
 for task in contract['actual_RTL_task_sources']:
  assert sha(R/task['path'])==task['sha256'] and task['task_text'] in (R/task['path']).read_text()
  if task['path'].endswith('/cu66_reconstruct_stream_v91k.sv'):assert task['task_text'] in (R/'fpga/experiments/cu66-v119-owner/cu66_reconstruct_stream_v91k.sv').read_text()
 assert candidate.count('need(')==(R/recipe['original']).read_text().count('need(')+1
 assert contract['physical_reference_or_scratch_ledger_assigned'] is False and contract['v118_poststate']['additional_tick'] is False
 base,parent,sources,origins,ancestor_replacements,packaging,files=m.prepare(True)
 # Selected new composition comes from the strict refined preparation. The
 # frozen V115 peer bench and complete original event/value oracles stay unchanged.
 replacements=ancestor_replacements
 assert len(replacements)==10 and len(sources)==18
 for meta in origins.values():assert sha(R/meta['path'])==meta['sha256']
 import runpy
 contract=runpy.run_path(str(R/'scripts/cu66-v124/integration/contract.py'));contract['verify']()
 bpath,baseline=contract['baseline']('control-peer');files+=contract['files']()+[bpath]
 files=sorted(set(files+[pathlib.Path(__file__).resolve(),P,S/'tb_peer.cpp',S/'bench_peer_base.hpp',S/'derivation.json',S/'fault-injection-contract.json',R/'scripts/cu66-v115/control-peer/qualify.py']))
 if not a.run:print('V124_CONTROL_PEER_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=A/'attempts'/stamp;out.mkdir(parents=True);build=pathlib.Path('/home/lori/gamebub-build/cu66-v69')/('v124-owner-peer-'+stamp);build.mkdir();mapped='/build/'+build.name
 r=dict(schema='v120-actual-full-top-peer-and-public-pending-cancel-v1',status='FAIL',actual_RTL_run=False,simulation_started=False,backend='Verilator',image_id=m.IMAGE,strict_warnings=True,assertions_disabled_or_downgraded=False,source_sha256={m.rel(p):sha(p)for p in files},rtl_source_order=[m.rel(p)for p in sources],source_origins=origins,replacements=replacements,bench_api_derivation=dict(path=m.rel(m.API_DERIVATION),sha256=sha(m.API_DERIVATION)),commands=[],runs=[],memory_samples=[],scope='Separate verification-only prepared child fault states during actual accepted scratch write/read and queued synchronous replay ownership; original independent functional/held/physical-owner checks retained; complete canonical retries; six real-parent abort/reset checks over all three scratch preparation boundaries with independent anti-replay/physical-owner/canonical retry checks; no production source or selected proof changes',original_oracle_checks_removed=0)
 started=time.monotonic()
 def command(argv,name,cap):
  gate=m.memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1 and gate['combined_used_ratio']<.85,gate;container='gamebub-v124-owner-peer-final-'+stamp.lower()+'-'+str(len(r['commands']))
  cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={out},dst={out},readonly','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,m.IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv];c=dict(argv=cmd,timeout_seconds=cap,resource_before=gate);r['commands'].append(c);t=time.monotonic()
  with(out/name).open('w')as f:
   if argv[0]==mapped+'/obj/Vcs88_pipeline_v91k':r['actual_RTL_run']=True;r['simulation_started']=True
   write(out/'receipt.json',r)
   p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);hi=0
   while p.poll()is None:
    sample=dict(command=name,elapsed_seconds=time.monotonic()-t,**m.memory());r['memory_samples'].append(sample);hi=hi+1 if sample['psi_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or hi>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);c['resource_stop']=sample;break
    time.sleep(2)
   c.update(exit_code=p.wait(timeout=20),wall_seconds=time.monotonic()-t)
  assert c['exit_code']==0 and 'resource_stop'not in c,name
 try:
  for p in files:
   q=out/'sources'/p.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  snap=lambda p:str(out/'sources'/p.relative_to(R))
  shutil.copyfile(S/'bench_peer_base.hpp',build/'bench_peer_base.hpp');r['peer_private_cancel_derivation']=dict(path=m.rel(S/'derivation.json'),sha256=sha(S/'derivation.json'));r['fault_injection_contract']=dict(path=m.rel(S/'fault-injection-contract.json'),sha256=sha(S/'fault-injection-contract.json'))
  for name,v in base['inputs'].items():
   p=R/v['source'];assert sha(p)==v['sha256'];b=gzip.decompress(p.read_bytes())if p.suffix=='.gz'else p.read_bytes();(build/name).write_bytes(b);assert sha(build/name)==v['expanded_sha256']
  pkg=json.loads(packaging.read_text());admission=next(p for p in sources if p.name=='cs88_admission_v91i2a.sv');data=admission.read_bytes();assert sha(admission)==pkg['production_sha256'];offs=[0]+pkg['split_byte_offsets']+[len(data)];frags=[]
  for i,v in enumerate(pkg['fragments']):p=build/v['filename'];p.write_bytes(data[offs[i]:offs[i+1]]);assert sha(p)==v['sha256'];frags.append(p)
  assert b''.join(p.read_bytes()for p in frags)==data;r['lossless_compile_packaging']=pkg
  compiled=[mapped+'/'+frags[0].name if p==admission else snap(p)for p in sources if p.suffix=='.sv']+[mapped+'/'+p.name for p in frags[1:]]
  command(['verilator','--version'],'version.log',30)
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','1000','--language','1800-2017','--top-module','cs88_pipeline_v91k','--Mdir',mapped+'/obj','-I'+str(out/'sources/fpga/experiments/cu66-v69/inverse'),'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror -DELASTIC=1 -I'+mapped,*compiled,snap(S/'tb_peer.cpp')],'compile.log',900)
  assert '%Warning-'not in(out/'compile.log').read_text();r['binary_sha256']=sha(build/'obj/Vcs88_pipeline_v91k')
  for seed in (115501,115502):
   prefix='peer-'+str(seed);command([mapped+'/obj/Vcs88_pipeline_v91k',mapped+'/cases.tsv',mapped+'/transform_tiles.tsv',mapped+'/canonical_goldens.tsv',str(seed),mapped+'/'+prefix+'-events.jsonl',mapped+'/'+prefix+'-canonical.tsv'],prefix+'-simulation.jsonl',900)
   lines=[json.loads(x)for x in(out/(prefix+'-simulation.jsonl')).read_text().splitlines()];v=[x for x in lines if x.get('type')=='peer_verdict'];assert len(v)==1 and v[0]['status']=='TEST_PASS'and v[0]['directed_checks']==8 and v[0]['canonical_retries']==8 and v[0]['accepted_write_checks']==2 and v[0]['accepted_read_checks']==4 and v[0]['queued_replay_checks']==2 and v[0]['prepared_child_fault_injections']==14 and v[0]['local_cancel_edges']==8 and v[0]['parent_pending_cancel_cases']==6 and v[0]['parent_canonical_retries']==6 and v[0]['total_canonical_retries']==14 and v[0]['parent_stage_mask']==7 and v[0]['parent_abort_cases']==v[0]['parent_reset_cases']==v[0]['parent_private_cancel_edges']==3 and v[0]['all_local_cancel_edges']==11 and v[0]['original_oracle_checks_removed']==0 and v[0]['peer_private_cancel_assumptions_corrected']==1
   case_rows=[x for x in lines if x.get('type')=='case'];assert len(case_rows)==14 and all(x['error']==0 and x['canonical']['samples']==518400 and not x['pending_drain'] for x in case_rows)
   parent_rows=[x for x in lines if x.get('type')=='parent_pending_case'];assert len(parent_rows)==6 and {(x['reset'],x['stage'])for x in parent_rows}=={(reset,stage)for reset in [False,True]for stage in range(3)}
   assert all(x['status']=='PASS'and x['parent_abort_tag_read_only'] for x in parent_rows)
   expected={row.split()[0]:row.split()[2]for row in(build/'canonical_goldens.tsv').read_text().splitlines()}
   canonical=(build/(prefix+'-canonical.tsv')).read_text().splitlines();assert len(canonical)==14
   for row in canonical:
    name,profile,pixels=row.split();assert name==v[0]['canonical_case_id']and profile=='0'and pixels==expected[name]
   oldlines=[json.loads(x) for x in (bpath.parent/(prefix+'-simulation.jsonl')).read_text().splitlines()]
   assert lines==oldlines,'V121 peer stdout/event cycles changed from Source B'
   for suffix in ('events.jsonl','canonical.tsv'):
    assert (build/(prefix+'-'+suffix)).read_bytes()==gzip.decompress((bpath.parent/(prefix+'-'+suffix+'.gz')).read_bytes()),suffix
   r['runs'].append(v[0])
  assert r['source_sha256']=={m.rel(p):sha(p)for p in files};r.update(status='PASS',actual_RTL_run=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in build.glob('peer-*'):
   if p.is_file():(out/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
  r['wall_seconds']=time.monotonic()-started;r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()and p.name!='receipt.json'};write(out/'receipt.json',r);write(A/'results.json',dict(r,selected_report=m.rel(out/'receipt.json'),selected_report_sha256=sha(out/'receipt.json')));print('V124_CONTROL_PEER',r['status'],out,flush=True)
if __name__=='__main__':main()
