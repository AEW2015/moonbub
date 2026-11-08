#!/usr/bin/env python3
"""Strict actual one-entry coefficient stage with latency-aware token/fence oracle."""
import datetime,gzip,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FPGA=ROOT/'fpga/experiments/cu66-v107-elastic'
AREA=ROOT/'experiments/python-gamebub-v107/elastic'
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'))
from run_rtl import resources

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,r):p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
def main():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v107-elastic-'+stamp);build.mkdir();mapped='/build/'+build.name
 files=[*sorted(FPGA.glob('*.*')),Path(__file__),*sorted((ROOT/'scripts/cu66-v107/elastic').glob('*.py'))]
 r={'schema':'v107-coefficient-elastic-unit-v1','status':'FAIL','source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in files},'commands':[],'runs':[],'strict_warnings':True,'warning_suppression':False,'assertions_disabled_or_downgraded':False,'limits':['Actual stage unit simulation with independent token/fence scoreboard; no complete pipeline, routed timing or hardware qualification.','Added one coefficient register; parent transcript checks must tolerate declared latency while preserving values/order/ownership/fault results.']}
 def cmd(args,name,timeout):
  gate=resources();argv=['docker','exec','-e','OMP_NUM_THREADS=1','-w',mapped,'gamebub-cu66-v69-build','timeout','--kill-after=5s',str(timeout)+'s']+args;start=time.monotonic()
  with (build/name).open('w') as log:p=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+15)
  r['commands'].append({'argv':argv,'exit_code':p.returncode,'wall_seconds':time.monotonic()-start,'resource_gate':gate});assert p.returncode==0,(name,p.returncode)
 try:
  for p in files:
   q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for name in ['cu66_coefficient_elastic.sv','tb_elastic.cpp']:shutil.copyfile(FPGA/name,build/name)
  cmd(['verilator','--version'],'tool.log',30)
  cmd(['verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--top-module','cu66_coefficient_elastic','--Mdir',mapped+'/obj','-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',mapped+'/cu66_coefficient_elastic.sv',mapped+'/tb_elastic.cpp'],'compile.log',300)
  assert '%Warning-' not in (build/'compile.log').read_text()
  cmd(['sha256sum',mapped+'/obj/Vcu66_coefficient_elastic'],'binary.log',30)
  for seed in [107601,107602,107603]:
   cmd([mapped+'/obj/Vcu66_coefficient_elastic',str(seed),mapped+'/trace-'+str(seed)+'.jsonl'],'seed-'+str(seed)+'.log',120)
   v=json.loads((build/('seed-'+str(seed)+'.log')).read_text());assert v['status']=='TEST_PASS';r['runs'].append(v)
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files}
  r['status']='PASS_ACTUAL_ELASTIC_UNIT';r['actual_clock_edges']=sum(x['edges'] for x in r['runs']);r['stage']={'path':str((FPGA/'cu66_coefficient_elastic.sv').relative_to(ROOT)),'sha256':sha(FPGA/'cu66_coefficient_elastic.sv')};r['top']={'path':str((FPGA/'cs88_pipeline_v91k.sv').relative_to(ROOT)),'sha256':sha(FPGA/'cs88_pipeline_v91k.sv')}
 except BaseException as e:r.update(error_class=type(e).__name__,error=str(e));raise
 finally:
  for p in sorted(build.iterdir()):
   if not p.is_file():continue
   if p.suffix=='.jsonl':
    with p.open('rb') as src,(out/(p.name+'.gz')).open('wb') as dst:
     with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
   else:shutil.copyfile(p,out/p.name)
  r['artifact_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};save(out/'receipt.json',r)
  save(AREA/'results.json',{'status':r['status'],'selected_receipt':str((out/'receipt.json').relative_to(ROOT)),'receipt_sha256':sha(out/'receipt.json')});print(r['status'],out,flush=True)
if __name__=='__main__':main()
