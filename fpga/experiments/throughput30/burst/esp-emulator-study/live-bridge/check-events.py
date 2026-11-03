#!/usr/bin/env python3
"""Validate recorded adapter ACK events against verified packet bytes."""
import hashlib,json,struct,sys
from pathlib import Path
if len(sys.argv) not in (2,3):raise SystemExit('usage: check-events.py FIXTURE_TRACE [EVIDENCE_DIR]')
d=Path(sys.argv[2]) if len(sys.argv)==3 else Path(__file__).parent;trace=Path(sys.argv[1]).read_bytes()
if hashlib.sha256(trace).hexdigest()!='a8ff3d87e165247637d97fd2b56414f54943337ff7cb11102aa73cba26f26e05':raise SystemExit('bad fixture trace')
packets=[];i=0
while i<len(trace):
 if i+2>len(trace):raise SystemExit('bad length')
 n=int.from_bytes(trace[i:i+2],'big');i+=2
 if not 40<=n<=1064 or i+n>len(trace):raise SystemExit('bad packet')
 packets.append(trace[i:i+n]);i+=n
if len(packets)!=26:raise SystemExit('bad count')
def event(kind,seq,body=b''):return kind+struct.pack('>II',seq,0)+body
expected=[event(b'B',0,struct.pack('>II',26159,0xeceeb9c5))];offset=0
for seq,p in enumerate(packets,1):
 payload=p[40:];expected.append(event(b'D',seq,struct.pack('>IH',offset,len(payload))+payload));offset+=len(payload)
expected.append(event(b'C',27))
recorded=[json.loads(x) for x in (d/'adapter-events.jsonl').read_text().splitlines()]
if len(recorded)!=28 or offset!=26159:raise SystemExit('bad event count')
for seq,(r,e) in enumerate(zip(recorded,expected)):
 if r!={'seq':seq,'type':chr(e[0]),'length':len(e),'sha256':hashlib.sha256(e).hexdigest()}:raise SystemExit(f'event mismatch {seq}')
if 'ADAPTER_PASS events=28 packets=26 bytes=26159' not in (d/'adapter.log').read_text() or 'BRIDGE_GUEST_PASS packets=26 bytes=26159 events=28' not in (d/'guest.log').read_text():raise SystemExit('missing pass marker')
print('PASS: 28 ordered RTL-acknowledged event hashes, guest and adapter pass markers')
