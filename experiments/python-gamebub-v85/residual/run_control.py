#!/usr/bin/env python3
"""Matched all-visible control plus independent encoder corner cases."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import subprocess
import tarfile
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CONTAINER='gamebub-cu66-v69-build'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def stats(v):return dict(min=min(v),median=statistics.median(v),max=max(v),total=sum(v))


def main():
    if (HERE/'matched-control.json').exists():raise FileExistsError('retained matched control exists')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=HERE/'control-attempts'/stamp;out.mkdir(parents=True)
    binary='/build/v85-residual-control-'+stamp
    sources=[Path(__file__).resolve(),HERE/'control.cpp',HERE/'encode.hpp',HERE/'data.py',HERE/'index.json']
    sources+=sorted((ROOT/'experiments/cu66-native-v69').glob('*.hpp'))
    sources+=[ROOT/'experiments/cu66-native-v69/index.tsv']
    pins={str(p.relative_to(ROOT)):sha(p) for p in sources}
    with tarfile.open(out/'sources.tar.gz','w:gz') as tar:
        for p in sources:tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    report=dict(schema='cu66-v85-matched-control-run-v1',status='FAIL',source_sha256=pins)
    started=time.monotonic();commands=[]
    def run(command,filename):
        commands.append(command);r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        (out/filename).write_text(r.stdout+r.stderr)
        if r.returncode:raise RuntimeError(f'{filename} exit {r.returncode}')
    try:
        run(['docker','exec',CONTAINER,'g++','--version'],'compiler.txt')
        run(['docker','exec',CONTAINER,'g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(HERE/'control.cpp'),'-o',binary],'compile.log')
        run(['docker','cp',f'{CONTAINER}:{binary}',str(out/'control.bin')],'copy.log')
        command=['docker','exec',CONTAINER,binary,str(ROOT/'experiments/cu66-native-v69/index.tsv')];commands.append(command)
        r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        (out/'frames.jsonl').write_text(r.stdout);(out/'native.log').write_text(r.stderr)
        assert r.returncode==0,r.stderr
        assert 'V85_ENCODER_SELFTEST_PASS cases=22' in r.stderr and 'V85_MATCHED_CONTROL_PASS frames=457' in r.stderr
        rows=[json.loads(line) for line in r.stdout.splitlines()]
        spec=importlib.util.spec_from_file_location('cu85_control_data',HERE/'data.py');data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)
        for row,frame in zip(rows,data.iter_frames(),strict=True):
            assert (row['cohort'],row['fid'],row['key'])==(frame['cohort'],frame['fid'],frame['key'])
            for axis,chunks in enumerate(frame['variants']['65536']):
                assert len(chunks)<=1
                packet=chunks[0]['data'] if chunks else b''
                assert row['residual_packet_sha256'][axis]==(hashlib.sha256(packet).hexdigest() if packet else '')
                assert row['residual_packet_bytes'][axis]==len(packet)
            assert row['residual_AB38_bytes']==frame['variant_stats']['65536']['AB38_bytes']
            if row['key']:assert row['all_visible_AB38_bytes']==row['residual_AB38_bytes']
        assert len(rows)==457
        assert pins=={name:sha(ROOT/name) for name in pins}
        result=dict(schema='cu66-v85-matched-control-v1',status='PASS',frames=457,encoder_corner_checks=22,
                    source_sha256=pins,frames_path=str((out/'frames.jsonl').relative_to(ROOT)),frames_sha256=sha(out/'frames.jsonl'),native_log_sha256=sha(out/'native.log'),
                    all_visible_AB38_bytes=stats([r['all_visible_AB38_bytes'] for r in rows]),
                    residual_AB38_bytes=stats([r['residual_AB38_bytes'] for r in rows]),
                    component_bytes_reduction=stats([r['all_visible_AB38_bytes']-r['residual_AB38_bytes'] for r in rows]),
                    improved_sources=sum(r['all_visible_AB38_bytes']>r['residual_AB38_bytes'] for r in rows),
                    regressed_sources=sum(r['all_visible_AB38_bytes']<r['residual_AB38_bytes'] for r in rows),
                    all_visible_encoder_decisions=sum(r['all_visible_encoder_decisions'] for r in rows),
                    residual_encoder_decisions=sum(r['residual_encoder_decisions'] for r in rows),
                    scope='Matched same-encoder bw1 whole-plane component comparison; map/envelope/HUD costs excluded. Encoder work counts include all arithmetic attempts and are not decoder clocks. Raw fallback is covered synthetically; all observed native chunks are compressed.')
        (HERE/'matched-control.json').write_text(json.dumps(result,indent=2)+'\n')
        report.update(status='PASS',result_sha256=sha(HERE/'matched-control.json'),frames_sha256=sha(out/'frames.jsonl'),source_archive_sha256=sha(out/'sources.tar.gz'))
    except BaseException as exc:
        report['failure']=repr(exc);raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('V85_MATCHED_CONTROL_REPORT',out/'results.json',report['status'],flush=True)


if __name__=='__main__':main()
