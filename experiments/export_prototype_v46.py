#!/usr/bin/env python3
"""Freeze V43–V46 receive, transform and rate-selection evidence."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUTABLE = ('README.md', 'docs/gamebub-application-specific-codec-plan.md')
STUDIES = ('direct-rx', 'block-rx', 'symmetric-inverse', 'rice-search')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def passing(path):
    content = path.read_text()
    match = re.search(r'^Ran (\d+) tests? in ', content, re.M)
    assert match and content.rstrip().endswith('OK'), path
    return int(match[1])


def main():
    parent = json.loads((ROOT / 'docs/prototype-v42-provenance.json').read_text())
    frozen = {name: digest for name, digest in parent['file_sha256'].items()
              if name not in MUTABLE}
    for name, digest in frozen.items():
        assert sha(ROOT / name) == digest, ('frozen v42', name)

    paths = {ROOT / name for name in parent['file_sha256']}
    names = (
        'docs/prototype-v42-provenance.json',
        'docs/custom-codec-prototype-v46-2026-11-05.md',
        'docs/v44-v45-evidence-audit.md',
        'docs/v46-rate-search-audit.md',
        'experiments/export_prototype_v46.py',
        'experiments/verify_prototype_v46.py',
    )
    paths.update(ROOT / name for name in names)

    run_artifacts = [
        'experiments/python-game-direct-rx-v43-study/results.json',
        'experiments/python-game-block-rx-v44-study/results.json',
        'experiments/python-game-symmetric-inverse-v45-study/results.json',
        'experiments/python-game-rice-search-v46-study/results.json',
        'experiments/python-game-rice-search-v46-study/frames.json',
    ]
    tests = {}
    for slug in STUDIES:
        folder = ROOT / f'experiments/python-game-{slug}-v{43 + STUDIES.index(slug)}-study'
        # V46 has one component search plus an added complete-frame verifier.
        if slug == 'rice-search':
            folder = ROOT / 'experiments/python-game-rice-search-v46-study'
        paths.update(path for path in folder.rglob('*')
                     if path.is_file() and '__pycache__' not in path.parts
                     and path.suffix != '.pyc')

    tests.update({
        'experiments/python-game-direct-rx-v43-study/tests.log': passing(
            ROOT / 'experiments/python-game-direct-rx-v43-study/tests.log'),
        'experiments/python-game-direct-rx-v43-study/tests_verify.log': passing(
            ROOT / 'experiments/python-game-direct-rx-v43-study/tests_verify.log'),
        'experiments/python-game-block-rx-v44-study/tests.log': passing(
            ROOT / 'experiments/python-game-block-rx-v44-study/tests.log'),
        'experiments/python-game-symmetric-inverse-v45-study/tests.log': passing(
            ROOT / 'experiments/python-game-symmetric-inverse-v45-study/tests.log'),
        'experiments/python-game-rice-search-v46-study/tests.log': passing(
            ROOT / 'experiments/python-game-rice-search-v46-study/tests.log'),
    })
    assert sum(tests.values()) == 28

    for artifact in run_artifacts:
        record = json.loads((ROOT / artifact).read_text())
        for name, digest in record['source_sha256'].items():
            relative = Path(name)
            assert not relative.is_absolute() and '..' not in relative.parts
            assert sha(ROOT / relative) == digest, ('producer', artifact, name)
            paths.add(ROOT / relative)

    parent_commit = '2cd22c19982b03ce74387ea1e5910b219308107d'
    data = dict(
        schema='gamebub-v46-provenance',
        parent_commit=parent_commit,
        file_sha256={path.relative_to(ROOT).as_posix(): sha(path)
                     for path in sorted(paths)},
        frozen_v42_sha256=frozen,
        passing_test_logs=tests,
        run_artifacts=run_artifacts,
        stored_helpers=[
            'experiments/python-game-direct-rx-v43-study/verify.py',
            'experiments/python-game-block-rx-v44-study/verify.py',
            'experiments/python-game-symmetric-inverse-v45-study/verify.py',
            'experiments/python-game-rice-search-v46-study/verify.py',
            'experiments/python-game-rice-search-v46-study/verify_frames.py',
        ],
        limitations=[
            '577-frame host receive comparison removes proof-adapter work; no physical FPS or target fit.',
            'V44 tile bytes exclude compressed input and total heap; atomic publication remains required.',
            'V45 multiply counts are logical models, not measured DSP work or cycles.',
            'V46 bounded Rice neighborhood; complete-frame saving is 902 bytes on 24 prefixes.',
            'No V47/V48 evidence included.',
        ],
    )
    (ROOT / 'docs/prototype-v46-provenance.json').write_text(
        json.dumps(data, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(files=len(paths), frozen_v42_files=len(frozen),
                          passing_tests=sum(tests.values()),
                          source_snapshot_bindings=sum(
                              len(json.loads((ROOT / name).read_text())['source_sha256'])
                              for name in run_artifacts))))


if __name__ == '__main__':
    main()
