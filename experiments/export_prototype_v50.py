#!/usr/bin/env python3
"""Freeze V47–V50 motion, receiver, and tile-schedule evidence."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUTABLE = ('README.md', 'docs/gamebub-application-specific-codec-plan.md')
STUDIES = (
    'python-game-motion-v47-study',
    'python-game-stream-rx-v48-study',
    'python-game-tile-schedule-v49-study',
    'python-game-guarded-motion-v50-study',
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def passing(path):
    content = path.read_text()
    match = re.search(r'^Ran (\d+) tests? in ', content, re.M)
    assert match and content.rstrip().endswith('OK'), path
    return int(match[1])


def main():
    parent = json.loads((ROOT / 'docs/prototype-v46-provenance.json').read_text())
    frozen = {name: digest for name, digest in parent['file_sha256'].items()
              if name not in MUTABLE}
    for name, digest in frozen.items():
        assert sha(ROOT / name) == digest, ('frozen v46', name)

    paths = {ROOT / name for name in parent['file_sha256']}
    paths.update(ROOT / name for name in (
        'docs/prototype-v46-provenance.json',
        'docs/v48-v49-evidence-audit.md',
        'docs/custom-codec-prototype-v50-2026-11-05.md',
        'experiments/export_prototype_v50.py',
        'experiments/verify_prototype_v50.py',
    ))
    for slug in STUDIES:
        folder = ROOT / 'experiments' / slug
        paths.update(path for path in folder.rglob('*')
                     if path.is_file() and '__pycache__' not in path.parts
                     and path.suffix != '.pyc')

    artifacts = [
        'experiments/python-game-motion-v47-study/results.json',
        'experiments/python-game-stream-rx-v48-study/results.json',
        'experiments/python-game-stream-rx-v48-study/memory-probe.json',
        'experiments/python-game-tile-schedule-v49-study/results.json',
        'experiments/python-game-tile-schedule-v49-study/schedule.json',
        'experiments/python-game-guarded-motion-v50-study/results.json',
    ]
    test_logs = (
        'experiments/python-game-motion-v47-study/tests.log',
        'experiments/python-game-motion-v47-study/tests_verify.log',
        'experiments/python-game-stream-rx-v48-study/tests.log',
        'experiments/python-game-stream-rx-v48-study/tests_verify.log',
        'experiments/python-game-tile-schedule-v49-study/tests.log',
        'experiments/python-game-tile-schedule-v49-study/tests_schedule.log',
        'experiments/python-game-guarded-motion-v50-study/tests.log',
        'experiments/python-game-guarded-motion-v50-study/tests_verify.log',
    )
    tests = {name: passing(ROOT / name) for name in test_logs}
    assert sum(tests.values()) == 33

    for artifact in artifacts:
        result = json.loads((ROOT / artifact).read_text())
        for name, digest in result['source_sha256'].items():
            relative = Path(name)
            assert not relative.is_absolute() and '..' not in relative.parts
            assert sha(ROOT / relative) == digest, ('producer', artifact, name)
            paths.add(ROOT / relative)

    stored_helpers = [
        dict(path='experiments/python-game-motion-v47-study/verify.py', args=[]),
        dict(path='experiments/python-game-stream-rx-v48-study/verify.py', args=[]),
        dict(path='experiments/python-game-tile-schedule-v49-study/verify.py', args=[]),
        dict(path='experiments/python-game-tile-schedule-v49-study/schedule.py', args=['--check']),
        dict(path='experiments/python-game-guarded-motion-v50-study/verify.py', args=[]),
    ]
    data = dict(
        schema='gamebub-v50-provenance',
        parent_commit='709c2bf9dfaca6af646d8a954d99b81367dedffd',
        file_sha256={path.relative_to(ROOT).as_posix(): sha(path)
                     for path in sorted(paths)},
        frozen_v46_sha256=frozen,
        passing_test_logs=tests,
        run_artifacts=artifacts,
        stored_helpers=stored_helpers,
        limitations=[
            'V47 global-grid search loses on four fresh prefixes; V50 same-reference guard admits zero grids on 96 frames.',
            'V48 tracemalloc reports call increments, not RSS or target memory; Python stream receiver is slower.',
            'V49 schedule is assumed component work demand, not RTL cycles, routed clock, or end-to-end timing.',
            'No physical 30fps, FPGA/ESP32 fit, or HEVC/AV1 superiority is proven.',
            'V51+ studies are not included.',
        ],
    )
    (ROOT / 'docs/prototype-v50-provenance.json').write_text(
        json.dumps(data, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(files=len(paths), frozen_v46_files=len(frozen),
                          passing_tests=sum(tests.values()),
                          source_snapshot_bindings=sum(
                              len(json.loads((ROOT / name).read_text())['source_sha256'])
                              for name in artifacts))))


if __name__ == '__main__':
    main()
