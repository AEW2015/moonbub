#!/usr/bin/env python3
"""Audit live 0/1-abort/2 event hashes and publication-preservation markers."""
import hashlib,json,struct,sys
from pathlib import Path
if len(sys.argv)!=3:raise SystemExit('usage: check-multi-events.py FIXTURE_TRACE EVIDENCE_DIR')
trace=Path(sys.argv[1]).read_bytes();d=Path(sys.argv[2])
if hashlib.sha256(trace).hexdigest()!='c7d7fad41df15810b7f241bbb63649b50656edebef5322633f396fc07e01a52b':raise SystemExit('bad fixture trace')
packets=[];i=0
while i<len(trace):
 if i+2>len(trace):raise SystemExit('bad length')
 n=int.from_bytes(trace[i:i+2],'big');i+=2
 if not 40<=n<=1064 or i+n>len(trace):raise SystemExit('bad packet')
 packets.append(trace[i:i+n]);i+=n
if len(packets)!=106:raise SystemExit('bad count')
def event(k,seq,id,body=b''):return k+struct.pack('>II',seq,id)+body
expected=[];offset=0
for p in packets:
 id=int.from_bytes(p[8:12],'big');off=int.from_bytes(p[20:24],'big');length=int.from_bytes(p[16:20],'big');crc=int.from_bytes(p[28:32],'big');last=bool(p[7]&2)
 if id not in (0,1,2,3) or off!=offset:raise SystemExit('bad source ordering')
 if off==0:expected.append(event(b'B',len(expected),id,struct.pack('>II',length,crc)))
 if id==1 and last:expected.append(event(b'A',len(expected),id));offset=0;continue
 data=p[40:];expected.append(event(b'D',len(expected),id,struct.pack('>IH',off,len(data))+data));offset+=len(data)
 if last:expected.append(event(b'C',len(expected),id));offset=0
if len(expected)!=113 or offset!=0:raise SystemExit('bad expected totals')
recorded=[json.loads(x) for x in (d/'adapter-events.jsonl').read_text().splitlines()]
if len(recorded)!=len(expected):raise SystemExit('bad recorded count')
for seq,(r,e) in enumerate(zip(recorded,expected)):
 if r!={'seq':seq,'type':chr(e[0]),'length':len(e),'sha256':hashlib.sha256(e).hexdigest()}:raise SystemExit(f'event mismatch {seq}')
if 'NACK_ADAPTER_PASS events=113 negative_status=5' not in (d/'adapter.log').read_text() or 'NACK_GUEST_PASS events=113 commits=2 aborts=1' not in (d/'guest.log').read_text() or 'GUEST_NACK id=2 seq=83' not in (d/'guest.log').read_text():raise SystemExit('negative ACK policy mismatch')
rtl=(d/'rtl.log').read_text()
for marker in ['MULTI_PRESENT seq=27 id=0','MULTI_ABORT seq=54 id=1','prior_front_intact=1','POST_GUEST_CRC_REJECT seq=83 id=2','crc_reject=1','TEST_PASS_POST_GUEST_CRC_REJECT','MULTI_PRESENT seq=112 id=3','TEST_PASS_LIVE_GUEST_NACK']:
 if marker not in rtl:raise SystemExit(f'missing RTL marker: {marker}')
print('PASS: 113 event hashes, 112 success ACKs, one NACK, guest continuation and two presentations')
