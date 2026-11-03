#!/usr/bin/env python3
"""Compare saved UDP sends to RTL packet descriptors through the shared trace."""
import hashlib, json, re, sys, zlib
from pathlib import Path
if len(sys.argv)!=2: raise SystemExit('usage: check-cross-stage.py FIXTURE_TRACE')
root=Path(__file__).resolve().parents[6];sys.path.insert(0,str(root/'host'))
from moonshine.protocol import parse_packet
burst=root/'fpga/experiments/throughput30/burst'
recorded=[json.loads(s) for s in (burst/'network-rtl-study/results-clean/packet-trace.jsonl').read_text().splitlines()];recorded=[r for r in recorded if r['id']==0]
rtl=(burst/'packet-stream-rtl/results/trace.txt').read_text().splitlines();descriptors=[tuple(map(int,s.split())) for s in rtl[1:]]
host=(Path(__file__).parent/'fixture-host.log').read_text().splitlines();sent=[]
for line in host:
 m=re.fullmatch(r'send (\d+) bytes (\d+) sha256 ([0-9a-f]{64})',line)
 if m:sent.append((int(m[1]),int(m[2]),m[3]))
blob=Path(sys.argv[1]).read_bytes()
if hashlib.sha256(blob).hexdigest()!='a8ff3d87e165247637d97fd2b56414f54943337ff7cb11102aa73cba26f26e05':raise SystemExit('packed fixture hash mismatch')
datagrams=[];pos=0
while pos<len(blob):
 if pos+2>len(blob):raise SystemExit('truncated length')
 n=int.from_bytes(blob[pos:pos+2],'big');pos+=2
 if pos+n>len(blob):raise SystemExit('truncated packet')
 datagrams.append(blob[pos:pos+n]);pos+=n
if int(rtl[0])!=26 or not (len(recorded)==len(descriptors)==len(datagrams)==len(sent)==26):raise SystemExit('count mismatch')
payload=bytearray()
for i,(row,desc,raw,hostrow) in enumerate(zip(recorded,descriptors,datagrams,sent)):
 h=parse_packet(raw);digest=hashlib.sha256(raw).hexdigest()
 if hostrow!=(i,len(raw),digest) or row['datagram_sha256']!=digest:raise SystemExit(f'datagram {i} mismatch')
 if desc!=(row['arrival_cycle'],h.offset,len(h.payload)) or row['offset']!=h.offset or row['payload_bytes']!=len(h.payload):raise SystemExit(f'descriptor {i} mismatch')
 if h.frame_id!=0 or h.crc32!=0xeceeb9c5:raise SystemExit(f'header {i} mismatch')
 payload.extend(h.payload)
if len(payload)!=26159 or zlib.crc32(payload)!=0xeceeb9c5 or hashlib.sha256(payload).hexdigest()!='8cc99ea7d50d1d20255e41ff7247b0770b3349e705c27152a41817418ce5c9de':raise SystemExit('JPEG mismatch')
print('PASS 26 datagrams, matching UDP host hashes/lengths and RTL descriptors; JPEG 26159 bytes CRC32 eceeb9c5')
print('Separate emulator and RTL runs; no co-simulation or real hardware.')
