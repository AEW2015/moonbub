#!/usr/bin/env python3
"""Dual-simulator dirty-strip rollback and subsequent overwrite checks."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
CONTAINER=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    files=[HERE/'cu70_painter_strip.sv',HERE/'tb_painter_strip_control.sv',Path(__file__).resolve()]
    before={str(p.relative_to(ROOT)):sha(p)for p in files}
    commands=[]
    def run(argv,name):
        p=HERE/name
        with p.open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=300)
        commands.append({'argv':argv,'exit_code':r.returncode,'log':str(p.relative_to(ROOT)),'sha256':sha(p)})
        assert r.returncode==0,(name,r.returncode)
        return p.read_text()
    src=list(map(str,files[:2]))
    run(['docker','exec',CONTAINER,'iverilog','-g2012','-s','tb_painter_strip_control','-o','/build/v70-display-strip-control-final.vvp',*src],'strip-control-final-iverilog-build.log')
    a=run(['docker','exec',CONTAINER,'vvp','/build/v70-display-strip-control-final.vvp'],'strip-control-final-iverilog.log')
    run(['docker','exec',CONTAINER,'verilator','--binary','--timing','--build','-j','2','--Wall','-Wno-BLKSEQ','--top-module','tb_painter_strip_control','--Mdir','/build/v70-display-strip-control-final',*src],'strip-control-final-verilator-build.log')
    b=run(['docker','exec',CONTAINER,'/build/v70-display-strip-control-final/Vtb_painter_strip_control'],'strip-control-final-verilator.log')
    marker='TEST_PASS_STRIP_CONTROL dirty_pixels_discarded=123 no_premature_canvas_writes=1 new_bias=91 first_contiguous_words=8 reads=4680 strip_pixels=5760 abort_drained=1'
    assert marker in a and marker in b and'FATAL'not in a and'FAIL'not in b
    assert before=={str(p.relative_to(ROOT)):sha(p)for p in files}
    (HERE/'strip-control-results.json').write_text(json.dumps({'status':'PASS','source_sha256':before,'commands':commands,'contract':'discard123dirtyRGBstripwordswithoutcanvaswrites; newframewithdifferentYbiasoverwritesoldstrip; first8portraitwordscontiguous+exact; acceptedmemorydrainedafterabort','testbench_style_waiver':'BLKSEQonlyforproceduralclock/oracletemporaries; nofunctionalassertionssuppressed'},indent=2)+'\n')
    print('STRIP_CONTROL_PASS backends=2 dirty_strip_abort=1 fresh_bias_overwrite=1 contiguous_first_words=8')


if __name__=='__main__':main()
