#!/usr/bin/env python3
"""Portable V42 HUD parity, provenance and inventory replay."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def path(raw):
    value = Path(raw)
    assert not value.is_absolute() and '..' not in value.parts
    resolved = (ROOT / value).resolve()
    assert resolved.is_relative_to(ROOT)
    return resolved


def sha(value):
    return hashlib.sha256(Path(value).read_bytes()).hexdigest()


def load(name):
    return json.loads(path(name).read_text())


def run(name):
    result = subprocess.run([sys.executable, str(path(name))],
                            capture_output=True, text=True)
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        result.check_returncode()
    return result.stdout.strip()


def main():
    data = load('docs/prototype-v42-provenance.json')
    assert data['schema'] == 'gamebub-v42-provenance'
    for name, digest in data['file_sha256'].items():
        assert sha(path(name)) == digest, ('inventory', name)
    for name, digest in data['frozen_v41_sha256'].items():
        assert sha(path(name)) == digest, ('frozen v41', name)

    tests = pins = 0
    for name, expected in data['passing_test_logs'].items():
        content = path(name).read_text()
        found = re.search(r'^Ran (\d+) tests? in ', content, re.M)
        assert found and int(found[1]) == expected and content.rstrip().endswith('OK'), name
        tests += expected
    for artifact in data['run_artifacts']:
        record = load(artifact)
        for name, digest in record['source_sha256'].items():
            assert sha(path(name)) == digest, ('producer', artifact, name)
            pins += 1

    replay = {name: run(name) for name in data['stored_helpers']}
    for name, digest in data['file_sha256'].items():
        assert sha(path(name)) == digest, ('post-replay inventory', name)
    print(json.dumps(dict(
        snapshot_files=len(data['file_sha256']),
        frozen_v41_files=len(data['frozen_v41_sha256']),
        new_passing_tests=tests,
        source_snapshot_bindings=pins,
        retained_verifiers=replay,
        physical_30fps_proven=False,
        compression_gain_proven=False,
        whole_chain_profile_diagnostic_only=True,
    ), indent=2))


if __name__ == '__main__':
    main()
