#!/usr/bin/env python3
"""Read-only integrity check for the frozen CU66 v69 inputs to the v70 plan."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / 'docs/cu66-v70/baseline.json'
V69_MANIFEST = ROOT / 'docs/cu66-v69/bundle-manifest.json'
V69_DIRS = ('docs/cu66-v69', 'scripts/cu66-v69', 'experiments/cu66-native-v69',
            'fpga/experiments/cu66-v69')


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def current_v69_files():
    files = [ROOT / 'README.md', ROOT / 'docs/gamebub-application-specific-codec-plan.md']
    for name in V69_DIRS:
        folder = ROOT / name
        if not folder.is_dir():
            continue
        files.extend(path for path in folder.rglob('*') if path.is_file()
                     and '__pycache__' not in path.parts and path.suffix != '.pyc'
                     and path != V69_MANIFEST)
    return {str(path.relative_to(ROOT)): sha256(path)
            for path in sorted(set(files))}


def main():
    try:
        baseline = json.loads(BASELINE.read_text(encoding='utf-8'))
        expected = baseline['files_sha256']
        if baseline.get('schema') != 'cu66-v70-plan-baseline-v1':
            raise ValueError('unexpected baseline schema')
        if not isinstance(expected, dict) or len(expected) != 15:
            raise ValueError('baseline must contain exactly 15 source pins')
        failures = []
        for relpath, want in sorted(expected.items()):
            path = ROOT / relpath
            if not path.is_file():
                failures.append(f'missing pinned file: {relpath}')
            elif sha256(path) != want:
                failures.append(f'pinned file changed: {relpath}')

        manifest = json.loads(V69_MANIFEST.read_text(encoding='utf-8'))['files_sha256']
        current = current_v69_files()
        missing = sorted(set(manifest) - set(current))
        extra = sorted(set(current) - set(manifest))
        changed = sorted(path for path in set(manifest) & set(current)
                         if manifest[path] != current[path])
        if missing:
            failures.append('v69 bundle files missing: ' + ', '.join(missing))
        if extra:
            failures.append('unmanifested v69 bundle files: ' + ', '.join(extra))
        if changed:
            failures.append('v69 bundle files changed: ' + ', '.join(changed))
        if failures:
            print('V70_BASELINE_INTEGRITY_FAIL')
            for failure in failures:
                print(f'  {failure}')
            return 1
        print(f'V70_BASELINE_INTEGRITY_PASS {len(expected)} reviewed pins; '
              f'{len(manifest)} v69 bundle files; integrity only, not test evidence')
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f'V70_BASELINE_INTEGRITY_ERROR {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
