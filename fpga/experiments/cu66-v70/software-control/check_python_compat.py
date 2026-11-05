#!/usr/bin/env python3
"""Cross-check native framing and actual endpoint replies with frozen Python ABI."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import zlib

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PY_CODEC=ROOT/'fpga/experiments/cu66-v70/control-abi/hud_control.py'
CONTAINER=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    before=sha(PY_CODEC)
    spec=importlib.util.spec_from_file_location('hc70_compat_codec',PY_CODEC)
    codec=importlib.util.module_from_spec(spec);sys.modules[spec.name]=codec;spec.loader.exec_module(codec)
    fixtures=HERE/'compat-fixtures';outputs=HERE/'compat-roundtrip';logs=HERE/'compat-logs'
    for p in fixtures,outputs,logs:p.mkdir(exist_ok=True)
    commands=[];records=[]
    def check(name,wire,valid):
        src=fixtures/(name+'.bin');dst=outputs/(name+'.bin');src.write_bytes(wire)
        try:m=codec.decode(wire);python_valid=True
        except codec.ProtocolError:python_valid=False
        assert python_valid==valid,name
        argv=['docker','exec',CONTAINER,'/build/v70-hc70-endpoint','--codec',str(src),str(dst)]
        log=logs/(name+'.log')
        with log.open('w')as out:r=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,timeout=15)
        assert r.returncode==(0 if valid else 2),(name,r.returncode)
        if valid:
            assert dst.read_bytes()==wire and codec.decode(dst.read_bytes())==m,name
            assert codec.encode(m)==wire,name
        else:assert 'CODEC_REJECT'in log.read_text(),name
        records.append({'name':name,'valid':valid,'input':str(src.relative_to(ROOT)),'input_sha256':sha(src),'output':str(dst.relative_to(ROOT))if valid else None,'output_sha256':sha(dst)if valid else None})
        commands.append({'argv':argv,'expected_exit_code':0 if valid else 2,'exit_code':r.returncode,'log':str(log.relative_to(ROOT)),'log_sha256':sha(log)})
    high=0x0102030405060708
    for op in range(1,8):
        p=b'original-hu'if op==1 else struct.pack('<II',0,21120)if op==3 else struct.pack('<I',21120)+bytes(range(16))if op==4 else b''
        arg=1 if op in (1,4,7)else 0
        check(f'request-{op}',codec.encode(codec.Message(b'HC70',op,high,0x11223344,0x55667788,arg,p)),True)
        check(f'response-{op}',codec.encode(codec.Message(b'HR70',op,high,0x11223344,0x55667788,200,b'opaque-reply')),True)
    check('maximum-request',codec.encode(codec.Message(b'HC70',1,(1<<64)-1,(1<<32)-1,(1<<32)-1,1,b'p'*49152)),True)
    check('maximum-response',codec.encode(codec.Message(b'HR70',3,(1<<64)-1,0,0,0,bytes(range(256))*192)),True)
    check('zero-generation-status',codec.encode(codec.Message(b'HC70',2,0,0,0,0)),True)
    good=codec.encode(codec.Message(b'HC70',1,1,0,0xffffffff,1,b'abc'))
    def renew(b):return bytes(b[:-4])+struct.pack('<I',zlib.crc32(b[:-4])&0xffffffff)
    for name,offset,value in [('magic',0,88),('version',4,2),('opcode',5,8),('reserved',6,1)]:
        b=bytearray(good);b[offset]=value;check('bad-'+name,renew(b),False)
    for name,b in [('truncated-header',good[:12]),('truncated-body',good[:-1]),('trailing',good+b'\0')]:check('bad-'+name,b,False)
    for name,offset in [('generation-crc',12),('payload-crc',32),('trailer-crc',len(good)-1)]:
        b=bytearray(good);b[offset]^=1;check('bad-'+name,bytes(b),False)
    for op,p in [(3,b'abcd'),(4,b'x'*19),(5,b'x')]:
        b=bytearray(codec.encode(codec.Message(b'HC70',1,1,0,0xffffffff,0,p)));b[5]=op;check('bad-shape-'+str(op),renew(b),False)
    b=bytearray(codec.encode(codec.Message(b'HC70',7,2,0,0xffffffff,1)));b[28]=0;check('bad-reset-quiescence',renew(b),False)
    b=bytearray(good);b[8:12]=struct.pack('<I',49153);check('bad-maximum-length',renew(b),False)
    # Independently interpret actual native endpoint output, not just framing.
    examples=HERE/'examples'
    req={op:codec.decode((examples/f'request-op{op}.bin').read_bytes())for op in range(1,6)}
    rsp={op:codec.decode((examples/f'response-op{op}.bin').read_bytes())for op in range(1,6)}
    for op in range(1,6):
        assert req[op].magic==b'HC70'and rsp[op].magic==b'HR70'and rsp[op].argument==0
        assert (req[op].generation,req[op].frame_id,req[op].reference_id)==(rsp[op].generation,rsp[op].frame_id,rsp[op].reference_id)
    raw=rsp[3].payload;assert len(raw)==42240
    domain=bytearray(struct.pack('<HHB',720,480,4));offset=0
    for rect in [(22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24)]:
        n=rect[2]*rect[3]*2;domain.extend(struct.pack('<4H',*rect));domain.extend(raw[offset:offset+n]);offset+=n
    tag=hashlib.sha256(domain).digest()[:16]
    assert tag==req[1].payload[38:54]
    unpack=struct.Struct('<BBHIQII16sQII16s');assert unpack.size==72
    for op,phase in [(1,1),(2,1),(4,2),(5,3)]:
        row=unpack.unpack(rsp[op].payload);assert row[0]==phase and row[2]==0 and row[3]==21120
        assert (row[4],row[5],row[6])==(req[1].generation,req[1].frame_id,req[1].reference_id)
        assert row[7]==tag
        if op==5:assert row[1]&16 and not row[1]&12 and row[11]==tag
    assert before==sha(PY_CODEC),'frozenPythoncodecchanged'
    result={'status':'PASS','python_codec':str(PY_CODEC.relative_to(ROOT)),'python_codec_sha256':before,'valid_roundtrip_frames':sum(r['valid']for r in records),'matching_malformed_rejections':sum(not r['valid']for r in records),'actual_native_response_semantic_checks':5,'actual_READ_HUD_bytes':42240,'actual_READ_HUD_tag':tag.hex(),'status_payload_bytes':72,'records':records,'commands':commands,'scope':'framingandnativeendpointartifactcrosscheck;notphysicaltransportorintegratedFPGApeer'}
    (HERE/'python-compat-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PYTHON_CPP_COMPAT_PASS valid_frames='+str(result['valid_roundtrip_frames'])+' malformed_rejections='+str(result['matching_malformed_rejections'])+' actual_endpoint_response_opcodes=5 hud_words=21120 status_bytes=72')


if __name__=='__main__':main()
