#!/usr/bin/env python3
"""Native/Python BR88 grammar, bounded symbols, raw fallback and malformed checks."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import struct
import subprocess
import uuid
import zlib

ROOT=Path(__file__).resolve().parents[3]
AREA=Path(__file__).resolve().parent
CONTAINER='gamebub-cu66-v69-build'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def crc(packet):return bytes(packet[:-4])+struct.pack('<I',zlib.crc32(packet[:-4]))


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'test-attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    sources=[Path(__file__).resolve(),AREA/'test_codec.cpp',AREA/'codec.hpp',AREA/'codec.py']
    pins={str(p.relative_to(ROOT)):sha(p) for p in sources}
    for p in sources:(out/p.name).write_bytes(p.read_bytes())
    spec=importlib.util.spec_from_file_location('br88_strict_test',AREA/'codec.py');codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
    command=['docker','exec',CONTAINER,'g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(AREA/'test_codec.cpp'),'-o','/build/v88-entropy-tests-'+stamp]
    compiled=subprocess.run(command,capture_output=True,text=True);(out/'compile.log').write_text(compiled.stdout+compiled.stderr);assert compiled.returncode==0,compiled.stderr
    log=(out/'native.stderr').open('wb');native=subprocess.Popen(['docker','exec','-i',CONTAINER,command[-1]],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log)
    checks=[]
    def ask(mode,blocks,body):
        native.stdin.write(struct.pack('<III',mode,blocks,len(body))+body);native.stdin.flush();answer=json.loads(native.stdout.readline());packet=None
        if mode==1 and answer['accepted']:
            size,=struct.unpack('<I',native.stdout.read(4));packet=native.stdout.read(size);assert len(packet)==size
        return answer,packet
    fixtures=[]
    rng=random.Random(8801)
    patterns=[('zero_1',[0]*64),('uniform_ones',[1]*64),('signed_extremes',[-2048,2048]*32),
              ('dense_random_16',[rng.randint(-2048,2048) for _ in range(16*64)]),
              ('sparse_high_band',[0]*(200*64)),('DC_signed_sweep',[0]*(40*64))]
    patterns[4][1][-1]=-17
    for i in range(40):patterns[5][1][i*64]=i-20
    patterns.append(('dense_random_1',[rng.randint(-2048,2048) for _ in range(64)]))
    for name,values in patterns:
        raw=struct.pack('<'+'h'*len(values),*values);answer,packet=ask(1,len(values)//64,raw)
        assert answer['accepted'],(name,answer)
        assert codec.decode(packet,len(values)//64)==values
        assert hashlib.sha256(raw).hexdigest()==answer['coefficient_sha256']
        (out/(name+'.br88')).write_bytes(packet);fixtures.append((name,len(values)//64,packet))
        checks.append(dict(name=name,status='PASS_NATIVE_ENCODE_INDEPENDENT_PYTHON_DECODE',raw=answer['raw'],bytes=len(packet),coefficient_sha256=answer['coefficient_sha256']))
    assert next(c for c in checks if c['name']=='dense_random_1')['raw']
    corpus=json.loads((AREA/'index.json').read_text());attempt=(ROOT/corpus['selected_report']).parent
    for fixture in sorted(attempt.glob('*.br88')):
        packet=fixture.read_bytes();blocks=int.from_bytes(packet[6:10],'little');values=codec.decode(packet,blocks);answer,_=ask(0,blocks,packet)
        assert answer['accepted'] and hashlib.sha256(struct.pack('<'+'h'*len(values),*values)).hexdigest()==answer['coefficient_sha256']
        checks.append(dict(name='native_fixture_'+fixture.name,status='PASS_CROSS_LANGUAGE_CORPUS_FIXTURE',packet_sha256=sha(fixture)))
    # Explicit maximum-length escaped Rice symbol: 15 zero unary bits +14 literal bits.
    bits=[0]*15+[int(x) for x in f'{4096:014b}'];body=bytearray((len(bits)+7)//8)
    for i,bit in enumerate(bits):body[i//8]|=bit<<(7-i%8)
    streams=[bytes([0,255])+struct.pack('<I',29)+bytes(body)]+[b'\x00\x00'+struct.pack('<I',0)]*3
    header=b'BR88\x01\x00'+struct.pack('<IHH',1,1,0)+struct.pack('<4I',*[len(s) for s in streams])+struct.pack('<3I',0,0,0)
    escaped=header+b''.join(streams)+bytes(4);escaped=crc(escaped)
    expected=[2048]+[0]*63;answer,_=ask(0,1,escaped)
    assert answer['accepted'] and codec.decode(escaped,1)==expected
    checks.append(dict(name='bounded_unary_15_escape_literal14',status='PASS_NATIVE_AND_PYTHON'))
    base=fixtures[0][2]
    def changed(packet,offset,values):
        raw=bytearray(packet);raw[offset:offset+len(values)]=values;return crc(raw)
    malformed=[('magic',changed(base,0,b'BAD!'),1),('version',changed(base,4,b'\x02'),1),('flags',changed(base,5,b'\x02'),1),
               ('block_binding',changed(base,6,struct.pack('<I',2)),1),('bw_binding',changed(base,10,b'\x02\x00'),1),
               ('reserved',changed(base,12,b'\x01\x00'),1),('lengths',changed(base,14,struct.pack('<I',1)),1),
               ('DC_parameter',changed(base,42,b'\x0e'),1),('DC_marker',changed(base,43,b'\x00'),1),
               ('DC_bit_count',changed(base,44,struct.pack('<I',0)),1),('DC_padding',changed(base,48,b'\x81'),1),
               ('AC_count',changed(base,30,struct.pack('<I',6)),1),('truncated',base[:-1],1),('geometry_zero',base,0)]
    corrupt=bytearray(base);corrupt[-1]^=1;malformed.append(('CRC',bytes(corrupt),1))
    rawpacket=next(p for name,_,p in fixtures if name=='dense_random_1')
    malformed.extend([('raw_fields',changed(rawpacket,30,struct.pack('<I',1)),1),('raw_range',changed(rawpacket,42,struct.pack('<h',32767)),1)])
    malformed.append(('AC_empty_trailing_bits',changed(base,14+4,struct.pack('<I',7))+b'',1))
    for name,packet,blocks in malformed:
        try:codec.decode(packet,blocks);python_accepted=True
        except ValueError:python_accepted=False
        answer,_=ask(0,blocks,packet)
        assert not python_accepted and not answer['accepted'],(name,python_accepted,answer)
        checks.append(dict(name=name,status='PASS_REJECT_BOTH',native_error=answer['error'],packet_sha256=hashlib.sha256(packet).hexdigest()))
    native.stdin.close();code=native.wait();log.close();assert code==0
    assert pins=={n:sha(ROOT/n) for n in pins}
    report=dict(schema='cu66-v88-br88-tests-v1',status='PASS_CROSS_LANGUAGE_BOUNDED_RICE_GRAMMAR',checks=checks,checks_count=len(checks),source_sha256=pins,
                command=command,compile_exit_code=compiled.returncode,native_exit_code=code,
                artifacts_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file()},
                scope='Native encoder/decoder and independent Python parser grammar/fixtures; not full-frame protocol or physical throughput proof.')
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'tests.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
    print(report['status'],len(checks),out/'results.json')


if __name__=='__main__':main()
