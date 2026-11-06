#!/usr/bin/env python3
"""Preserve failed-attempt text fixtures by exact reconstruction from pinned gzip.

The two identical early text fixtures add 168,640 redundant diff lines. Keep
their original manifest hashes, canonical compressed input and exact serializer.
Unpacked local copies remain untouched; --restore recreates them if missing.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91b'
DEST = AREA / 'historical-vector-storage.json'
FIXTURE = ROOT / 'experiments/python-gamebub-v91b/context-vectors/contexts.jsonl.gz'
ATTEMPTS = ('20261106T171515002819Z-74b8334a', '20261106T171620543576Z-80a9a79f')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def reconstructed():
    lines = []
    for raw in gzip.decompress(FIXTURE.read_bytes()).splitlines():
        case = json.loads(raw)
        expected = case['expected']
        fields = (case['id'], case['blocks'], case['band'], case['k0'], case['k1'],
                  case['event_count'], case['bit_size'], case['data_hex'] or '-',
                  case.get('expected_error', 0), len(expected))
        lines.append(' '.join(map(str, fields)) + '\n')
        lines.extend(' '.join(map(str, coefficient)) + '\n' for coefficient in expected)
    return ''.join(lines).encode()


def verify():
    metadata = json.loads(DEST.read_text())
    assert metadata['fixture_sha256'] == digest(FIXTURE.read_bytes())
    assert metadata['serializer_sha256'] == digest(Path(__file__).read_bytes())
    data = reconstructed()
    assert metadata['raw_sha256'] == digest(data) and metadata['raw_bytes'] == len(data)
    assert metadata['aliases'] == [str((AREA / 'attempts' / name / 'vectors.txt').relative_to(ROOT)) for name in ATTEMPTS]
    for relative in metadata['aliases']:
        path = ROOT / relative
        result = json.loads(path.with_name('results.json').read_text())
        assert result['status'] == 'FAIL'
        assert result['artifacts_sha256']['vectors.txt'] == digest(data)
        assert result['text_vectors_sha256'] == digest(data)
        assert result['vectors_sha256'] == digest(FIXTURE.read_bytes())
        if path.exists():
            assert path.read_bytes() == data
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    if args.write:
        data = reconstructed()
        metadata = dict(schema='cu66-v91b-historical-vector-storage-v1',
                        fixture=str(FIXTURE.relative_to(ROOT)), fixture_sha256=digest(FIXTURE.read_bytes()),
                        serializer=str(Path(__file__).relative_to(ROOT)), serializer_sha256=digest(Path(__file__).read_bytes()),
                        raw_sha256=digest(data), raw_bytes=len(data),
                        aliases=[str((AREA / 'attempts' / name / 'vectors.txt').relative_to(ROOT)) for name in ATTEMPTS],
                        scope='Exact reconstruction of duplicate text input only; original failed-run reports and raw hashes unchanged. Local copies are ignored, not deleted.')
        DEST.write_text(json.dumps(metadata, indent=2) + '\n')
    metadata = verify()
    if args.restore:
        data = reconstructed()
        for relative in metadata['aliases']:
            path = ROOT / relative
            if not path.exists():
                path.write_bytes(data)
    print('HISTORICAL_VECTOR_STORAGE_PASS', len(metadata['aliases']), metadata['raw_bytes'])


if __name__ == '__main__':
    main()
