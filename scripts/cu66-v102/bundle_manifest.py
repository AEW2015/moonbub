#!/usr/bin/env python3
"""Hash the explicit V102 handoff scope, excluding unrelated experiments/builds."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v102'
MANIFEST = AREA / 'bundle-manifest.json'
CHECK = AREA / 'packaging-check.json'
BASELINE = '6b36a3228804953c50c10db61f620cad5412ecce'
FOLDERS = ('docs/cu66-v102', 'scripts/cu66-v102',
           'experiments/python-gamebub-v102',
           'fpga/experiments/cu66-v102-flow',
           'fpga/experiments/cu66-v102-memory',
           'fpga/experiments/cu66-v102-predicate')
DOCUMENTS = ('docs/gamebub-v91-v110-development-plan.md',
             'docs/gamebub-application-specific-codec-plan.md',
             'docs/literature-review-2026-11-06/README.md')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files():
    found = {ROOT / name for name in DOCUMENTS}
    for folder in FOLDERS:
        found.update(p for p in (ROOT / folder).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts
                     and p.suffix not in ('.pyc', '.pyo')
                     and p not in (MANIFEST, CHECK))
    return sorted(found)


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    paths = files()
    if args.verify:
        pins = read(MANIFEST)['files']
        expected = {str(p.relative_to(ROOT)) for p in paths + [CHECK]}
        assert set(pins) == expected, 'handoff file set changed'
        for name, pin in pins.items():
            assert sha(ROOT / name) == pin, ('handoff file changed', name)
        print('PASS_V102_BUNDLE_FRESH', len(pins), 'files')
        return

    for audit_name in ('source-audit.json', 'native-audit.json'):
        audit = read(AREA / audit_name)
        assert audit['status'] == 'PASS_EVIDENCE', ('independent evidence audit required', audit_name)
        inputs = audit.get('input_hashes', audit.get('input_sha256'))
        assert isinstance(inputs, dict) and inputs, ('audit input bindings missing', audit_name)
        for name, pin in inputs.items():
            assert sha(ROOT / name) == pin, ('audited input changed', name)
    for variant, mode in [('memory', 'fresh'), ('memory', 'canonical'),
                          ('predicate', 'canonical'), ('combined', 'canonical')]:
        assert read(AREA / 'regression' / variant / mode / 'results.json')['status'] == 'PASS'
    raw_artifacts = {}
    for ledger in AREA.rglob('*.json'):
        if ledger in (MANIFEST, CHECK):
            continue
        obj = read(ledger)
        if not isinstance(obj, dict):
            continue
        entries = obj if ledger.name == 'artifacts.json' else obj.get('artifacts', obj.get('artifacts_sha256', obj.get('artifact_sha256', {})))
        if not isinstance(entries, dict):
            continue
        for name, value in entries.items():
            pin = value.get('sha256') if isinstance(value, dict) else value
            candidate = ledger.parent / name
            if not candidate.is_file() and (ledger.parent / 'reports' / name).is_file():
                candidate = ledger.parent / 'reports' / name
            if candidate.is_file() and isinstance(pin, str) and len(pin) == 64:
                assert sha(candidate) == pin, ('retained artifact changed', candidate)
                raw_artifacts[candidate.resolve()] = pin
    exceptions = []
    for path in paths:
        assert path.stat().st_size < 95 * 1024 * 1024, ('oversize artifact', path)
        result = subprocess.run(['git', 'diff', '--no-index', '--check', '--', '/dev/null', str(path)],
                                cwd=ROOT, capture_output=True, text=True)
        assert not result.stderr, result.stderr
        if not result.stdout:
            continue
        # Exact transcripts and source snapshots remain byte-for-byte intact.
        # Do not whitelist current implementation code, scripts or prose.
        snapshot = any(name in path.parts for name in ('sources', 'source-snapshot', 'original-sources', 'snapshot'))
        raw_report = path.resolve() in raw_artifacts and ('reports' in path.parts or path.suffix in ('.txt', '.rpt', '.tsv'))
        exact_diff = False
        if path == AREA / 'memory/candidate.diff':
            change = read(AREA / 'memory/change.json')
            before, after = change['original'], change['candidate']
            assert sha(ROOT / before) == change['original_sha256']
            assert sha(ROOT / after) == change['candidate_sha256']
            expected = ''.join(difflib.unified_diff(
                (ROOT / before).read_text().splitlines(keepends=True),
                (ROOT / after).read_text().splitlines(keepends=True),
                fromfile=before, tofile=after))
            exact_diff = path.read_text() == expected
        assert path.suffix in ('.log', '.stderr') or snapshot or raw_report or exact_diff, ('unqualified whitespace', path, result.stdout)
        exceptions.append({'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                           'reason': ('Verified unified diff; context blank line retains its required prefix' if exact_diff else
                                      'Exact frozen source snapshot' if snapshot else
                                      'Hash-qualified raw tool report' if raw_report else 'Exact retained tool transcript'),
                           'diagnostic': result.stdout})
    report = {'schema': 'v102-packaging-check-v1', 'status': 'PASS',
              'baseline_commit': BASELINE, 'payload_file_count': len(paths),
              'total_payload_bytes': sum(p.stat().st_size for p in paths),
              'maximum_file_bytes': max(p.stat().st_size for p in paths),
              'whitespace_exceptions': exceptions,
              'scope': {'folders': FOLDERS, 'documents': DOCUMENTS},
              'excluded': ['unrelated marker-recovery experiment', 'external builds/binaries/checkpoints',
                           'Python caches', 'other worktrees and firmware']}
    CHECK.write_text(json.dumps(report, indent=2) + '\n')
    paths.append(CHECK)
    MANIFEST.write_text(json.dumps({'schema': 'v102-partial-baseline-bundle-v1',
        'baseline_commit': BASELINE,
        'physical_qualification': 'Native variant synthesis/implementation measured; see final native-audit phase gates. Hardware/full-system goals remain OPEN.',
        'files': {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}}, indent=2) + '\n')
    print('PASS_V102_BUNDLE', len(paths), 'files;', len(exceptions), 'exact-evidence whitespace exceptions')


if __name__ == '__main__':
    main()
