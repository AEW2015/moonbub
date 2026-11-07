#!/usr/bin/env python3
"""Retained versus independent tile BL8 gathers using actual-source chroma-prefill order."""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91l-rowpair'
PREFILL = ROOT / 'experiments/python-gamebub-v91l-tiled'
SOURCE = ROOT / 'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
    out = AREA / 'comparison-attempts' / stamp
    out.mkdir(parents=True)
    sources = [AREA/'tile_rowpair_reader.sv', AREA/'tb_rowpair.cpp', Path(__file__).resolve(),
               PREFILL/'prefill_model.py', ROOT/'fpga/experiments/cu66-v91k-lines/canonical_line_reader.sv',
               ROOT/'fpga/experiments/cu66-v91k-lines/canonical_rgb565_lines.sv',
               ROOT/'fpga/experiments/cu66-v91k-lines/tb_lines.cpp',
               ROOT/'fpga/experiments/cu66-v91k-cache/canonical_rgb565_cached.sv']
    inputs = [SOURCE/'inputs/canonical_actual.tsv.gz', SOURCE/'results.json',
              PREFILL/'vectors/prefill-lines.hex.gz', PREFILL/'prefill-results.json']
    report = dict(schema='cu66-v91l-rowpair-comparison-v1', status='FAIL',
                  source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},
                  inputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs},
                  commands=[], modes=[], seeds=[912501,912502],
                  service='One aligned16-byte physical request/response owner; eight payload cycles plus1..5 seeded wait cycles, seeded request ready stalls. No SDRAM commands/refresh/arbiter.',
                  schedule_provenance='DERIVED_SOURCE_CHROMA_PREFILL_ORDER; not captured per-address RTL trace',
                  physical_hardware_tested=False, physical_sdram_controller_join=False,
                  actual_converter_rtl_join=False, shared_service_complete=False,
                  sustained_hardware_30fps_proven=False, validated_full_frame_under10ms_proven=False)
    started = time.monotonic()
    temporary = []
    def command(argv, name, timeout):
        entry = dict(argv=argv,log=name,exit_code=None)
        report['commands'].append(entry)
        with (out/name).open('w') as log:
            result = subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        entry['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError(f'command exit {result.returncode}: {out/name}')
    try:
        for source in sources:
            target=out/'sources'/source.relative_to(ROOT)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
        for source in inputs:
            target=out/'inputs'/source.name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
        prefill=read(PREFILL/'prefill-results.json')
        assert prefill['status']=='PASS_PYTHON_SOURCE_DERIVED_EXACT'
        assert prefill['generator_sha256']==sha(PREFILL/'prefill_model.py')
        assert prefill['vector']['gzip_sha256']==sha(PREFILL/'vectors/prefill-lines.hex.gz')
        report['input_expansions']=[]
        for packed,plain in (('canonical_actual.tsv.gz','canonical.tsv'),('prefill-lines.hex.gz','prefill.hex')):
            target=out/plain;target.write_bytes(gzip.decompress((out/'inputs'/packed).read_bytes()));temporary.append(target)
            report['input_expansions'].append(dict(path=plain,sha256=sha(target),compressed_path='inputs/'+packed,compressed_sha256=sha(out/'inputs'/packed)))
        golden={}
        for line in (out/'canonical.tsv').read_text().splitlines():
            name,profile,payload=line.split('\t')
            if profile=='0' and name in ('actual_001','actual_006'):
                raw=bytes.fromhex(payload);assert len(raw)==518400
                golden[name]=dict(bytes=518400,sha256=hashlib.sha256(raw).hexdigest())
        assert set(golden)=={'actual_001','actual_006'}
        report['goldens']=golden
        command(['docker','exec',CONTAINER,'verilator','--version'],'tool-version.log',30)
        command(['docker','exec',CONTAINER,'g++','--version'],'compiler-version.log',30)
        for variant,retain in (('independent',0),('retained',1)):
            build='/build/v91l-rowpair-'+stamp+'-'+variant
            snapshot=lambda p:str(out/'sources'/p.relative_to(ROOT))
            command(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','--assert','-Wall','-j','2',
                     '--top-module','tile_rowpair_reader',"-GRETAIN_ROWS=1'b"+str(retain),'--Mdir',build,
                     '-CFLAGS','-std=c++20 -O2 -Wall -Wextra -Werror',snapshot(sources[0]),snapshot(sources[1])],
                    'compile-'+variant+'.log',600)
            for seed in report['seeds']:
                directory=out/(variant+'-'+str(seed));directory.mkdir()
                mode=dict(variant=variant,retain=retain,seed=seed,status='FAIL',event_log=str(directory.relative_to(out)/'events.jsonl.gz'))
                report['modes'].append(mode)
                command(['docker','exec',CONTAINER,build+'/Vtile_rowpair_reader',str(out/'canonical.tsv'),str(out/'prefill.hex'),
                         str(directory/'events.jsonl'),str(directory),str(seed),str(retain)],
                        'simulation-'+variant+'-'+str(seed)+'.log',600)
                verdict=[];frames=[];checks=[]
                with (directory/'events.jsonl').open() as stream:
                    for line in stream:
                        event=json.loads(line)
                        if event['type']=='verdict':verdict.append(event)
                        elif event['type']=='frame':frames.append(event)
                        elif event['type']=='check':
                            assert event['status']=='PASS'
                            checks.append(event['name'])
                assert len(verdict)==1 and verdict[0]['status']=='TEST_PASS'
                assert verdict[0]['seed']==seed and verdict[0]['retain']==retain
                assert len(frames)==2 and verdict[0]['checks']==len(checks)==17
                for frame in frames:
                    output=directory/frame['output']
                    assert output.stat().st_size==golden[frame['name']]['bytes']
                    frame['output_sha256']=sha(output)
                    assert frame['output_sha256']==golden[frame['name']]['sha256']
                    assert frame['physical_reads']==(32400 if retain else 64800)
                    assert frame['requests']==32400 and frame['bytes']==518400
                mode.update(status='PASS_BYTE_EXACT_PREFILL_ORDER_AND_OWNERSHIP_UNIT_TESTS',verdict=verdict[0],frames=frames,checks=checks)
        report['comparisons']=[]
        for seed in report['seeds']:
            baseline=next(m for m in report['modes'] if m['seed']==seed and m['retain']==0)
            candidate=next(m for m in report['modes'] if m['seed']==seed and m['retain']==1)
            for before,after in zip(baseline['frames'],candidate['frames']):
                assert before['name']==after['name'] and before['output_sha256']==after['output_sha256']
                report['comparisons'].append(dict(seed=seed,frame=after['name'],independent_bl8=before['physical_reads'],retained_bl8=after['physical_reads'],
                                                  independent_cycles=before['cycles'],retained_cycles=after['cycles'],
                                                  component_cycle_reduction_percent=(before['cycles']-after['cycles'])/before['cycles']*100))
        assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sources}
        assert report['inputs_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in inputs}
        report['status']='PASS_STATIC_ROWPAIR_PREFILL_COMPARISON'
    except BaseException as error:
        report.update(error_class=type(error).__name__,error=str(error))
        raise
    finally:
        for path in temporary:
            if path.exists():path.unlink()
        report['compressed_artifacts']={}
        for path in sorted(out.glob('*/events.jsonl')):
            raw=path.read_bytes();packed=path.with_suffix('.jsonl.gz')
            packed.write_bytes(gzip.compress(raw,mtime=0))
            assert gzip.decompress(packed.read_bytes())==raw
            report['compressed_artifacts'][str(path.relative_to(out))]=dict(path=str(packed.relative_to(out)),gzip_sha256=sha(packed),raw_sha256=hashlib.sha256(raw).hexdigest(),rows=len(raw.splitlines()))
            path.unlink()
        report['wall_seconds']=time.monotonic()-started
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        (AREA/'comparison-results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
        print('ROWPAIR_COMPARISON',report['status'],out,flush=True)


if __name__=='__main__':
    main()
