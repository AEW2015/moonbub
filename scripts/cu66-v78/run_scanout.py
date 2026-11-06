#!/usr/bin/env python3
"""Continuous native pixel replay of committed descriptors through direct scanout."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v78/scanout';NATIVE=ROOT/'experiments/cu66-native-v69'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 sources=[AREA/'cu78_direct_scanout.sv',ROOT/'fpga/experiments/cu66-v77/render/cu77_render_bounded_sim.sv',ROOT/'fpga/experiments/cu66-v77/cache/cu77_direct_cache_bounded.sv',ROOT/'fpga/experiments/cu66-v77/render/cu77_yuv_rgb.sv',ROOT/'fpga/experiments/cu66-v70/display/cu70_lcd_lines.sv']
 files=sources+[AREA/'tb_scanout.cpp',Path(__file__).resolve(),NATIVE/'index.tsv',*NATIVE.glob('*.hpp')]
 for line in (NATIVE/'index.tsv').read_text().splitlines()[:3]:files.append(NATIVE/line.split('\t')[2])
 pins={str(p.relative_to(ROOT)):sha(p)for p in files};commands=[]
 def run(argv,name,t):
  path=AREA/name
  with path.open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=t)
  commands.append(dict(argv=argv,log=str(path.relative_to(ROOT)),exit_code=r.returncode,sha256=sha(path)))
  assert r.returncode==0,(name,r.returncode)
  return path.read_text()
 run(['docker','exec','gamebub-cu66-v69-build','verilator','--cc','--exe','--build','-j','1','--timing','--Wall','-Wno-BLKSEQ','-Wno-PINCONNECTEMPTY','--top-module','cu78_direct_scanout','--Mdir','/build/v78-scanout','-CFLAGS','-O2 -std=c++17',*map(str,sources),str(AREA/'tb_scanout.cpp')],'build.log',1200)
 rows=[]
 for seed in (0,7801):
  log=run(['docker','exec','gamebub-cu66-v69-build','/build/v78-scanout/Vcu78_direct_scanout',str(NATIVE/'index.tsv'),str(seed)],f'run-{seed}.log',1200);m=re.search(r'^SCANOUT_PASS (.+)$',log,re.M);assert m and 'FAIL'not in log
  row={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',m[1])};assert row['descriptor_wait_cycles']>0 and row['distinct_sources']==3 and row['invalid_descriptors']==5 and row['late_pending']==1 and row['underruns']==row['memory_errors']==0 and row['native_pixels']==row['exact_pixels'];rows.append(row)
 assert pins=={p:sha(ROOT/p)for p in pins},'sourceschanged'
 result=dict(schema='cu78-continuous-scanout-v1',status='PASS_EXACT_CONTINUOUS_NATIVE_SCANOUT',source_sha256=pins,commands=commands,runs=rows,scope='Actual direct cache/converter/native LCD RTL with ideal delayed immutable memory of native CPU-decoded fixtures; three committed source epochs, repeats and late pending descriptor without per-source reset',limitations=['Not actual SDRAM or FPGA packet decoder; fullsystem integration separate','No physical30fps/under10ms decode/targetfit/Fmax/CDC proof','Fatal cache/memory failures latch diagnostic stop until reset; global recovery not qualified'])
 (AREA/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('V78_SCANOUT_EVIDENCE_PASS')
if __name__=='__main__':main()
