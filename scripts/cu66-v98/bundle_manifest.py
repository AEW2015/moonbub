#!/usr/bin/env python3
"""Hash the bounded V98 handoff; preserve exact measured logs and snapshots."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v98'
BASELINE = '4234feadaabbad41cb53b47137c124166bf0fab8'
MANIFEST = AREA/'bundle-manifest.json'
CHECK = AREA/'packaging-check.json'
TEXT = {'.py', '.md', '.json', '.log', '.txt', '.csv'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    paths = [ROOT/p for p in ('docs/gamebub-v91-v110-development-plan.md',
             'docs/gamebub-application-specific-codec-plan.md',
             'docs/literature-review-2026-11-06/README.md')]
    for folder in ('docs/cu66-v98', 'scripts/cu66-v98', 'experiments/python-gamebub-v98'):
        paths += [p for p in (ROOT/folder).rglob('*') if p.is_file() and
                  '__pycache__' not in p.parts and p not in (CHECK, MANIFEST)]
    return sorted(set(paths))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        manifest = json.loads(MANIFEST.read_text())
        for name, digest in manifest['files'].items():
            assert sha(ROOT/name) == digest, ('bundle file changed', name)
        assert set(manifest['files']) == {str(p.relative_to(ROOT)) for p in inventory()} | {
            str(CHECK.relative_to(ROOT))}, 'bundle file set changed'
        print('PASS_V98_BUNDLE_FRESH', len(manifest['files']), 'files')
        return
    pointer = json.loads((AREA/'index.json').read_text())
    report_path = ROOT/pointer['attempt_json']
    assert sha(report_path) == pointer['sha256']
    report = json.loads(report_path.read_text())
    assert report['status'] == 'PASS'
    summary = json.loads((AREA/'summary.json').read_text())
    for name, digest in summary['input_sha256'].items():
        assert sha(ROOT/name) == digest
    for name, digest in report['source_sha256'].items():
        assert sha(ROOT/name) == digest, ('measured code changed', name)
    command = json.loads((AREA/'validation/comparison-command.json').read_text())
    assert sha(ROOT/command['stdout_stderr']) == command['stdout_stderr_sha256']
    vpointer = json.loads((AREA/'validation/index.json').read_text())
    test_path = ROOT/vpointer['receipt']
    assert sha(test_path) == vpointer['sha256']
    tests = json.loads(test_path.read_text())
    assert tests['status'] == 'PASS' and tests['returncode'] == 0
    for name, digest in tests['source_sha256'].items():
        assert sha(ROOT/name) == digest, ('tested source changed', name)
    exceptions = []
    paths = inventory()
    for path in paths:
        assert path.stat().st_size < 95*1024*1024, ('oversize artifact', path)
        if path.suffix not in TEXT:
            continue
        result = subprocess.run(['git', 'diff', '--no-index', '--check', '--', '/dev/null', str(path)],
                                cwd=ROOT, capture_output=True, text=True)
        assert not result.stderr
        if not result.stdout:
            continue
        if path.is_relative_to(report_path.parent/'source-snapshot'):
            name = str(path.relative_to(report_path.parent/'source-snapshot'))
            assert report['source_sha256'][name] == sha(path)
            reason = 'exact measured dependency snapshot'
        elif path.is_relative_to(report_path.parent) and path.name in ('syntax.log', 'ffmpeg-version.txt'):
            assert report['artifact_sha256'][str(path.relative_to(report_path.parent))] == sha(path)
            reason = 'exact raw codec inspection/version output'
        elif path == ROOT/command['stdout_stderr']:
            assert sha(path) == command['stdout_stderr_sha256']
            reason = 'exact native encoder stdout/stderr and comparison command output'
        elif path == test_path.parent/'tests.log':
            assert sha(path) == tests['artifacts_sha256']['tests.log']
            reason = 'exact unit-test and native encoder output'
        else:
            raise AssertionError((str(path.relative_to(ROOT)), result.stdout))
        exceptions.append({'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                           'reason': reason, 'diagnostic': result.stdout})
    check = {'schema': 'v98-packaging-check-v1', 'status': 'PASS',
             'baseline_commit': BASELINE, 'payload_file_count': len(paths),
             'maximum_file_bytes': max(p.stat().st_size for p in paths),
             'total_payload_bytes': sum(p.stat().st_size for p in paths),
             'whitespace_exceptions': exceptions,
             'scope': 'V98 comparison sources, retained short common inputs, encoded evidence, docs and three explicit plan documents; no build caches or unrelated RTL.'}
    CHECK.write_text(json.dumps(check, indent=2)+'\n')
    paths.append(CHECK)
    MANIFEST.write_text(json.dumps({'schema': 'v98-bundle-v1', 'baseline_commit': BASELINE,
        'files': {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}}, indent=2)+'\n')
    print('PASS_V98_BUNDLE', len(paths), 'files;', len(exceptions), 'hash-bound raw-evidence whitespace exceptions')


if __name__ == '__main__':
    main()
