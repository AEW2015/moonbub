#!/usr/bin/env python3
"""Strict RGB RTL smoke with an independently known neutral-gray frame."""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import uuid

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v91k/rgb'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    out=AREA/'smoke-attempts'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    sources=[AREA/'canonical_rgb565_v91k.sv',AREA/'tb_rgb.cpp',Path(__file__).resolve()]
    report=dict(status='FAIL',source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},commands=[])
    for source in sources:
        target=out/'sources'/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    canonical=out/'neutral-actual.tsv';rgb=out/'neutral-rgb.tsv'
    canonical.write_text('neutral\t0\t'+('80'*518400)+'\n')
    rgb.write_text('neutral\t'+('1084'*345600)+'\n')
    build='/build/v91k-rgb-smoke-'+out.name
    try:
        commands=[(['docker','exec','gamebub-cu66-v69-build','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--top-module','canonical_rgb565_v91k','--Mdir',build,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',*[str(out/'sources'/p.relative_to(ROOT)) for p in sources[:2]]],'compile.log'),
                  (['docker','exec','gamebub-cu66-v69-build',build+'/Vcanonical_rgb565_v91k',str(canonical),str(rgb),'911501'],'simulation.jsonl')]
        for argv,name in commands:
            with (out/name).open('w') as log:
                result=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=300)
            report['commands'].append(dict(argv=argv,log=name,exit_code=result.returncode))
            assert result.returncode==0,(name,result.returncode)
        rows=[json.loads(line) for line in (out/'simulation.jsonl').read_text().splitlines()]
        assert rows[-1]['status']=='TEST_PASS'
        report.update(status='PASS_NEUTRAL_GRAY_RGB_AND_RECOVERY',verdict=rows[-1])
    finally:
        for path in (canonical,rgb):
            target=path.with_suffix(path.suffix+'.gz')
            with target.open('wb') as dest:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dest,mtime=0) as stream:stream.write(path.read_bytes())
            path.unlink()
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print(report['status'],out,flush=True)

if __name__=='__main__':
    main()
