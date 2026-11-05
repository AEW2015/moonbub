#!/usr/bin/env python3
"""Read-only audit of frozen CU66 v69/v70/v71 bundles and v71 source pins."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PINS = ROOT / 'fpga/experiments/cu66-v72/baseline-sources.json'
EXPECTED_COMMIT = '207b16d8f0e04a928810a294787609c6e664db71'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def check_files(entries, label, failures):
    if not isinstance(entries, dict) or not entries:
        failures.append(f'{label}: empty or invalid files_sha256')
        return 0
    for name, expected in sorted(entries.items()):
        path = ROOT / name
        if not path.is_file():
            failures.append(f'{label}: missing {name}')
        elif sha256(path) != expected:
            failures.append(f'{label}: changed {name}')
    return len(entries)


def check_inventory(entries, roots, label, failures):
    expected = set(entries)
    actual = set()
    for relroot in roots:
        base = ROOT / relroot
        if base.exists():
            actual.update(str(path.relative_to(ROOT)) for path in base.rglob('*')
                          if path.is_file() and '__pycache__' not in path.parts
                          and path.suffix != '.pyc'
                          and str(path.relative_to(ROOT)) not in {
                              'docs/cu66-v69/bundle-manifest.json',
                              'docs/cu66-v70/bundle-manifest.json',
                              'docs/cu66-v71/bundle-manifest.json'})
    if label == 'v69 bundle':
        actual.update(name for name in ('README.md',
                     'docs/gamebub-application-specific-codec-plan.md')
                      if (ROOT / name).is_file())
    missing, extra = sorted(expected - actual), sorted(actual - expected)
    if missing:
        failures.append(f'{label}: missing inventory entries: ' + ', '.join(missing))
    if extra:
        failures.append(f'{label}: extra inventory entries: ' + ', '.join(extra))


def main():
    try:
        pins = json.loads(PINS.read_text(encoding='utf-8'))
        if pins.get('schema') != 'cu66-v72-frozen-baseline-v1':
            raise ValueError('unexpected v72 baseline schema')
        if pins.get('baseline_commit') != EXPECTED_COMMIT:
            raise ValueError('unexpected pinned baseline commit')
        failures = []
        ancestor = subprocess.run(['git', 'merge-base', '--is-ancestor',
                                   EXPECTED_COMMIT, 'HEAD'], cwd=ROOT,
                                  text=True, capture_output=True, check=False)
        if ancestor.returncode:
            failures.append('frozen v71 baseline is not an ancestor of checkout HEAD: ' +
                            EXPECTED_COMMIT)
        counts = {}
        for bundle in pins['bundles']:
            manifest = json.loads((ROOT / bundle['manifest']).read_text(encoding='utf-8'))
            actual = manifest.get('files_sha256')
            if actual != bundle['files_sha256']:
                failures.append(f"{bundle['name']} bundle manifest differs from v72 frozen copy")
            counts[bundle['name']] = check_files(bundle['files_sha256'],
                                                  bundle['name'] + ' bundle', failures)
            roots = {'v69': ('docs/cu66-v69', 'scripts/cu66-v69',
                             'experiments/cu66-native-v69', 'fpga/experiments/cu66-v69'),
                     'v70': ('docs/cu66-v70', 'scripts/cu66-v70',
                             'fpga/experiments/cu66-v70'),
                     'v71': ('docs/cu66-v71', 'scripts/cu66-v71',
                             'fpga/experiments/cu66-v71')}[bundle['name']]
            check_inventory(bundle['files_sha256'], roots, bundle['name'] + ' bundle', failures)
            if bundle['name'] == 'v69':
                for root_file in ('README.md', 'docs/gamebub-application-specific-codec-plan.md'):
                    if root_file not in bundle['files_sha256']:
                        failures.append('v69 bundle: expected root pin absent: ' + root_file)
        counts['v71_source_pins'] = check_files(pins['v71_source_pins'],
                                                'v71 reviewed-source pin', failures)
        # Keep prior audited authorities in the chain; these verifiers are read-only.
        for script in ('scripts/cu66-v70/verify_baseline.py',
                       'scripts/cu66-v71/verify_baseline.py'):
            prior = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT,
                                   text=True, capture_output=True, check=False)
            if prior.returncode:
                failures.append(f'{script} failed: ' +
                                (prior.stdout + prior.stderr).strip().replace('\n', ' | '))
        if failures:
            print('V72_BASELINE_INTEGRITY_FAIL')
            for failure in failures:
                print('  ' + failure)
            return 1
        print('V72_BASELINE_INTEGRITY_PASS '
              f"v69_bundle={counts['v69']} files; v70_bundle={counts['v70']} files; "
              f"v71_bundle={counts['v71']} files; "
              f"v71_source_pins={counts['v71_source_pins']} files; "
              f'baseline={EXPECTED_COMMIT} is ancestor of HEAD; integrity only, not functional/cadence evidence')
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f'V72_BASELINE_INTEGRITY_ERROR {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
