#!/usr/bin/env python3
"""Freeze the focused V68 zero-motion predictor study over the V67 bundle."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUTABLE = ('README.md', 'docs/gamebub-application-specific-codec-plan.md')
PARENT_MANIFEST = 'docs/prototype-v67-provenance.json'
STUDY = 'python-game-zero-predict-v68-study'
REPORT = 'docs/custom-codec-prototype-v68-2026-11-05.md'
ARTIFACTS = [f'experiments/{STUDY}/results.json']
EXTRA = (
    PARENT_MANIFEST,
    'experiments/export_prototype_v68.py',
    'experiments/verify_prototype_v68.py',
    REPORT,
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def passing(path):
    content = path.read_text()
    match = re.search(r'^Ran (\d+) tests? in ', content, re.M)
    assert match and content.rstrip().endswith('OK'), path
    return int(match[1])


def main():
    parent = json.loads((ROOT / PARENT_MANIFEST).read_text())
    frozen = {name: digest for name, digest in parent['file_sha256'].items()
              if name not in MUTABLE}
    for name, digest in frozen.items():
        assert sha(ROOT / name) == digest, ('frozen v67', name)
    parent_sha = sha(ROOT / PARENT_MANIFEST)

    folder = ROOT / 'experiments' / STUDY
    assert (folder / 'results.json').is_file(), ('unfinished study', STUDY)
    assert (folder / 'verify.py').is_file(), ('missing independent verifier', STUDY)
    for name in (*EXTRA,):
        assert (ROOT / name).is_file(), ('unfinished V68 bundle', name)

    paths = {ROOT / name for name in parent['file_sha256']}
    # Include this release's updates to the two intentionally mutable indexes.
    paths.update(ROOT / name for name in MUTABLE)
    paths.update(ROOT / name for name in EXTRA)
    paths.update(path for path in folder.rglob('*')
                 if path.is_file() and '__pycache__' not in path.parts
                 and path.suffix != '.pyc')
    for artifact in ARTIFACTS:
        data = json.loads((ROOT / artifact).read_text())
        for name, digest in data.get('source_sha256', {}).items():
            relative = Path(name)
            assert not relative.is_absolute() and '..' not in relative.parts
            assert sha(ROOT / relative) == digest, ('producer', artifact, name)
            paths.add(ROOT / relative)

    logs = sorted(p for p in folder.glob('tests*.log') if p.is_file())
    assert logs, ('missing V68 test transcript', STUDY)
    tests = {p.relative_to(ROOT).as_posix(): passing(p) for p in logs}
    paths.update(logs)
    helpers = [dict(path=f'experiments/{STUDY}/verify.py', args=[])]

    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                   text=True).strip()
    assert head == '043939f89fb2c9626accc9652884520a68c5fc8d', (
        'unexpected V67 parent', head)
    data = dict(
        schema='gamebub-v68-provenance',
        parent_commit=head,
        parent_manifest=PARENT_MANIFEST,
        parent_manifest_sha256=parent_sha,
        included_studies=[STUDY],
        file_sha256={p.relative_to(ROOT).as_posix(): sha(p)
                     for p in sorted(paths)},
        frozen_v67_sha256=frozen,
        passing_test_logs=tests,
        run_artifacts=ARTIFACTS,
        stored_helpers=helpers,
        limitations=[
            'The V68 experiment preserves the existing packet/wire format and borrows readonly references; it measures encoder-stage work only.',
            'Stage timings are not end-to-end latency or physical 30fps evidence.',
            'V67 device, transport, memory-fit, FPGA-cycle, and target-throughput limitations remain in force.',
        ],
    )
    (ROOT / 'docs/prototype-v68-provenance.json').write_text(
        json.dumps(data, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(files=len(paths), frozen_v67_files=len(frozen),
                          passing_tests=sum(tests.values()),
                          source_bindings=sum(len(json.loads((ROOT / p).read_text()).get('source_sha256', {}))
                                              for p in ARTIFACTS),
                          helpers=len(helpers), parent_commit=head)))


if __name__ == '__main__':
    main()
