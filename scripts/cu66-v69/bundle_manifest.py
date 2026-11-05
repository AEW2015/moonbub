#!/usr/bin/env python3
"""Pin the completed v69 handoff files, or verify their bytes after transfer."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'docs/cu66-v69/bundle-manifest.json'
DIRS = ('docs/cu66-v69', 'scripts/cu66-v69', 'experiments/cu66-native-v69',
        'fpga/experiments/cu66-v69')


def collect():
    files = [ROOT / 'README.md', ROOT / 'docs/gamebub-application-specific-codec-plan.md']
    for name in DIRS:
        files.extend(p for p in (ROOT / name).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix != '.pyc' and p != DEST)
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(files))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    current = collect()
    if args.write:
        DEST.write_text(json.dumps({'schema': 'cu66-v69-handoff-file-sha256-v1',
                                   'scope': 'file integrity only; not a test verdict',
                                   'files_sha256': current}, indent=2) + '\n')
        print(f'WROTE bundle manifest: {len(current)} files')
        return
    old = json.loads(DEST.read_text())['files_sha256']
    missing = sorted(set(old) - set(current))
    extra = sorted(set(current) - set(old))
    changed = sorted(p for p in set(old) & set(current) if old[p] != current[p])
    if missing or extra or changed:
        raise SystemExit(json.dumps({'status': 'FAIL', 'missing': missing,
                                     'extra': extra, 'changed': changed}, indent=2))
    print(f'BUNDLE_FILE_INTEGRITY_PASS {len(current)} files; test verdicts remain separate')


if __name__ == '__main__':
    main()
