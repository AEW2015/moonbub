#!/usr/bin/env python3
"""Actual bounded Rice re-encoding of every frozen whole-plane residual chunk."""
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v88/entropy'
CONTAINER='gamebub-cu66-v69-build'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    sources=[Path(__file__).resolve(),AREA/'codec.hpp',AREA/'codec.py',AREA/'collect.cpp',AREA/'data.py',
             ROOT/'experiments/python-gamebub-v85/residual/encode.hpp',ROOT/'experiments/python-gamebub-v85/residual/data.py',
             ROOT/'experiments/python-gamebub-v85/residual/index.json']
    sources+=sorted((ROOT/'experiments/cu66-native-v69').glob('*.hpp'))
    pins={str(p.relative_to(ROOT)):sha(p) for p in sources}
    for p in sources:
        if p.suffix in ('.py','.hpp','.cpp'):
            dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    binary='/build/v88-entropy-'+stamp
    report=dict(schema='cu66-v88-bounded-rice-components-v1',status='FAIL',source_sha256=pins,commands=[],
                physical_timing_proven=False,scope='Actual re-encoded complete chunk bytes/native coefficient parity and independent Python parse. No frame wire/pixel or FPGA/ESP32 timing claim in this component report.')
    started=time.monotonic();process=None;stderr=None
    try:
        command=['docker','exec',CONTAINER,'g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(AREA/'collect.cpp'),'-o',binary]
        result=subprocess.run(command,capture_output=True,text=True);report['commands'].append(dict(argv=command,exit_code=result.returncode))
        (out/'compile.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
        command=['docker','cp',CONTAINER+':'+binary,str(out/'collector.bin')]
        result=subprocess.run(command,capture_output=True,text=True);report['commands'].append(dict(argv=command,exit_code=result.returncode));assert result.returncode==0
        codec=load('br88_python',AREA/'codec.py');old=load('br88_residual',ROOT/'experiments/python-gamebub-v85/residual/data.py')
        stderr=(out/'collector.stderr').open('wb');command=['docker','exec','-i',CONTAINER,binary]
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr);report['commands'].append(dict(argv=command))
        def take(n):
            data=process.stdout.read(n);assert len(data)==n,('native helper truncated',process.poll());return data
        raw_sha=hashlib.sha256();frames=[];chunks=0;coefficients=0;total_old=total_new=0;old_decisions=old_renorm=new_bits=0;raw_chunks=0
        with gzip.open(out/'data.bin.gz','wb',compresslevel=6) as stream:
            def write(data):raw_sha.update(data);stream.write(data)
            for frame in old.iter_frames():
                meta={k:frame[k] for k in ('cohort','fid','ordinal','key','canonical_coefficients_sha256')};meta['planes']=[];payload=[]
                for axis,plane in enumerate(frame['variants']['65536']):
                    observed=[]
                    for chunk in plane:
                        process.stdin.write(struct.pack('<II',chunk['blocks'],len(chunk['data']))+chunk['data']);process.stdin.flush()
                        stats=json.loads(process.stdout.readline());length,=struct.unpack('<I',take(4));data=take(length)
                        assert stats['blocks']==chunk['blocks'] and stats['old_bytes']==len(chunk['data']) and stats['new_bytes']==length
                        values=codec.decode(data,chunk['blocks']);packed=struct.pack('<'+'h'*len(values),*values)
                        assert hashlib.sha256(packed).hexdigest()==stats['coefficient_sha256'],'independent Python coefficient mismatch'
                        assert len(data)<=46+128*chunk['blocks']
                        stats['br88_sha256']=hashlib.sha256(data).hexdigest();stats['br88_bits']=stats.pop('new_bits');stats['br88_raw']=stats.pop('raw')
                        observed.append(stats);payload.append(data);chunks+=1;coefficients+=len(values);total_old+=len(chunk['data']);total_new+=len(data)
                        old_decisions+=sum(stats['old_decisions']);old_renorm+=sum(stats['old_renorm']);new_bits+=sum(stats['br88_bits']);raw_chunks+=stats['br88_raw']
                        if (frame['cohort']==0 and frame['ordinal'] in (0,1)) or (frame['cohort']==3 and frame['fid']==50):
                            (out/f"c{frame['cohort']}-f{frame['fid']}-p{axis}.br88").write_bytes(data)
                    meta['planes'].append(observed)
                encoded=json.dumps(meta,separators=(',',':')).encode();write(struct.pack('<I',len(encoded))+encoded)
                for data in payload:write(data)
                frames.append({k:meta[k] for k in ('cohort','fid','ordinal','key','canonical_coefficients_sha256')})
                if len(frames)==1 or len(frames)%50==0:print('BR88_PROGRESS',len(frames),chunks,flush=True)
        process.stdin.close();code=process.wait();stderr.close();report['native_exit_code']=code;assert code==0
        assert len(frames)==457 and chunks==1371
        assert pins=={name:sha(ROOT/name) for name in pins},'executed sources changed'
        report.update(status='PASS_NATIVE_AND_INDEPENDENT_PYTHON_CHUNK_PARITY',native_sources=457,chunks=chunks,coefficient_values=coefficients,
                      AB38_bytes=total_old,BR88_bytes=total_new,byte_delta=total_new-total_old,old_feedback_decisions=old_decisions,
                      old_renormalizations=old_renorm,BR88_bit_reads=new_bits,BR88_raw_chunks=raw_chunks,
                      data=dict(path=str((out/'data.bin.gz').relative_to(AREA)),gzip_sha256=sha(out/'data.bin.gz'),raw_sha256=raw_sha.hexdigest()),frames=frames)
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
    finally:
        if process is not None and process.poll() is None:process.terminate();process.wait()
        if stderr is not None and not stderr.closed:stderr.close()
        report['wall_seconds']=time.monotonic()-started;(out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('BR88_REPORT',out/'results.json',report['status'],flush=True)
    (AREA/'index.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')


if __name__=='__main__':main()
