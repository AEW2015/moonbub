#!/usr/bin/env python3
"""Portable V47–V50 motion, stream and schedule evidence verifier."""
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


def last_json(output):
    return json.loads(output.splitlines()[-1])


def main():
    data = load('docs/prototype-v50-provenance.json')
    assert data['schema'] == 'gamebub-v50-provenance'
    for name, digest in data['file_sha256'].items():
        assert sha(local(name)) == digest, ('inventory', name)
    for name, digest in data['frozen_v46_sha256'].items():
        assert sha(local(name)) == digest, ('frozen v46', name)

    tests = pins = 0
    for name, expected in data['passing_test_logs'].items():
        content = local(name).read_text()
        found = re.search(r'^Ran (\d+) tests? in ', content, re.M)
        assert found and int(found[1]) == expected and content.rstrip().endswith('OK'), name
        tests += expected
    assert tests == 33

    for artifact in data['run_artifacts']:
        for name, digest in load(artifact)['source_sha256'].items():
            assert sha(local(name)) == digest, ('producer', artifact, name)
            pins += 1

    replay = {}
    for spec in data['stored_helpers']:
        key = spec['path'] + (' ' + ' '.join(spec['args']) if spec['args'] else '')
        print('Replay ' + key, flush=True)
        replay[key] = run(spec)

    summaries = [last_json(replay[spec['path'] + (' ' + ' '.join(spec['args']) if spec['args'] else '')])
                 for spec in data['stored_helpers'] if spec['path'].endswith('verify.py')]
    assert summaries[0]['accepted_causal_frames'] == 192
    assert summaries[1]['causal_frames'] == 577
    assert summaries[2]['frames'] == 96 and summaries[2]['tiles'] == 777600
    assert summaries[3]['accepted_selected_frames'] == 96 and summaries[3]['selected_grid_frames'] == 0

    for name, digest in data['file_sha256'].items():
        assert sha(local(name)) == digest, ('post-replay inventory', name)
    print(json.dumps(dict(
        snapshot_files=len(data['file_sha256']),
        frozen_v46_files=len(data['frozen_v46_sha256']),
        passing_tests=tests,
        source_snapshot_bindings=pins,
        retained_verifiers=replay,
        later_studies_included=False,
        physical_30fps_proven=False,
        target_fit_proven=False,
    ), indent=2))


if __name__ == '__main__':
    main()
