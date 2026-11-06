"""Load retained real all-visible control AB38 components; no video timing model."""
import gzip
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent
CAPS = (256, 65536)


def read_record(stream, digest=None):
    raw = bytearray()
    def take(n):
        data = stream.read(n)
        if len(data) != n:
            raise ValueError('truncated residual component record')
        raw.extend(data)
        return data
    def u32():
        return struct.unpack('<I', take(4))[0]
    first = stream.read(4)
    if not first:
        return None
    if len(first) != 4:
        raise ValueError('truncated record length')
    raw.extend(first)
    size = struct.unpack('<I', first)[0]
    if not 1 <= size <= 65536:
        raise ValueError('component metadata bound')
    frame = json.loads(take(size))
    qsize = u32()
    if qsize != 338:
        raise ValueError('fixed quant-map length')
    frame['qmap'] = take(qsize)
    hsize = u32()
    if not 110 <= hsize <= 49152:
        raise ValueError('encoded HUD length')
    frame['hud'] = take(hsize)
    variants = {}
    for cap in CAPS:
        planes = []
        for axis in range(3):
            count = u32()
            if count > (5400 if axis == 0 else 1350):
                raise ValueError('component chunk-count bound')
            chunks = []
            for _ in range(count):
                blocks, length = u32(), u32()
                if not 1 <= blocks <= min(cap, 5400 if axis == 0 else 1350):
                    raise ValueError('component chunk-block bound')
                if not 46 <= length <= 46 + 128 * blocks:
                    raise ValueError('component AB38 length bound')
                chunks.append(dict(blocks=blocks, data=take(length)))
            planes.append(chunks)
        variants[str(cap)] = planes
    frame['variants'] = variants
    frame['component_sha256'] = hashlib.sha256(raw).hexdigest()
    frame['component_bytes'] = len(raw)
    if digest is not None:
        digest.update(raw)
    return frame


def iter_frames(root=None, *, verify=True):
    root = Path(root) if root is not None else ROOT
    index = json.loads((root / 'index.json').read_text())
    path = root / index['data']['path']
    if verify and hashlib.sha256(path.read_bytes()).hexdigest() != index['data']['gzip_sha256']:
        raise ValueError('residual compressed data SHA')
    digest = hashlib.sha256()
    count = 0
    with gzip.open(path, 'rb') as stream:
        while True:
            frame = read_record(stream, digest)
            if frame is None:
                break
            if verify:
                expected = index['frames'][count]
                if frame['component_sha256'] != expected['component_sha256']:
                    raise ValueError('residual record SHA')
                for name in ('cohort', 'ordinal', 'fid', 'refid', 'key', 'canonical_coefficients_sha256'):
                    if frame[name] != expected[name]:
                        raise ValueError('residual frame identity')
            count += 1
            yield frame
    if verify and (count != index['record_count'] or digest.hexdigest() != index['data']['raw_sha256']):
        raise ValueError('residual raw/count SHA')
