#!/usr/bin/env python3
"""Actually re-encode residual coefficients and retain independently decoded chunks."""
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tarfile
import time
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v85/residual'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    if (AREA/'index.json').exists():
        raise FileExistsError('refusing to overwrite retained residual data')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA/'attempts'/stamp
    out.mkdir(parents=True)
    binary = '/build/v85-residual-'+stamp
    sources = [Path(__file__).resolve(), AREA/'collect.cpp', AREA/'encode.hpp', AREA/'data.py',
               ROOT/'experiments/python-game-binary-v38-study/model.py',
               ROOT/'experiments/python-game-binary-v38-study/decoder.py',
               ROOT/'experiments/python-gamebub-v82/native/index.json',
               ROOT/'experiments/python-gamebub-v82/native/data.py',
               ROOT/'experiments/cu66-native-v69/index.tsv']
    sources += sorted((ROOT/'experiments/cu66-native-v69').glob('*.hpp'))
    pins = {str(p.relative_to(ROOT)):sha(p) for p in sources}
    with tarfile.open(out/'sources.tar.gz', 'w:gz') as tar:
        for path in sources:
            tar.add(path,arcname=str(path.relative_to(ROOT)),recursive=False)
    started = time.monotonic()
    report = dict(schema='cu66-v85-residual-collection-v1',status='FAIL',source_sha256=pins,
                  encoder='C++ port of frozen V38 BinaryEncoder with minimum uncoded Rice-cost parameter selection; bw=1 per residual tile.',
                  scope='Actual component bytes; no whole-frame or timing inference until an explicit envelope is measured.')
    commands, process = [], None
    def run(command, filename):
        commands.append(command)
        result = subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        (out/filename).write_text(result.stdout+result.stderr)
        if result.returncode:
            raise RuntimeError(f'{filename} command exit {result.returncode}')
    try:
        run(['docker','exec',CONTAINER,'g++','--version'],'compiler.txt')
        run(['docker','exec',CONTAINER,'g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(AREA/'collect.cpp'),'-o',binary],'compile.log')
        run(['docker','cp',f'{CONTAINER}:{binary}',str(out/'collector.bin')],'copy.log')
        native = module('cu85_original_native',ROOT/'experiments/python-gamebub-v82/native/data.py')
        data = module('cu85_components',AREA/'data.py')
        expected = iter(native.iter_frames())
        command = ['docker','exec',CONTAINER,binary,str(ROOT/'experiments/cu66-native-v69/index.tsv')]
        commands.append(command)
        digest, rows, history = hashlib.sha256(), [], [0,0,0,0]
        totals = {str(cap):dict(AB38_bytes=0,chunks=0,raw_chunks=0,max_chunk_bytes=0) for cap in data.CAPS}
        # The process emits framed binary records. Retain exactly the received
        # bytes while the independent Python parser validates their structure.
        class Recording:
            def __init__(self, source, dest):
                self.source,self.dest = source,dest
            def read(self,n=-1):
                value=self.source.read(n);self.dest.write(value);return value
        with (out/'native.log').open('wb') as log:
            process = subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=log)
            with gzip.open(out/'data.bin.gz','wb') as dest:
                stream = Recording(process.stdout,dest)
                while True:
                    record = data.read_record(stream,digest)
                    if record is None:
                        break
                    original = next(expected)
                    for name in ('cohort','ordinal','fid','refid','key','packet_sha256','canonical_sha256','hud_sha256','display_sha256'):
                        assert record[name] == original[name],('native parity',name)
                    assert record['zero_mask'] == ''.join(str(x) for x in original['zero_coeff_mask'])
                    assert record['residual_counts'] == [sum(not h and (record['key'] or not c) for h,c in zip(original['hidden_mask'][a:b],original['zero_coeff_mask'][a:b])) for a,b in ((0,5400),(5400,6750),(6750,8100))]
                    assert len(record['qmap'])==338 and len(record['hud'])==record['hud_bytes']
                    assert hashlib.sha256(record['hud']).hexdigest()==original['encoded_hud_sha256']
                    for cap, planes in record['variants'].items():
                        stats=dict(AB38_bytes=0,chunks=0,raw_chunks=0,max_chunk_bytes=0)
                        for axis,chunks in enumerate(planes):
                            assert sum(c['blocks'] for c in chunks)==record['residual_counts'][axis]
                            for chunk in chunks:
                                packet=chunk['data'];blocks=chunk['blocks']
                                assert packet[:6] in (b'AB38\x01\x00',b'AB38\x01\x01')
                                assert struct.unpack_from('<IHH',packet,6)==(blocks,1,0)
                                assert zlib.crc32(packet[:-4])==struct.unpack('<I',packet[-4:])[0]
                                assert len(packet)==46+sum(struct.unpack_from('<4I',packet,14))
                                stats['AB38_bytes']+=len(packet);stats['chunks']+=1;stats['raw_chunks']+=packet[5]
                                stats['max_chunk_bytes']=max(stats['max_chunk_bytes'],len(packet))
                        assert all(record['variant_stats'][cap][k]==v for k,v in stats.items())
                        for k,v in stats.items():
                            if k=='max_chunk_bytes':totals[cap][k]=max(totals[cap][k],v)
                            else:totals[cap][k]+=v
                    meta={k:v for k,v in record.items() if k not in ('variants','qmap','hud','zero_mask')}
                    meta.update(qmap_sha256=hashlib.sha256(record['qmap']).hexdigest(),encoded_hud_sha256=hashlib.sha256(record['hud']).hexdigest())
                    rows.append(meta);history[record['cohort']]+=1
                    if len(rows)%25==0:
                        print('V85_RESIDUAL_PROGRESS',len(rows),flush=True)
            code=process.wait()
            assert code==0,('native collector exit',code)
        assert len(rows)==457 and history==[119,119,119,100]
        assert next(expected,None) is None
        assert pins=={name:sha(ROOT/name) for name in pins},'executed residual source mutation'
        index=dict(schema='cu66-v85-residual-components-v1',record_count=457,cohort_counts=history,caps=list(data.CAPS),
                   source_sha256=pins,data=dict(path=str((out/'data.bin.gz').relative_to(AREA)),gzip_sha256=sha(out/'data.bin.gz'),raw_sha256=digest.hexdigest()),
                   frames=rows,totals=totals,
                   binary_format='u32le metadata length+JSON; u32 qmapbytes+qmap; u32 hudbytes+encodedHUD; fixedcaps16/64/256/65536 x3planes: u32chunkcount; each u32blocks/u32packetbytes/actualAB38packet.',
                   semantics='Residual tiles are all visible tiles for keys; visible nonzero-coefficient tiles for deltas. Hidden CONST/COPY zero coefficients omitted. Residual order is ascending canonical tile within each plane; DC predictor resets per residual tile (bw1).',
                   scope='Components only, no frame-envelope/transport bytes or physical timing claim.')
        (AREA/'index.json').write_text(json.dumps(index,indent=2)+'\n')
        report.update(status='PASS',records=457,original_native_plane_checks=1371,
                      generated_chunks_checked=sum(v['chunks'] for v in totals.values()),cohort_counts=history,totals=totals,
                      data_sha256=sha(out/'data.bin.gz'),index_sha256=sha(AREA/'index.json'),source_archive_sha256=sha(out/'sources.tar.gz'))
    except BaseException as exc:
        report['failure']=repr(exc)
        if process is not None and process.poll() is None:
            process.terminate();process.wait()
        raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('V85_RESIDUAL_REPORT',out/'results.json',report['status'],flush=True)


if __name__=='__main__':
    main()
