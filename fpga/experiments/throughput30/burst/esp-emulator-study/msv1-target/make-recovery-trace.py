#!/usr/bin/env python3
"""Verify and pack 3 clean-trace frames for target-side corruption replay."""
from pathlib import Path
import hashlib, json, struct, sys, zlib
if len(sys.argv)!=3: raise SystemExit('usage: make-recovery-trace.py FIXTURE_DIR OUTPUT_TRACE')
root=Path(__file__).resolve().parents[6];sys.path.insert(0,str(root/'host'))
from moonshine.protocol import packets
study=root/'fpga/experiments/throughput30/burst/network-rtl-study/results-clean'
rows=[json.loads(s) for s in (study/'packet-trace.jsonl').read_text().splitlines()]
manifest=json.loads((study/'trace-manifest.json').read_text())
expected=[(26159,0xeceeb9c5,26),(26358,0x9e75ea8b,26),(26991,0x1ea3e1d5,27)]
blob=b''
for i,(size,crc,n) in enumerate(expected):
    jpeg=(Path(sys.argv[1])/f'{i:04}.jpg').read_bytes()
    selected=[r for r in rows if r['id']==i]
    datagrams=list(packets(jpeg,i,(i*10_000_000//3)//100))
    if (len(jpeg),zlib.crc32(jpeg),len(datagrams))!=(size,crc,n): raise SystemExit('fixture size/CRC/count mismatch')
    if hashlib.sha256(jpeg).hexdigest()!=manifest['complete'][i]['jpeg_sha256'] or len(selected)!=n: raise SystemExit('fixture hash/count mismatch')
    if any(hashlib.sha256(d).hexdigest()!=r['datagram_sha256'] for d,r in zip(datagrams,selected)): raise SystemExit('datagram hash mismatch')
    blob+=b''.join(struct.pack('>H',len(d))+d for d in datagrams)
if hashlib.sha256(blob).hexdigest()!='bef1ac9f645d0378849d4e3b0d6b4d7c935e309338a41c6a067891596405d372': raise SystemExit('packed trace mismatch')
with Path(sys.argv[2]).open('xb') as f: f.write(blob)
print('verified 79 clean-trace datagrams across three fixtures')
