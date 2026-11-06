#!/usr/bin/env python3
"""Verify/restore the early failed run's text fixture from its pinned gzip."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91c'
DEST = AREA / 'historical-vector-storage.json'
FIXTURE = ROOT / 'experiments/python-gamebub-v91c/packet-vectors/packets.jsonl.gz'
ALIAS = AREA / 'attempts/20261106T172953411539Z-fbc64b81/vectors.txt'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def reconstructed():
    lines = []
    for raw in gzip.decompress(FIXTURE.read_bytes()).splitlines():
        case = json.loads(raw)
        lines.append(' '.join(map(str, (case['id'], case['blocks'], case['packet_hex'],
                                       case.get('expected_error', 0), len(case['expected'])))) + '\n')
        lines.extend(' '.join(map(str, coefficient)) + '\n' for coefficient in case['expected'])
    return ''.join(lines).encode()


def verify():
    metadata = json.loads(DEST.read_text())
    assert metadata['fixture_sha256'] == digest(FIXTURE.read_bytes())
    assert metadata['serializer_sha256'] == digest(Path(__file__).read_bytes())
    assert metadata['alias'] == str(ALIAS.relative_to(ROOT))
    data = reconstructed()
    assert metadata['raw_sha256'] == digest(data) and metadata['raw_bytes'] == len(data)
    result = json.loads(ALIAS.with_name('results.json').read_text())
    assert result['status'] == 'FAIL'
    assert result['artifacts_sha256']['vectors.txt'] == result['text_vectors_sha256'] == digest(data)
    assert result['vectors_sha256'] == digest(FIXTURE.read_bytes())
    if ALIAS.exists():
        assert ALIAS.read_bytes() == data
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    if args.write:
        data = reconstructed()
        DEST.write_text(json.dumps(dict(schema='cu66-v91c-retained-text-vector-v1',
            fixture=str(FIXTURE.relative_to(ROOT)), fixture_sha256=digest(FIXTURE.read_bytes()),
            serializer=str(Path(__file__).relative_to(ROOT)), serializer_sha256=digest(Path(__file__).read_bytes()),
            raw_sha256=digest(data), raw_bytes=len(data), alias=str(ALIAS.relative_to(ROOT)),
            scope='Exact reconstruction of failed-attempt text input; original receipt hashes unchanged and local unpacked copy retained.'), indent=2) + '\n')
    metadata = verify()
    if args.restore and not ALIAS.exists():
        ALIAS.write_bytes(reconstructed())
    print('V91C_RETAINED_VECTOR_PASS', metadata['raw_bytes'])


if __name__ == '__main__':
    main()
