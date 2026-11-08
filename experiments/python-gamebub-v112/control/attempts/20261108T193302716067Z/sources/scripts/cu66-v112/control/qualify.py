#!/usr/bin/env python3
"""Bounded strict Verilator focused proof against complete frozen Count bodies."""
import argparse,datetime,gzip,hashlib,importlib.util,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v112-control';V=SRC/'verification';AREA=ROOT/'experiments/python-gamebub-v112/control'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def module(p):
 spec=importlib.util.spec_from_file_location('v112_'+p.stem,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def verify():
 recipe=json.loads((SRC/'edit-recipe.json').read_text())
 for e in recipe['production'].values():
  p=ROOT/e['original'];q=ROOT/e['candidate'];assert sha(p)==e['original_sha256'] and sha(q)==e['candidate_sha256'];s=p.read_text()
  for x in e['edits']:assert s.count(x['before'])==1;s=s.replace(x['before'],x['after'],1)
  assert s==q.read_text()
  for x in reversed(e['edits']):assert s.count(x['after'])==1;s=s.replace(x['after'],x['before'],1)
  assert s==p.read_text()
 a=json.loads((V/'adapters.json').read_text())
 for e in a['adapters']:
  s=(ROOT/e['source']).read_text();assert sha(ROOT/e['source'])==e['source_sha256']
  for x,y in e['edits']:assert s.count(x)==1;s=s.replace(x,y,1)
  assert s==(ROOT/e['path']).read_text() and sha(ROOT/e['path'])==e['sha256']
 assert recipe['added_public_cycles']==0 and recipe['all_original_assertions_retained']
 return recipe

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');a=ap.parse_args();recipe=verify()
 if not a.run:print('V112_CONTROL_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v112-control-'+stamp);build.mkdir();mapped='/build/'+build.name
 vectors=ROOT/'experiments/python-gamebub-v91i/vectors/vectors.txt'
 files=sorted(set([p for p in SRC.rglob('*')if p.is_file()]+[ROOT/e['original'] for e in recipe['production'].values()]+[p for p in Path(__file__).parent.glob('*.py')]+[vectors,AREA/'preparation.json',ROOT/'experiments/cu66-native-v69/generated_constants.hpp']))
 r=dict(schema='v112-local-control-focused-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p)for p in files},commands=[],scratch_runs=[],admission_runs=[],domain_runs=[],strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,added_public_cycles=0,scope='Full frozen Count scratch and admission bodies; every existing public/invalid/debug/counter/request comparison active. Original independent coefficient, malformed packet, coordinate, port and ownership oracles retained. No timing/hardware/CDC qualification.')
 started=time.monotonic()
 def command(argv,name,cap):
  gate=memory();assert gate['available_bytes']>=10*1024**3 and gate['psi_full_avg10']<1,gate
  container='gamebub-v112-control-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  e=dict(argv=cmd,resource_before=gate,timeout_seconds=cap);r['commands'].append(e);began=time.monotonic()
  with(out/name).open('w')as log:
   p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while p.poll()is None:
    if time.monotonic()-began>cap+20:
     subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);raise RuntimeError('HOST_TIMEOUT '+name)
    time.sleep(.5)
   code=p.wait(timeout=20)
  e.update(exit_code=code,wall_seconds=time.monotonic()-began);assert code==0,(name,code)
 def compile(top,names):
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror','--top-module',top,'--Mdir',mapped+'/'+top+'-obj',*[mapped+'/'+n for n in names]],top+'-compile.log',600)
  assert '%Warning-'not in(out/(top+'-compile.log')).read_text();r[top+'_binary_sha256']=sha(build/(top+'-obj')/('V'+top))
 try:
  for p in files:q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for p in V.iterdir():
   if p.is_file():shutil.copyfile(p,build/p.name)
  # The inherited test's original side now also uses the frozen Count TABLES
  # helper. Translate only its physical hierarchy path; every oracle stays.
  p=build/'tb_admission.cpp';s=p.read_text();n=s.count('original__DOT__modes');assert n==4;s=s.replace('original__DOT__modes','original__DOT__mode_store__DOT__words');p.write_text(s)
  r['test_hierarchy_translation']=dict(before='original__DOT__modes',after='original__DOT__mode_store__DOT__words',occurrences=n,semantic_checker_edits=0,compiled_sha256=sha(p))
  # Identical shared helper modules are compiled once; both main bodies exact.
  for variant in ('original','candidate'):
   p=build/('admission_'+variant+'.sv');s=p.read_text();first=s.index('module cu66_scale_tdp_v107 (');second=s.index('module cu66_mode_store_v107 (')
   for name,t in [('cu66_scale_tdp_v107.sv',s[first:second]),('cu66_mode_store_v107.sv',s[second:])]:
    q=build/name
    if q.exists():assert q.read_text()==t
    else:q.write_text(t)
   p.write_text(s[:first]);assert p.read_text()+(build/'cu66_scale_tdp_v107.sv').read_text()+(build/'cu66_mode_store_v107.sv').read_text()==s
  shutil.copyfile(vectors,build/'vectors.txt')
  command(['verilator','--version'],'version.log',30)
  compile('scratch_probe',['observed_original.sv','observed_candidate.sv','scratch_probe.sv','tb_bank.cpp'])
  for seed in (112101,112102):
   name=f'scratch-{seed}.log';command([mapped+'/scratch_probe-obj/Vscratch_probe',str(seed),mapped+f'/scratch-{seed}.jsonl'],name,180)
   v=json.loads((out/name).read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['full_transactions']==72 and v['corrupt_response_cases']==128 and v['read_owner_cases']==4 and v['bank_mask']==15 and v['offset_mask']==65535 and v['dc_line_boundary_transactions']==48 and v['begin_input_noise_edges']>10000;r['scratch_runs'].append(v)
  compile('admission_probe',['admission_original.sv','admission_candidate.sv','cu66_scale_tdp_v107.sv','cu66_mode_store_v107.sv','admission_probe.sv','tb_admission.cpp'])
  # These independent replay helpers remain frozen and read candidate events.
  replaymod=module(ROOT/'scripts/cu66-v107/tables.py')
  for seed in (112201,112202):
   name=f'admission-{seed}.log';command([mapped+'/admission_probe-obj/Vadmission_probe',mapped+'/vectors.txt',str(seed)],name,240)
   v=json.loads((out/name).read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['prepared_edges']==348673 and v['header_prepared_edges']==738933 and v['scale_prepared_edges']==40585 and v['mode_prepared_edges']==158230
   replay=dict(terminal_verdict=v,seed=seed,coordinate=replaymod.replay(build/'trace.jsonl',vectors),quant=replaymod.quant_replay(build/'trace.jsonl',vectors),scale=replaymod.scale_replay(build/'scale-ports.csv'),mode=replaymod.mode_replay(build/'mode-ports.jsonl',seed));r['admission_runs'].append(replay)
   for stem in ('trace.jsonl','scale-ports.csv','mode-ports.jsonl'):(build/stem).rename(build/(str(seed)+'-'+stem))
  compile('geometry_probe',['geometry_probe.sv','tb_geometry.cpp'])
  for seed in (112301,112302):
   name=f'geometry-{seed}.log';command([mapped+'/geometry_probe-obj/Vgeometry_probe',str(seed)],name,120);v=json.loads((out/name).read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['all_mask_counts']==65536 and v['generic_tiles']==262208;r['domain_runs'].append(v)
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p)for p in files};r.update(status='PASS',actual_RTL_run=True,frozen_after_focused_PASS=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in sorted([*build.glob('*.jsonl'),*build.glob('*.csv')]):
   with p.open('rb')as source,(out/(p.name+'.gz')).open('wb')as dest:
    with gzip.GzipFile(filename='',fileobj=dest,mode='wb',mtime=0)as z:shutil.copyfileobj(source,z)
  r['wall_seconds']=time.monotonic()-started;r['artifacts_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT)),selected_report_sha256=sha(out/'results.json')));print('V112_CONTROL_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
