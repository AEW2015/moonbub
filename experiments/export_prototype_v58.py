#!/usr/bin/env python3
"""Freeze V51–V58 recovery, scanout, motion, and error evidence."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUTABLE = ('README.md', 'docs/gamebub-application-specific-codec-plan.md')
STUDIES = (
    'python-game-fault-recovery-v51-study',
    'python-game-yuv-scanout-v52-study',
    'python-game-quantized-motion-v53-study',
    'python-game-motion-rx-v54-study',
    'python-game-exact-motion-v56-study',
    'python-game-error-quality-v57-study',
    'python-game-exact-cell16-v58-study',
)
ARTIFACTS = [
    'experiments/python-game-fault-recovery-v51-study/results.json',
    'experiments/python-game-yuv-scanout-v52-study/results.json',
    'experiments/python-game-yuv-scanout-v52-study/memory-budget.json',
    'experiments/python-game-quantized-motion-v53-study/results.json',
    'experiments/python-game-motion-rx-v54-study/results.json',
    'experiments/python-game-motion-rx-v54-study/fractional.json',
    'experiments/python-game-exact-motion-v56-study/results.json',
    'experiments/python-game-error-quality-v57-study/results.json',
    'experiments/python-game-exact-cell16-v58-study/results.json',
    'docs/prototype-v53-native-prefix-comparison.json',
]
TEST_LOGS = (
    'experiments/python-game-yuv-scanout-v52-study/tests.log',
    'experiments/python-game-yuv-scanout-v52-study/tests_memory_budget.log',
    'experiments/python-game-quantized-motion-v53-study/tests.log',
    'experiments/python-game-quantized-motion-v53-study/tests_verify.log',
    'experiments/python-game-exact-motion-v56-study/tests.log',
    'experiments/python-game-exact-motion-v56-study/tests_verify.log',
    'experiments/python-game-error-quality-v57-study/tests.log',
    'experiments/python-game-exact-cell16-v58-study/tests.log',
    'experiments/python-game-exact-cell16-v58-study/tests_verify.log',
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def passing(path):
    content = path.read_text()
    match = re.search(r'^Ran (\d+) tests? in ', content, re.M)
    assert match and content.rstrip().endswith('OK'), path
    return int(match[1])


def main():
    parent_path = ROOT / 'docs/prototype-v50-provenance.json'
    parent = json.loads(parent_path.read_text())
    frozen = {name: digest for name, digest in parent['file_sha256'].items()
              if name not in MUTABLE}
    for name, digest in frozen.items():
        assert sha(ROOT / name) == digest, ('frozen v50', name)

    paths = {ROOT / name for name in parent['file_sha256']}
    paths.update(ROOT / name for name in (
        'docs/prototype-v50-provenance.json',
        'docs/v51-v52-evidence-audit.md',
        'docs/prototype-v53-native-prefix-comparison.json',
        'docs/custom-codec-prototype-v58-2026-11-05.md',
        'experiments/compare_motion_v53.py',
        'experiments/export_prototype_v58.py',
        'experiments/verify_prototype_v58.py',
    ))
    for slug in STUDIES:
        folder = ROOT / 'experiments' / slug
        paths.update(path for path in folder.rglob('*')
                     if path.is_file() and '__pycache__' not in path.parts
                     and path.suffix != '.pyc')

    tests = {name: passing(ROOT / name) for name in TEST_LOGS}
    assert sum(tests.values()) == 42, tests
    for name in TEST_LOGS:
        paths.add(ROOT / name)

    for artifact in ARTIFACTS:
        data = json.loads((ROOT / artifact).read_text())
        assert data.get('source_sha256'), ('missing source pins', artifact)
        for name, digest in data['source_sha256'].items():
            relative = Path(name)
            assert not relative.is_absolute() and '..' not in relative.parts
            assert sha(ROOT / relative) == digest, ('producer', artifact, name)
            paths.add(ROOT / relative)

    helpers = []
    for slug in STUDIES:
        helpers.append(dict(path=f'experiments/{slug}/verify.py', args=[]))
    helpers.extend([
        dict(path='experiments/python-game-yuv-scanout-v52-study/memory_budget.py', args=['--check']),
        dict(path='experiments/compare_motion_v53.py', args=['--check']),
    ])
    data = dict(
        schema='gamebub-v58-provenance',
        parent_commit='e580866236d5e4477e5f13296ea90d21d10965f2',
        parent_manifest='docs/prototype-v50-provenance.json',
        file_sha256={path.relative_to(ROOT).as_posix(): sha(path)
                     for path in sorted(paths)},
        frozen_v50_sha256=frozen,
        passing_test_logs=tests,
        run_artifacts=ARTIFACTS,
        stored_helpers=helpers,
        included_studies=list(STUDIES),
        limitations=[
            'V51 is software receiver API fault-state evidence, not network or panel recovery.',
            'V52 bandwidth delta is conditional traffic arithmetic; scanout interface is not exclusive to this codec.',
            'V53 rate/error trade increases cumulative source error; native points are reused, not newly encoded.',
            'V54 is a bounded dataset qualification; tiled Python receiver is slower than direct receive.',
            'V56 finds zero eligible nonzero macroblocks; V58 finds no visible coefficient or fine-bit savings.',
            'V57 coordinate temporal error change is not perceptual flicker.',
            'No physical 30fps, deployed transport capacity, FPGA cycles, or target memory fit is established.',
            'V55 and V59+ studies are excluded.',
        ],
    )
    out = ROOT / 'docs/prototype-v58-provenance.json'
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(files=len(paths) + 1, frozen_v50_files=len(frozen),
                          passing_tests=sum(tests.values()),
                          source_snapshot_bindings=sum(
                              len(json.loads((ROOT / name).read_text())['source_sha256'])
                              for name in ARTIFACTS))))


if __name__ == '__main__':
    main()
