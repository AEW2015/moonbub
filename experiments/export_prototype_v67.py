#!/usr/bin/env python3
"""Freeze the V58-parented temporal/filter/transport bundle for V67."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUTABLE = ('README.md', 'docs/gamebub-application-specific-codec-plan.md')
PARENT_MANIFEST = 'docs/prototype-v58-provenance.json'
STUDIES = (
    'python-game-temporal-qual-v59-study',
    'python-game-display-filter-v60-study',
    'python-game-native-temporal-v61-study',
    'python-game-native-temporal-cap-v61-study',
    'python-game-filter-temporal-v62-study',
    'python-game-filter-frontier-v63-study',
    'python-game-filtered-scanout-v64-study',
    'python-game-forwarder-budget-v65-study',
    'python-game-canonical-tag-v66-study',
    'python-game-filter-qual-v67-study',
    'python-game-hash-stream-v67-study',
)
ARTIFACTS = [
    f'experiments/{slug}/results.json' for slug in STUDIES
] + [
    'experiments/python-game-display-filter-v60-study/calibration.json',
    'experiments/python-game-filter-frontier-v63-study/comparison.json',
    'docs/figures/prototype-v67/evidence.json',
    'docs/prototype-v67-environment.json',
    'docs/prototype-v67-mask-program.json',
]
DOCS = (
    'docs/v51-v52-evidence-audit.md',
    'docs/v60-v64-evidence-audit.md',
    'docs/v67-integration-audit.md',
    'docs/v67-final-evidence-audit.md',
    'docs/custom-codec-prototype-v67-2026-11-05.md',
    'docs/gamebub-v67-hardware-research-handoff.md',
)
EXTRA = (
    PARENT_MANIFEST,
    'experiments/render_prototype_v67.py',
    'experiments/export_prototype_v67.py',
    'experiments/verify_prototype_v67.py',
    'docs/figures/prototype-v67/evidence.json',
    'docs/prototype-v67-environment.json',
    'experiments/derive_filter_mask_v67.py',
    'experiments/verify_filter_mask_v67.py',
    'docs/prototype-v67-mask-verify.log',
    'docs/prototype-v67-mask-program.json',
    'docs/figures/prototype-v67/sampled-rate-error.png',
    'docs/figures/prototype-v67/sampled-rate-error.svg',
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
        assert sha(ROOT / name) == digest, ('frozen v58', name)

    for slug in STUDIES:
        folder = ROOT / 'experiments' / slug
        assert (folder / 'results.json').is_file(), ('unfinished study', slug)
        assert (folder / 'verify.py').is_file(), ('missing independent verifier', slug)
    for name in (*DOCS, *EXTRA):
        assert (ROOT / name).is_file(), ('unfinished v67 bundle', name)

    paths = {ROOT / name for name in parent['file_sha256']}
    paths.update(ROOT / name for name in (*DOCS, *EXTRA))
    for slug in STUDIES:
        folder = ROOT / 'experiments' / slug
        paths.update(path for path in folder.rglob('*')
                     if path.is_file() and '__pycache__' not in path.parts
                     and path.suffix != '.pyc')
    for artifact in ARTIFACTS:
        data = json.loads((ROOT / artifact).read_text())
        paths.add(ROOT / artifact)
        for name, digest in data.get('source_sha256', {}).items():
            relative = Path(name)
            assert not relative.is_absolute() and '..' not in relative.parts
            assert sha(ROOT / relative) == digest, ('producer', artifact, name)
            paths.add(ROOT / relative)
    figure = json.loads((ROOT / 'docs/figures/prototype-v67/evidence.json').read_text())
    for name, digest in figure['inputs'].items():
        assert sha(ROOT / name) == digest, ('figure input', name)
        paths.add(ROOT / name)

    logs = []
    for slug in STUDIES:
        folder = ROOT / 'experiments' / slug
        logs.extend(p for p in folder.glob('tests*.log') if p.is_file())
    logs = sorted(set(logs))
    tests = {p.relative_to(ROOT).as_posix(): passing(p) for p in logs}
    paths.update(logs)

    helpers = []
    for slug in STUDIES:
        helpers.append(dict(path=f'experiments/{slug}/verify.py', args=[]))
    helpers.extend([
        dict(path='experiments/python-game-display-filter-v60-study/calibrate.py', args=['--check']),
        dict(path='experiments/python-game-filter-frontier-v63-study/compare.py', args=['--check']),
        dict(path='experiments/render_prototype_v67.py', args=[]),
        dict(path='experiments/derive_filter_mask_v67.py', args=['--check']),
        dict(path='experiments/verify_filter_mask_v67.py', args=[]),
    ])
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert head == '1dc2cfcc2b35532a928facf4621fb34ac936e4c3', ('unexpected V58 parent', head)
    data = dict(
        schema='gamebub-v67-provenance',
        parent_commit=head,
        parent_manifest=PARENT_MANIFEST,
        included_studies=list(STUDIES),
        file_sha256={p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)},
        frozen_v58_sha256=frozen,
        passing_test_logs=tests,
        run_artifacts=ARTIFACTS,
        stored_helpers=helpers,
        figure_outputs=['docs/figures/prototype-v67/sampled-rate-error.png',
                        'docs/figures/prototype-v67/sampled-rate-error.svg',
                        'docs/figures/prototype-v67/evidence.json'],
        limitations=[
            'V59 is a temporal qualification on later windows from known related Mass Effect clips.',
            'V60–V64 are display-only quality and scanout models; their metrics are not subjective quality, device bandwidth, or FPS.',
            'V61 native results reuse existing clip family and are sampled parameter points, not an optimal frontier.',
            'V65 models a constrained firmware/FPGA forwarding path; it does not execute ESP32, RF, or QSPI hardware.',
            'V66 software tag-verification workload does not demonstrate physical hash-cycle or FPGA fit.',
            'Figure rate normalization at 30 fps is arithmetic, not a throughput measurement.',
            'No physical 30fps, network/panel throughput, FPGA cycle count, or target memory fit is claimed.',
        ],
    )
    (ROOT / 'docs/prototype-v67-provenance.json').write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(files=len(paths), frozen_v58_files=len(frozen),
                          passing_tests=sum(tests.values()),
                          source_bindings=sum(len(json.loads((ROOT / p).read_text()).get('source_sha256', {}))
                                              for p in ARTIFACTS if p.endswith('.json')),
                          helpers=len(helpers), parent_commit=head)))


if __name__ == '__main__':
    main()
