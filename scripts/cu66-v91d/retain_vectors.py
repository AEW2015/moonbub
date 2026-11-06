#!/usr/bin/env python3
"""Verify/restore the regression failure's text fixture from pinned gzip."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91d'
FIXTURE = ROOT / 'experiments/python-gamebub-v91d/vectors/coefficients.jsonl.gz'
DEST = AREA / 'historical-vector-storage.json'
ALIAS = AREA / 'pipeline-attempts/20261106T175724427619Z-afe10872/vectors.txt'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def reconstructed():
    rows = [json.loads(line) for line in gzip.decompress(FIXTURE.read_bytes()).splitlines()]
    return ''.join(' '.join(map(str, (row['id'], row['blocks'], row['packet_hex'],
                                      row['dense_hex'], row['packed_hex']))) + '\n' for row in rows).encode()


def verify():
    metadata = json.loads(DEST.read_text())
    assert metadata['fixture_sha256'] == digest(FIXTURE.read_bytes())
    assert metadata['serializer_sha256'] == digest(Path(__file__).read_bytes())
    data = reconstructed()
    assert metadata['raw_sha256'] == digest(data) and metadata['raw_bytes'] == len(data)
    assert metadata['alias'] == str(ALIAS.relative_to(ROOT))
    report = json.loads(ALIAS.with_name('results.json').read_text())
    assert report['status'] == 'FAIL'
    assert report['text_vectors_sha256'] == report['artifacts_sha256']['vectors.txt'] == digest(data)
    assert report['vectors_sha256'] == digest(FIXTURE.read_bytes())
    assert 'replacement start lost after write ACK error' in ALIAS.with_name('simulation.jsonl').read_text()
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
        DEST.write_text(json.dumps(dict(schema='cu66-v91d-retained-vector-v1',
            fixture=str(FIXTURE.relative_to(ROOT)), fixture_sha256=digest(FIXTURE.read_bytes()),
            serializer=str(Path(__file__).relative_to(ROOT)), serializer_sha256=digest(Path(__file__).read_bytes()),
            raw_sha256=digest(data), raw_bytes=len(data), alias=str(ALIAS.relative_to(ROOT)),
            scope='Exact reconstruction of failed regression text input; original failure/source/receipt hashes unchanged and unpacked local copy retained.'), indent=2) + '\n')
    metadata = verify()
    if args.restore and not ALIAS.exists():
        ALIAS.write_bytes(reconstructed())
    print('V91D_RETAINED_VECTOR_PASS', metadata['raw_bytes'])


if __name__ == '__main__':
    main()
