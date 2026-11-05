#!/usr/bin/env python3
"""Freeze the exact HUD host optimization and its evidence inventory."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUTABLE = ('README.md', 'docs/gamebub-application-specific-codec-plan.md')
STUDY = ROOT / 'experiments/python-game-hud-fast-v42-study'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def passing(path):
    content = path.read_text()
    match = re.search(r'^Ran (\d+) tests? in ', content, re.M)
    assert match and content.rstrip().endswith('OK'), path
    return int(match[1])


def main():
    parent = json.loads((ROOT / 'docs/prototype-v41-provenance.json').read_text())
    frozen = {path: digest for path, digest in parent['file_sha256'].items()
              if path not in MUTABLE}
    for path, digest in frozen.items():
        assert sha(ROOT / path) == digest, ('frozen v41', path)

    paths = {ROOT / path for path in parent['file_sha256']}
    names = (
        'docs/prototype-v41-provenance.json',
        'docs/custom-codec-prototype-v42-2026-11-05.md',
        'docs/v42-evidence-audit.md',
        'experiments/export_prototype_v42.py',
        'experiments/verify_prototype_v42.py',
    )
    paths.update(ROOT / path for path in names)
    paths.update(path for path in STUDY.rglob('*')
                 if path.is_file() and '__pycache__' not in path.parts
                 and path.suffix != '.pyc')

    runs = [
        'experiments/python-game-hud-fast-v42-study/results.json',
        'experiments/python-game-hud-fast-v42-study/whole-chain-profile.json',
    ]
    tests = {}
    for name in ('tests.log', 'tests_verify.log'):
        path = STUDY / name
        tests[path.relative_to(ROOT).as_posix()] = passing(path)

    for name in runs:
        record = json.loads((ROOT / name).read_text())
        for path, digest in record['source_sha256'].items():
            source = Path(path)
            assert not source.is_absolute() and '..' not in source.parts
            assert sha(ROOT / source) == digest, ('producer', name, path)
            paths.add(ROOT / source)

    manifest = dict(
        schema='gamebub-v42-provenance',
        parent_commit='93c369ca23ccb284a5064218e143895cac494509',
        file_sha256={path.relative_to(ROOT).as_posix(): sha(path)
                     for path in sorted(paths)},
        frozen_v41_sha256=frozen,
        passing_test_logs=tests,
        run_artifacts=runs,
        stored_helpers=['experiments/python-game-hud-fast-v42-study/verify.py'],
        limitations=[
            'Paired result covers only HX32 then HX33; HU25 generation/search/selection excluded.',
            'Whole-chain cProfile diagnostic has pstats alias-key aggregation mismatch and is qualitative.',
            'No compression gain, hardware fit, native optimality, or physical 30fps claim.',
            'HUD byte work is shared by native and custom hybrid paths.',
        ],
    )
    output = ROOT / 'docs/prototype-v42-provenance.json'
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(files=len(paths), frozen_v41_files=len(frozen),
                          new_passing_tests=sum(tests.values()),
                          source_snapshot_bindings=sum(
                              len(json.loads((ROOT / name).read_text())['source_sha256'])
                              for name in runs))))


if __name__ == '__main__':
    main()
