#!/usr/bin/env python3
"""Read-only integrity audit for frozen CU66 v69/v70 inputs to v71."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PINS = ROOT / 'fpga/experiments/cu66-v71/baseline-sources.json'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def check_manifest(relpath, field, failures):
    manifest_path = ROOT / relpath
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    entries = manifest[field]
    if not isinstance(entries, dict) or not entries:
        failures.append(f'{relpath}: empty or invalid {field}')
        return 0
    for name, expected in sorted(entries.items()):
        path = ROOT / name
        if not path.is_file():
            failures.append(f'{relpath}: missing pinned file {name}')
        elif sha256(path) != expected:
            failures.append(f'{relpath}: changed pinned file {name}')
    return len(entries)


def main():
    try:
        pins = json.loads(PINS.read_text(encoding='utf-8'))
        if pins.get('schema') != 'cu66-v71-frozen-inputs-v1':
            raise ValueError('unexpected v71 input-pin schema')
        failures = []
        counts = {}
        counts['v69_bundle'] = check_manifest(
            'docs/cu66-v69/bundle-manifest.json', 'files_sha256', failures)
        counts['v70_bundle'] = check_manifest(
            'docs/cu66-v70/bundle-manifest.json', 'files_sha256', failures)
        counts['v70_reviewed_sources'] = check_manifest(
            'docs/cu66-v70/baseline.json', 'files_sha256', failures)
        for relpath, expected in sorted(pins['files_sha256'].items()):
            path = ROOT / relpath
            if not path.is_file():
                failures.append(f'v71 pin: missing {relpath}')
            elif sha256(path) != expected:
                failures.append(f'v71 pin: changed {relpath}')
        # Preserve the prior verifier's scope/count checks, including the full v69
        # directory inventory. It is read-only and emits no artifacts.
        prior = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/cu66-v70/verify_baseline.py')],
            cwd=ROOT, text=True, capture_output=True, check=False)
        if prior.returncode:
            failures.append('v70 prior verifier failed: ' +
                            (prior.stdout + prior.stderr).strip().replace('\n', ' | '))
        if failures:
            print('V71_BASELINE_INTEGRITY_FAIL')
            for failure in failures:
                print('  ' + failure)
            return 1
        print('V71_BASELINE_INTEGRITY_PASS '
              f"v69_bundle={counts['v69_bundle']} files; "
              f"v70_bundle={counts['v70_bundle']} files; "
              f"v70_reviewed_sources={counts['v70_reviewed_sources']} files; "
              f"additional_v71_pins={len(pins['files_sha256'])}; "
              'integrity only, not test/cadence evidence')
        print(prior.stdout.strip())
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f'V71_BASELINE_INTEGRITY_ERROR {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
