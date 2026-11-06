#!/usr/bin/env python3
"""Actual CS88 rejection/retention/recovery, including late BR88 corruption."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import uuid
import zlib

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v88/wire'
CONTAINER='gamebub-cu66-v69-build'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def checksum(data):return bytes(data[:-4])+struct.pack('>I',zlib.crc32(data[:-4]))
def inner_checksum(data):return bytes(data[:-4])+struct.pack('<I',zlib.crc32(data[:-4]))


def chunks(packet):
    start=128+int.from_bytes(packet[36:40],'big')+int.from_bytes(packet[40:44],'big');out=[]
    for axis in range(3):
        count=struct.unpack_from('>I',packet,start)[0];start+=4
        for _ in range(count):
            blocks,n=struct.unpack_from('>II',packet,start);start+=8
            out.append((start,n,blocks));start+=n
    return out


def main():
    full=json.loads((AREA/'results.json').read_text());run=(ROOT/full['selected_report']).parent
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'test-attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    spec=importlib.util.spec_from_file_location('br88_independent_reader',ROOT/'experiments/python-gamebub-v88/entropy/codec.py')
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    key=(run/'c0-f0-all_BR88.cs88').read_bytes();delta=(run/'c0-f1-all_BR88.cs88').read_bytes()
    start,n,blocks=chunks(delta)[0];original=delta[start:start+n]
    assert original[:4]==b'BR88'
    cases=[]
    def replace_chunk(chunk):
        assert len(chunk)==n
        return checksum(delta[:start]+chunk+delta[start+n:])
    def mutate(name,offset,value):
        chunk=bytearray(original);chunk[offset]=value
        cases.append((name,replace_chunk(inner_checksum(chunk))))
    mutate('BR88_magic',0,0)
    mutate('BR88_version',4,2)
    mutate('BR88_flags',5,2)
    mutate('BR88_blocks',6,(original[6]+1)%256)
    mutate('BR88_width',10,0)
    mutate('BR88_reserved',12,1)
    mutate('BR88_DC_k',42,14)
    mutate('BR88_DC_reserved_k1',43,0)
    chunk=bytearray(original);struct.pack_into('<I',chunk,14,0);cases.append(('BR88_stream_length',replace_chunk(inner_checksum(chunk))))
    chunk=bytearray(original);struct.pack_into('<I',chunk,30,blocks*5+1);cases.append(('BR88_AC_event_overrun',replace_chunk(inner_checksum(chunk))))
    chunk=bytearray(original);struct.pack_into('<I',chunk,44,0);cases.append(('BR88_bit_length',replace_chunk(inner_checksum(chunk))))
    chunk=bytearray(original);chunk[-1]^=1;cases.append(('BR88_inner_CRC',replace_chunk(chunk)))
    bad=bytearray(delta);bad[-1]^=1;cases.append(('outer_CRC',bytes(bad)))
    bad=bytearray(delta);bad[:4]=b'CS87';cases.append(('explicit_CS87_profile_reject',checksum(bad)))
    # Find a valid, semantically different plain stream by flipping a used DC
    # bit. Both readers must accept its grammar before the full frame is tested.
    expected=reader.decode(original,blocks)
    changed=None
    dc_length=struct.unpack_from('<I',original,14)[0]
    for offset in range(48,min(42+dc_length,80)):
        for bit in range(8):
            chunk=bytearray(original);chunk[offset]^=1<<bit;chunk=inner_checksum(chunk)
            try:decoded=reader.decode(chunk,blocks)
            except (ValueError,AssertionError,IndexError):continue
            if decoded!=expected:
                changed=chunk;break
        if changed is not None:break
    assert changed is not None,'no valid coefficient mutation found'
    cases.append(('valid_BR88_changed_coefficients_late_reject',replace_chunk(changed)))
    # Exercise actual nonzero bit padding instead of a header-shortcut failure.
    stream_start=42
    for length in struct.unpack_from('<4I',original,14):
        bits=struct.unpack_from('<I',original,stream_start+2)[0]
        if bits%8:
            chunk=bytearray(original);chunk[stream_start+length-1]|=1
            cases.append(('BR88_nonzero_bit_padding',replace_chunk(inner_checksum(chunk))));break
        stream_start+=length
    report=dict(schema='cu66-v88-wire-protocol-tests-v1',status='FAIL',checks=[],
                source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),AREA/'receiver.cpp',ROOT/'experiments/python-gamebub-v88/entropy/codec.hpp',ROOT/'experiments/python-gamebub-v88/entropy/codec.py',ROOT/full['selected_report']]},
                scope='Actual native synchronous reject/retain/recover/replay. No asynchronous hardware cancellation or physical drain proof.')
    for name,packet in cases:
        process=subprocess.Popen(['docker','exec','-i',CONTAINER,full['binary']],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        def receive(p):
            process.stdin.write(struct.pack('>II',0,len(p))+p);process.stdin.flush();return json.loads(process.stdout.readline())
        accepted=receive(key);rejected=receive(packet)
        assert accepted['accepted'] and not rejected['accepted'] and rejected['retained_fid']==0,(name,rejected)
        if name=='valid_BR88_changed_coefficients_late_reject':assert rejected['error']=='CS88 reconstructed content root',rejected
        recovered=receive(delta);replayed=receive(delta)
        assert recovered['accepted'] and not recovered['replayed'] and replayed==dict(recovered,replayed=True)
        process.stdin.close();assert process.wait()==0
        report['checks'].append(dict(name=name,status='PASS_NATIVE_REJECT_RETAIN_RECOVER_REPLAY',packet_sha256=hashlib.sha256(packet).hexdigest(),rejected=rejected,recovered=recovered,observed_exit_code=process.returncode))
    # Cross-spelling histories: same validated picture, alternate coding on
    # successive identities, exact replay only for the accepted bytes.
    for policy in ('AB38_control','byte_min','feedback_overhead5','feedback_overhead15'):
        process=subprocess.Popen(['docker','exec','-i',CONTAINER,full['binary']],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        def receive(p):
            process.stdin.write(struct.pack('>II',0,len(p))+p);process.stdin.flush();return json.loads(process.stdout.readline())
        first=receive(key)
        second_packet=(run/f'c0-f1-{policy}.cs88').read_bytes();second=receive(second_packet)
        third=receive((run/'c0-f2-all_BR88.cs88').read_bytes())
        assert first['accepted'] and second['accepted'] and third['accepted']
        replay=receive((run/'c0-f2-all_BR88.cs88').read_bytes());assert replay==dict(third,replayed=True)
        process.stdin.close();assert process.wait()==0
        report['checks'].append(dict(name='cross_spelling_'+policy,status='PASS_MIXED_NATIVE_HISTORY_REPLAY',observed_exit_code=process.returncode))
    assert report['source_sha256']=={name:sha(ROOT/name) for name in report['source_sha256']}
    report.update(status='PASS_NATIVE_CS88_PROTOCOL_RECOVERY',checks_count=len(report['checks']))
    (out/'source-test_wire.py').write_bytes(Path(__file__).read_bytes())
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    (AREA/'tests.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
    print(report['status'],len(report['checks']))


if __name__=='__main__':main()
