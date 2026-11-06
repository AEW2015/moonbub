#!/usr/bin/env python3
"""Bind V91e evidence without turning coefficient timings into frame claims."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91e'
RTL = ROOT / 'fpga/experiments/cu66-v91e'
DOCS = ROOT / 'docs/cu66-v91e'
BASE = 'bebd308caae58b235263c728c4994a7340c42f73'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def retained_vectors():
    path = Path(__file__).with_name('retain_vectors.py')
    spec = importlib.util.spec_from_file_location('v91e_retained_vectors', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify()


def summary():
    retained_vectors()
    audit = read(AREA / 'audit.json')
    assert audit['status'] == 'PASS_VECTORS_TIMESTAMPS_PARTITIONS_AND_V91D_PARITY'
    analysis = read(AREA / 'analysis.json')
    assert analysis['status'] == 'PASS_RECONCILED_IDENTIFIED_STAGE_WORK'
    for relative, digest in analysis['source_sha256'].items():
        assert sha(ROOT / relative) == digest
    seeds = audit['integrated_rtl']['selected_seeds']
    assert {row['verdict']['seed'] for row in seeds} == {910432, 910433}
    public = read(RTL / 'pipeline-results.json')
    assert public['status'] == 'PASS_RECONCILED_TELEMETRY_WITH_FROZEN_V91D_PARITY' and public['seed'] == 910433
    for run in seeds:
        path = RTL / 'pipeline-attempts' / run['attempt'] / 'results.json'
        result = read(path)
        assert run['result_sha256'] == sha(path)
        assert result['source_sha256'] == run['source_sha256'] == public['source_sha256']
        assert result['artifacts_sha256'] == run['artifact_sha256']
        for relative, digest in result['source_sha256'].items():
            assert sha(ROOT / relative) == digest
        for relative, digest in result['artifacts_sha256'].items():
            assert sha(path.parent / relative) == digest
        matching = next(row for row in analysis['seed_runs'] if row['seed'] == result['seed'])
        assert matching['result_sha256'] == run['result_sha256']
        assert matching['baseline'] == result['baseline_v91d']
        assert matching['population_totals'] == result['population_totals']
        if result['seed'] == 910433:
            assert ROOT / public['selected_report'] == path
            assert {key: value for key, value in public.items() if key != 'selected_report'} == result
    selected = next(row for row in analysis['seed_runs'] if row['seed'] == 910433)
    slow = next(row for row in selected['population_totals']
                if row['population'] == 'all_actual' and row['memory_profile'] == 1 and row['serial_clear'] == 0)
    evidence = [AREA / 'audit.json', AREA / 'analysis.json', AREA / 'telemetry-contract.json',
                AREA / 'vectors/index.json', RTL / 'pipeline-results.json', RTL / 'historical-vector-storage.json']
    source_paths = [Path(__file__).resolve(), Path(__file__).with_name('retain_vectors.py'),
                    Path(__file__).with_name('analyze.py'), Path(__file__).with_name('telemetry.py'), AREA / 'verify_results.py']
    return dict(schema='cu66-v91e-combined-evidence-v1', status='PASS_RECONCILED_OBSERVABILITY_EXPANDED_WORKLOADS',
                parent_commit=BASE, last_functional_architecture_commit='c9bc0f98ef65891631ed95bab3609efc777e826a',
                evidence_sha256={str(path.relative_to(ROOT)): sha(path) for path in evidence},
                source_sha256={str(path.relative_to(ROOT)): sha(path) for path in source_paths},
                integrated_seeds=[dict(seed=row['verdict']['seed'], attempt=row['attempt'], result_sha256=row['result_sha256']) for row in seeds],
                cases=20, actual_packets=15, actual_source_frames=5, configurations_per_seed=4,
                dense_comparisons_per_seed=9003776, directed_checks_per_seed=11,
                tile_trace_records_per_seed=140684, exact_original_v91d_metric_values_compared=1224,
                slower_mask_all_actual_cycles=slow['cycles'], slower_mask_exclusive_group_percent=slow['group_percent'],
                slower_mask_dense_accepted_cycles=slow['dense_coefficients'],
                slower_mask_overlapping_counters=slow['overlapping_edges'],
                measured_register_highwaters=slow['highwaters'],
                source_services=selected['source_services'],
                current_endpoint=analysis['current_endpoint'],
                full_frame_validated_publication_timestamp=None,
                full_frame_validated_decode_latency_measured=False,
                telemetry_changes_scheduling=False,
                scheduling_speedup_claimed=False,
                hardware_30fps_proven=False,
                complete_validated_FPGA_decode_strictly_under10ms_proven=False,
                target_frequency_physical_fit_or_controller_calibration_proven=False,
                firmware_or_hardware_deployed=False)


def collect():
    alias = ROOT / read(RTL / 'historical-vector-storage.json')['alias']
    directories = ('docs/cu66-v91e', 'scripts/cu66-v91e', 'experiments/python-gamebub-v91e', 'fpga/experiments/cu66-v91e')
    files = [path for folder in directories for path in (ROOT / folder).rglob('*')
             if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc'
             and path != alias and path != DOCS / 'bundle-manifest.json']
    files.extend(ROOT / name for name in ('docs/gamebub-application-specific-codec-plan.md',
                 'docs/gamebub-v91-v110-development-plan.md', 'docs/literature-review-2026-11-06/README.md'))
    return {str(path.relative_to(ROOT)): sha(path) for path in sorted(files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-manifest', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = summary()
    if args.check:
        assert read(AREA / 'summary.json') == result
        manifest = read(DOCS / 'bundle-manifest.json')
        assert manifest['parent_commit'] == BASE
        assert manifest['sha256'] == collect() and manifest['file_count'] == len(manifest['sha256'])
        print('V91E_BUNDLE_PASS', manifest['file_count'])
        return
    (AREA / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    if args.write_manifest:
        files = collect()
        (DOCS / 'bundle-manifest.json').write_text(json.dumps(dict(schema='cu66-v91e-bundle-v1',
            parent_commit=BASE, file_count=len(files), sha256=files,
            scope='Checkpoint tree integrity only; shared roadmap docs evolve. Measured endpoint remains dense coefficients.',
            excluded=['manifest itself', '__pycache__', '*.pyc', 'rejected analysis text fixture retained by exact serializer',
                      'unrelated marker-recovery experiment']), indent=2) + '\n')
    print(result['status'])


if __name__ == '__main__':
    main()
