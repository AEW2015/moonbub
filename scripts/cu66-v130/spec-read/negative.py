#!/usr/bin/env python3
"""Build and detect two intentionally broken actual-admission RTL variants."""
from pathlib import Path
import datetime,hashlib,json,re,shutil,subprocess,time
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v130/spec-read/negative'
SRC=ROOT/'fpga/experiments/cu66-v130-spec-read'
FIX=ROOT/'experiments/python-gamebub-v91i/vectors/vectors.txt'
BUILD=Path('/home/lori/gamebub-build/cu66-v69')
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf';G=1024**3
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel=lambda p:str(Path(p).resolve().relative_to(ROOT))
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def mem():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};q=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
 return {'available':m['MemAvailable'],'psi_full_avg10':float(q.split('avg10=')[1].split()[0]),'combined_used':(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal'])}
def main():
 m=mem();assert m['available']>=8*G and m['psi_full_avg10']<1 and m['combined_used']<.85,m
 assert sum(bool(re.match(r'^gamebub-v\d+-',n)) for n in subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines())<2
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=BUILD/('v130-spec-negative-'+stamp);build.mkdir()
 inputs=[FIX,*sorted(p for p in SRC.glob('*') if p.is_file()),Path(__file__).resolve()];pins={rel(p):sha(p) for p in inputs}
 for p in inputs:
  dst=out/'sources'/rel(p);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
 candidate=(SRC/'admission_candidate.sv').read_text()
 changes={
 'unclamped':('((replay_addr<32\'d49152) ? replay_addr[15:0] : 16\'d0)','replay_addr[15:0]'),
 'abort_mask_removed':('state==FINISHED&&!reset&&!start&&!abort_packet&&replay_addr<size_bytes','state==FINISHED&&!reset&&!start&&replay_addr<size_bytes')}
 for name,(old,new) in changes.items():
  assert candidate.count(old)==1;d=out/'mutants'/name;d.mkdir(parents=True);(d/'admission_candidate.sv').write_text(candidate.replace(old,new,1))
 freeze={'status':'FROZEN_BEFORE_EXECUTION','source_sha256':pins,'mutants':{n:sha(out/'mutants'/n/'admission_candidate.sv') for n in changes},'image':IMAGE};write(out/'freeze.json',freeze)
 rec={'status':'RUNNING','actual_RTL_run':False,'freeze_sha256':sha(out/'freeze.json'),'source_sha256':pins,'mutants':freeze['mutants'],'commands':[],'runs':[],'memory_samples':[],'scope':'negative controls are intentionally incorrect and are not promoted RTL'};write(out/'receipt.json',rec)
 print('SPEC_NEGATIVE_STARTED',rel(out),flush=True)
 def command(args,tag,timeout,expected):
  m=mem();assert m['available']>=8*G and m['psi_full_avg10']<1 and m['combined_used']<.85,m
  name='gamebub-v130-spec-negative-'+stamp.lower()+'-'+tag
  cmd=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={out},dst=/snapshot,readonly','--mount',f'type=bind,src={build},dst=/work','-w','/work',IMAGE,'timeout','--kill-after=5s',str(timeout)+'s']+args
  entry={'argv':cmd};rec['commands'].append(entry);write(out/'receipt.json',rec);last=-15;high=0;stop=None;t=time.monotonic()
  with (out/(tag+'.log')).open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    age=time.monotonic()-t
    if age-last>=15:
     s=mem();rec['memory_samples'].append(dict(command=tag,elapsed=age,**s));last=age;high=high+1 if s['psi_full_avg10']>=5 else 0
     if s['available']<4*G or high>=2 or s['combined_used']>=.90:stop='HOST_MEMORY_PRESSURE'
    if age>timeout+30:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','10',name],capture_output=True,timeout=20);break
    time.sleep(1)
   code=proc.wait(timeout=30)
  entry.update(exit_code=code,stop=stop,wall_seconds=time.monotonic()-t);write(out/'receipt.json',rec)
  assert stop is None and ((code==0) if expected=='success' else (code!=0 and code not in (124,137))), (tag,code,stop)
  return (out/(tag+'.log')).read_text(errors='replace')
 try:
  src='/snapshot/sources/'+rel(SRC);fix='/snapshot/sources/'+rel(FIX)
  for name in changes:
   files=[src+'/admission_original.sv','/snapshot/mutants/'+name+'/admission_candidate.sv',src+'/cu66_scale_tdp_v107.sv',src+'/cu66_mode_store_v107.sv',src+'/admission_pair.sv',src+'/tb_pair.cpp']
   command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--language','1800-2017','--top-module','admission_pair','--Mdir','/work/'+name,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror']+files,'compile-'+name,900,'success')
   rec['actual_RTL_run']=True;log=command(['/work/'+name+'/Vadmission_pair',fix,'130101'],'mutant-'+name,600,'failure')
   expected='speculative RAM address out of bounds' if name=='unclamped' else 'public output mismatch';assert expected in log,(name,log[-600:])
   rec['runs'].append({'mutant':name,'expected_failure':expected,'observed_detection':True})
  rec['status']='PASS_NEGATIVE_CONTROLS'
 except Exception as e:rec.update(status='FAIL',error=repr(e))
 rec['source_snapshot_unchanged']=all(sha(ROOT/p)==h and sha(out/'sources'/p)==h for p,h in pins.items());rec['mutants_unchanged']=all(sha(out/'mutants'/n/'admission_candidate.sv')==h for n,h in freeze['mutants'].items())
 if not rec['source_snapshot_unchanged'] or not rec['mutants_unchanged']:rec.update(status='FAIL',error='snapshot changed')
 rec['artifact_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='receipt.json'};write(out/'receipt.json',rec)
 if rec['status']=='PASS_NEGATIVE_CONTROLS':write(AREA/'results.json',{'status':rec['status'],'path':rel(out/'receipt.json'),'sha256':sha(out/'receipt.json'),'actual_RTL_run':True})
 print('SPEC_NEGATIVE_FINISHED',rec['status'],rel(out/'receipt.json'),rec.get('error',''),flush=True)
 if rec['status']!='PASS_NEGATIVE_CONTROLS':raise SystemExit(1)
if __name__=='__main__':main()
