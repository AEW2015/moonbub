#!/usr/bin/env python3
"""Bind the exact V96 software inventory and addressed-materialization handoff."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v96'
MANIFEST = AREA/'bundle-manifest.json'
CHECK = AREA/'packaging-check.json'
BASELINE = 'd856e5fa909bc308d53debc1aeabb5bca8230fa9'
MAX_FILE_BYTES = 95*1024*1024


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files():
    paths = [ROOT/p for p in (
        'docs/gamebub-application-specific-codec-plan.md',
        'docs/gamebub-v91-v110-development-plan.md',
        'docs/literature-review-2026-11-06/README.md')]
    for name in (
        'docs/cu66-v96',
        'scripts/cu66-v96',
        'experiments/python-gamebub-v96',
        'fpga/experiments/cu66-v96-materialize'):
        base = ROOT/name
        if base.exists():
            paths += [p for p in base.rglob('*') if p.is_file()
                      and '__pycache__' not in p.parts
                      and p not in (MANIFEST, CHECK)]
    return sorted(set(paths))


def main():
    paths = files()
    exceptions = []
    checked = 0
    for path in paths:
        assert path.stat().st_size < MAX_FILE_BYTES, ('oversize artifact', path)
        if path.suffix not in ('.py', '.cpp', '.hpp', '.sv', '.md', '.json',
                               '.log', '.stderr', '.txt'):
            continue
        result = subprocess.run(
            ['git', 'diff', '--no-index', '--check', '--', '/dev/null', str(path)],
            capture_output=True, text=True)
        checked += 1
        assert result.returncode in (0, 1, 2, 3) and not result.stderr, (
            path, result.stderr)
        if not result.stdout and not result.stderr:
            continue
        name = str(path.relative_to(ROOT))
        # Whitespace exceptions are limited to exact, receipt-bound snapshots
        # of qualified sources or raw compiler evidence. Editable V96 sources,
        # prose, and warning-bearing compiler output remain fatal.
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
        else:
            raise AssertionError((name, result.stdout, result.stderr))
        exceptions.append(dict(path=name, sha256=sha(path), reason=reason,
                               diagnostic=result.stdout))
    check = dict(
        schema='cu66-v96-packaging-v1', status='PASS',
        text_files_checked=checked, whitespace_exceptions=exceptions,
        maximum_file_bytes=max(p.stat().st_size for p in paths),
        scope=('Only docs/cu66-v96, scripts/cu66-v96, '
               'experiments/python-gamebub-v96, '
               'fpga/experiments/cu66-v96-materialize and the three explicit '
               'existing plan documents; other FPGA areas excluded.'),
        baseline_commit=BASELINE)
    CHECK.write_text(json.dumps(check, indent=2)+'\n')
    paths.append(CHECK)
    manifest = dict(
        schema='cu66-v96-bundle-v1', baseline_commit=BASELINE,
        checkpoint=('V96 software inventory and standalone addressed '
                    'materialization checkpoint; full path and hardware open'),
        files={str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)})
    MANIFEST.write_text(json.dumps(manifest, indent=2)+'\n')
    print('PASS_V96_BUNDLE', len(paths), 'files;', len(exceptions),
          'exact-evidence whitespace exceptions')


if __name__ == '__main__':
    main()
