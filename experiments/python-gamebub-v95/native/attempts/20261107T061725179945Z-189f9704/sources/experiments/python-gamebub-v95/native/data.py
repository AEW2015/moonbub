"""Frozen V95 six-profile planes joined to V88 coefficient and V82 pixel inputs.

Canonical pixels are predecoded targets: capture, transform, target generation and
full host encoder timing are outside the native palette generation measurement.
"""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
ROOT = Path(__file__).resolve().parents[3]
AREA = Path(__file__).resolve().parent
PROFILES = ('control', 'P2', 'P4', 'P8', 'E8', 'W8')

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def iter_frames(*, verify=True, index_path=None):
    index = json.loads((Path(index_path) if index_path else AREA / 'index.json').read_text())
    frozen = load('pa95_frozen', ROOT / 'experiments/python-gamebub-v88/entropy/data.py')
    targets = load('pa95_targets', ROOT / 'experiments/python-gamebub-v82/native/data.py')
    originals = iter(zip(frozen.iter_frames(verify=verify), targets.iter_frames(verify=verify), strict=True))
    count = 0
    for shard in index['shards']:
        path = AREA / shard['path']
        if verify:
            assert hashlib.sha256(path.read_bytes()).hexdigest() == shard['gzip_sha256']
        digest = hashlib.sha256()
        with gzip.open(path, 'rb') as stream:
            def take(n):
                data = stream.read(n)
                assert len(data) == n, 'PA95 archive truncation'
                digest.update(data)
                return data
            for _ in range(shard['frames']):
                frame, target = next(originals)
                length, = struct.unpack('<I', take(4))
                assert 1 <= length <= 2097152
                meta = json.loads(take(length))
                for key in ('cohort', 'ordinal', 'fid', 'key', 'canonical_coefficients_sha256'):
                    assert frame[key] == meta[key]
                for key in ('cohort', 'ordinal', 'fid', 'key', 'canonical_sha256'):
                    assert target[key] == meta[key]
                frame['plane_variants'], frame['palette_stats'] = [], []
                for axis in range(3):
                    packets = []
                    stats = meta['planes'][axis]['profiles']
                    for profile in range(6):
                        length, = struct.unpack('<I', take(4))
                        assert 12 <= length <= 48 + 146 * (5400 if axis == 0 else 1350)
                        packet = take(length)
                        assert length == stats[profile]['bytes']
                        if verify:
                            assert hashlib.sha256(packet).hexdigest() == stats[profile]['sha256']
                        packets.append(packet)
                    frame['plane_variants'].append(packets)
                    frame['palette_stats'].append(stats)
                frame['palette_generation'] = meta['planes']
                frame['target'] = target
                frame['canonical_sha256'] = target['canonical_sha256']
                frame['hidden_mask'] = target['hidden_mask']
                frame['copy_ref_mask'] = target['copy_ref_mask']
                frame['tiles'] = target['tiles']
                frame['planes'] = target['planes']
                count += 1
                yield frame
            assert stream.read(1) == b'', 'PA95 trailing archive bytes'
        if verify:
            assert digest.hexdigest() == shard['raw_sha256']
    assert next(originals, None) is None
    assert count == index['native_sources'] == 457
