#!/usr/bin/env python3
"""Separate bounded-address cache variant, same unchanged native render oracle."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'fpga/experiments/cu66-v77/render';AREA=BASE/'bounded';NATIVE=ROOT/'experiments/cu66-native-v69'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 AREA.mkdir(exist_ok=True);sources=[ROOT/'fpga/experiments/cu66-v77/cache/cu77_direct_cache_bounded.sv',BASE/'cu77_yuv_rgb.sv',BASE/'cu77_render_bounded_sim.sv']
 files=sources+[BASE/'tb_render.cpp',BASE/'results.json',Path(__file__).resolve(),NATIVE/'index.tsv',*NATIVE.glob('*.hpp'),*sorted((NATIVE/'fixtures').glob('*.cu66'))];pins={str(p.relative_to(ROOT)):sha(p)for p in files};commands=[]
 def run(argv,name):
  path=AREA/name
  with path.open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=600)
  commands.append(dict(argv=argv,log=str(path.relative_to(ROOT)),exit_code=r.returncode,sha256=sha(path)));assert r.returncode==0,(name,r.returncode);return path.read_text()
 run(['docker','exec','gamebub-cu66-v69-build','verilator','--cc','--exe','--build','-j','1','--Wall','--top-module','cu77_render_bounded_sim','--prefix','Vcu77_render_sim','--Mdir','/build/v77-render-bounded','-CFLAGS','-O2 -std=c++17',*map(str,sources),str(BASE/'tb_render.cpp')],'build.log')
 baseline=json.loads((BASE/'results.json').read_text());runs=[]
 for seed in(0,7701,7702):
  log=run(['docker','exec','gamebub-cu66-v69-build','/build/v77-render-bounded/Vcu77_render_sim',str(NATIVE/'index.tsv'),str(seed)],f'run-{seed}.log');assert f'RENDER_PASS actual_frames=8 patterns=4 recovery=1 full_frames=13 RGB_words=4492800 fault_probes={2 if seed else 0} seed={seed}'in log and 'FAIL'not in log
  rows=[{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}for line in log.splitlines()if line.startswith('RENDER_CASE_PASS')];old=next(x for x in baseline['runs']if x['seed']==seed);assert rows==old['per_case'],'bounded address variant changed case counters/cycles'
  runs.append(dict(seed=seed,full_frames=13,fault_probes=2 if seed else 0,per_case=rows))
 assert pins=={str(p.relative_to(ROOT)):sha(p)for p in files},'inputs changed'
 result=dict(schema='cu77-bounded-native-render-v1',status='PASS_NATIVE_CACHE_BACKED_RGB_AND_BASE_PARITY',source_sha256=pins,commands=commands,runs=runs,total_frames=39,total_active_RGB_words=13478400,fault_probes=4,base_native_case_counters_identical=True,scope='Separate bounded-address cache RTL with unchanged converter and native frame/memory oracle; ideal delayed streamed memory, not realSDRAM or pixelclockCDC',limitations=['No targetfit/route/Fmax/physical30fps/sub10ms proof','Full native parity is finite regression, not formal equivalence or whole receiver/frontbank lease proof'])
 (AREA/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('V77_BOUNDED_RENDER_PASS frames=39 RGB_words=13478400 faults=4 base_cycles_equal=true')
if __name__=='__main__':main()
