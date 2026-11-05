#!/usr/bin/env python3
"""Portable V43–V46 evidence and replay verifier."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def local(raw):
    value = Path(raw)
    assert not value.is_absolute() and '..' not in value.parts
    resolved = (ROOT / value).resolve()
    assert resolved.is_relative_to(ROOT)
    return resolved


def sha(value):
    return hashlib.sha256(Path(value).read_bytes()).hexdigest()


def load(name):
    return json.loads(local(name).read_text())


def run(name):
    result = subprocess.run([sys.executable, str(local(name))],
                            capture_output=True, text=True)
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        result.check_returncode()
    return result.stdout.strip()


def main():
    data = load('docs/prototype-v46-provenance.json')
    assert data['schema'] == 'gamebub-v46-provenance'
    for name, digest in data['file_sha256'].items():
        assert sha(local(name)) == digest, ('inventory', name)
    for name, digest in data['frozen_v42_sha256'].items():
        assert sha(local(name)) == digest, ('frozen v42', name)

    tests = pins = 0
    for name, expected in data['passing_test_logs'].items():
        content = local(name).read_text()
        found = re.search(r'^Ran (\d+) tests? in ', content, re.M)
        assert found and int(found[1]) == expected and content.rstrip().endswith('OK'), name
        tests += expected
    assert tests == 28
    for artifact in data['run_artifacts']:
        for name, digest in load(artifact)['source_sha256'].items():
            assert sha(local(name)) == digest, ('producer', artifact, name)
            pins += 1

    replay = {}
    for name in data['stored_helpers']:
        print('Replay ' + name, flush=True)
        replay[name] = run(name)
    for name, digest in data['file_sha256'].items():
        assert sha(local(name)) == digest, ('post-replay inventory', name)

    v43 = json.loads(replay[data['stored_helpers'][0]].splitlines()[-1])
    v46 = json.loads(replay[data['stored_helpers'][-1]].splitlines()[-1])
    assert v43['exact_causal_frames'] == 577
    assert v46['causal_complete_frames'] == 24
    print(json.dumps(dict(
        snapshot_files=len(data['file_sha256']),
        frozen_v42_files=len(data['frozen_v42_sha256']),
        passing_tests=tests,
        source_snapshot_bindings=pins,
        retained_verifiers=replay,
        v47_v48_included=False,
        physical_30fps_proven=False,
        hardware_fit_proven=False,
    ), indent=2))


if __name__ == '__main__':
    main()
