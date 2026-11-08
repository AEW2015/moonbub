#!/usr/bin/env python3
"""Hash the explicit V106 handoff scope, excluding unrelated experiments/builds."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v106'
MANIFEST = AREA / 'bundle-manifest.json'
CHECK = AREA / 'packaging-check.json'
BASELINE = 'eececf35da97c9b14230d464ecde7576cb7840db'
FOLDERS = ('docs/cu66-v106', 'scripts/cu66-v106',
           'experiments/python-gamebub-v106',
           'fpga/experiments/cu66-v106-flow',
           'fpga/experiments/cu66-v106-math',
           'fpga/experiments/cu66-v106-locality',
           'fpga/experiments/cu66-v106-composed',
           'fpga/experiments/cu66-v106-plan',
           'fpga/experiments/cu66-v106-context',
           'fpga/experiments/cu66-v106-rice',
           'fpga/experiments/cu66-v106-prefix',
           'fpga/experiments/cu66-v106-telemetry',
           'fpga/experiments/cu66-v106-suffix',
           'fpga/experiments/cu66-v106-idct',
           'fpga/experiments/cu66-v106-producer-cache',
           'fpga/experiments/cu66-v106-suffix24',
           'fpga/experiments/cu66-v106-idct-area',
           'fpga/experiments/cu66-v106-ingress',
           'fpga/experiments/cu66-v106-scratch',
           'fpga/experiments/cu66-v106-postroute')
DOCUMENTS = ('docs/gamebub-v91-v110-development-plan.md',
             'docs/gamebub-application-specific-codec-plan.md',
             'docs/literature-review-2026-11-06/README.md')
# These exact already-simulated production files retain the indentation left
# by the frozen write-removal recipe. Do not change tested bytes for formatting.
FROZEN_CANDIDATE_BLANK = {
    'fpga/experiments/cu66-v106-locality/cu66_inverse_stream_v91j.sv': 167,
    'fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv': 1016,
}
FROZEN_WRAPPER_EOF = {
    'fpga/experiments/cu66-v106-ingress/packet_original.sv': 174,
    'fpga/experiments/cu66-v106-ingress/packet_candidate.sv': 174,
}


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


def audited_sha(name):
    if name.startswith('git/'):
        _, revision, path = name.split('/', 2)
        assert revision == BASELINE, ('unexpected virtual Git input', name)
        data = subprocess.check_output(['git', 'show', revision + ':' + path], cwd=ROOT)
        return hashlib.sha256(data).hexdigest()
    return sha(ROOT / name)




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
        print('PASS_V106_BUNDLE_FRESH', len(pins), 'files')
        return

    for audit_name in ('source-audit.json', 'native-audit.json'):
        audit = read(AREA / audit_name)
        assert audit['status'] == 'PASS_EVIDENCE', ('independent evidence audit required', audit_name)
        inputs = audit.get('input_hashes', audit.get('input_sha256'))
        assert isinstance(inputs, dict) and inputs, ('audit input bindings missing', audit_name)
        for name, pin in inputs.items():
            assert audited_sha(name) == pin, ('audited input changed', name)
    from campaign import LANES
    for variant, mode in LANES:
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
        # Current code/prose have no blanket whitespace exemption.
        snapshot = any(name in path.parts for name in ('sources', 'source-snapshot', 'original-sources', 'snapshot'))
        raw_report = path.resolve() in raw_artifacts and ('reports' in path.parts or path.suffix in ('.txt', '.rpt', '.tsv'))
        frozen_probe_input = (path.resolve() in raw_artifacts and 'attempts' in path.parts
                              and path.suffix == '.sv')
        name = str(path.relative_to(ROOT))
        line = FROZEN_CANDIDATE_BLANK.get(name)
        frozen_candidate = False
        if line is not None:
            source_audit = read(AREA / 'source-audit.json')
            bindings = source_audit.get('input_hashes', source_audit.get('input_sha256', {}))
            frozen_candidate = (bindings.get(name) == sha(path)
                and result.stdout.splitlines() == [str(path) + ':' + str(line) + ': trailing whitespace.', '+' + ' ' * 20]
                and path.read_text().splitlines()[line - 1] == ' ' * 20)
        frozen_wrapper_eof = False
        line = FROZEN_WRAPPER_EOF.get(name)
        if line is not None:
            source_audit = read(AREA / 'source-audit.json')
            bindings = source_audit.get('input_hashes', source_audit.get('input_sha256', {}))
            frozen_wrapper_eof = (bindings.get(name) == sha(path)
                and result.stdout.splitlines() == [str(path) + ':' + str(line) + ': new blank line at EOF.']
                and path.read_bytes().endswith(b'endmodule\n\n')
                and len(path.read_text().splitlines()) == line)
        exact_diff = False
        assert path.suffix in ('.log', '.stderr') or snapshot or raw_report or exact_diff or frozen_probe_input or frozen_candidate or frozen_wrapper_eof, ('unqualified whitespace', path, result.stdout)
        exceptions.append({'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                           'reason': ('Verified unified diff; context blank line retains its required prefix' if exact_diff else
                                      'Exact audit-bound frozen candidate; one retained 20-space blank recipe line' if frozen_candidate else
                                      'Exact audit-bound frozen verification adapter; one retained final blank line' if frozen_wrapper_eof else
                                      'Hash-qualified retained probe input' if frozen_probe_input else
                                      'Exact frozen source snapshot' if snapshot else
                                      'Hash-qualified raw tool report' if raw_report else 'Exact retained tool transcript'),
                           'diagnostic': result.stdout})
    report = {'schema': 'v106-packaging-check-v1', 'status': 'PASS',
              'baseline_commit': BASELINE, 'payload_file_count': len(paths),
              'total_payload_bytes': sum(p.stat().st_size for p in paths),
              'maximum_file_bytes': max(p.stat().st_size for p in paths),
              'whitespace_exceptions': exceptions,
              'scope': {'folders': FOLDERS, 'documents': DOCUMENTS},
              'excluded': ['unrelated marker-recovery experiment', 'external builds/binaries/checkpoints',
                           'Python caches', 'other worktrees and firmware']}
    CHECK.write_text(json.dumps(report, indent=2) + '\n')
    paths.append(CHECK)
    MANIFEST.write_text(json.dumps({'schema': 'v106-partial-baseline-bundle-v1',
        'baseline_commit': BASELINE,
        'physical_qualification': 'Native variant synthesis/implementation measured; see final native-audit phase gates. Hardware/full-system goals remain OPEN.',
        'files': {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}}, indent=2) + '\n')
    print('PASS_V106_BUNDLE', len(paths), 'files;', len(exceptions), 'exact-evidence whitespace exceptions')


if __name__ == '__main__':
    main()
