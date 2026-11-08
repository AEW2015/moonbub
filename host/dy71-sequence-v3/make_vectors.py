"""Regenerate explicit v3 golden data/reply vectors from pinned packet manifest."""
from pathlib import Path
import hashlib
import json
import struct
import zlib
import sequence_sender as sender

HERE = Path(__file__).resolve().parent
SESSION = 0x0102030405060708
CAPTURE = 0x1112131415161718
rows = []


def save(name, data, **meta):
    (HERE/name).write_bytes(data)
    rows.append(dict(file=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), **meta))


for count in [3, 12]:
    seq = sender.Sequence(HERE/'manifest.json', sender.PROFILE, count)
    for index in [0, count-1]:
        packet = seq.read(index)
        frame = struct.unpack_from('<I', packet, 8)[0]
        prefix = f'count{count}-frame{frame}'
        for offset in [0, (len(packet)-1)//1024*1024]:
            save(f'{prefix}-offset{offset}.dyn3', sender.core.datagram(packet, SESSION, CAPTURE+frame, offset, count), kind='data', frame=frame, offset=offset, sequence_count=count)
        h = list(sender.core.HEADER.unpack(sender.core.datagram(packet, SESSION, CAPTURE+frame, 0, count)[:48]))
        h[0] = b'DYA1'
        h[11] = 0
        for status in range(4):
            h[2] = status
            h[8] = 1024 if status in [0, 3] else len(packet)
            wire = sender.core.HEADER.pack(*h)
            save(f'{prefix}-status{status}.dya3', wire+struct.pack('<I', zlib.crc32(wire)), kind='reply', frame=frame, status=status, sequence_count=count)
(HERE/'golden-vectors.json').write_text(json.dumps({'profile': sender.PROFILE, 'session': SESSION, 'capture_us_frame0': CAPTURE, 'vectors': rows}, indent=2)+'\n')
print(f'Wrote {len(rows)} count-bound v3 vectors')
