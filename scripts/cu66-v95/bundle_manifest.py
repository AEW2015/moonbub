#!/usr/bin/env python3
"""Bind the exact V95 software handoff, preserving snapshots and raw tool logs."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v95'
MANIFEST = AREA/'bundle-manifest.json'
CHECK = AREA/'packaging-check.json'
BASELINE = '7902df3e56d512f602bcf510bec25350dda124d0'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files():
    paths = [ROOT/p for p in ('docs/gamebub-application-specific-codec-plan.md',
        'docs/gamebub-v91-v110-development-plan.md', 'docs/literature-review-2026-11-06/README.md')]
    for name in ('docs/cu66-v95', 'scripts/cu66-v95', 'experiments/python-gamebub-v95'):
        paths += [p for p in (ROOT/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p not in (MANIFEST, CHECK)]
    return sorted(paths)


def main():
    paths = files()
    exceptions = []
    checked = 0
    for path in paths:
        assert path.stat().st_size < 95*1024*1024, ('oversize artifact', path)
        if path.suffix not in ('.py', '.cpp', '.hpp', '.sv', '.md', '.json', '.log', '.stderr', '.txt'):
            continue
        result = subprocess.run(['git', 'diff', '--no-index', '--check', '--', '/dev/null', str(path)], capture_output=True, text=True)
        checked += 1
        assert result.returncode in (0, 1, 2, 3) and not result.stderr, (path, result.stderr)
        if not result.stdout and not result.stderr:
            continue
        name = str(path.relative_to(ROOT))
        # Exceptions preserve exact qualified source/tool evidence. They never
        # cover editable working sources, new prose, or warning-bearing builds.
        if 'sources' in path.parts:
            at = path.parts.index('sources')
            report_path = Path(*path.parts[:at])/'results.json'
            report = json.loads(report_path.read_text())
            source = str(Path(*path.parts[at+1:]))
            assert report['source_sha256'][source] == sha(path), ('unbound snapshot exception', name)
            reason = 'exact source snapshot bound by its attempt receipt'
        elif path.name in ('compiler.log', 'compiler-version.log'):
            report = json.loads(path.with_name('results.json').read_text())
            assert report['artifacts_sha256'][path.name] == sha(path)
            assert 'warning:' not in path.read_text().lower()
            reason = 'exact compiler version stdout; trailing blank line retained'
        else:
            raise AssertionError((name, result.stdout, result.stderr))
        exceptions.append(dict(path=name, sha256=sha(path), reason=reason, diagnostic=result.stdout))
    check = dict(schema='cu66-v95-packaging-v1', status='PASS', text_files_checked=checked,
                 whitespace_exceptions=exceptions, maximum_file_bytes=max(p.stat().st_size for p in paths),
                 scope='Only docs/cu66-v95, scripts/cu66-v95, experiments/python-gamebub-v95 and the three explicit existing plan documents; FPGA areas excluded.',
                 baseline_commit=BASELINE)
    CHECK.write_text(json.dumps(check, indent=2)+'\n')
    paths.append(CHECK)
    manifest = dict(schema='cu66-v95-bundle-v1', baseline_commit=BASELINE,
                    checkpoint='V95 exact-palette software qualified; no rate win, promotion or hardware milestone',
                    files={str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)})
    MANIFEST.write_text(json.dumps(manifest, indent=2)+'\n')
    print('PASS_V95_BUNDLE', len(paths), 'files;', len(exceptions), 'exact-evidence whitespace exceptions')


if __name__ == '__main__':
    main()
