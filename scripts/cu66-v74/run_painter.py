#!/usr/bin/env python3
"""Exact portrait output and drain checks for V74 wide-write producer."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v74/display'
NATIVE=ROOT/'experiments/cu66-native-v69'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    files=[AREA/'cu74_painter_burst.sv',AREA/'tb_painter_burst.cpp',Path(__file__).resolve(),NATIVE/'index.tsv',*NATIVE.glob('*.hpp'),*sorted((NATIVE/'fixtures').glob('*.cu66'))]
    before={str(p.relative_to(ROOT)):sha(p) for p in files};commands=[]
    def run(argv,name,timeout=600):
        path=AREA/name
        with path.open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
        commands.append(dict(argv=argv,exit_code=r.returncode,log=str(path.relative_to(ROOT)),sha256=sha(path)))
        if r.returncode:raise RuntimeError(f'{name}: exit {r.returncode}; inspect retained log')
        return path.read_text()
    container=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')
    run(['docker','exec',container,'verilator','--cc','--exe','--build','-j','1','--Wall','--top-module','cu74_painter_burst','--Mdir','/build/v74-painter','-CFLAGS','-O2 -std=c++17',str(AREA/'cu74_painter_burst.sv'),str(AREA/'tb_painter_burst.cpp')],'build.log')
    outputs=[]
    for seed in (0,7201,7202):
        log=run(['docker','exec',container,'/build/v74-painter/Vcu74_painter_burst',str(NATIVE/'index.tsv'),str(seed)],f'run-{seed}.log')
        assert f'PASS actual_frames=8 patterns=4 recovery=1 fault_probes={8 if seed else 0} seed={seed}'in log and 'FAIL'not in log
        assert log.count('START_REJECT_PASS ')==10
        rows=[{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}for line in log.splitlines()if line.startswith('CASE_PASS')]
        good=[r for r in rows if r['mode']==0]
        assert len(good)==13 and all(r['read_commands']==35040 and r['read_words']==280320 and r['write_words']==384000 and r['write_commands']==48000 and r['painted']==345600 for r in good)
        outputs.append(dict(seed=seed,full_rasters=13,fault_probes=8 if seed else 0,per_case=rows))
    assert before=={str(p.relative_to(ROOT)):sha(p) for p in files},'inputs changed'
    result=dict(status='PASS',source_sha256=before,commands=commands,runs=outputs,total_rasters=39,total_compared_RGB_words=14976000,total_fault_probes=16,start_rejects=30,scope='actual V74 painter exact native RGB565/HUD output; ideal delayed BL8 read/write service with request stability and abort/drain; not actual SDRAM service',limitations=['not target clock/fit/BRAM or physical30fps','full command-model system required separately'])
    (AREA/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('V74_PAINTER_EVIDENCE_PASS rasters=39 RGB_words=14976000 write_commands_per_frame=48000 fault_probes=16')

if __name__=='__main__':main()
