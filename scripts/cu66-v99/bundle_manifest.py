#!/usr/bin/env python3
"""Package exact V99 research evidence and keep unrelated work outside scope."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v99'
MANIFEST = AREA/'bundle-manifest.json'
CHECK = AREA/'packaging-check.json'
BASELINE = '35949d6f41366cd5725b433a136fadb1b6ce95f6'
TEXT = {'.py', '.cpp', '.hpp', '.md', '.json', '.jsonl', '.log', '.stderr', '.txt', '.csv', '.tsv'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def files():
    paths = [ROOT/name for name in ('docs/gamebub-v91-v110-development-plan.md',
             'docs/gamebub-application-specific-codec-plan.md',
             'docs/literature-review-2026-11-06/README.md', 'docs/cu66-v98/README.md')]
    for folder in ('docs/cu66-v99', 'scripts/cu66-v99', 'experiments/python-gamebub-v99'):
        paths += [path for path in (ROOT/folder).rglob('*') if path.is_file() and
                  '__pycache__' not in path.parts and path not in (MANIFEST, CHECK)]
    return sorted(set(paths))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        manifest = read(MANIFEST)
        for name, digest in manifest['files'].items():
            assert sha(ROOT/name) == digest, ('bundle file changed', name)
        assert set(manifest['files']) == {str(path.relative_to(ROOT)) for path in files()} | {str(CHECK.relative_to(ROOT))}
        print('PASS_V99_BUNDLE_FRESH', len(manifest['files']), 'files')
        return
    profile, qualified, summary = read(AREA/'profile.json'), read(AREA/'qualification.json'), read(AREA/'summary.json')
    assert qualified['status'] == 'PASS_RC1_SOFTWARE_NATIVE_SCOPE' and summary['status'] == 'PASS_RC1_SOFTWARE_NATIVE_ONLY'
    for item in [qualified['profile'], *qualified['evidence']]:
        assert sha(ROOT/item['path']) == item['sha256'], ('qualification changed', item['path'])
    for item in read(AREA/'inventory.json')['interface_files']:
        assert item['status'] == 'present' and sha(ROOT/item['path']) == item['sha256']
    for name in ('audit-fresh.json', 'audit-native.json', 'audit-cs88.json', 'audit-direct.json'):
        audit = read(AREA/name)
        assert audit['status'].startswith('PASS')
        if 'auditor_sha256' in audit:
            assert sha(ROOT/audit['auditor']) == audit['auditor_sha256']
        else:
            path = audit.get('auditor_source_path', audit.get('auditor'))
            pin = audit.get('auditor_source_sha256', audit.get('auditor_sha256'))
            if path and pin:
                assert sha(ROOT/path) == pin
    # Build exact-byte bindings for raw logs and historical source snapshots.
    bindings = {}
    for report_path in sorted(AREA.rglob('*.json')):
        if report_path in (MANIFEST, CHECK):
            continue
        obj = read(report_path)
        if not isinstance(obj, dict):
            continue
        pins = obj.get('source_sha256', obj.get('sources', {}))
        if isinstance(pins, dict):
            for name, pin in pins.items():
                if not isinstance(pin, str) or len(pin) != 64:
                    continue
                for prefix in ('sources', 'source-snapshot'):
                    path = report_path.parent/prefix/name
                    if path.is_file():
                        assert sha(path) == pin
                        bindings[path.resolve()] = ('exact historical/measured source snapshot', pin)
        for key in ('artifact_sha256', 'artifacts_sha256'):
            for name, pin in obj.get(key, {}).items():
                path = report_path.parent/name
                if path.is_file() and isinstance(pin, str):
                    assert sha(path) == pin, ('artifact changed', path)
                    if path.suffix in ('.log', '.stderr', '.txt'):
                        bindings[path.resolve()] = ('exact raw command/tool output', pin)
    commands = read(AREA/'validation/commands.json')
    for item in commands['commands']:
        assert item['observed_exit_code'] == 0
        path = ROOT/item['stdout_stderr']
        assert sha(path) == item['stdout_stderr_sha256']
        assert sha(ROOT/item['terminal_report']) == item['terminal_report_sha256']
        bindings[path.resolve()] = ('exact root-observed command output', item['stdout_stderr_sha256'])
    vp = read(AREA/'validation/index.json')
    test_path = ROOT/vp['receipt']
    assert sha(test_path) == vp['sha256']
    test = read(test_path)
    assert test['status'] == 'PASS' and test['returncode'] == 0
    for name, digest in test['source_sha256'].items():
        assert sha(ROOT/name) == digest
    paths, exceptions = files(), []
    for path in paths:
        assert path.stat().st_size < 95*1024*1024, ('oversize artifact', path)
        if path.suffix not in TEXT:
            continue
        result = subprocess.run(['git', 'diff', '--no-index', '--check', '--', '/dev/null', str(path)],
                                cwd=ROOT, capture_output=True, text=True)
        assert not result.stderr
        if not result.stdout:
            continue
        assert path.resolve() in bindings, ('unbound whitespace issue', path, result.stdout)
        reason, pin = bindings[path.resolve()]
        assert sha(path) == pin
        exceptions.append({'path': str(path.relative_to(ROOT)), 'sha256': pin,
                           'reason': reason, 'diagnostic': result.stdout})
    report = {'schema': 'v99-packaging-check-v1', 'status': 'PASS', 'baseline_commit': BASELINE,
              'payload_file_count': len(paths), 'total_payload_bytes': sum(path.stat().st_size for path in paths),
              'maximum_file_bytes': max(path.stat().st_size for path in paths),
              'whitespace_exceptions': exceptions,
              'scope': 'V99 source/evidence/docs and four explicit roadmap/follow-up documents; includes superseded and failed attempts, excludes caches, external build binaries and unrelated RTL.'}
    CHECK.write_text(json.dumps(report, indent=2)+'\n')
    paths.append(CHECK)
    MANIFEST.write_text(json.dumps({'schema': 'v99-research-bundle-v1', 'baseline_commit': BASELINE,
        'files': {str(path.relative_to(ROOT)): sha(path) for path in sorted(paths)}}, indent=2)+'\n')
    print('PASS_V99_BUNDLE', len(paths), 'files;', len(exceptions), 'exact-evidence whitespace exceptions')


if __name__ == '__main__':
    main()
