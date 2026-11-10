#!/usr/bin/env python3
"""Strict bounded actual scratch pair plus source-extracted full tuple algebra."""
import argparse,datetime,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v128-raw';V=SRC/'verification';AREA=ROOT/'experiments/python-gamebub-v128/raw'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
GIB=1024**3
WIRE_SEEDS=(128501,128502);CLOCK_SEEDS=(128601,128602)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def rel(p):return str(Path(p).relative_to(ROOT))
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '))
 return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))
def verify():
 for name in ['prepare.py','prepare_verification.py']:subprocess.run([sys.executable,str(Path(__file__).with_name(name))],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
 recipe=load(SRC/'verification-recipe.json');assert recipe['baseline_module_rename_only']and recipe['original_assertions_retained']and recipe['source_payload_or_owner_forces']==0
 for p,h in recipe['files'].items():assert sha(ROOT/p)==h
 original=ROOT/recipe['baseline']['path'];renamed=V/'v128_scratch_baseline.sv';assert original.read_text().replace('module packed_scratch_v91g2 (','module v128_scratch_baseline (',1)==renamed.read_text()
 mapping=load(SRC/'source-map.json')['source_origins'];assert len(mapping)==4
 for m in mapping.values():assert sha(ROOT/m['path'])==m['sha256']
 return recipe,mapping

def check_wire(rows,seed):
 assert len(rows)==1;r=rows[0];assert r['type']=='v128_raw_wire_verdict'and r['status']=='TEST_PASS'and r['seed']==seed
 expected=dict(cases=196608,boundary_cases=131072,random_cases=65536,phase_checks=1572864,selector_mask=3,format_mask=3,phase_mask=255,DUT_clocks=0,new_result_forces=0)
 assert all(r[k]==v for k,v in expected.items());assert r['natural_packets']is False
 assert r['coherent_literal_checks']==16384 and r['arbitrary_mask_cases']==180224
 assert all(r[k]>0 for k in ['coherent_literal_checks','good','bad','selected_only_bad','other_only_bad','high_epoch_cases','high_block_cases','arbitrary_mask_cases'])
 return r

def check_clock(rows,seed):
 assert len(rows)==1;r=rows[0];assert r['type']=='v128_raw_clock_verdict'and r['status']=='TEST_PASS'and r['seed']==seed
 expected=dict(cases=74,epoch_errors=10,format_errors=50,phase_mask=15,selector_mask=3,format_mask=3,pending_faults=4,wrong_ack_cases=2,cancel_cases=4,unready_offers=2,band_epoch_errors=2,same_edge_accept_faults=2,retries=12,public_cycle_delta=0,prepared_state_forces=0,new_result_forces=0)
 assert all(r[k]==v for k,v in expected.items());assert r['clock_edges']>0 and r['eval_checks']>=3*r['clock_edges'] and r['requests']==r['acks'] and r['requests']>0
 return r


def input_files(recipe=None,mapping=None):
 if recipe is None:recipe,mapping=verify()
 parent=ROOT/'experiments/python-gamebub-v127/integration/results.json'
 files=set([Path(__file__).resolve(),Path(__file__).with_name('prepare.py'),Path(__file__).with_name('prepare_verification.py'),parent,SRC/'edit-recipe.json',SRC/'source-map.json',SRC/'verification-recipe.json',ROOT/'docs/cu66-v128/verification-plan.md'])
 files.update(ROOT/p for p in recipe['files']);files.update(ROOT/m['path']for m in mapping.values());files.add(ROOT/recipe['baseline']['path'])
 production=load(SRC/'edit-recipe.json')
 for r in production['production'].values():files.add(ROOT/r['original']['path'])
 return sorted(files)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');a=ap.parse_args();recipe,mapping=verify()
 if not a.run:print('V128_RAW_FOCUSED_PREPARED_NOT_RUN');return
 assert a.root_grant=='ROOT_V128_RAW','Exact Root heavy dispatch grant required'
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v128-raw-focused-'+stamp);build.mkdir();mapped='/build/'+build.name
 files=input_files(recipe,mapping)
 r=dict(schema='v128-raw-paired-scratch-and-extracted-algebra-v1',status='RUNNING',actual_RTL_run=False,source_sha256={rel(p):sha(p)for p in sorted(files)},source_origins=mapping,commands=[],wire_runs=[],clock_runs=[],memory_samples=[],backend='Verilator 5.020',image_id=IMAGE,strict_warnings=True,assertions_disabled_or_downgraded=False,all_original_oracles_retained=True,declared_public_cycle_delta=0,original_assertion_blocks_retained=True,new_result_or_owner_forces=0,prepared_phase_domain_is_natural_packets=False,clock_pair_uses_actual_public_begin_and_memory=True,build_external=str(build),scope='Finite source-extracted two-state algebra and paired real scratch public/controller/memory edges. Four raw component origins pinned; capacity/ingress actual packet behavior checked by separate full composition.')
 started=time.monotonic()
 def command(args,name,cap,actual=False):
  before=memory();assert before['available_bytes']>=8*GIB and before['psi_full_avg10']<1 and before['combined_used_ratio']<.85,before
  container='gamebub-v128-raw-focused-'+stamp.lower()+'-'+str(len(r['commands']))
  cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*args]
  c=dict(argv=cmd,timeout_seconds=cap,resource_before=before);r['commands'].append(c);t=time.monotonic()
  if actual:r['actual_RTL_run']=True
  write(out/'receipt.json',r)
  with(out/name).open('w')as log:
   p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);high=0
   while p.poll()is None:
    sample=dict(elapsed_seconds=time.monotonic()-t,**memory());r['memory_samples'].append(sample);high=high+1 if sample['psi_full_avg10']>=5 else 0
    if sample['available_bytes']<4*GIB or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:
     subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15);c['resource_stop']=sample;break
    time.sleep(2)
   c.update(exit_code=p.wait(timeout=20),wall_seconds=time.monotonic()-t)
  write(out/'receipt.json',r);assert c['exit_code']==0 and 'resource_stop'not in c,name
 try:
  for p in files:
   dst=out/'sources'/p.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
  compiled=[V/'v128_scratch_baseline.sv',SRC/'packed_scratch_v91g2.sv',V/'v128_raw_scalar_probe.sv',V/'raw_probe.sv',V/'tb_raw.cpp']
  for p in compiled:
   shutil.copyfile(p,build/p.name);assert sha(build/p.name)==sha(p)
  assert all(sha(out/'sources'/p.relative_to(ROOT))==r['source_sha256'][rel(p)]for p in files)
  r['compile_inputs_sha256']={p.name:sha(build/p.name)for p in compiled}
  command(['verilator','--version'],'version.log',30);assert 'Verilator 5.020'in(out/'version.log').read_text()
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','1000','--language','1800-2017','--top-module','raw_probe','--Mdir',mapped+'/obj','-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',*[mapped+'/'+p.name for p in compiled]],'compile.log',900)
  assert '%Warning-'not in(out/'compile.log').read_text();r['binary_sha256']=sha(build/'obj/Vraw_probe')
  for suite,seeds,checker in [('wire',WIRE_SEEDS,check_wire),('clock',CLOCK_SEEDS,check_clock)]:
   for seed in seeds:
    name=suite+'-'+str(seed)+'.jsonl';command([mapped+'/obj/Vraw_probe',suite,str(seed)],name,900,True);rows=[json.loads(x)for x in(out/name).read_text().splitlines()];r[suite+'_runs'].append(checker(rows,seed))
  assert r['source_sha256']=={rel(p):sha(p)for p in sorted(files)}
  assert all(sha(out/'sources'/p.relative_to(ROOT))==r['source_sha256'][rel(p)]for p in files)
  assert r['compile_inputs_sha256']=={p.name:sha(build/p.name)for p in compiled}
  r['compiled_input_snapshots_unchanged']=True;r['retained_source_snapshots_unchanged']=True;r['status']='PASS'
 except BaseException as e:r.update(status='FAIL',error=repr(e));raise
 finally:
  r['wall_seconds']=time.monotonic()-started;r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()and p.name!='receipt.json'};write(out/'receipt.json',r)
  write(AREA/'results.json',dict(path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json'),status=r['status'],actual_RTL_run=r['actual_RTL_run']))
  print('V128_RAW_FOCUSED',r['status'],rel(out),flush=True)
if __name__=='__main__':main()
