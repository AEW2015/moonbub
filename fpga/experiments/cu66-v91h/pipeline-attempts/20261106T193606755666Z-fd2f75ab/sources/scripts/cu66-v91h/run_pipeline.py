#!/usr/bin/env python3
"""Qualify static synchronous packet RAM against the frozen V91g2 control."""
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
import telemetry

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v91h'
VECTORS=ROOT/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'
CONTAINER='gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compress_trace(path):
    if not path.exists():return None
    target=path.with_suffix(path.suffix+'.gz')
    with path.open('rb') as src,target.open('wb') as dst:
        with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0,compresslevel=9) as out:
            shutil.copyfileobj(src,out)
    data=gzip.decompress(target.read_bytes())
    assert hashlib.sha256(data).hexdigest()==sha(path)
    receipt=dict(path=target.name,gzip_sha256=sha(target),jsonl_sha256=sha(path),records=len(data.splitlines()))
    path.unlink()
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,default=910432)
    args=parser.parse_args()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'pipeline-attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    build='/build/v91h-pipeline-'+out.name
    sv=[ROOT/'fpga/experiments/cu66-v91/br88_rice_elastic.sv',
        ROOT/'fpga/experiments/cu66-v91b/br88_context.sv',
        ROOT/'fpga/experiments/cu66-v91d/br88_packet_ingress.sv',
        ROOT/'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv',
        AREA/'br88_packet_ingress_v91h.sv',AREA/'br88_pipeline_v91h.sv']
    cpp=AREA/'tb_pipeline.cpp'
    old_hazard=ROOT/'fpga/experiments/cu66-v91g2/tb_scratch_hazards.cpp'
    sources=sv+[cpp,old_hazard,Path(__file__).resolve(),Path(telemetry.__file__).resolve(),telemetry.CONTRACT_PATH]
    report=dict(schema='cu66-v91h-observed-coefficient-pipeline-v1',status='FAIL',seed=args.seed,
        source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},vectors_sha256=sha(VECTORS),
        vector_index_sha256=sha(VECTORS.with_name('index.json')),commands=[],build_directory=build,
        scope='Static synchronous packet-staging port qualification; coded two-bank coefficient endpoint. No mapped BRAM fit, routed clock, calibrated transport/memory, hardware fps or full-frame validated decode result.',
        fence='Start excluded; active rising edges through dense coefficient completion; packet/metadata/dense/publication fences distinct.',
        full_frame_publication_timestamp=None,full_frame_decode_under10ms_proven=False,hardware_distinct_30fps_proven=False)
    started=time.monotonic()
    def command(argv,name,timeout):
        entry=dict(argv=argv,log=name,exit_code=None);report['commands'].append(entry)
        with (out/name).open('w') as f:
            result=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
        entry['exit_code']=result.returncode
        if result.returncode:raise RuntimeError(f'Command exit {result.returncode}: {out/name}')
    def snapshot(p):return str(out/'sources'/p.relative_to(ROOT))
    try:
        for p in sources:
            dest=Path(snapshot(p));dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        shutil.copyfile(VECTORS,out/'vectors.jsonl.gz');shutil.copyfile(VECTORS.with_name('index.json'),out/'index.json')
        cases=telemetry.cases();text_path=out/'vectors.txt'
        text_path.write_text(''.join(' '.join(map(str,(r['id'],r['blocks'],r['packet_hex'],r['dense_hex'],r['packed_hex'])))+'\n' for r in cases))
        report['text_vectors_sha256']=sha(text_path)
        command(['docker','exec',CONTAINER,'verilator','--version'],'tool-version.log',30)
        command(['docker','exec',CONTAINER,'g++','--version'],'compiler-version.log',30)
        commands=['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','-j','2','--assert','-Wall']
        for mode,label in ((0,'legacy'),(1,'sync')):
            binary_build=build+'-'+label
            command(commands+['--top-module','br88_pipeline_v91h','--Mdir',binary_build,f'-GSYNC_STAGING={mode}',
                '-CFLAGS',f'-std=c++17 -O2 -Wall -Wextra -Werror -DSYNC_STAGING={mode}',
                *[snapshot(p) for p in sv+[cpp]]],f'compile-{label}.log',300)
            command(['docker','exec',CONTAINER,binary_build+'/Vbr88_pipeline_v91h',str(text_path),str(args.seed),
                str(out/f'tile-events-{label}.jsonl')],f'simulation-{label}.jsonl',600)
        hazard_build=build+'-hazards'
        command(commands+['--top-module','packed_scratch_v91g2','--Mdir',hazard_build,
            '-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',snapshot(sv[3]),snapshot(old_hazard)],'hazard-compile.log',300)
        command(['docker','exec',CONTAINER,hazard_build+'/Vpacked_scratch_v91g2'],'hazards.jsonl',60)
        hazards=[json.loads(s) for s in (out/'hazards.jsonl').read_text().splitlines()]
        assert len(hazards)==1 and hazards[0]['status']=='TEST_PASS' and hazards[0]['directed_checks']==9
        report['scratch_hazards']=hazards[0]
        with (out/'simulation.jsonl').open('wb') as f:
            for label in ('legacy','sync'):f.write((out/f'simulation-{label}.jsonl').read_bytes())
        with (out/'tile-events.jsonl').open('wb') as f:
            for label in ('legacy','sync'):
                path=out/f'tile-events-{label}.jsonl';f.write(path.read_bytes());path.unlink()
        report['tile_trace']=compress_trace(out/'tile-events.jsonl')
        rows=[json.loads(s) for s in (out/'simulation.jsonl').read_text().splitlines()]
        verdicts=[r for r in rows if r['type']=='verdict']
        assert len(verdicts)==2 and {r['sync_staging'] for r in verdicts}=={0,1}
        for v in verdicts:
            assert v['status']=='TEST_PASS' and v['seed']==args.seed and v['packets']==len(cases)==20
            assert v['case_rows']==40 and v['configurations']==2 and v['directed_checks']>=47
            assert v['dense_comparisons']==sum(r['blocks']*64 for r in cases)*2
        records=telemetry.validate_rows(rows,cases)
        baseline=telemetry.compare_v91g2(records,args.seed)
        tiles=telemetry.validate_tiles(out/report['tile_trace']['path'],records,cases)
        assert report['tile_trace']['records']==sum(r['blocks'] for r in cases)*4
        (out/'tile-summary.json').write_text(json.dumps(tiles,indent=2)+'\n')
        report.update(verdicts=verdicts,baseline_v91g2=baseline,population_totals=telemetry.aggregate(records),
            tile_summary_sha256=sha(out/'tile-summary.json'),telemetry_reconciliation='PASS_TWO_STATIC_MODES_WITH_EXACT_LEGACY_CONTROL')
        assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sources}
        assert report['vectors_sha256']==sha(VECTORS) and report['vector_index_sha256']==sha(VECTORS.with_name('index.json'))
        report['status']='PASS_SYNCHRONOUS_STAGING_WITH_FROZEN_V91G2_CONTROL';text_path.unlink()
    except BaseException as e:
        report.update(status='FAIL',error_class=type(e).__name__,error=str(e));raise
    finally:
        if 'tile_trace' not in report:
            traces=[]
            for p in sorted(out.glob('tile-events*.jsonl')):
                item=compress_trace(p)
                if item:traces.append(item)
            if traces:report['partial_tile_traces']=traces
        report['wall_seconds']=time.monotonic()-started
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        (AREA/'pipeline-results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
        print('V91H_PIPELINE',report['status'],out,flush=True)


if __name__=='__main__':main()
