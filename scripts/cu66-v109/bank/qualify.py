#!/usr/bin/env python3
"""Strict complete prefetch/bank scratch pair and unchanged oracles; --run opts in."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v109-bank';AREA=ROOT/'experiments/python-gamebub-v109/bank';IMAGE='gamebub-cu66-v69-tools:20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def verify():
 recipe=json.loads((SRC/'edit-recipe.json').read_text())
 for n,e in recipe['production'].items():
  p=ROOT/e['original'];q=ROOT/e['candidate'];assert sha(p)==e['original_sha256'] and sha(q)==e['candidate_sha256'];s=p.read_text()
  for x in e['edits']:assert s.count(x['before'])==1;s=s.replace(x['before'],x['after'],1)
  assert s==q.read_text()
  for x in reversed(e['edits']):assert s.count(x['after'])==1;s=s.replace(x['after'],x['before'],1)
  assert s==p.read_text()
 a=json.loads((SRC/'verification/adapters.json').read_text())
 for e in a['adapters']:
  p=ROOT/e['source'];q=ROOT/e['path'];assert sha(p)==e['source_sha256'] and sha(q)==e['sha256'];s=p.read_text()
  for before,after in e['renames']:assert s.count(before)==1;s=s.replace(before,after,1)
  assert s==q.read_text()
 for name,h in a['unchanged_fixtures'].items():assert sha(ROOT/name)==h and (ROOT/name).read_bytes()==(SRC/'verification'/Path(name).name).read_bytes()
 for n in ('tb_scratch.cpp','historical_hazards.cpp'):assert (SRC/'verification'/n).read_bytes()==(ROOT/'fpga/experiments/cu66-v106-scratch'/n).read_bytes()
 return recipe

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');args=ap.parse_args();recipe=verify()
 if not args.run:print('BANK_QUALIFICATION_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v109-bank-'+stamp);build.mkdir();mapped='/build/'+build.name
 files=sorted(set([p for p in SRC.rglob('*') if p.is_file()]+[ROOT/e['original'] for e in recipe['production'].values()]+[p for p in Path(__file__).parent.glob('*.py')]+[AREA/'preparation.json',AREA/'model.json']+[ROOT/'fpga/experiments/cu66-v106-scratch'/n for n in ('tb_scratch.cpp','historical_hazards.cpp','adapter.json')]))
 r=dict(schema='v109-onehot-cache-bank-complete-scratch-focused-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},production=[dict(path=e['candidate'],sha256=e['candidate_sha256']) for e in recipe['production'].values()],replacements=[dict(original=e['original'],candidate=e['candidate']) for e in recipe['production'].values()],commands=[],scratch_runs=[],memory_samples=[],strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,added_public_cycles=0,scope='Complete frozen V109 prefetch scratch versus redundant-OH bank scratch; unchanged full V106 scratch/golden/hazard oracles, V108 coherent capacity-prefix plumbing, every existing public/invalid/debug/counter/request comparison active. No four-body recompile, full pipeline, physical timing or hardware claim.')
 started=time.monotonic()
 def command(argv,name,cap):
  gate=memory();assert gate['available_bytes']>=6*1024**3 and gate['psi_full_avg10']<1,gate
  container='gamebub-v109-bank-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','4g','--memory-swap','4g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  e=dict(argv=cmd,resource_before=gate,timeout_seconds=cap);r['commands'].append(e);began=time.monotonic();stop=None;last=-5
  with (out/name).open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    elapsed=time.monotonic()-began
    if elapsed-last>=5:
     sample=dict(command=name,elapsed_seconds=elapsed,**memory());r['memory_samples'].append(sample);last=elapsed
     if sample['available_bytes']<3*1024**3 or sample['psi_full_avg10']>=5:stop='HOST_MEMORY_GATE'
    if elapsed>cap+20:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);break
    time.sleep(.5)
   code=proc.wait(timeout=20)
  e.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-began);assert code==0 and not stop,(name,code,stop)
 try:
  for p in files:q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for p in (SRC/'verification').iterdir():shutil.copyfile(p,build/p.name)
  command(['verilator','--version'],'version.log',30)
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror','--top-module','scratch_probe','--Mdir',mapped+'/scratch-obj',*[mapped+'/'+n for n in ('observed_original.sv','observed_candidate.sv','scratch_probe.sv','tb_bank.cpp')]],'scratch-compile.log',300)
  assert '%Warning-' not in (out/'scratch-compile.log').read_text();r['binary_sha256']=sha(build/'scratch-obj/Vscratch_probe')
  for seed in (109501,109502):
   name=f'scratch-{seed}.log';command([mapped+'/scratch-obj/Vscratch_probe',str(seed),mapped+f'/scratch-{seed}.jsonl'],name,120)
   v=json.loads((out/name).read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['full_transactions']==72 and v['corrupt_response_cases']==128 and v['read_owner_cases']==4 and v['bank_mask']==15 and v['offset_mask']==65535 and v['dc_line_boundary_transactions']==48 and v['begin_input_noise_edges']>10000;r['scratch_runs'].append(v)
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r.update(status='PASS',actual_RTL_run=True,frozen_after_focused_PASS=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in build.glob('scratch-*.jsonl'):
   with p.open('rb') as source,(out/(p.name+'.gz')).open('wb') as dest:
    with gzip.GzipFile(filename='',fileobj=dest,mode='wb',mtime=0) as z:shutil.copyfileobj(source,z)
  r['wall_seconds']=time.monotonic()-started;r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT)),selected_report_sha256=sha(out/'results.json')));print('BANK_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
