#!/usr/bin/env python3
"""Freeze V91j two-seed exact inverse integration and the direct V91k handoff."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91j'
BASELINE = 'dbccd7cddcf0d8fd3c2750db326493d7a051313d'
SHARED = ['docs/gamebub-application-specific-codec-plan.md',
          'docs/gamebub-v91-v110-development-plan.md',
          'docs/literature-review-2026-11-06/README.md']
PRIMARY = ('actual_001', 'actual_006', 'actual_043', 'actual_031')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    audit = read(AREA / 'audit.json')
    assert audit['status'] == 'PASS_INDEPENDENT_MATH_AND_BOTH_INTEGRATION_SEEDS'
    assert all(sha(ROOT / name) == value for name, value in audit['source_sha256'].items())
    assert audit['math']['golden_rows'] == 31706
    assert audit['boundary'] == dict(boundary_cases=48, boundary_invalid=6, boundary_valid=42)
    attempts, fences = [], []
    for item in audit['attempts']:
        path = ROOT / item['path']
        assert sha(path) == item['sha256']
        report = read(path)
        assert report['status'] == 'PASS_INTEGRATED_DEQUANT_AND_IDCT_RESIDUALS'
        assert all(sha(ROOT / name) == value for name, value in report['source_sha256'].items())
        for name, value in report['vectors_sha256'].items():
            assert sha(AREA / 'vectors' / name) == value
        assert report['verdict']['directed_checks'] == 13
        assert report['inverse_verdict']['directed_checks'] == 15
        assert report['inverse_verdict']['boundary_cases'] == 48
        for counter in ('dense_comparisons', 'assembly_comparisons', 'dequant_comparisons', 'residual_comparisons'):
            assert report['verdict'][counter] == 4058368
        assert item['integration']['status'] == 'PASS_TRACE_AND_CONTROL'
        rows = [json.loads(line) for line in (path.parent / 'simulation.jsonl').read_text().splitlines()]
        cases = {(row['id'], row['memory_profile']): row for row in rows if row['type'] == 'case'}
        assert len(cases) == 22
        for profile in (0, 1):
            for identity in PRIMARY:
                row = cases[identity, profile]
                assert row['error'] == 0 and not row['full_frame_publication'] and not row['pending_drain']
                assert row['requests'] == row['acks'] and row['inverse']['owned_banks'] == 0
                assert row['inverse']['max_owned_banks'] == 2
                assert row['inverse']['assembly_during_math_inputs'] > 0
                fences.append(dict(seed=report['seed'], id=identity, memory_profile=profile,
                                   start_to_residual_done_cycles=row['cycles'],
                                   last_outer_byte_to_residual_done_cycles=row['done_cycle'] - row['last_input'],
                                   residual_tail_after_coefficient_done_cycles=row['done_cycle'] - row['coefficient_done_cycle'],
                                   cache_preload_cycles=row['cache_cycles'],
                                   residual_samples=row['inverse']['residual_samples']))
        attempts.append(dict(path=item['path'], sha256=item['sha256'], seed=report['seed'],
                             verdict=report['verdict'], inverse_verdict=report['inverse_verdict'],
                             audit=item['integration'], trace=report['transform_trace']))
    assert {item['seed'] for item in attempts} == {911401, 911402} and len(attempts) == 2
    prior = {}
    for name in ('experiments/python-gamebub-v91i2b/summary.json', 'experiments/python-gamebub-v91i2b/audit.json',
                 'docs/cu66-v91i2b/README.md', 'fpga/experiments/cu66-v91i2b/cs88_pipeline_v91i2b.sv',
                 'fpga/experiments/cu66-v69/inverse/cu66_dequant.sv',
                 'fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv',
                 'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh'):
        original = subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=ROOT)
        assert hashlib.sha256(original).hexdigest() == sha(ROOT / name)
        prior[name] = sha(ROOT / name)
    summary = dict(schema='cu66-v91j-integrated-inverse-qualified-v1', status='PASS', baseline_revision=BASELINE,
                   attempts=attempts, residual_fences=fences,
                   total_dequant_comparisons=sum(item['verdict']['dequant_comparisons'] for item in attempts),
                   total_residual_comparisons=sum(item['verdict']['residual_comparisons'] for item in attempts),
                   boundary_valid_per_seed=42, boundary_invalid_per_seed=6,
                   actual_native_content_frames=4, transform_golden_tiles=31706,
                   two_coefficient_banks_logical_bytes=256, packet_staging_logical_bytes=98304,
                   prior_evidence_and_math_unchanged=prior,
                   audit_sha256=sha(AREA / 'audit.json'), independent_verifier_sha256=sha(AREA / 'verify_results.py'),
                   python_model_sha256=sha(AREA / 'model.py'), model_results_sha256=sha(AREA / 'model-results.json'),
                   vector_manifest_sha256=sha(AREA / 'vectors/manifest.json'),
                   worst_tested_native_residual_cycles=max(row['start_to_residual_done_cycles'] for row in fences),
                   scope='Real BR88 frame-to-residual RTL. Signed20 DQ; signed24 unclipped two-pass Q14 IDCT; no prediction/pixel/publication endpoint.',
                   timing_caveat='Measured simulation cycles include actual transforms. Earlier coefficient-only endpoints are not matched latency comparisons; no achieved operating clock is inferred.',
                   full_frame_publication_timestamp=None, full_frame_decode_under10ms_proven=False,
                   hardware_distinct_30fps_proven=False, mapped_memory_fit_proven=False,
                   next_milestone='V91k directly: accepted-reference prediction, COPY/constant handling, residual reconstruction, hidden-pixel normalization and output conversion with actual memory service. V91l then validates HUD/content and atomic publication.')
    (AREA / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    manifest_path = AREA / 'bundle-manifest.json'
    paths = [ROOT / name for name in SHARED]
    for directory in ('docs/cu66-v91j', 'scripts/cu66-v91j', 'experiments/python-gamebub-v91j', 'fpga/experiments/cu66-v91j'):
        paths.extend(path for path in (ROOT / directory).rglob('*')
                     if path.is_file() and '__pycache__' not in path.parts and path != manifest_path)
    manifest = dict(schema='cu66-v91j-bundle-manifest-v1', baseline_revision=BASELINE,
                    files_sha256={str(path.relative_to(ROOT)): sha(path) for path in sorted(set(paths))},
                    prior_shared_plan_sha256={name: hashlib.sha256(subprocess.check_output(
                        ['git', 'show', BASELINE + ':' + name], cwd=ROOT)).hexdigest() for name in SHARED})
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print('V91J_SUMMARY_PASS', summary['total_residual_comparisons'], 'exact residual checks;',
          len(manifest['files_sha256']), 'bundle files; next V91k')


if __name__ == '__main__':
    main()
