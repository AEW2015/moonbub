#!/usr/bin/env python3
"""Bind the exact V97 transport and forwarding handoff inputs."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v97'
MANIFEST = AREA/'bundle-manifest.json'
CHECK = AREA/'packaging-check.json'
BASELINE = 'bd8fcc49c1c6b069432dd1ae93109640359fea8e'
MAX_FILE_BYTES = 95*1024*1024
TEXT_SUFFIXES = {'.py', '.rs', '.cpp', '.hpp', '.sv', '.md', '.json',
                 '.log', '.stderr', '.txt', '.tsv'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def modified(path):
    result = subprocess.run(
        ['git', 'status', '--short', '--', str(path.relative_to(ROOT))],
        cwd=ROOT, capture_output=True, text=True, check=True)
    if result.stdout.strip():
        return True
    # Keep committed V97 additions in a regenerated bundle too. A clean
    # post-commit worktree must not silently drop the optional source files.
    compared = subprocess.run(
        ['git', 'diff', '--name-only', BASELINE, '--', str(path.relative_to(ROOT))],
        cwd=ROOT, capture_output=True, text=True, check=True)
    return bool(compared.stdout.strip())


def files():
    paths = [ROOT/p for p in (
        'docs/gamebub-application-specific-codec-plan.md',
        'docs/gamebub-v91-v110-development-plan.md',
        'docs/literature-review-2026-11-06/README.md',
        'docs/esp32-compact-transport-plan.md', '.gitattributes')]
    for name in (
        'docs/cu66-v97',
        'scripts/cu66-v97',
        'experiments/python-gamebub-v97',
        'fpga/experiments/cu66-v97-forward'):
        base = ROOT/name
        if base.exists():
            paths += [p for p in base.rglob('*') if p.is_file()
                      and '__pycache__' not in p.parts
                      and p not in (MANIFEST, CHECK)]

    # Protocol source and its vectors are individual scope additions. Include
    # only when present and changed from the frozen baseline, as requested.
    optional = (
        'host/moonshine/protocol97.py',
        'firmware/handheld/src/streaming/protocol97.rs',
        'host/moonshine/transport97_sender.py',
        'firmware/handheld/src/streaming/mod.rs')
    for name in optional:
        path = ROOT/name
        if path.is_file() and modified(path):
            paths.append(path)
    return sorted(set(paths))


def main():
    paths = files()
    exceptions = []
    checked = 0
    for path in paths:
        assert path.stat().st_size < MAX_FILE_BYTES, ('oversize artifact', path)
        if path.suffix not in TEXT_SUFFIXES:
            continue
        result = subprocess.run(
            ['git', 'diff', '--no-index', '--check', '--', '/dev/null', str(path)],
            cwd=ROOT, capture_output=True, text=True)
        checked += 1
        assert result.returncode in (0, 1, 2, 3) and not result.stderr, (
            path, result.stderr)
        if not result.stdout and not result.stderr:
            continue
        name = str(path.relative_to(ROOT))
        # Whitespace exceptions are limited to exact source snapshots and raw
        # compiler evidence bound by their attempt receipts.
        if 'sources' in path.parts:
            at = path.parts.index('sources')
            report_path = Path(*path.parts[:at])/'results.json'
            report = json.loads(report_path.read_text())
            source = str(Path(*path.parts[at+1:]))
            assert report['source_sha256'][source] == sha(path), (
                'unbound source snapshot exception', name)
            reason = 'exact source snapshot bound by its attempt receipt'
        elif path.name in ('compiler.log', 'compiler-version.log'):
            report = json.loads(path.with_name('results.json').read_text())
            assert report['artifacts_sha256'][path.name] == sha(path)
            assert 'warning:' not in path.read_text().lower()
            reason = 'exact compiler output bound by its attempt receipt'
        elif path.name == 'vectors.tsv':
            # A final empty hex-payload field is part of the test grammar:
            # truncation/reset/timeout rows intentionally end in a tab.
            pointer = json.loads((AREA/'protocol/index.json').read_text())
            report = json.loads((ROOT/pointer['attempt_json']).read_text())
            assert sha(path) == report['artifacts']['data/vectors.tsv']
            assert all(len(line.split('\t')) == 5 for line in path.read_text().splitlines())
            reason = 'intentional empty final TSV payload field; exact table matches qualified native artifact SHA'
        elif path.name in ('native-tests.log', 'native-compile.log', 'ffi-tests.log',
                           'ffi-test-compile.log', 'ffi-staticlib-compile.log'):
            # Preserve exact raw stdout, including historical failed/warning
            # attempts. Its packaging SHA does not retroactively claim the
            # original receipt hashed the log. Selected current compile logs
            # are checked separately by summarize.py; no source warning is waived.
            report_path = next((path.parent/n for n in ('attempt.json', 'receipt.json')
                                if (path.parent/n).is_file()), None)
            assert report_path is not None and any(x in path.parts for x in ('attempts', 'ffi-attempts'))
            report = json.loads(report_path.read_text())
            assert report.get('commands'), ('raw log without command provenance', name)
            reason = 'raw command output retained byte-for-byte; bound by packaging SHA (including historical failures)'
        else:
            raise AssertionError((name, result.stdout, result.stderr))
        exceptions.append(dict(path=name, sha256=sha(path), reason=reason,
                               diagnostic=result.stdout))

    check = dict(
        schema='cu66-v97-packaging-v1', status='PASS',
        text_files_checked=checked, whitespace_exceptions=exceptions,
        maximum_file_bytes=max(p.stat().st_size for p in paths),
        scope=('Only docs/cu66-v97, scripts/cu66-v97, '
               'experiments/python-gamebub-v97, '
               'fpga/experiments/cu66-v97-forward, the four explicit plan '
               'documents, and present modified V97 protocol/entrypoint files. '
               'No GPIO or physical-hardware claim is made.'),
        baseline_commit=BASELINE)
    CHECK.write_text(json.dumps(check, indent=2)+'\n')
    paths.append(CHECK)
    manifest = dict(
        schema='cu66-v97-bundle-v1', baseline_commit=BASELINE,
        checkpoint=('V97 bounded transport and forwarding evidence; hardware '
                    'and ESP32/Wi-Fi fidelity remain limited to measured scope'),
        files={str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)})
    MANIFEST.write_text(json.dumps(manifest, indent=2)+'\n')
    print('PASS_V97_BUNDLE', len(paths), 'files;', len(exceptions),
          'exact-evidence whitespace exceptions')


if __name__ == '__main__':
    main()
