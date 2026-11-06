#!/usr/bin/env python3
"""Observe four stream contexts and verify every V84 aggregate tile counter."""
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
import time

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v85/contexts'
FIELDS = ('decisions','renorm','stream_bytes','rice_values','events','raw_bytes',
          'header_bytes','crc_bytes','emits','raw_bits','prob_init')
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if (AREA/'index.json').exists():
        raise FileExistsError('Refusing to overwrite native context observations')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA/'attempts'/stamp
    out.mkdir(parents=True)
    binary = '/build/v85-contexts-'+stamp
    sources = [Path(__file__).resolve(), AREA/'trace.hpp', AREA/'collect.cpp', AREA/'data.py']
    sources += sorted((ROOT/'experiments/cu66-native-v69').glob('*.hpp'))
    sources += [ROOT/'experiments/cu66-native-v69/index.tsv',
                ROOT/'experiments/python-gamebub-v84/entropy/index.json',
                ROOT/'experiments/python-gamebub-v84/entropy/data.py',
                ROOT/'fpga/experiments/cu66-v69/entropy/cu66_ab38_decoder.sv']
    old_index = json.loads((ROOT/'experiments/python-gamebub-v84/entropy/index.json').read_text())
    sources += [ROOT/'experiments/python-gamebub-v84/entropy'/old_index['data']['path']]
    pins = {str(p.relative_to(ROOT)):sha(p) for p in sources}
    with tarfile.open(out/'sources.tar.gz','w:gz') as tar:
        for path in sources:
            if path.suffix!='.gz':
                tar.add(path,arcname=str(path.relative_to(ROOT)),recursive=False)
    commands=[]
    report=dict(schema='cu66-v85-context-collection-v1',status='FAIL',source_sha256=pins)
    started=time.monotonic()
    process=None
    def run(command,name):
        commands.append(command)
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
        (out/name).write_text(result.stdout+result.stderr)
        if result.returncode:
            raise RuntimeError((name,result.returncode))
    try:
        run(['docker','exec',CONTAINER,'g++','--version'],'compiler.txt')
        run(['docker','exec',CONTAINER,'g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(AREA/'collect.cpp'),'-o',binary],'compile.log')
        run(['docker','cp',CONTAINER+':'+binary,str(out/'collector.bin')],'copy.log')
        spec=importlib.util.spec_from_file_location('cu85_old_entropy',ROOT/'experiments/python-gamebub-v84/entropy/data.py')
        old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        expected=iter(old.iter_frames())
        command=['docker','exec',CONTAINER,binary,str(ROOT/'experiments/cu66-native-v69/index.tsv')]
        commands.append(command)
        rows=[];history=[0]*4;totals=[[0]*11 for _ in range(5)];raw=hashlib.sha256()
        with (out/'native.log').open('wb') as log:
            process=subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=log)
            with gzip.open(out/'data.jsonl.gz','wb') as stream:
                for line in process.stdout:
                    record=json.loads(line);baseline=next(expected)
                    for name in ('cohort','ordinal','fid','key','packet_sha256','canonical_sha256','hud_sha256','display_sha256','zero_mask','dispatches','plane_bytes','coefficient_sha256'):
                        assert record[name]==baseline[name],name
                    assert len(record['shared'])==len(record['contexts'])==8100
                    frame_totals=[[0]*11 for _ in range(5)]
                    for shared,contexts,original in zip(record['shared'],record['contexts'],baseline['tile_work'],strict=True):
                        assert len(shared)==11 and len(contexts)==4 and all(len(c)==11 for c in contexts)
                        aggregate=[s+sum(c[i] for c in contexts) for i,s in enumerate(shared)]
                        assert aggregate==[original[f] for f in FIELDS], 'V84 per-tile primitive parity'
                        assert shared[8]==1 and all(c[8]==0 for c in contexts)
                        for part,data in enumerate([shared,*contexts]):
                            for i,value in enumerate(data):
                                assert type(value)is int and value>=0
                                frame_totals[part][i]+=value;totals[part][i]+=value
                    for context in range(1,5):
                        assert frame_totals[context][10]==264
                    assert frame_totals[0][10]==0
                    stream.write(line);raw.update(line);history[record['cohort']]+=1
                    meta={k:v for k,v in record.items() if k not in ('shared','contexts','zero_mask')}
                    meta['shared_totals']=dict(zip(FIELDS,frame_totals[0]))
                    meta['context_totals']=[dict(zip(FIELDS,x)) for x in frame_totals[1:]]
                    meta['work_sha256']=hashlib.sha256(json.dumps([record['shared'],record['contexts']],separators=(',',':')).encode()).hexdigest()
                    rows.append(meta)
                    if len(rows)%25==0:print('V85_CONTEXT_PROGRESS',len(rows),flush=True)
            assert process.wait()==0
        assert len(rows)==457 and history==[119,119,119,100]
        try:next(expected)
        except StopIteration:pass
        else:raise AssertionError('trailing V84 frame')
        assert pins=={name:sha(ROOT/name) for name in pins},'source mutation'
        index=dict(schema='cu66-v85-native-contexts-v1',record_count=457,cohort_counts=history,fields=FIELDS,
                   data=dict(path=str((out/'data.jsonl.gz').relative_to(AREA)),gzip_sha256=sha(out/'data.jsonl.gz'),raw_sha256=raw.hexdigest()),
                   source_sha256=pins,frames=rows,shared_totals=dict(zip(FIELDS,totals[0])),
                   context_totals=[dict(zip(FIELDS,t)) for t in totals[1:]],
                   validation='All native coefficients/digests match frozen decoder; every shared+four-context tile counter equals V84.',
                   scope='Primitive attribution only, not RTL clocks or measured speedup. Raw fallback absent in native corpus.')
        (AREA/'index.json').write_text(json.dumps(index,indent=2)+'\n')
        report.update(status='PASS',records=457,planes=1371,cohort_counts=history,
                      index_sha256=sha(AREA/'index.json'),gzip_sha256=sha(out/'data.jsonl.gz'),source_archive_sha256=sha(out/'sources.tar.gz'))
    except BaseException as exc:
        report['failure']=repr(exc)
        if process is not None and process.poll()is None:
            process.terminate();process.wait()
        raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('V85_CONTEXT_REPORT',out/'results.json',report['status'],flush=True)


if __name__=='__main__':main()
