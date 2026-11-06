#!/usr/bin/env python3
"""Strict lint/build and finite transactional tests; separate V80 build tree."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[4]
component=root/'fpga/experiments/cu66-v80/integration'
subprocess.run(['docker','exec','gamebub-cu66-v69-build','mkdir','-p','/build/v80-integration/reference_path'],check=True)
cmd=['verilator','--cc','--exe','--build','-j','1','--Wall','--top-module','cu80_reference_path','--Mdir','/build/v80-integration/reference_path',f'-I{root}/fpga/experiments/cu66-v70/memory',str(component/'cu80_reference_path.sv'),str(root/'fpga/experiments/cu66-v79/prefetch/cu79_reference_prefetch.sv'),str(component/'tb_reference_path.cpp')]
for name,args in [('build.log',cmd),('run.log',['/build/v80-integration/reference_path/Vcu80_reference_path'])]:
 with (component/name).open('w') as log:
  p=subprocess.run(['docker','exec','gamebub-cu66-v69-build',*args],stdout=log,stderr=subprocess.STDOUT)
 if p.returncode:
  print((component/name).read_text());raise SystemExit(p.returncode)
 print((component/name).read_text()[-1800:])
