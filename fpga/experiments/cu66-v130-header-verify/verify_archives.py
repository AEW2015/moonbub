#!/usr/bin/env python3
"""Verify header-index object archives against unchanged receipts without extraction."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[3]
ATTEMPTS = ROOT / 'experiments/python-gamebub-v130/header-verify/attempts'
NAMES = ('20261111T023151282166Z',)

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    manifest = {}
    for name in NAMES:
        root = ATTEMPTS / name
        receipt = json.loads((root / 'receipt.json').read_text())
        expected = {k:v for k,v in receipt['artifacts'].items() if k.startswith('obj/')}
        archive = root / 'obj.tar.zst'
        proc = subprocess.Popen(['zstd', '-q', '-d', '-c', str(archive)], stdout=subprocess.PIPE)
        seen = {}
        with tarfile.open(fileobj=proc.stdout, mode='r|') as tar:
            for member in tar:
                p = PurePosixPath(member.name)
                if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] != 'obj':
                    raise ValueError('unsafe archive member: ' + member.name)
                if member.isdir():
                    continue
                if not member.isfile() or member.name not in expected or member.name in seen:
                    raise ValueError('unexpected archive member: ' + member.name)
                h = hashlib.sha256()
                f = tar.extractfile(member)
                for block in iter(lambda: f.read(1024 * 1024), b''):
                    h.update(block)
                seen[member.name] = h.hexdigest()
        proc.stdout.close()
        if proc.wait() != 0 or seen != expected:
            raise ValueError('archive/receipt content mismatch in ' + name)
        manifest[name] = {'status':receipt['status'], 'receipt_sha256':sha(root/'receipt.json'),
                          'archive_sha256':sha(archive), 'verified_files':len(seen)}
    out = ATTEMPTS / 'object-archives.json'
    out.write_text(json.dumps({'schema':'v130-header-object-archives-v1', 'attempts':manifest},
                              indent=2, sort_keys=True) + '\n')
    print('PASS: streamed archive contents match all receipt-listed object hashes; no files extracted')

if __name__ == '__main__':
    main()
