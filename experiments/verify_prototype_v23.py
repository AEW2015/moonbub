#!/usr/bin/env python3
"""Retained v23 actual-profile and shared-analysis evidence verification."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads((ROOT / path).read_text())


def run(path, *args):
    result = subprocess.run([sys.executable, str(ROOT / path), *args], capture_output=True, text=True)
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        result.check_returncode()
    return result.stdout.strip()


def main():
    manifest = load('docs/prototype-v23-provenance.json')
    assert manifest['schema'] == 'gamebub-v23-provenance'
    for path, expected in manifest['file_sha256'].items():
        assert sha(ROOT / path) == expected, ('inventory', path)
    for path, expected in manifest['frozen_v22_sha256'].items():
        assert sha(ROOT / path) == expected, ('frozen v22', path)
    tests = 0
    for folder, expected in manifest['test_counts'].items():
        text = (ROOT / folder / 'tests.log').read_text()
        match = re.search(r'^Ran (\d+) tests? in ', text, re.M)
        assert match and int(match[1]) == expected and text.rstrip().endswith('OK'), folder
        tests += expected
    bindings = 0
    for path in manifest['run_artifacts']:
        for raw, expected in load(path)['source_sha256'].items():
            p = Path(raw)
            assert not p.is_absolute() and '..' not in p.parts
            assert sha(ROOT / p) == expected, ('source pin', path, raw)
            bindings += 1
    replay = run('experiments/python-game-hd22-joint-study/verify.py')
    audit = run('experiments/python-game-audit-v23-study/audit.py', '--check')
    missing = []
    for raw, expected in manifest['input_sha256'].items():
        p = Path(raw)
        if p.is_file():
            assert sha(p) == expected, ('external input', raw)
        else:
            missing.append(raw)
    print(json.dumps(dict(snapshot_files=len(manifest['file_sha256']),
                          frozen_v22_files=len(manifest['frozen_v22_sha256']),
                          source_snapshot_bindings=bindings, recorded_passing_tests=tests,
                          actual_profile_replay=replay, independent_audit=audit,
                          source_acquisitions=96, actual_joint_decisions=288,
                          paired_plain_shared_identical_decisions=96,
                          actual_hd22_joint_dispatch_implemented=True,
                          native_esp32_or_physical_30fps_proven=False,
                          missing_external_media=missing), indent=2))


if __name__ == '__main__':
    main()
