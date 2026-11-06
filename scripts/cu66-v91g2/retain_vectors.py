#!/usr/bin/env python3
"""Recreate exact failed-attempt text vectors from the retained frozen fixture."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'fpga/experiments/cu66-v91g2'
FIXTURE = ROOT/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'
DEST = AREA/'historical-vector-storage.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def reconstruct():
    rows = [json.loads(line) for line in gzip.decompress(FIXTURE.read_bytes()).splitlines()]
    return ''.join(' '.join(map(str,(r['id'],r['blocks'],r['packet_hex'],r['dense_hex'],r['packed_hex'])))+'\n' for r in rows).encode()


def verify():
    metadata = json.loads(DEST.read_text())
    raw = reconstruct()
    assert metadata['fixture_sha256'] == sha(FIXTURE.read_bytes())
    assert metadata['serializer_sha256'] == sha(Path(__file__).read_bytes())
    assert metadata['raw_sha256'] == sha(raw) and metadata['raw_bytes'] == len(raw)
    for entry in metadata['failed_aliases']:
        path = ROOT/entry['alias']
        report = json.loads(path.with_name('results.json').read_text())
        assert report['status'] == 'FAIL'
        assert sha(path.with_name('results.json').read_bytes()) == entry['report_sha256']
        assert report['text_vectors_sha256'] == report['artifacts_sha256']['vectors.txt'] == sha(raw)
        assert report['vectors_sha256'] == sha(FIXTURE.read_bytes())
        if path.exists():
            assert path.read_bytes() == raw
    return metadata,raw


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--restore',action='store_true')
    args=parser.parse_args()
    if args.write:
        aliases=[]
        for path in sorted((AREA/'pipeline-attempts').glob('*/results.json')):
            report=json.loads(path.read_text())
            if report['status']=='FAIL':
                aliases.append(dict(alias=str(path.with_name('vectors.txt').relative_to(ROOT)),
                    report_sha256=sha(path.read_bytes()),error_class=report['error_class']))
        raw=reconstruct()
        DEST.write_text(json.dumps(dict(schema='cu66-v91g2-failed-vector-aliases-v1',
            fixture=str(FIXTURE.relative_to(ROOT)),fixture_sha256=sha(FIXTURE.read_bytes()),
            serializer=str(Path(__file__).relative_to(ROOT)),serializer_sha256=sha(Path(__file__).read_bytes()),
            raw_sha256=sha(raw),raw_bytes=len(raw),failed_aliases=aliases,
            scope='Original failed receipts and source snapshots stay unchanged. Local transient text remains; exact reconstruction supplies ignored files in a fresh checkout.'),indent=2)+'\n')
    metadata,raw=verify()
    if args.restore:
        for entry in metadata['failed_aliases']:
            path=ROOT/entry['alias']
            if not path.exists():path.write_bytes(raw)
    print('V91G2_FAILED_VECTOR_ALIASES_PASS',len(metadata['failed_aliases']),len(raw))


if __name__=='__main__':
    main()
