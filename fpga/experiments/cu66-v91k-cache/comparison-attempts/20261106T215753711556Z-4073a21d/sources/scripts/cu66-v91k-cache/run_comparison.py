#!/usr/bin/env python3
"""Strict unchanged-control versus bounded registered chroma-cache RTL replay."""
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
AREA=ROOT/'fpga/experiments/cu66-v91k-cache'
MODEL=ROOT/'experiments/python-gamebub-v91k-cache'
BASE=ROOT/'fpga/experiments/cu66-v91k/rgb'
OLD_SUMMARY=ROOT/'experiments/python-gamebub-v91k/summary.json'
OLD_AUDIT=OLD_SUMMARY.with_name('audit.json')
RGB_GOLDENS=ROOT/'experiments/python-gamebub-v91k/vectors/rgb_goldens.tsv.gz'
CONTAINER='gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seed',type=int,choices=(911601,911602),default=911601)
    args=ap.parse_args()
    prior=json.loads(OLD_SUMMARY.read_text())
    selected=next(item for item in prior['attempts'] if item['seed']==args.seed-100)
    prior_path=ROOT/selected['path'];assert sha(prior_path)==selected['sha256']
    old_report=json.loads(prior_path.read_text())
    assert old_report['status']=='PASS_CANONICAL_AND_BASE_RGB565_RTL_REPLAY'
    actual_source=prior_path.parent/old_report['canonical_actual']['path']
    assert sha(actual_source)==old_report['canonical_actual']['gzip_sha256']
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'comparison-attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    source_paths=[BASE/'canonical_rgb565_v91k.sv',BASE/'tb_rgb.cpp',AREA/'canonical_rgb565_cached.sv',AREA/'tb_cache.cpp',
                  MODEL/'model.py',ROOT/'docs/cu66-v91k-cache/cache-contract.md',Path(__file__).resolve()]
    inputs=[OLD_SUMMARY,OLD_AUDIT,RGB_GOLDENS,prior_path,actual_source,MODEL/'model-results.json']
    report=dict(schema='cu66-v91k-chroma-cache-comparison-v1',status='FAIL',seed=args.seed,
        source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in source_paths},
        inputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        source_canonical_receipt=dict(source_report=str(prior_path.relative_to(ROOT)),source_report_sha256=sha(prior_path),
            source_seed=old_report['seed'],path=str(actual_source.relative_to(ROOT)),sha256=sha(actual_source),
            raw_sha256=old_report['canonical_actual']['raw_sha256'],rows=12),
        commands=[],input_expansions=[],verdicts={},
        service_rule='Both benches: FAST ready/no stalls, matching byte ACK two edges postaccept; SLOW same seeded rule of random request/output stalls and ACK two through six edges. Scheduling changes RNG consumption; absolute stall traces differ. FAST isolates deterministic schedule; SLOW is a measured comparison under the declared common service rules.',
        full_frame_publication_timestamp=None,hardware_distinct_30fps_proven=False,
        full_frame_decode_under10ms_proven=False,mapped_cache_fit_proven=False,
        monolithic_full_frame_rtl_proven=False)
    start=time.monotonic();build='/build/v91k-cache-'+out.name;temporary=[]

    def command(argv,name,timeout):
        entry=dict(argv=argv,log=name,exit_code=None);report['commands'].append(entry)
        with (out/name).open('w') as log:
            result=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=timeout,cwd=ROOT)
        entry['exit_code']=result.returncode
        if result.returncode:raise RuntimeError(f'Command exit {result.returncode}: {out/name}')

    try:
        for source in source_paths:
            target=out/'sources'/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        (out/'inputs').mkdir()
        for source,name in ((actual_source,'canonical_actual.tsv.gz'),(RGB_GOLDENS,'rgb_goldens.tsv.gz'),
                            (prior_path,'v91k-source-report.json'),(OLD_SUMMARY,'v91k-summary.json'),
                            (OLD_AUDIT,'v91k-audit.json'),(MODEL/'model-results.json','model-results.json')):
            shutil.copyfile(source,out/'inputs'/name)
        for name in ('canonical_actual','rgb_goldens'):
            packed=out/'inputs'/(name+'.tsv.gz');plain=out/(name+'.tsv');raw=gzip.decompress(packed.read_bytes());plain.write_bytes(raw);temporary.append(plain)
            report['input_expansions'].append(dict(path=plain.name,compressed_path=str(packed.relative_to(out)),
                compressed_sha256=sha(packed),raw_sha256=sha(plain),rows=len(raw.splitlines())))
        command(['docker','exec',CONTAINER,'verilator','--version'],'tool-version.log',30)
        command(['docker','exec',CONTAINER,'g++','--version'],'compiler-version.log',30)
        snapshot=lambda path:str(out/'sources'/path.relative_to(ROOT))
        base=['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','-j','2','--assert','-Wall',
              '-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror']
        for label,top,sv,cpp in (('control','canonical_rgb565_v91k',source_paths[0],source_paths[1]),
                                 ('cache','canonical_rgb565_cached',source_paths[2],source_paths[3])):
            target=build+'-'+label
            command(base+['--top-module',top,'--Mdir',target,snapshot(sv),snapshot(cpp)],'compile-'+label+'.log',300)
            argv=['docker','exec',CONTAINER,target+'/V'+top,str(out/'canonical_actual.tsv'),str(out/'rgb_goldens.tsv'),str(args.seed)]
            if label=='cache':argv.append(str(out/'cache-events.jsonl'))
            command(argv,'simulation-'+label+'.jsonl',900)
            rows=[json.loads(line) for line in (out/('simulation-'+label+'.jsonl')).read_text().splitlines()]
            verdicts=[row for row in rows if row['type']=='verdict']
            assert len(verdicts)==1 and verdicts[0]['status']=='TEST_PASS'
            assert verdicts[0]['seed']==args.seed and verdicts[0]['cases']==12 and verdicts[0]['pixels']==4147200
            assert verdicts[0]['reads_per_frame']==(3110400 if label=='control' else 518400)
            report['verdicts'][label]=verdicts[0]
        report['status']='PASS_EXACT_REGISTERED_CHROMA_CACHE_COMPARISON'
        assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in source_paths}
        assert report['inputs_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in inputs}
    except BaseException as error:
        report.update(status='FAIL',error_class=type(error).__name__,error=str(error));raise
    finally:
        for path in temporary:
            if path.exists():path.unlink()
        events=out/'cache-events.jsonl'
        if events.exists():
            raw=events.read_bytes();packed=events.with_suffix(events.suffix+'.gz')
            with packed.open('wb') as dest:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dest,mtime=0,compresslevel=9) as stream:stream.write(raw)
            assert gzip.decompress(packed.read_bytes())==raw
            report['row_trace']=dict(path=packed.name,gzip_sha256=sha(packed),raw_sha256=sha(events),rows=len(raw.splitlines()))
            events.unlink()
        report['wall_seconds']=time.monotonic()-start
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        (AREA/'comparison-results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
        print('CHROMA_CACHE',report['status'],out,flush=True)


if __name__=='__main__':
    main()
