#!/usr/bin/env python3
"""Verify the portable V67 temporal/filter/transport evidence bundle."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def local(raw):
    path = Path(raw)
    assert not path.is_absolute() and '..' not in path.parts
    resolved = (ROOT / path).resolve()
    assert resolved.is_relative_to(ROOT)
    return resolved


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(local(path).read_text())


def run(spec):
    path = local(spec['path'])
    result = subprocess.run([sys.executable, str(path), *spec['args']],
                            capture_output=True, text=True)
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        result.check_returncode()
    return result.stdout


def main():
    data = load('docs/prototype-v67-provenance.json')
    assert data['schema'] == 'gamebub-v67-provenance'
    for name, digest in data['file_sha256'].items():
        assert sha(local(name)) == digest, ('inventory', name)
    for name, digest in data['frozen_v58_sha256'].items():
        assert sha(local(name)) == digest, ('frozen v58', name)

    tests = pins = 0
    for name, expected in data['passing_test_logs'].items():
        content = local(name).read_text()
        match = re.search(r'^Ran (\d+) tests? in ', content, re.M)
        assert match and int(match[1]) == expected and content.rstrip().endswith('OK'), name
        tests += expected
    for artifact in data['run_artifacts']:
        item = load(artifact)
        for name, digest in item.get('source_sha256', {}).items():
            assert sha(local(name)) == digest, ('producer', artifact, name)
            pins += 1
    evidence = load('docs/figures/prototype-v67/evidence.json')
    for name, digest in evidence['inputs'].items():
        assert sha(local(name)) == digest, ('figure input', name)

    for spec in data['stored_helpers']:
        label = spec['path'] + (' ' + ' '.join(spec['args']) if spec['args'] else '')
        print('Replay ' + label, flush=True)
        run(spec)
    for name, digest in data['file_sha256'].items():
        assert sha(local(name)) == digest, ('post-replay inventory', name)
    print(json.dumps(dict(snapshot_files=len(data['file_sha256']),
                          frozen_v58_files=len(data['frozen_v58_sha256']),
                          passing_tests=tests, source_snapshot_bindings=pins,
                          replayed_helpers=len(data['stored_helpers']),
                          figure_files=len(data['figure_outputs']),
                          future_studies_included=False,
                          physical_30fps_proven=False,
                          target_fit_proven=False), indent=2))


if __name__ == '__main__':
    main()
