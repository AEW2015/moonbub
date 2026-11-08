"""Explicit two-frame DYN1 lab sender. Not JPEG, Sunshine negotiation or a rate test."""
import argparse
import json
from pathlib import Path
import secrets
import socket
import struct
import time
import zlib

HEADER = struct.Struct('<4sBBHQIIIIIQHH')


def datagram(body, session, capture_us, offset):
    frame, reference = struct.unpack_from('<II', body, 8)
    payload = body[offset:offset + 1024]
    b = HEADER.pack(b'DYN1', 1, 0, 48, session, frame, reference,
                    len(body), offset, zlib.crc32(body), capture_us, len(payload), 0) + payload
    return b + struct.pack('<I', zlib.crc32(b))


def decode_reply(b):
    if len(b) != 52 or zlib.crc32(b[:48]) != struct.unpack_from('<I', b, 48)[0]:
        raise ValueError('reply length/CRC')
    h = HEADER.unpack(b[:48])
    if h[0] != b'DYA1' or h[1] != 1 or h[2] not in range(4) or h[3] != 48 or h[-2:] != (0, 0):
        raise ValueError('reply header')
    return h


def validate(body):
    if not 80 <= len(body) <= 49152 or body[:5] != b'CU66\x01':
        raise ValueError('requires original CU66 v1, 80..49152 bytes')
    if struct.unpack_from('<HH', body, 16) != (720, 480):
        raise ValueError('requires 720x480 CU66 canvas')
    if zlib.crc32(body[:-4]) != struct.unpack_from('<I', body, len(body)-4)[0]:
        raise ValueError('CU66 inner CRC')
    offset, size = struct.unpack_from('<II', body, 68)
    if 76 + offset + size != len(body)-4 or size > 20000:
        raise ValueError('HU extent/budget')


def send_frame(sock, receiver, body, session, log):
    validate(body)
    capture = time.time_ns() // 1000
    frame, reference = struct.unpack_from('<II', body, 8)
    identity = (session, frame, reference, len(body), zlib.crc32(body), capture)
    def presented():
        row = dict(frame=frame, reference=reference, capture_us=capture,
                   bytes=len(body), crc32=f'{identity[4]:08x}', status='presented')
        log.write(json.dumps(row)+'\n')
        log.flush()
        return row
    for offset in range(0, len(body), 1024):
        wire = datagram(body, session, capture, offset)
        end = min(offset + 1024, len(body))
        accepted = False
        for attempt in range(10):
            sock.sendto(wire, receiver)
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline:
                try:
                    b, peer = sock.recvfrom(2048)
                except socket.timeout:
                    continue
                if peer != receiver:
                    continue
                try:
                    h = decode_reply(b)
                except ValueError:
                    continue
                if (h[4], h[5], h[6], h[7], h[9], h[10]) != identity:
                    continue
                if h[2] == 3:
                    raise RuntimeError(f'frame {frame}: receiver failed/retained')
                if h[2] == 2 and end == len(body) and h[8] == len(body):
                    return presented()  # final storage ACK may have been lost/reordered
                if h[8] == end and h[2] in (0, 1):
                    accepted = True
                    break
            if accepted:
                break
        if not accepted:
            raise TimeoutError(f'frame {frame}: stored offset {end}')
    # All bytes stored != decoded/presented. Allow the deliberately scalar diagnostic time.
    deadline = time.monotonic() + 90
    query_at = time.monotonic() + 60
    while time.monotonic() < deadline:
        if time.monotonic() >= query_at:
            sock.sendto(wire, receiver)  # identical final chunk: idempotent presentation query
            query_at = time.monotonic() + 5
        try:
            b, peer = sock.recvfrom(2048)
        except socket.timeout:
            continue
        if peer != receiver:
            continue
        try:
            h = decode_reply(b)
        except ValueError:
            continue
        if (h[4], h[5], h[6], h[7], h[9], h[10]) != identity:
            continue
        if h[2] == 3:
            raise RuntimeError(f'frame {frame}: receiver failed/retained')
        if h[2] == 2 and h[8] == len(body):
            return presented()
    raise TimeoutError(f'frame {frame}: presentation unknown')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receiver', required=True)
    p.add_argument('--port', type=int, default=5535)
    p.add_argument('--bind', default='0.0.0.0')
    p.add_argument('--log', type=Path, required=True)
    p.add_argument('packets', nargs=2, type=Path, help='original key then dependent P CU66 files')
    a = p.parse_args()
    bodies = [x.read_bytes() for x in a.packets]
    for b in bodies:
        validate(b)
    if not bodies[0][5] & 1 or bodies[1][5] & 1:
        p.error('requires key then predicted frame')
    if struct.unpack_from('<I', bodies[1], 12)[0] != struct.unpack_from('<I', bodies[0], 8)[0]:
        p.error('P reference does not match key ID')
    session = secrets.randbits(64) or 1
    receiver = (socket.gethostbyname(a.receiver), a.port)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s, a.log.open('x') as log:
        s.bind((a.bind, 0))
        s.settimeout(0.1)
        for b in bodies:
            print(send_frame(s, receiver, b, session, log), flush=True)


if __name__ == '__main__':
    main()
