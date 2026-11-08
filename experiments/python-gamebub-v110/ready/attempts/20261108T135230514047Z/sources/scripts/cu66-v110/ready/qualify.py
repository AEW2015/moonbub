#!/usr/bin/env python3
"""Strict complete existing-edge ready pair and unchanged independent oracle; --run opts in."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v110-ready';AREA=ROOT/'experiments/python-gamebub-v110/ready';IMAGE='gamebub-cu66-v69-tools:20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def verify():
 recipe=json.loads((SRC/'edit-recipe.json').read_text())
 for e in recipe['production'].values():
  p=ROOT/e['original'];q=ROOT/e['candidate'];assert sha(p)==e['original_sha256'] and sha(q)==e['candidate_sha256'];s=p.read_text()
  for x in e['edits']:assert s.count(x['before'])==1;s=s.replace(x['before'],x['after'],1)
  assert s==q.read_text()
  for x in reversed(e['edits']):assert s.count(x['after'])==1;s=s.replace(x['after'],x['before'],1)
  assert s==p.read_text()
 assert json.loads((AREA/'model.json').read_text())['status']=='PASS_SOURCE_AND_EXHAUSTIVE_PREDICATE_MODEL_NOT_RTL'
 return recipe

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');args=ap.parse_args();recipe=verify()
 if not args.run:print('READY_QUALIFICATION_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v110-ready-'+stamp);build.mkdir();mapped='/build/'+build.name
 card=json.loads((ROOT/'experiments/python-gamebub-v110/prepared/v110-combined-dequant-20261108T133243897862Z-6c73c6/preflight.json').read_text())
 excluded={'cs88_pipeline_v91k.sv','cs88_coefficients_v91k.sv','cu66_inverse_stream_v91j.sv','cu66_reconstruct_stream_v91k.sv','cu66_dequant.sv','cu66_idct8x8.sv','cu66_reconstruct_tile.sv','cu66_coefficient_elastic.sv','cu66_quant_rom.svh'}
 children=[ROOT/m['path'] for a,m in card['source_contract']['source_origins'].items()if Path(a).name not in excluded]
 assert len(children)==9
 packpath=ROOT/'fpga/experiments/cu66-v107-tables/packaging.json'
 files=sorted(set([p for p in SRC.rglob('*')if p.is_file()]+children+[ROOT/e['original']for e in recipe['production'].values()]+[p for p in Path(__file__).parent.glob('*.py')]+[AREA/'preparation.json',AREA/'model.json',packpath]))
 r=dict(schema='v110-ready-existing-edge-operands-focused-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},production=[dict(path=e['candidate'],sha256=e['candidate_sha256']) for e in recipe['production'].values()],replacements=[dict(original=e['original'],candidate=e['candidate']) for e in recipe['production'].values()],commands=[],runs=[],memory_samples=[],strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,added_public_cycles=0,scope='Complete selected V109 producer old/new bodies and actual selected child bodies. Every public output including invalid data/counters, private producer ownership, full raw scale RAM compared. Independent cache count/tag/error/completion/RAM oracle. Explicit verification-only counter preparation covers all2048 count values; does not claim reachability. Frame fixture goldens and full pipeline remain separate root canonical gate.')
 started=time.monotonic()
 def command(argv,name,cap):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
  container='gamebub-v110-ready-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','4g','--memory-swap','4g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
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
  for p in (SRC/'verification').iterdir():
   if p.is_file():shutil.copyfile(p,build/p.name)
  for p in children:shutil.copyfile(p,build/p.name)
  admission=next(p for p in children if p.name=='cs88_admission_v91i2a.sv');pack=json.loads(packpath.read_text());data=admission.read_bytes();assert sha(admission)==pack['production_sha256'];offsets=[0]+pack['split_byte_offsets']+[len(data)];fragments=[]
  for j,m in enumerate(pack['fragments']):
   p=build/m['filename'];p.write_bytes(data[offsets[j]:offsets[j+1]]);assert sha(p)==m['sha256'];fragments.append(p)
  assert b''.join(p.read_bytes()for p in fragments)==data;r['lossless_admission_packaging']=pack
  compiled=[mapped+'/'+p.name for p in children]+[mapped+'/'+p.name for p in fragments[1:]]
  command(['verilator','--version'],'version.log',30)
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-I'+mapped,'-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror','--top-module','ready_probe','--Mdir',mapped+'/ready-obj',*compiled,*[mapped+'/'+n for n in ('ready_original.sv','ready_candidate.sv','ready_probe.sv','tb_ready.cpp')]],'ready-compile.log',600)
  assert '%Warning-'not in(out/'ready-compile.log').read_text();r['binary_sha256']=sha(build/'ready-obj/Vready_probe')
  for seed in(111001,111002):
   name=f'ready-{seed}.log';command([mapped+'/ready-obj/Vready_probe',str(seed),mapped+f'/ready-{seed}.csv'],name,120)
   v=json.loads((out/name).read_text());assert v['status']=='TEST_PASS' and v['prepared_counter_cases']==2048 and v['cache_beats']>10000 and v['public_comparisons']>50000;r['runs'].append(v)
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r.update(status='PASS',actual_RTL_run=True,frozen_after_focused_PASS=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in build.glob('ready-*.csv'):
   with p.open('rb') as source,(out/(p.name+'.gz')).open('wb') as dest:
    with gzip.GzipFile(filename='',fileobj=dest,mode='wb',mtime=0) as z:shutil.copyfileobj(source,z)
  r['wall_seconds']=time.monotonic()-started;r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT)),selected_report_sha256=sha(out/'results.json')));print('READY_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
