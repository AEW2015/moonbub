#!/usr/bin/env python3
"""Bounded V130 admission-pair experiment: immutable inputs and actual RTL."""
from pathlib import Path
import datetime,hashlib,json,re,shutil,subprocess,time
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v130/active-prefetch'
SRC=ROOT/'fpga/experiments/cu66-v130-active-prefetch'
BUILD=Path('/home/lori/gamebub-build/cu66-v69')
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
BASE=ROOT/'fpga/experiments/cu66-v130-spec-read/cs88_admission_v91i2a.sv'
FIX=ROOT/'experiments/python-gamebub-v91i/vectors/vectors.txt'
G=1024**3
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel=lambda p:str(Path(p).resolve().relative_to(ROOT))
def mem():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()}
 q=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
 return {'available':m['MemAvailable'],'psi_full_avg10':float(q.split('avg10=')[1].split()[0]),'combined_used':(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal'])}
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def main():
 deriv=json.loads((SRC/'derivation.json').read_text());assert sha(BASE)==deriv['source_sha256'];orig=BASE.read_text();cand=(SRC/'cs88_admission_v91i2a.sv').read_text();check=orig
 for e in deriv['edits']:
  assert check.count(e['old'])==1;check=check.replace(e['old'],e['new'],1)
 assert check==cand and sha(SRC/'cs88_admission_v91i2a.sv')==deriv['candidate_sha256']
 for e in reversed(deriv['edits']):
  assert check.count(e['new'])==1;check=check.replace(e['new'],e['old'],1)
 assert check==orig
 files=[BASE,FIX,*sorted(SRC.glob('*')),ROOT/'scripts/cu66-v130/active-prefetch/prepare.py',Path(__file__).resolve()]
 assert all(p.is_file() for p in files)
 status=mem();assert status['available']>=8*G and status['psi_full_avg10']<1 and status['combined_used']<.85,status
 active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines();assert sum(bool(re.match(r'^gamebub-v\d+-',n)) for n in active)<2
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=BUILD/('v130-active-prefetch-'+stamp);build.mkdir();mapped='/work'
 pins={rel(p):sha(p) for p in files}
 for p in files:
  target=out/'sources'/rel(p);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
 freeze={'status':'FROZEN_BEFORE_EXECUTION','source_sha256':pins,'image':IMAGE};write(out/'freeze.json',freeze)
 rec={'status':'RUNNING','actual_RTL_run':False,'source_sha256':pins,'freeze_sha256':sha(out/'freeze.json'),'commands':[],'memory_samples':[],'scope':'two actual admission FSMs; injected active-map states, valid-qualified invalid data; not full parent or timing'};write(out/'receipt.json',rec)
 print('ACTIVE_PREFETCH_STARTED',rel(out),flush=True)
 def run(args,tag,timeout,expected_failure=None):
  m=mem();assert m['available']>=8*G and m['psi_full_avg10']<1 and m['combined_used']<.85,m
  name='gamebub-v130-active-prefetch-'+stamp.lower()+'-'+tag
  cmd=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={out}/sources,dst=/src,readonly','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(timeout)+'s']+args
  entry={'argv':cmd};rec['commands'].append(entry);write(out/'receipt.json',rec);start=time.monotonic();last=-15;high=0;stop=None
  with (out/(tag+'.log')).open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    elapsed=time.monotonic()-start
    if elapsed-last>=15:
     s=mem();rec['memory_samples'].append(dict(command=tag,elapsed=elapsed,**s));last=elapsed;high=high+1 if s['psi_full_avg10']>=5 else 0
     if s['available']<4*G or high>=2 or s['combined_used']>=.90:stop='HOST_MEMORY_PRESSURE'
    if elapsed>timeout+30:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','10',name],capture_output=True,timeout=20);break
    time.sleep(1)
   code=proc.wait(timeout=30)
  entry.update(exit_code=code,stop=stop,wall_seconds=time.monotonic()-start);write(out/'receipt.json',rec);assert stop is None and ((code==0) if expected_failure is None else (code!=0 and code not in (124,137))),(tag,code,stop)
  result=(out/(tag+'.log')).read_text()
  if expected_failure is not None:assert expected_failure in result,(tag,result[-600:])
  return result
 try:
  src='/src/'+rel(SRC)
  compile=['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--language','1800-2017','--top-module','admission_pair','--Mdir','/work/obj','-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror']+[src+'/'+n for n in ['admission_original.sv','admission_candidate.sv','cu66_scale_tdp_v107.sv','cu66_mode_store_v107.sv','admission_pair.sv','tb_pair.cpp']]
  run(compile,'compile',900);rec['binary_sha256']=sha(build/'obj/Vadmission_pair');rec['actual_RTL_run']=True
  rec['runs']=[]
  for seed in (130301,130302):
   log=run(['/work/obj/Vadmission_pair','/src/'+rel(FIX),str(seed)],'seed-'+str(seed),600)
   data=[json.loads(x) for x in log.splitlines() if x.startswith('{')];assert len(data)==2 and all(x['status']=='PASS' for x in data) and data[0]['type']=='scan' and data[0]['cases']==6 and data[0]['cancellations']==15 and data[1]['seed']==seed;rec['runs'].append(data)
  rec['status']='PASS'
 except Exception as e:rec.update(status='FAIL',error=repr(e))
 rec['source_snapshot_unchanged']=all(sha(ROOT/p)==h and sha(out/'sources'/p)==h for p,h in pins.items())
 if not rec['source_snapshot_unchanged']:rec.update(status='FAIL',error='source changed')
 rec['artifact_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='receipt.json'};write(out/'receipt.json',rec)
 if rec['status']=='PASS':write(AREA/'results.json',{'status':'PASS','path':rel(out/'receipt.json'),'sha256':sha(out/'receipt.json'),'actual_RTL_run':True})
 print('ACTIVE_PREFETCH_FINISHED',rec['status'],rel(out/'receipt.json'),rec.get('error',''),flush=True)
 if rec['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
