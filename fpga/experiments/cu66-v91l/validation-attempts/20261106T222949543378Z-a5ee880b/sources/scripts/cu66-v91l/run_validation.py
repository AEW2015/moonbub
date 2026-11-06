#!/usr/bin/env python3
"""Retain actual RTL C2/seal/atomic-publication tests with explicit software HUD."""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v91l'
MODEL=ROOT/'experiments/python-gamebub-v91l'
CONTAINER='gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seed',type=int,choices=(911801,911802),default=911801)
    args=ap.parse_args()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'validation-attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    sv=[ROOT/'fpga/experiments/cu66-v69/hash/cu66_sha256_bytes.sv',
        ROOT/'fpga/experiments/cu66-v69/banks/cu66_frame_bank_control.sv',
        AREA/'cs88_validate_publish_v91l.sv']
    cpp=AREA/'tb_validate.cpp'
    headers=[ROOT/'experiments/cu66-native-v69'/name for name in ('hud.hpp','bytes.hpp','generated_constants.hpp')]
    sources=[*sv,cpp,*headers,MODEL/'model.py',ROOT/'docs/cu66-v91l/validation-contract.md',Path(__file__).resolve()]
    vector_paths=sorted(path for path in (MODEL/'vectors').rglob('*') if path.is_file())
    report=dict(schema='cu66-v91l-heterogeneous-c2-publication-v1',status='FAIL',seed=args.seed,
        source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},
        vectors_sha256={str(p.relative_to(MODEL/'vectors')):sha(p) for p in vector_paths},
        model_results_sha256=sha(MODEL/'model-results.json'),commands=[],
        scope='Actual packet HU25/HX32/HX33 semantic decoding in frozen native C++; real RTL SHA256 canonical C2 tree/HUD/seal and atomic three-bank commit/presentation. Canonical replay plus finite candidate-write service. Explicit software HUD partition; no full monolithic decoder/display join.',
        full_rtl_hud_decoder=False,full_rtl_hud_overlay=False,monolithic_full_frame_rtl_proven=False,
        complete_v91l_full_rtl_proven=False,hardware_distinct_30fps_proven=False,
        full_frame_decode_under10ms_proven=False,physical_bank_fit_proven=False)
    start=time.monotonic();plain=out/'validation.tsv';build='/build/v91l-'+out.name

    def command(argv,name,timeout):
        item=dict(argv=argv,log=name,exit_code=None);report['commands'].append(item)
        with (out/name).open('w') as log:
            result=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=timeout,cwd=ROOT)
        item['exit_code']=result.returncode
        if result.returncode:raise RuntimeError(f'Command exit {result.returncode}: {out/name}')

    try:
        for source in sources:
            dest=out/'sources'/source.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
        shutil.copytree(MODEL/'vectors',out/'vectors')
        shutil.copyfile(MODEL/'model-results.json',out/'model-results.json')
        packed=out/'vectors/validation.tsv.gz';raw=gzip.decompress(packed.read_bytes());plain.write_bytes(raw)
        report['input_expansion']=dict(path=plain.name,compressed_path='vectors/validation.tsv.gz',
            compressed_sha256=sha(packed),raw_sha256=sha(plain),header=True,rows=len(raw.splitlines())-1)
        assert report['input_expansion']['rows']==7
        command(['docker','exec',CONTAINER,'verilator','--version'],'tool-version.log',30)
        command(['docker','exec',CONTAINER,'g++','--version'],'compiler-version.log',30)
        snapshot=lambda p:str(out/'sources'/p.relative_to(ROOT))
        command(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','-j','2','--assert','-Wall',
                 '--top-module','cs88_validate_publish_v91l','--Mdir',build,
                 '-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',*[snapshot(p) for p in sv],snapshot(cpp)],'compile.log',300)
        command(['docker','exec',CONTAINER,build+'/Vcs88_validate_publish_v91l',str(plain),str(args.seed),str(out/'events.jsonl')],
                'simulation.jsonl',1200)
        rows=[json.loads(line) for line in (out/'simulation.jsonl').read_text().splitlines()]
        verdicts=[row for row in rows if row['type']=='verdict']
        assert len(verdicts)==1 and verdicts[0]['status']=='TEST_PASS'
        assert verdicts[0]['seed']==args.seed and verdicts[0]['cases']==14 and verdicts[0]['source_fixture_frames']==7
        assert verdicts[0]['full_rtl_hud_decoder'] is False
        report['verdict']=verdicts[0]
        assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sources}
        assert report['vectors_sha256']=={str(p.relative_to(MODEL/'vectors')):sha(p) for p in vector_paths}
        assert report['model_results_sha256']==sha(MODEL/'model-results.json')
        report['status']='PASS_C2_AND_ATOMIC_PUBLICATION_WITH_SOFTWARE_HUD'
    except BaseException as error:
        report.update(status='FAIL',error_class=type(error).__name__,error=str(error));raise
    finally:
        if plain.exists():plain.unlink()
        events=out/'events.jsonl'
        if events.exists():
            raw=events.read_bytes();packed=events.with_suffix(events.suffix+'.gz')
            with packed.open('wb') as dest:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dest,mtime=0,compresslevel=9) as z:z.write(raw)
            assert gzip.decompress(packed.read_bytes())==raw
            report['hash_trace']=dict(path=packed.name,gzip_sha256=sha(packed),raw_sha256=sha(events),rows=len(raw.splitlines()))
            events.unlink()
        report['wall_seconds']=time.monotonic()-start
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        (AREA/'validation-results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
        print('V91L_VALIDATION',report['status'],out,flush=True)


if __name__=='__main__':
    main()
