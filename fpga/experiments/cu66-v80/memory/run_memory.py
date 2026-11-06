#!/usr/bin/env python3
"""Bounded raw stream arbitration test through frozen bridge/controller/model."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[4];area=root/'fpga/experiments/cu66-v80/memory'
base=['docker','exec','gamebub-cu66-v69-build']
sources=[area/'tb_memory_v80.sv',area/'cu80_memory_system.sv']+[root/'fpga/experiments/cu66-v74/memory'/s for s in ('cu74_word_bridge.sv','cu74_tile_memory.sv')]+[root/'fpga/experiments/cu66-v72/memory'/s for s in ('cu72_sdram_controller.sv','cu72_sdram_model.sv')]
for tac in (2,7):
 build=f'/build/v80-integration/memory-tac{tac}'
 subprocess.run(base+['mkdir','-p',build],check=True)
 cmd=base+['verilator','--binary','--timing','--Wall','-Wno-BLKSEQ','--top-module','tb_memory_v80',f'-GTAC_NS={tac}.0','--Mdir',build,'-j','1','-DSIMULATION',f'-I{root}/fpga/experiments/cu66-v70/memory',*map(str,sources)]
 for name,args in [(f'build-tac{tac}.log',cmd),(f'run-tac{tac}.log',base+[build+'/Vtb_memory_v80'])]:
  with (area/name).open('w') as f:p=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT)
  if p.returncode:print((area/name).read_text());raise SystemExit(p.returncode)
  if name.startswith('run'):print((area/name).read_text())
