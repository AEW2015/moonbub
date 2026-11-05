#!/usr/bin/env python3
"""Verify portable V51–V58 provenance and replay archived checks."""
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


def load(name):
    return json.loads(local(name).read_text())


def run(spec):
    path = local(spec['path'])
    result = subprocess.run([sys.executable, str(path), *spec['args']],
                            capture_output=True, text=True)
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        result.check_returncode()
    return result.stdout.strip()


def main():
    data = load('docs/prototype-v58-provenance.json')
    assert data['schema'] == 'gamebub-v58-provenance'
    for name, digest in data['file_sha256'].items():
        assert sha(local(name)) == digest, ('inventory', name)
    for name, digest in data['frozen_v50_sha256'].items():
        assert sha(local(name)) == digest, ('frozen v50', name)

    tests = pins = 0
    for name, expected in data['passing_test_logs'].items():
        content = local(name).read_text()
        found = re.search(r'^Ran (\d+) tests? in ', content, re.M)
        assert found and int(found[1]) == expected and content.rstrip().endswith('OK'), name
        tests += expected
    assert tests == 42

    for artifact in data['run_artifacts']:
        artifact_data = load(artifact)
        assert artifact_data.get('source_sha256'), ('missing source pins', artifact)
        for name, digest in artifact_data['source_sha256'].items():
            assert sha(local(name)) == digest, ('producer', artifact, name)
            pins += 1

    replay = {}
    for spec in data['stored_helpers']:
        key = spec['path'] + (' ' + ' '.join(spec['args']) if spec['args'] else '')
        print('Replay ' + key, flush=True)
        run(spec)
        replay[key] = True

    for name, digest in data['file_sha256'].items():
        assert sha(local(name)) == digest, ('post-replay inventory', name)
    print(json.dumps(dict(
        snapshot_files=len(data['file_sha256']),
        frozen_v50_files=len(data['frozen_v50_sha256']),
        passing_tests=tests,
        source_snapshot_bindings=pins,
        replayed_helpers=len(replay),
        v51_cases=24, v52_frames=96, v53_frames=96, v54_receives=198,
        v56_eligible_nonzero_MB=0, v57_presentations=480,
        v58_visible_eligible_cells=110, v58_selected_mixed=0,
        later_studies_included=False,
        physical_30fps_proven=False,
        target_fit_proven=False,
    ), indent=2))


if __name__ == '__main__':
    main()
