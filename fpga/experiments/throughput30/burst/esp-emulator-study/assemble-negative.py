#!/usr/bin/env python3
"""Assemble the deliberately incomplete erased-system-data emulator fixture."""
import hashlib
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[5] / 'firmware'
if len(sys.argv) != 2:
    raise SystemExit('usage: assemble-negative.py WORK_DIRECTORY')
work = Path(sys.argv[1])
parts = [(0, 0x8000, root/'handheld/bootloader.bin', '016d3f89c1957af7fe2a30a5c539530c3eda90b3f01f5a337a255c0760947b27'),
         (0x8000, 0x9000, work/'gamebub-partitions.bin', 'fd1dc4016a02d66f41f25a0ca96b856b0f5e2ef6b2c02790e973755cd460316e'),
         (0x100000, 0x600000, root/'release/moonshine-rev4.bin', 'bf67421c0baf5c3277032742bc7c321a0d5b80056d099d02f95243a233c9d4cb')]
out = bytearray(b'\xff') * 0x800000
for start, end, path, digest in parts:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise SystemExit(f'hash mismatch: {path}')
    if not 0 <= start < end <= len(out) or not data or len(data) > end-start:
        raise SystemExit(f'invalid size or bounds: {path}')
    if out[start:start+len(data)] != b'\xff' * len(data):
        raise SystemExit(f'overlap: {path}')
    out[start:start+len(data)] = data
    print(f'{path.name} offset={start:#x} size={len(data)} end={start+len(data):#x} limit={end:#x}')
if out[0x600000:0x800000] != b'\xff' * 0x200000:
    raise SystemExit('system_data is not erased')
path = work/'gamebub-erased-system-negative.bin'
try:
    with path.open('xb') as f:
        f.write(out)
except FileExistsError:
    raise SystemExit(f'refusing to overwrite {path}')
print('image sha256', hashlib.sha256(out).hexdigest())
