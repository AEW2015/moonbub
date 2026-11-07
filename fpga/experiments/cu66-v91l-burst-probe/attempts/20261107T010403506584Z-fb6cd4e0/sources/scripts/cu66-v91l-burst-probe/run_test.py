#!/usr/bin/env python3
"""Finite strict RTL test for the direct-read probe's ownership boundaries."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v91l-burst-probe'
CONTAINER='gamebub-cu66-v69-build'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
    out=AREA/'attempts'/stamp; out.mkdir(parents=True)
    sources=[ROOT/'fpga/experiments/cu66-v91l-burst-converter/canonical_line_reader.sv',AREA/'tb_probe.cpp',Path(__file__).resolve()]
    report=dict(schema='cu66-v91l-direct-probe-contract-v1',status='FAIL',source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},commands=[],hardware_tested=False)
    begin=time.monotonic()
    def command(argv,name,timeout):
        entry=dict(argv=argv,log=name); report['commands'].append(entry)
        with (out/name).open('w') as stream:
            result=subprocess.run(argv,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
        entry['exit_code']=result.returncode
        if result.returncode: raise RuntimeError(f'{name} failed with {result.returncode}')
    try:
        for p in sources:
            target=out/'sources'/p.relative_to(ROOT); target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,target)
        snap=lambda p:str(out/'sources'/p.relative_to(ROOT))
        command(['docker','exec',CONTAINER,'verilator','--version'],'tool-version.log',30)
        command(['docker','exec',CONTAINER,'g++','--version'],'compiler-version.log',30)
        build='/build/v91l-probe-'+stamp
        command(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','--timing','--assert','-Wall','--timescale','1ns/1ps','-j','2','--top-module','canonical_line_reader','--Mdir',build,'-CFLAGS','-std=c++20 -O2 -Wall -Wextra -Werror',*[snap(p) for p in sources[:2]]],'compile.log',600)
        command(['docker','exec',CONTAINER,build+'/Vcanonical_line_reader'],'run.log',30)
        verdict=json.loads((out/'run.log').read_text()); assert verdict['status']=='PASS_DIRECT_PROBE_OWNERSHIP'
        assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sources}
        report.update(status='PASS_DIRECT_PROBE_OWNERSHIP',verdict=verdict,
            scope='Directed standalone RTL adapter contract only; no formal/exhaustive, physical timing, complete codec or live hardware claim.')
    except BaseException as error:
        report.update(error_class=type(error).__name__,error=str(error)); raise
    finally:
        report['wall_seconds']=time.monotonic()-begin
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        (AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
        print(json.dumps(dict(status=report['status'],attempt=str(out.relative_to(ROOT)))))
if __name__=='__main__': main()
