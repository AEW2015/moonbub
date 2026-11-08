#!/usr/bin/env python3
"""Capture real loopback MSV1 datagrams; validate bytes without timing claims."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import socket
import struct
import time
import zlib

HEADER = struct.Struct('!4sBBHIHHIIHHIQ')


def validate(path):
    trace = json.loads(Path(path).read_text())
    assert trace['schema'] == 'v111-host-datagram-trace-v1'
    assert trace['clock_domain'] == 'host_monotonic_ns'
    assert trace['shared_simulation_time'] is False
    frames = {}
    previous = -1
    wire_bytes = 0
    for row in trace['datagrams']:
        now = row['arrival_ns']
        assert type(now) is int and now >= previous
        previous = now
        packet = base64.b64decode(row['base64'], validate=True)
        assert hashlib.sha256(packet).hexdigest() == row['sha256']
        assert len(packet) == row['wire_bytes'] >= HEADER.size
        magic, version, codec, flags, fid, w, h, total, offset, size, reserved, crc, capture_us = HEADER.unpack_from(packet)
        assert magic == b'MSV1' and version == codec == 1 and reserved == 0
        assert flags & ~3 == 0 and (w, h) == (720, 480)
        assert 0 < total <= 256 * 1024 and 0 < size <= 1024
        assert len(packet) == HEADER.size + size and offset + size <= total
        assert bool(flags & 1) == (offset == 0)
        assert bool(flags & 2) == (offset + size == total)
        if fid not in frames:
            assert offset == 0
            frames[fid] = dict(payload=bytearray(), total=total, crc=crc, capture_us=capture_us, complete=False)
        f = frames[fid]
        assert not f['complete'] and (total, crc, capture_us) == (f['total'], f['crc'], f['capture_us'])
        assert offset == len(f['payload']), 'gap, duplicate or reorder'
        f['payload'].extend(packet[HEADER.size:])
        if flags & 2:
            assert len(f['payload']) == total
            assert zlib.crc32(f['payload']) == crc, 'frame CRC mismatch'
            f['complete'] = True
        wire_bytes += len(packet)
    assert frames and all(x['complete'] for x in frames.values())
    return dict(status='PASS_BYTE_TRACE', producer=trace['producer'], datagrams=len(trace['datagrams']),
                wire_bytes=wire_bytes, payload_bytes=sum(len(f['payload']) for f in frames.values()),
                frames=[dict(id=fid, payload_bytes=len(f['payload']), crc32=f'{f["crc"]:08x}',
                             payload_sha256=hashlib.sha256(f['payload']).hexdigest()) for fid, f in frames.items()],
                clock_domain=trace['clock_domain'], shared_simulation_time=False,
                target_timing_qualified=False, sunshine_execution_verified=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('capture')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--producer-manifest', type=Path, required=True)
    p.add_argument('--port', type=int, required=True)
    p.add_argument('--packets', type=int, required=True)
    p.add_argument('--timeout', type=float, default=10)
    p = sub.add_parser('validate')
    p.add_argument('trace', type=Path)
    a = ap.parse_args()
    if a.command == 'validate':
        print(json.dumps(validate(a.trace), sort_keys=True))
        return
    assert a.packets > 0 and 0 < a.timeout <= 60 and not a.out.exists()
    producer = json.loads(a.producer_manifest.read_text())
    assert producer['kind'] in ('python_msv1_packetizer', 'external_capture_unattested')
    rows = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('127.0.0.1', a.port))
        s.settimeout(a.timeout)
        print('CAPTURE_READY', flush=True)
        for _ in range(a.packets):
            data, peer = s.recvfrom(65536)
            assert peer[0] == '127.0.0.1'
            rows.append(dict(arrival_ns=time.monotonic_ns(), wire_bytes=len(data),
                             sha256=hashlib.sha256(data).hexdigest(), base64=base64.b64encode(data).decode()))
    trace = dict(schema='v111-host-datagram-trace-v1', producer=producer,
                 clock_domain='host_monotonic_ns', shared_simulation_time=False,
                 target_timing_qualified=False, datagrams=rows)
    a.out.write_text(json.dumps(trace, indent=2, sort_keys=True) + '\n')
    print(json.dumps(validate(a.out), sort_keys=True))


if __name__ == '__main__':
    main()
