#!/usr/bin/env python3
"""Strict complete existing-edge dequant pair and unchanged independent oracle; --run opts in."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v110-dequant';AREA=ROOT/'experiments/python-gamebub-v110/dequant';IMAGE='gamebub-cu66-v69-tools:20261105'
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
 a=json.loads((SRC/'adapters.json').read_text())
 for e in a['adapters']:
  p=ROOT/e['source'];q=ROOT/e['path'];assert sha(p)==e['source_sha256'] and sha(q)==e['sha256'];s=p.read_text()
  for before,after in e['renames']:assert s.count(before)==1;s=s.replace(before,after,1)
  assert s==q.read_text()
 for name,h in a['unchanged_fixtures'].items():assert sha(ROOT/name)==h and (ROOT/name).read_bytes()==(SRC/Path(name).name).read_bytes()
 assert (SRC/'tb_dequant.cpp').read_bytes()==(ROOT/'fpga/experiments/cu66-v107-payload-reset/tb_dequant.cpp').read_bytes()
 return recipe

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');args=ap.parse_args();recipe=verify()
 if not args.run:print('DEQUANT_QUALIFICATION_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v110-dequant-'+stamp);build.mkdir();mapped='/build/'+build.name
 files=sorted(set([p for p in SRC.rglob('*') if p.is_file()]+[ROOT/e['original'] for e in recipe['production'].values()]+[p for p in Path(__file__).parent.glob('*.py')]+[AREA/'preparation.json',AREA/'model.json']+[ROOT/'fpga/experiments/cu66-v107-payload-reset'/n for n in ('tb_dequant.cpp','dequant_probe.sv')]+[ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',ROOT/'experiments/cu66-native-v69/generated_constants.hpp']))
 r=dict(schema='v110-dequant-existing-edge-operands-focused-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},production=[dict(path=e['candidate'],sha256=e['candidate_sha256']) for e in recipe['production'].values()],replacements=[dict(original=e['original'],candidate=e['candidate']) for e in recipe['production'].values()],commands=[],runs=[],memory_samples=[],strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,added_public_cycles=0,scope='Complete actual V107 payload-reset dequant versus existing-edge operand preparation; unchanged full independent integer/partial-output oracle. Every public output including invalid partial data compared on every cycle. No private intermediate equality assumed; owned operand/product invariants added. No full pipeline, physical timing or hardware claim.')
 started=time.monotonic()
 def command(argv,name,cap):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
  container='gamebub-v110-dequant-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','4g','--memory-swap','4g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  e=dict(argv=cmd,resource_before=gate,timeout_seconds=cap);r['commands'].append(e);began=time.monotonic();stop=None;last=-5;pressure_breaches=0
  with (out/name).open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    elapsed=time.monotonic()-began
    if elapsed-last>=5:
     sample=dict(command=name,elapsed_seconds=elapsed,**memory());r['memory_samples'].append(sample);last=elapsed
     pressure_breaches=pressure_breaches+1 if sample['psi_full_avg10']>=5 else 0
     if sample['available_bytes']<4*1024**3 or pressure_breaches>=2:stop='HOST_MEMORY_GATE'
    if elapsed>cap+20:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);break
    time.sleep(.5)
   code=proc.wait(timeout=20)
  e.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-began);assert code==0 and not stop,(name,code,stop)
 try:
  for p in files:q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for p in SRC.iterdir():
   if p.is_file():shutil.copyfile(p,build/p.name)
  for p in (ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',ROOT/'experiments/cu66-native-v69/generated_constants.hpp'):shutil.copyfile(p,build/p.name)
  command(['verilator','--version'],'version.log',30)
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--language','1800-2017','-I'+mapped,'-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror -I'+mapped,'--top-module','dequant_probe','--Mdir',mapped+'/dequant-obj',*[mapped+'/'+n for n in ('dequant_original.sv','dequant_candidate.sv','dequant_probe.sv','tb_dequant.cpp')]],'dequant-compile.log',240)
  assert '%Warning-' not in (out/'dequant-compile.log').read_text();r['binary_sha256']=sha(build/'dequant-obj/Vdequant_probe')
  for seed in (110901,110902,110903):
   name=f'dequant-{seed}.log';command([mapped+'/dequant-obj/Vdequant_probe',str(seed),mapped+f'/dequant-{seed}.csv'],name,90)
   v=json.loads((out/name).read_text());assert v['status']=='TEST_PASS' and v['accepted']==v['retired']+v['discarded'] and v['multiply_edges']>5000 and v['held_edges']>100 and v['kill_edges']>100 and v['idle_invalid_edges']>100;r['runs'].append(v)
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r.update(status='PASS',actual_RTL_run=True,frozen_after_focused_PASS=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in build.glob('dequant-*.csv'):
   with p.open('rb') as source,(out/(p.name+'.gz')).open('wb') as dest:
    with gzip.GzipFile(filename='',fileobj=dest,mode='wb',mtime=0) as z:shutil.copyfileobj(source,z)
  r['wall_seconds']=time.monotonic()-started;r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT)),selected_report_sha256=sha(out/'results.json')));print('DEQUANT_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
