#!/usr/bin/env python3
"""Reconstruct first clean-study frame; verify every recorded datagram hash."""
from pathlib import Path
import hashlib, json, struct, sys, zlib
if len(sys.argv) != 3:
    raise SystemExit('usage: make-trace.py 0000.jpg OUTPUT_TRACE')
root = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(root/'host'))
from moonshine.protocol import packets
jpeg = Path(sys.argv[1]).read_bytes()
if hashlib.sha256(jpeg).hexdigest() != '8cc99ea7d50d1d20255e41ff7247b0770b3349e705c27152a41817418ce5c9de':
    raise SystemExit('fixture mismatch')
trace = root/'fpga/experiments/throughput30/burst/network-rtl-study/results-clean/packet-trace.jsonl'
rows = [json.loads(line) for line in trace.read_text().splitlines()]
rows = [row for row in rows if row['id'] == 0]
datagrams = list(packets(jpeg, 0, 0))
if len(datagrams) != 26 or len(rows) != len(datagrams):
    raise SystemExit('packet count mismatch')
for datagram, row in zip(datagrams, rows):
    if hashlib.sha256(datagram).hexdigest() != row['datagram_sha256']:
        raise SystemExit('datagram mismatch')
if len(jpeg) != 26159 or zlib.crc32(jpeg) != 0xeceeb9c5:
    raise SystemExit('independent fixture CRC mismatch')
blob = b''.join(struct.pack('>H',len(p))+p for p in datagrams)
if hashlib.sha256(blob).hexdigest() != 'a8ff3d87e165247637d97fd2b56414f54943337ff7cb11102aa73cba26f26e05':
    raise SystemExit('packed trace mismatch')
with Path(sys.argv[2]).open('xb') as f:
    f.write(blob)
print('verified 26 datagrams, 26159 bytes, crc32 eceeb9c5')
