#!/usr/bin/env python3
"""Retain failed prefetch post-analysis input by exact frozen serializer."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91g'
FIXTURE = ROOT / 'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'
DEST = AREA / 'historical-vector-storage.json'
ALIAS = AREA / 'pipeline-attempts/20261106T185759511833Z-dd297d1f/vectors.txt'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def reconstructed():
    rows = [json.loads(line) for line in gzip.decompress(FIXTURE.read_bytes()).splitlines()]
    return ''.join(' '.join(map(str, (row['id'], row['blocks'], row['packet_hex'], row['dense_hex'], row['packed_hex']))) + '\n' for row in rows).encode()


def verify():
    metadata = json.loads(DEST.read_text())
    data = reconstructed()
    assert metadata['fixture_sha256'] == digest(FIXTURE.read_bytes())
    assert metadata['serializer_sha256'] == digest(Path(__file__).read_bytes())
    assert metadata['raw_sha256'] == digest(data) and metadata['raw_bytes'] == len(data)
    assert metadata['alias'] == str(ALIAS.relative_to(ROOT))
    report = json.loads(ALIAS.with_name('results.json').read_text())
    assert report['status'] == 'FAIL' and report['error_class'] == 'TypeError'
    assert report['text_vectors_sha256'] == report['artifacts_sha256']['vectors.txt'] == digest(data)
    assert report['vectors_sha256'] == digest(FIXTURE.read_bytes())
    verdict = json.loads(ALIAS.with_name('simulation.jsonl').read_text().splitlines()[-1])
    assert verdict['type'] == 'verdict' and verdict['status'] == 'TEST_PASS'
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
        DEST.write_text(json.dumps(dict(schema='cu66-v91g-retained-vector-v1',
            fixture=str(FIXTURE.relative_to(ROOT)), fixture_sha256=digest(FIXTURE.read_bytes()),
            serializer=str(Path(__file__).relative_to(ROOT)), serializer_sha256=digest(Path(__file__).read_bytes()),
            raw_sha256=digest(data), raw_bytes=len(data), alias=str(ALIAS.relative_to(ROOT)),
            scope='Original failed post-analysis receipt/source hashes unchanged; C++ RTL verdict was PASS. Local unpacked text stays on disk.'), indent=2) + '\n')
    metadata = verify()
    if args.restore and not ALIAS.exists():
        ALIAS.write_bytes(reconstructed())
    print('V91G_RETAINED_VECTOR_PASS', metadata['raw_bytes'])


if __name__ == '__main__':
    main()
