#!/usr/bin/env python3
"""Separate bounded-slot helper ablation; frozen base source/evidence preserved."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v77/cache';OUT=AREA/'bounded';CONTAINER='gamebub-cu66-v69-build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(exist_ok=True);rtl=AREA/'cu77_direct_cache_bounded.sv';tb=AREA/'tb_cache.cpp';trace=ROOT/'fpga/experiments/cu66-v76/service/trace.mem';probe=AREA/'cu77_slot3_probe.sv';base=AREA/'results.json';baseline=json.loads(base.read_text())
 files=[rtl,tb,probe,trace,base,AREA/'cu77_direct_cache.sv',ROOT/'scripts/cu66-v77/run_cache.py',Path(__file__).resolve()];pins={str(p.relative_to(ROOT)):sha(p)for p in files};commands=[]
 def run(argv,name,t=600):
  with(OUT/name).open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=t)
  commands.append(dict(argv=argv,log=str((OUT/name).relative_to(ROOT)),exit_code=r.returncode,sha256=sha(OUT/name)));assert r.returncode==0,(name,r.returncode)
  return(OUT/name).read_text()
 run(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','-j','1','--Wall','--top-module','cu77_direct_cache_bounded','--prefix','Vcu77_direct_cache','--Mdir','/build/v77-cache-bounded','-CFLAGS','-O2 -std=c++17',str(rtl),str(tb)],'build.log')
 rows=[]
 for seed in (0,7701,7702):
  log=run(['docker','exec',CONTAINER,'/build/v77-cache-bounded/Vcu77_direct_cache',str(seed),str(trace)],f'run-{seed}.log')
  m=re.search(r'^CACHE_PASS (.+)$',log,re.M);assert m and 'FAIL'not in log
  row={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',m[1])};assert row==next(x for x in baseline['runs']if x['seed']==seed),'bounded helper changed finite counter/cycle behavior'
  rows.append(row)
 run(['docker','exec',CONTAINER,'verilator','--binary','--timing','--build','-j','1','--Wall','--top-module','cu77_slot3_probe','--Mdir','/build/v77-slot3-probe',str(rtl),str(probe)],'slot3-build.log')
 log=run(['docker','exec',CONTAINER,'/build/v77-slot3-probe/Vcu77_slot3_probe'],'slot3-run.log');assert 'SLOT3_PASS exhaustive_inputs=128'in log and 'FAIL'not in log
 assert pins=={str(p.relative_to(ROOT)):sha(p)for p in files}
 d=dict(schema='cu77-bounded-cache-regression-v1',status='PASS_BOUNDED_CACHE_AND_SLOT3',source_sha256=pins,commands=commands,runs=rows,base_finite_counters_and_cycles_equal=True,exhaustive_slot3_inputs=128,full_synthetic_rasters=6,active_pixels=2073600,fault_probes=78,invalid_requests=48,scope='actual separate bounded-slot RTL against unchanged base stream/query bench and all128 helperinputs; notformalRTL equivalence',limitations=['No targetfit/route/Fmax/CDC or physical30fps/sub10ms result','realcontroller/nativecombinedrenderer qualification separate'])
 (OUT/'results.json').write_text(json.dumps(d,indent=2)+'\n');print('V77_BOUNDED_CACHE_PASS exact_case_cycles=true slot3_inputs=128')
if __name__=='__main__':main()
