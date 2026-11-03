#!/usr/bin/env python3
"""Audit accepted events and no-publication markers for corrupt-final test."""
import hashlib,json,struct,sys
from pathlib import Path
if len(sys.argv)!=3:raise SystemExit('usage: check-abort.py FIXTURE_TRACE EVIDENCE_DIR')
trace=Path(sys.argv[1]).read_bytes();d=Path(sys.argv[2])
if hashlib.sha256(trace).hexdigest()!='a8ff3d87e165247637d97fd2b56414f54943337ff7cb11102aa73cba26f26e05':raise SystemExit('bad fixture trace')
packets=[];i=0
while i<len(trace):
 if i+2>len(trace):raise SystemExit('truncated length')
 n=int.from_bytes(trace[i:i+2],'big');i+=2
 if not 40<=n<=1064 or i+n>len(trace):raise SystemExit('bad packet')
 packets.append(trace[i:i+n]);i+=n
if len(packets)!=26:raise SystemExit('bad count')
def event(kind,seq,body=b''):return kind+struct.pack('>II',seq,0)+body
expected=[event(b'B',0,struct.pack('>II',26159,0xeceeb9c5))];offset=0
for seq,p in enumerate(packets[:25],1):
 data=p[40:];expected.append(event(b'D',seq,struct.pack('>IH',offset,len(data))+data));offset+=len(data)
expected.append(event(b'A',26))
recorded=[json.loads(x) for x in (d/'adapter-events.jsonl').read_text().splitlines()]
if len(recorded)!=27 or offset!=25600:raise SystemExit('bad event count')
for seq,(r,e) in enumerate(zip(recorded,expected)):
 if r!={'seq':seq,'type':chr(e[0]),'length':len(e),'sha256':hashlib.sha256(e).hexdigest()}:raise SystemExit(f'event mismatch {seq}')
if 'ADAPTER_ABORT_PASS events=27 accepted_packets=25 bytes=25600' not in (d/'adapter.log').read_text():raise SystemExit('adapter marker missing')
if 'BRIDGE_GUEST_ABORT_PASS accepted_packets=25 bytes=25600 events=27' not in (d/'guest.log').read_text():raise SystemExit('guest marker missing')
rtl=(d/'rtl.log').read_text()
if 'TEST_PASS_LIVE_ABORT' not in rtl or 'BRIDGE_PRESENT' in rtl or 'presented=0 pixels=0 writes=0' not in rtl:raise SystemExit('RTL no-publication marker missing')
print('PASS: 25 acknowledged DATA events then ABORT; no presentation/pixels/writes')
