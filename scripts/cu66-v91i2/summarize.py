#!/usr/bin/env python3
"""Freeze audited V91i2a results without promoting coefficient fences to pixels."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / 'experiments/python-gamebub-v91i2'
AREA = ROOT / 'fpga/experiments/cu66-v91i2'
BASELINE = '20edfc8344f287512d3ec6c5b12f84e2defa7a9a'
SHARED = ['docs/gamebub-application-specific-codec-plan.md',
          'docs/gamebub-v91-v110-development-plan.md',
          'docs/literature-review-2026-11-06/README.md']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    audit = read(MODEL / 'audit.json')
    assert audit['status'].startswith('PASS'), audit['status']
    vectors = read(MODEL / 'vectors/manifest.json')
    expected_ids = {row['id'] for row in vectors['cases']}
    native_ids = {row['id'] for row in vectors['cases'] if row['case_kind'] == 'native_golden'}
    assert len(native_ids) == 4
    reports, fences = [], []
    for seed in (911201, 911202):
        choices = []
        for path in sorted((AREA / 'pipeline-attempts').glob('*/results.json')):
            report = read(path)
            if report.get('seed') != seed or report['status'] != 'PASS_CS88_BR88_COEFFICIENT_PLACEMENT':
                continue
            if not all(sha(ROOT / name) == value for name, value in report['source_sha256'].items()):
                continue
            if not all(sha(MODEL / 'vectors' / name) == value for name, value in report['vectors_sha256'].items()):
                continue
            choices.append((path, report))
        assert choices, f'No current passing attempt for seed {seed}'
        path, report = choices[-1]
        rows = [json.loads(line) for line in (path.parent / 'simulation.jsonl').read_text().splitlines()]
        cases = [row for row in rows if row['type'] == 'case']
        assert {(row['id'], row['memory_profile']) for row in cases} == {
            (name, profile) for name in expected_ids for profile in (0, 1)}
        assert report['verdict']['dense_comparisons'] == sum(row['coefficients'] for row in cases)
        assert report['tile_trace']['records'] * 64 == report['verdict']['dense_comparisons']
        reports.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path), seed=seed,
                            case_rows=len(cases), verdict=report['verdict'],
                            tile_trace=report['tile_trace']))
        for row in cases:
            if row['id'] in native_ids:
                assert row['error'] == 0 and row['last_input'] < row['first_coef']
                assert row['first_coef'] <= row['last_coef'] < row['done_cycle']
                fences.append(dict(seed=seed, id=row['id'], memory_profile=row['memory_profile'],
                                   start_to_coefficient_done_cycles=row['cycles'],
                                   packet_complete_to_coefficient_done_cycles=row['done_cycle'] - row['last_input'],
                                   cache_preload_cycles=row['cache_cycles'],
                                   preload_plus_frame_service_cycles=row['cache_cycles'] + row['cycles'],
                                   coefficients=row['coefficients']))
    assert [r['path'] for r in audit['retained_rtl_attempts']] == [r['path'] for r in reports]
    frozen_names = ['docs/cu66-v91i/README.md', 'experiments/python-gamebub-v91i/audit.json',
                    'experiments/python-gamebub-v91i/summary.json',
                    'experiments/python-gamebub-v91h/summary.json']
    frozen = {}
    for name in frozen_names:
        original = subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=ROOT)
        assert hashlib.sha256(original).hexdigest() == sha(ROOT / name), name
        frozen[name] = sha(ROOT / name)
    summary = dict(schema='cu66-v91i2a-qualified-coefficient-placement-v1', status='PASS',
                   baseline_revision=BASELINE, retained_rtl_attempts=reports,
                   model_sha256=sha(MODEL / 'model.py'), model_report_sha256=sha(MODEL / 'model-results.json'),
                   independent_audit_sha256=sha(MODEL / 'audit.json'),
                   vector_manifest_sha256=sha(MODEL / 'vectors/manifest.json'),
                   vectors=len(expected_ids), native_golden_frames=len(native_ids),
                   total_qualification_coefficient_comparisons=sum(r['verdict']['dense_comparisons'] for r in reports),
                   total_qualification_tile_records=sum(r['tile_trace']['records'] for r in reports),
                   native_coefficient_fences=fences, unchanged_prior_evidence=frozen,
                   packet_staging_bytes=2 * 49152,
                   scope='All-BR88 CS88 residual dispatch and exact dense coefficient positional/quantizer binding; provisional outputs, no pixel or publication endpoint.',
                   full_frame_publication_timestamp=None, full_frame_decode_under10ms_proven=False,
                   hardware_distinct_30fps_proven=False,
                   unexercised_boundary='32-bit child nonce exhaustion guard is implemented but not exhausted in RTL regression.',
                   next_gate='Use this frozen integration baseline for bounded packet-refill overlap, then complete mixed-entropy handling and transform/reconstruction/validation integration.')
    (MODEL / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    manifest_path = MODEL / 'bundle-manifest.json'
    paths = [ROOT / name for name in SHARED]
    for directory in ('docs/cu66-v91i2', 'scripts/cu66-v91i2',
                      'experiments/python-gamebub-v91i2', 'fpga/experiments/cu66-v91i2'):
        paths.extend(path for path in (ROOT / directory).rglob('*')
                     if path.is_file() and '__pycache__' not in path.parts and path != manifest_path)
    manifest = dict(schema='cu66-v91i2a-bundle-manifest-v1', baseline_revision=BASELINE,
                    scope='All new checkpoint files plus three shared plans, excluding this manifest itself.',
                    files_sha256={str(path.relative_to(ROOT)): sha(path) for path in sorted(set(paths))},
                    prior_shared_plan_sha256={name: hashlib.sha256(subprocess.check_output(
                        ['git', 'show', BASELINE + ':' + name], cwd=ROOT)).hexdigest() for name in SHARED})
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print('V91I2A_SUMMARY_PASS', summary['total_qualification_coefficient_comparisons'],
          'coefficient checks;', len(manifest['files_sha256']), 'bundle files')


if __name__ == '__main__':
    main()
