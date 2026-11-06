#!/usr/bin/env python3
"""Strict native functional cache regression; no controller/target timing claim."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v77/cache'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=[AREA/'cu77_direct_cache.sv',AREA/'tb_cache.cpp',Path(__file__).resolve(),ROOT/'fpga/experiments/cu66-v76/service/trace.mem'];pins={str(p.relative_to(ROOT)):sha(p)for p in src};commands=[]
 def run(argv,name,t=600):
  with(AREA/name).open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=t)
  commands.append(dict(argv=argv,log=str((AREA/name).relative_to(ROOT)),exit_code=r.returncode,sha256=sha(AREA/name)));assert r.returncode==0,(name,r.returncode)
  return(AREA/name).read_text()
 run(['docker','exec','gamebub-cu66-v69-build','verilator','--cc','--exe','--build','-j','1','--Wall','--top-module','cu77_direct_cache','--Mdir','/build/v77-cache','-CFLAGS','-O2 -std=c++17',str(src[0]),str(src[1])],'build.log')
 rows=[]
 for seed in (0,7701,7702):
  log=run(['docker','exec','gamebub-cu66-v69-build','/build/v77-cache/Vcu77_direct_cache',str(seed),str(src[-1])],f'run-{seed}.log')
  m=re.search(r'^CACHE_PASS (.+)$',log,re.M);assert m and 'FAIL'not in log
  row={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',m[1])};assert row['rasters']==2 and row['active_pixels']==691200 and row['fault_probes']==26 and row['invalid_requests']==16 and row['canceled_pixel_responses']==1 and row['accepted_pixel_queries']==row['pixel_responses']+row['canceled_pixel_responses'];rows.append(row)
 assert pins=={str(p.relative_to(ROOT)):sha(p)for p in src}
 d=dict(schema='cu77-cache-regression-v1',status='PASS',source_sha256=pins,commands=commands,runs=rows,full_synthetic_rasters=sum(r['rasters']for r in rows),active_pixels=sum(r['active_pixels']for r in rows),scope='actual streamed RTL cache/neighborhood query, synthetic independent physicalmemory/pixel oracle, perstrip miss-set equality to frozenV76trace',limitations=['ideal delayed memorysource not realcontroller','no targetfit/route/Fmax/CDC or physical30fps/sub10ms result','native converter/fullreceiver integration separate'])
 (AREA/'results.json').write_text(json.dumps(d,indent=2)+'\n');print('V77_CACHE_REGRESSION_PASS')
if __name__=='__main__':main()
