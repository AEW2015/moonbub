#!/usr/bin/env python3
"""Prepared only until Root emits a route-justified certificate candidate."""
import argparse,datetime,gzip,hashlib,importlib.util,json,pathlib,shutil,subprocess,sys,time
sys.dont_write_bytecode=True
R=pathlib.Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v115-owner-cut-focus';A=R/'experiments/python-gamebub-v115/owner-cut-focus'
SOURCE=R/'fpga/experiments/cu66-v115-owner/cs88_pipeline_v91k.sv';RECIPE=SOURCE.parent/'edit-recipe.json'
SUMMARY=R/'experiments/python-gamebub-v115/refined/spatial/results.json';SELECTED=R/'experiments/python-gamebub-v115/refined/spatial/attempts/20261109T021900879958Z/receipt.json';GOLD=R/'experiments/python-gamebub-v113/spatial/attempts/20261108T212355592057Z/receipt.json';PACK=R/'fpga/experiments/cu66-v112-control/packaging.json';OLD_BENCH=R/'fpga/experiments/cu66-v107-elastic/verification/bench.cpp'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');a=ap.parse_args()
 spec=importlib.util.spec_from_file_location('owner_focus_prepare',pathlib.Path(__file__).with_name('prepare.py'));prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep);preparation=prep.prepare()
 if not a.run:print(preparation['status']);return
 assert SOURCE.is_file() and RECIPE.is_file(),'Root production candidate/recipe not emitted; no run permitted'
 assert sha(SUMMARY)==preparation['baseline']['summary_sha256'] and sha(SELECTED)==preparation['baseline']['receipt_sha256']
 frozen=json.loads(SELECTED.read_text());assert frozen['status']=='PASS_V115_REFINED_SPATIAL_CANONICAL' and frozen['actual_RTL_run']
 top_old=R/'fpga/experiments/cu66-v114-control/cs88_pipeline_v91k.sv';assert 'base_kill_authorized' in SOURCE.read_text()
 sources=[R/p for p in preparation['rtl_source_order']];assert len(sources)==18 and sources.count(SOURCE)==1
 for origin in preparation['source_origins'].values():assert sha(R/origin['path'])==origin['sha256']
 override_files=[R/v[k] for v in preparation['production_overrides'] for k in ['candidate','original','recipe']]
 files=set(sources+override_files+[SOURCE,RECIPE,SUMMARY,SELECTED,GOLD,PACK,OLD_BENCH,top_old,S/'immutable_control.hpp',S/'bench-derivation.json',S/'tb_owner.cpp',R/'fpga/experiments/cu66-v114-control/tb_control.cpp',R/'fpga/experiments/cu66-v115-control-peer/tb_peer.cpp',pathlib.Path(__file__).resolve(),pathlib.Path(__file__).with_name('prepare.py'),R/'scripts/cu66-v114/optimized_spatial.py'])
 gold=json.loads(GOLD.read_text());files.update(R/v['source'] for v in gold['inputs'].values());files=sorted(files)
 spec=importlib.util.spec_from_file_location('bounded_resources',R/'scripts/cu66-v114/optimized_spatial.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=A/'attempts'/stamp;out.mkdir(parents=True);build=pathlib.Path('/home/lori/gamebub-build/cu66-v69')/('v115-owner-focus-'+stamp);build.mkdir();(build/'tmp').mkdir();mapped='/build/'+build.name
 raw=dict(schema='v115-owner-certificate-original-control-plus-additive-focus-v1',status='FAIL',actual_RTL_run=False,simulation_started=False,baseline_refined_selected=preparation['baseline'],source_origins=preparation['source_origins'],production_overrides=preparation['production_overrides'],image_id=m.IMAGE,source_sha256={str(p.relative_to(R)):sha(p)for p in files},rtl_source_order=[str(p.relative_to(R))for p in sources],commands=[],runs=[],memory_samples=[],assertions_disabled_or_downgraded=False,old_assertions_removed=0,limits='New focus retries are accepted-command/delivery retries, not full canonical frame retries. Separate actual18 peer/canonical and live-parent campaigns remain mandatory. No native timing claim.')
 started=time.monotonic()
 def command(argv,name,cap):
  gate=m.memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
  container='gamebub-v115-owner-focus-'+stamp.lower()+'-'+str(len(raw['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={out},dst={out},readonly','--mount',f'type=bind,src={build},dst={mapped}','--mount',f'type=bind,src={build}/tmp,dst=/tmp','-w',mapped,m.IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv];c=dict(argv=cmd,timeout_seconds=cap,resource_before=gate);raw['commands'].append(c);t=time.monotonic()
  with(out/name).open('w')as f:
   p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);high=0
   while p.poll()is None:
    sample=dict(command=name,elapsed_seconds=time.monotonic()-t,**m.memory());raw['memory_samples'].append(sample);high=high+1 if sample['psi_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or high>=2 or sample['elapsed_seconds']>cap+20:
     subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);c['resource_stop']=sample;break
    time.sleep(2)
   c.update(exit_code=p.wait(timeout=20),wall_seconds=time.monotonic()-t)
  assert c['exit_code']==0 and 'resource_stop'not in c,name
 try:
  for p in files:q=out/'sources'/p.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  snap=lambda p:str(out/'sources'/p.relative_to(R))
  shutil.copyfile(OLD_BENCH,build/'bench.cpp');assert sha(build/'bench.cpp')==sha(OLD_BENCH)
  for name,v in gold['inputs'].items():
   p=R/v['source'];assert sha(p)==v['sha256'];data=gzip.decompress(p.read_bytes())if p.suffix=='.gz'else p.read_bytes();(build/name).write_bytes(data);assert sha(build/name)==v['expanded_sha256']
  pkg=json.loads(PACK.read_text());admission=next(p for p in sources if p.name=='cs88_admission_v91i2a.sv');data=admission.read_bytes();assert sha(admission)==pkg['production_sha256'];offs=[0]+pkg['split_byte_offsets']+[len(data)];frags=[]
  for i,v in enumerate(pkg['fragments']):p=build/v['filename'];p.write_bytes(data[offs[i]:offs[i+1]]);assert sha(p)==v['sha256'];frags.append(p)
  assert b''.join(p.read_bytes()for p in frags)==data;raw['lossless_compile_packaging']=pkg
  compiled=[mapped+'/'+frags[0].name if p==admission else snap(p)for p in sources if p.suffix=='.sv']+[mapped+'/'+p.name for p in frags[1:]]
  command(['verilator','--version'],'version.log',30)
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','1000','--language','1800-2017','--top-module','cs88_pipeline_v91k','--Mdir',mapped+'/obj','-I'+str(out/'sources/fpga/experiments/cu66-v69/inverse'),'-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror -DELASTIC=1 -I'+mapped,*compiled,snap(S/'tb_owner.cpp')],'compile.log',900)
  assert '%Warning-'not in(out/'compile.log').read_text();raw['binary_sha256']=sha(build/'obj/Vcs88_pipeline_v91k')
  for seed in [115701,115702]:
   name='owner-'+str(seed);raw.update(actual_RTL_run=True,simulation_started=True);command([mapped+'/obj/Vcs88_pipeline_v91k',mapped+'/cases.tsv',mapped+'/transform_tiles.tsv',mapped+'/canonical_goldens.tsv',str(seed),mapped+'/'+name+'-trace.jsonl'],name+'-simulation.jsonl',300)
   rows=[json.loads(x)for x in(out/(name+'-simulation.jsonl')).read_text().splitlines()];original=[x for x in rows if x.get('status')=='TEST_PASS'and x.get('directed_checks')==78];new=[x for x in rows if x.get('type')=='owner_certificate_verdict'];assert len(original)==len(new)==1
   assert original[0]['real_physical_drain_checks']==4 and original[0]['backdoor_fault_tests_declared']==7 and original[0]['original_bench_checks_removed']==0
   v=new[0];assert v['status']=='TEST_PASS' and v['frozen_directed_checks']==78 and v['frozen_physical_drain_checks']==4 and v['real_peer_cases']==v['real_peer_births']==v['real_peer_consumes']==4 and v['stale_private_injections']==1 and v['no_owner_abort_cases']==2 and v['cache_abort_cases']==v['reset_pending_cases']==v['wrap_cases']==1 and v['fresh_command_retries']==9 and v['old_assertions_removed']==0
   raw['runs'].append(dict(seed=seed,original=original[0],added=v))
   for file in(build/'tmp').glob('*'):
    if file.is_file():shutil.copyfile(file,out/(name+'-'+file.name))
  assert raw['source_sha256']=={str(p.relative_to(R)):sha(p)for p in files};raw.update(status='PASS',actual_RTL_run=True)
 except BaseException as e:raw['error']=repr(e);raise
 finally:
  for p in build.glob('owner-*'):
   if p.is_file():(out/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
  raw['wall_seconds']=time.monotonic()-started;raw['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()};write(out/'receipt.json',raw);write(A/'results.json',dict(status=raw['status'],path=str((out/'receipt.json').relative_to(R)),sha256=sha(out/'receipt.json')));print('V115_OWNER_FOCUS',raw['status'],out,flush=True)
if __name__=='__main__':main()
