#!/usr/bin/env python3
"""Verify the portable V68 zero-motion predictor evidence bundle."""
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


def main():
    data = json.loads(local('docs/prototype-v68-provenance.json').read_text())
    assert data['schema'] == 'gamebub-v68-provenance'
    assert sha(local(data['parent_manifest'])) == data['parent_manifest_sha256']
    for name, digest in data['file_sha256'].items():
        assert sha(local(name)) == digest, ('inventory', name)
    for name, digest in data['frozen_v67_sha256'].items():
        assert sha(local(name)) == digest, ('frozen v67', name)

    tests = pins = 0
    for name, expected in data['passing_test_logs'].items():
        content = local(name).read_text()
        match = re.search(r'^Ran (\d+) tests? in ', content, re.M)
        assert match and int(match[1]) == expected and content.rstrip().endswith('OK'), name
        tests += expected
    for artifact in data['run_artifacts']:
        item = json.loads(local(artifact).read_text())
        for name, digest in item.get('source_sha256', {}).items():
            assert sha(local(name)) == digest, ('producer', artifact, name)
            pins += 1

    for spec in data['stored_helpers']:
        path = local(spec['path'])
        label = spec['path'] + (' ' + ' '.join(spec['args']) if spec['args'] else '')
        print('Replay ' + label, flush=True)
        result = subprocess.run([sys.executable, str(path), *spec['args']],
                                capture_output=True, text=True)
        if result.returncode:
            sys.stderr.write(result.stdout + result.stderr)
            result.check_returncode()
    for name, digest in data['file_sha256'].items():
        assert sha(local(name)) == digest, ('post-replay inventory', name)
    print(json.dumps(dict(snapshot_files=len(data['file_sha256']),
                          frozen_v67_files=len(data['frozen_v67_sha256']),
                          passing_tests=tests, source_snapshot_bindings=pins,
                          replayed_helpers=len(data['stored_helpers']),
                          stage_only=True, physical_30fps_proven=False,
                          target_fit_proven=False), indent=2))


if __name__ == '__main__':
    main()
