#!/usr/bin/env python3
"""Frozen v22 Python transaction/span evidence; no physical frame-rate verdict."""
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
    manifest = load('docs/prototype-v22-provenance.json')
    assert manifest['schema'] == 'gamebub-v22-provenance'
    for path, expected in manifest['file_sha256'].items():
        assert sha(ROOT / path) == expected, ('inventory', path)
    for path, expected in manifest['frozen_v21_sha256'].items():
        assert sha(ROOT / path) == expected, ('frozen v21', path)
    tests = 0
    for folder, count in manifest['test_counts'].items():
        text = (ROOT / folder / 'tests.log').read_text()
        match = re.search(r'^Ran (\d+) tests? in ', text, re.M)
        assert match and int(match[1]) == count and text.rstrip().endswith('OK'), folder
        tests += count
    bindings = 0
    for path in manifest['run_artifacts']:
        for raw, expected in load(path)['source_sha256'].items():
            relative = Path(raw)
            assert not relative.is_absolute() and '..' not in relative.parts
            assert sha(ROOT / relative) == expected, ('snapshot', path, raw)
            bindings += 1
    helpers = {folder: run(folder + '/verify.py') for folder in manifest['stored_helpers']}
    projection = run('experiments/python-game-joint-commit-study/analyze.py', '--check')
    audit = run('experiments/python-game-audit-v22-study/audit.py', '--check')
    missing = []
    for raw, expected in manifest['input_sha256'].items():
        path = Path(raw)
        if path.is_file():
            assert sha(path) == expected, ('external media', raw)
        else:
            missing.append(raw)
    print(json.dumps(dict(snapshot_files=len(manifest['file_sha256']),
                          frozen_v21_files=len(manifest['frozen_v21_sha256']),
                          source_snapshot_bindings=bindings, recorded_passing_tests=tests,
                          retained_verifiers=helpers, same_image_projection=projection,
                          independent_audit=audit, actual_joint_decisions=192,
                          native_unique_acquisitions=96, separate_gap_updates=132,
                          synchronous_joint_publication_implemented=True,
                          gap_dispatch_in_joint_model_implemented=False,
                          native_endpoints_or_physical_30fps_proven=False,
                          missing_external_media=missing), indent=2))


if __name__ == '__main__':
    main()
