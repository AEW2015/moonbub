#!/usr/bin/env python3
"""Validate native negative fixtures and export the C++ runner's TSV input."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
NATIVE = ROOT / 'experiments/cu66-native-v69'
MANIFEST = NATIVE / 'negative_manifest.json'
OUTPUT = Path(__file__).resolve().parent / 'case-list.tsv'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def validate_blob(spec, label):
    path = NATIVE / spec['path']
    data = path.read_bytes()
    actual = sha256(data)
    if len(data) != spec['bytes'] or actual != spec['sha256']:
        raise ValueError(f'{label}: fixture size/hash mismatch: {path}')
    return data


def main():
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get('schema') != 'cu66-native-v69-negative':
        raise ValueError('unexpected negative manifest schema')
    cases = manifest.get('cases')
    if not isinstance(cases, list) or len(cases) != 28:
        raise ValueError('expected exactly 28 negative cases')
    names = [case.get('name') for case in cases]
    if len(set(names)) != len(names) or any(not name for name in names):
        raise ValueError('negative case names must be unique and non-empty')
    seed = manifest['seed_key_packet']
    recovery = manifest['recovery_key_packet']
    seed_data = validate_blob(seed, 'seed key')
    recovery_data = validate_blob(recovery, 'recovery key')
    if len(seed_data) == 0 or len(recovery_data) == 0:
        raise ValueError('seed/recovery packet must not be empty')

    rows = []
    for case in cases:
        data = validate_blob(case['packet'], case['name'])
        rows.append('\t'.join((case['name'], case['category'], case['packet']['path'],
                               str(len(data)), sha256(data))))
    OUTPUT.write_text('\n'.join(rows) + '\n', encoding='utf-8')
    print(f'NEGATIVE_CASE_EXPORT_PASS cases={len(rows)} '
          f'manifest_sha256={sha256(manifest_bytes)} tsv={OUTPUT.name}')


if __name__ == '__main__':
    main()
