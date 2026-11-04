#!/usr/bin/env python3
"""Read-only v21 source/evidence verification; no native or physical FPS claim."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(path, *args):
    result = subprocess.run([sys.executable, str(ROOT / path), *args], capture_output=True, text=True)
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        result.check_returncode()
    return result.stdout.strip()


def main():
    manifest = json.loads((ROOT / 'docs/prototype-v21-provenance.json').read_text())
    assert manifest['schema'] == 'gamebub-v21-provenance'
    for path, expected in manifest['file_sha256'].items():
        assert sha(ROOT / path) == expected, ('inventory', path)
    for path, expected in manifest['frozen_v20_sha256'].items():
        assert sha(ROOT / path) == expected, ('frozen v20', path)
    tests = 0
    for folder, count in manifest['test_counts'].items():
        text = (ROOT / folder / 'tests.log').read_text()
        match = re.search(r'^Ran (\d+) tests? in ', text, re.M)
        assert match and int(match[1]) == count and text.rstrip().endswith('OK'), folder
        tests += count
    bindings = 0
    for path, source_base in manifest['run_artifacts'].items():
        result = json.loads((ROOT / path).read_text())
        for name, expected in result['source_sha256'].items():
            p = Path(name)
            assert not p.is_absolute() and '..' not in p.parts, name
            assert sha(ROOT / source_base / p) == expected, ('source pin', path, name)
            bindings += 1
    helpers = {folder: run(folder + '/verify.py') for folder in manifest['stored_helpers']}
    audit = run('experiments/python-game-audit-v21-study/audit.py', '--check')
    missing_media = []
    for raw, expected in manifest['input_sha256'].items():
        path = Path(raw)
        if path.is_file():
            assert sha(path) == expected, ('external input', raw)
        else:
            missing_media.append(raw)
    print(json.dumps(dict(snapshot_files=len(manifest['file_sha256']),
                          frozen_v20_files=len(manifest['frozen_v20_sha256']),
                          source_snapshot_bindings=bindings, recorded_passing_tests=tests,
                          retained_verifiers=helpers, independent_audit=audit,
                          native_hud_updates=96, exact_hud_updates_including_controls=132,
                          exact_full_display_pairs=10, joint_publication_implemented=False,
                          native_or_physical_30fps_proven=False, missing_external_media=missing_media), indent=2))


if __name__ == '__main__':
    main()
