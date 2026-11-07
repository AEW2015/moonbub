"""Verified actual EC94 choices joined to the frozen V88 component identities.

Each original whole-plane chunk gains ec94 (9 byte strings: AB, BR, six rANS variants, local minimum) and
ec94_stats (all native counters/timings). This does not choose a frame policy.
"""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[3]
AREA = Path(__file__).resolve().parent


def iter_frames(*, verify=True, index_path=None):
    index_path = Path(index_path) if index_path is not None else AREA / 'index.json'
    index = json.loads(index_path.read_text())
    path = AREA / index['data']['path']
    if verify:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == index['data']['gzip_sha256']
    spec = importlib.util.spec_from_file_location('ec94_frozen_data', ROOT / 'experiments/python-gamebub-v88/entropy/data.py')
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    digest = hashlib.sha256()
    count = 0
    chunks = 0
    with gzip.open(path, 'rb') as stream:
        def take(length):
            value = stream.read(length)
            assert len(value) == length, 'EC94 archive truncation'
            digest.update(value)
            return value
        for frame in frozen.iter_frames(verify=verify):
            length, = struct.unpack('<I', take(4))
            assert 1 <= length <= 131072, 'EC94 metadata bound'
            meta = json.loads(take(length))
            for key in ('cohort', 'fid', 'ordinal', 'key', 'canonical_coefficients_sha256'):
                assert frame[key] == meta[key], 'EC94 frame identity'
            for axis, plane in enumerate(frame['variants']['65536']):
                assert len(plane) == len(meta['planes'][axis]), 'EC94 plane chunk count'
                for chunk, stats in zip(plane, meta['planes'][axis], strict=True):
                    assert chunk['blocks'] == stats['blocks'] and len(chunk['data']) == stats['old_bytes']
                    assert len(stats['masks']) == 9
                    candidates = []
                    for mask, observation in enumerate(stats['masks']):
                        length, = struct.unpack('<I', take(4))
                        assert 48 <= length <= 48 + 128 * chunk['blocks']
                        data = take(length)
                        assert observation['requested_selector'] == ([0, 85, 170, 170, 170, 255, 255, 255][mask] if mask < 8 else stats['masks'][8]['requested_selector']) and length == observation['bytes']
                        if verify:
                            assert hashlib.sha256(data).hexdigest() == observation['sha256'], 'EC94 candidate SHA'
                        candidates.append(data)
                    chunk.update(ec94=candidates, ec94_stats=stats)
                    chunks += 1
            count += 1
            yield frame
        assert stream.read(1) == b'', 'EC94 archive trailing bytes'
    if verify:
        assert count == index['native_sources'] == 457 and chunks == index['chunks'] == 1371
        assert digest.hexdigest() == index['data']['raw_sha256'], 'EC94 archive raw SHA'
