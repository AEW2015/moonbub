#!/usr/bin/env python3
"""V77 exact elastic pixel pipeline and cache-backed rendering regression."""
import hashlib,json,subprocess,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v77/render'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 files=[AREA/'cu77_yuv_rgb.sv',AREA/'tb_pixel.cpp',Path(__file__).resolve()];pins={str(p.relative_to(ROOT)):sha(p)for p in files};cmds=[]
 def run(argv,name):
  with(AREA/name).open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=600)
  cmds.append(dict(argv=argv,log=str((AREA/name).relative_to(ROOT)),exit_code=r.returncode,sha256=sha(AREA/name)));assert r.returncode==0,(name,r.returncode);return(AREA/name).read_text()
 run(['docker','exec','gamebub-cu66-v69-build','verilator','--cc','--exe','--build','-j','1','--Wall','--top-module','cu77_yuv_rgb','--Mdir','/build/v77-pixel','-CFLAGS','-O2 -std=c++17',str(AREA/'cu77_yuv_rgb.sv'),str(AREA/'tb_pixel.cpp')],'pixel-build.log')
 log=run(['docker','exec','gamebub-cu66-v69-build','/build/v77-pixel/Vcu77_yuv_rgb'],'pixel-run.log');assert 'PIXEL_PASS'in log and 'FAIL'not in log
 pixel_commands=list(cmds)
 assert pins=={str(p.relative_to(ROOT)):sha(p)for p in files}
 (AREA/'pixel-results.json').write_text(json.dumps(dict(status='PASS_EXACT_ELASTIC_PIXEL_PIPELINE',source_sha256=pins,commands=pixel_commands,scope='Exact mathematical CU66 color oracle; bounded random/extreme/stalled elastic arithmetic; not cache/controller/CDC/frameproof'),indent=2)+'\n')
 native=ROOT/'experiments/cu66-native-v69';cache=ROOT/'fpga/experiments/cu66-v77/cache/cu77_direct_cache.sv'
 sources=[cache,AREA/'cu77_yuv_rgb.sv',AREA/'cu77_render_sim.sv']
 files=sources+[AREA/'tb_render.cpp',Path(__file__).resolve(),native/'index.tsv',*native.glob('*.hpp'),*sorted((native/'fixtures').glob('*.cu66'))]
 pins={str(p.relative_to(ROOT)):sha(p)for p in files};cmds=[]
 run(['docker','exec','gamebub-cu66-v69-build','verilator','--cc','--exe','--build','-j','1','--Wall','--top-module','cu77_render_sim','--Mdir','/build/v77-render','-CFLAGS','-O2 -std=c++17',*map(str,sources),str(AREA/'tb_render.cpp')],'build.log')
 runs=[]
 for seed in (0,7701,7702):
  log=run(['docker','exec','gamebub-cu66-v69-build','/build/v77-render/Vcu77_render_sim',str(native/'index.tsv'),str(seed)],f'run-{seed}.log')
  assert f'RENDER_PASS actual_frames=8 patterns=4 recovery=1 full_frames=13 RGB_words=4492800 fault_probes={2 if seed else 0} seed={seed}'in log and 'FAIL'not in log
  rows=[{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',l)}for l in log.splitlines()if l.startswith('RENDER_CASE_PASS')];good=[x for x in rows if x['mode']==0]
  assert len(good)==13 and all(x['commands']==35040 and x['words']==280320 and x['pixels']==345600 and x['accepted']==345600 for x in good)
  runs.append(dict(seed=seed,full_frames=13,fault_probes=2 if seed else 0,per_case=rows))
 assert pins=={str(p.relative_to(ROOT)):sha(p)for p in files},'inputs changed'
 (AREA/'results.json').write_text(json.dumps(dict(status='PASS_NATIVE_CACHE_BACKED_RGB',source_sha256=pins,commands=cmds,runs=runs,total_frames=39,total_active_RGB_words=13478400,fault_probes=4,scope='Actual clocked cache/neighborhood/converter RTL against native decoded YUV/HUD/render fixtures and synthetic patterns with ideal delayed streamed memory; not actual SDRAM or pixelclock CDC',limitations=['100MHz conversion not targetFmax','No complete receiver/descriptorfront/reference lease or physical30fps/sub10ms proof','Only active345600pixels/frame; blackborder/physicalpanel timing separate']),indent=2)+'\n')
 print('V77_RENDER_PASS frames=39 RGB_words=13478400 faults=4')
if __name__=='__main__':main()
