#!/usr/bin/env python3
"""Actual SDRAM/cache/converter and frozen native LCD integration experiment."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v77/system';NATIVE=ROOT/'experiments/cu66-native-v69'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--quick',action='store_true');a=p.parse_args();out=AREA/'quick'if a.quick else AREA;out.mkdir(exist_ok=True)
 sources=[AREA/'cu77_display_sim.sv',ROOT/'fpga/experiments/cu66-v77/cache/cu77_direct_cache.sv',ROOT/'fpga/experiments/cu66-v77/render/cu77_yuv_rgb.sv',*[ROOT/'fpga/experiments/cu66-v74/memory'/n for n in ['cu74_word_bridge.sv','cu74_tile_memory.sv','cu74_memory_system.sv']],*[ROOT/'fpga/experiments/cu66-v72/memory'/n for n in ['cu72_sdram_controller.sv','cu72_sdram_model.sv']],ROOT/'fpga/experiments/cu66-v71/display/cu71_scanout.sv',ROOT/'fpga/experiments/cu66-v70/display/cu70_lcd_lines.sv']
 paths=sources+[AREA/'tb_display.cpp',Path(__file__).resolve(),ROOT/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',*NATIVE.glob('*.hpp'),NATIVE/'index.tsv']
 for line in (NATIVE/'index.tsv').read_text().splitlines()[:2]:paths.append(NATIVE/line.split('\t')[2])
 pins={str(p.relative_to(ROOT)):sha(p)for p in paths};commands=[];runs=[]
 def run(argv,name,timeout):
  path=out/name
  with path.open('w')as f:p=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  commands.append(dict(argv=argv,log=str(path.relative_to(ROOT)),exit_code=p.returncode,sha256=sha(path)))
  if p.returncode:raise RuntimeError(f'{name} exit{p.returncode}; retainedlog')
  return path.read_text()
 for tac in ([2]if a.quick else[2,7]):
  mdir=f'/build/v77-display-tac{tac}'
  run(['docker','exec','gamebub-cu66-v69-build','verilator','--cc','--exe','--build','-j','1','--timing','--Wall','-Wno-BLKSEQ','-Wno-PINCONNECTEMPTY','-DSIMULATION',f'-GTAC_NS={tac}.0','--top-module','cu77_display_sim','--Mdir',mdir,'-CFLAGS','-O2 -std=c++17','-I'+str(ROOT/'fpga/experiments/cu66-v70/memory'),*map(str,sources),str(AREA/'tb_display.cpp')],f'build-tac{tac}.log',1200)
  for bg in ([0]if a.quick else[0,1]):
   log=run(['docker','exec','gamebub-cu66-v69-build',mdir+'/Vcu77_display_sim',str(NATIVE/'index.tsv'),str(bg)],f'run-tac{tac}-bg{bg}.log',600)
   assert 'DIRECT_DISPLAY_PASS frames=2'in log and 'FAIL'not in log
   rows=[{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}for line in log.splitlines()if line.startswith('DISPLAY_CASE_PASS')]
   assert len(rows)==2 and [r['epoch']for r in rows]==[1,2] and [r['bank']for r in rows]==[0,2]
   assert all(r['pixels']==r['good']==384000 and r['mismatches']==r['underruns']==r['memory_errors']==0 and r['exact_rasters']==1 and r['cache_reads']==35040 and r['cache_words']==280320 and r['queries']==345600 and r['released_w']==r['complete_w']and r['released_r']==r['complete_r']for r in rows)
   runs.append(dict(tac_ns=tac,background=bg,frames=rows));print(f'DISPLAY_RUN_PASS tac={tac} bg={bg} frames=2',flush=True)
 assert pins=={p:sha(ROOT/p)for p in pins},'qualifiedsourceschanged'
 d=dict(schema='v77-real-controller-display-v1',status='PASS_EXACT_NATIVE_DISPLAY',quick=a.quick,source_sha256=pins,commands=commands,runs=runs,
  clocks=dict(memory_period_ps=10000,read_phase_degrees=279,pixel_half_period_ps=17029),scope='NewRTLstructuredcache+elasticconverter withactualfrozenSDRAMcontroller/model andfrozenLCDlinebuffers/descriptor, nativeCPUdecodedfixtureplanes physicallyseededthroughrealwrites',limitations=['Not theFPGAdecoder or fullreceiver integrated; nativefixturedecodeCPUtime outside measurement','Each source is one panel with blank/reset between epochs; not seamlessgeneration-switching or continuous30fps proof','SyntheticpacedP0uploads/references at30fps workload, not timedpacketentropydecode','FrozenlinebufferCDC is reused behaviorally; no newtargetCDC/Fmax/fit/bitstream signoff','No physical30fps or validatedunder10msFPGAdecode result'])
 (out/'results.json').write_text(json.dumps(d,indent=2)+'\n');print('V77_DISPLAY_EVIDENCE_PASS')
if __name__=='__main__':main()
