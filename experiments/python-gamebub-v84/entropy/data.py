"""Verified per-canonical-tile entropy primitive observations; not cycle costs."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIELDS = ('decisions', 'renorm', 'stream_bytes', 'rice_values', 'events',
          'raw_bytes', 'header_bytes', 'crc_bytes', 'emits', 'raw_bits', 'prob_init')


def iter_frames(root=None, *, verify=True):
    root = Path(root) if root is not None else ROOT
    index = json.loads((root / 'index.json').read_text())
    path = root / index['data']['path']
    if verify:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == index['data']['gzip_sha256']
    digest = hashlib.sha256()
    count = 0
    with gzip.open(path, 'rb') as stream:
        for line in stream:
            digest.update(line)
            frame = json.loads(line)
            work = frame.pop('work')
            assert len(work) == 8100
            assert all(len(row) == len(FIELDS) and all(type(x) is int and x >= 0 for x in row) for row in work)
            frame['tile_work'] = [dict(zip(FIELDS, row)) for row in work]
            assert len(frame['zero_mask']) == 8100 and set(frame['zero_mask']) <= {'0', '1'}
            count += 1
            yield frame
    if verify:
        assert digest.hexdigest() == index['data']['raw_sha256']
        assert count == index['record_count'] == 457
