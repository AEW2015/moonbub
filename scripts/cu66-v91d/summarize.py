#!/usr/bin/env python3
"""Bind V91d finite-memory RTL audits and checkpoint file integrity."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91d'
RTL = ROOT / 'fpga/experiments/cu66-v91d'
DOCS = ROOT / 'docs/cu66-v91d'
BASE = '4ff660d4be06ef522de977bb78badd2b64a79e72'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def storage():
    spec = importlib.util.spec_from_file_location('v91d_retained_vectors', Path(__file__).with_name('retain_vectors.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify()


def verify_receipt(receipt, folder):
    path = RTL / folder / receipt['attempt'] / 'results.json'
    result = read(path)
    assert receipt['result_sha256'] == sha(path)
    assert result['source_sha256'] == receipt['source_sha256']
    assert result['artifacts_sha256'] == receipt['artifact_sha256']
    for relative, digest in result['source_sha256'].items():
        assert sha(ROOT / relative) == digest
    for relative, digest in result['artifacts_sha256'].items():
        assert sha(path.parent / relative) == digest
    return path, result


def summary():
    storage()
    audit = read(AREA / 'audit.json')
    assert audit['status'] == 'PASS_VECTORS_PACKED_IMAGES_AND_FINITE_MEMORY_RTL'
    assert audit['parent_commit'] == BASE
    scratch_path, scratch = verify_receipt(audit['standalone_rtl']['receipt'], 'scratch-attempts')
    public_scratch = read(RTL / 'scratch-results.json')
    assert ROOT / public_scratch.pop('selected_report') == scratch_path
    assert public_scratch == scratch
    pipeline = read(RTL / 'pipeline-results.json')
    assert pipeline['status'] == 'PASS_INTEGRATED_FINITE_MEMORY_COEFFICIENT_PIPELINE'
    assert pipeline['seed'] == 910433
    runs = audit['integrated_rtl']['selected_seeds']
    assert {run['seed'] for run in runs} == {910432, 910433}
    for run in runs:
        path, result = verify_receipt(run['receipt'], 'pipeline-attempts')
        assert result['source_sha256'] == pipeline['source_sha256']
        assert result['verdict']['directed_checks'] == 11
        if run['seed'] == 910433:
            assert ROOT / pipeline['selected_report'] == path
            assert {key: value for key, value in pipeline.items() if key != 'selected_report'} == result
    failure = audit['integrated_rtl']['retained_pre_fix_regression']
    failure_path = RTL / 'pipeline-attempts' / failure['attempt'] / 'results.json'
    assert failure['result_sha256'] == sha(failure_path)
    assert read(failure_path)['status'] == 'FAIL'
    rows = [json.loads(line) for line in (ROOT / pipeline['selected_report']).with_name('simulation.jsonl').read_text().splitlines()]
    source_sums = {}
    for row in rows:
        if row['type'] != 'case' or not row['id'].startswith('actual:') or row['serial_clear']:
            continue
        key = ':'.join(row['id'].split(':')[:3])
        source_sums.setdefault(key, {})['FAST' if row['memory_profile'] == 0 else 'SLOW'] = (
            source_sums.get(key, {}).get('FAST' if row['memory_profile'] == 0 else 'SLOW', 0) + row['cycles'])
    assert len(source_sums) == 4
    vector_path = AREA / 'vectors/coefficients.jsonl.gz'
    cases = [json.loads(line) for line in gzip.open(vector_path, 'rt')]
    actual = [case for case in cases if case['id'].startswith('actual:')]
    coded_blocks = sum(case['blocks'] for case in actual if not case['raw'])
    comparisons = [row for row in pipeline['comparisons'] if row['population'] == 'actual']
    fast = next(row for row in comparisons if row['memory_profile'] == 0)
    assert fast['serial_cycles'] - fast['mask_cycles'] == 63 * coded_blocks
    evidence = [AREA / 'audit.json', AREA / 'vectors/index.json', RTL / 'scratch-results.json',
                RTL / 'pipeline-results.json', RTL / 'historical-vector-storage.json']
    sources = [Path(__file__).resolve(), Path(__file__).with_name('retain_vectors.py'), AREA / 'verify_results.py']
    return dict(schema='cu66-v91d-combined-evidence-v1', status='PASS_INTEGRATED_COEFFICIENT_RTL_FINITE_MEMORY',
                parent_commit=BASE,
                evidence_sha256={str(path.relative_to(ROOT)): sha(path) for path in evidence},
                source_sha256={str(path.relative_to(ROOT)): sha(path) for path in sources},
                vector_packets=len(cases), actual_packets=len(actual), actual_source_frames=4,
                dense_coefficients_per_configuration=sum(case['blocks'] * 64 for case in cases),
                standalone_directed_checks=26, integrated_directed_checks_per_seed=11,
                integrated_seeds=[dict(seed=run['seed'], attempt=run['receipt']['attempt'],
                     result_sha256=run['receipt']['result_sha256']) for run in runs],
                actual_packet_comparisons=comparisons, actual_coded_blocks=coded_blocks,
                exact_FAST_clear_cycles_saved=63 * coded_blocks,
                source_serialized_three_chunk_service_cycles=source_sums,
                reference_100MHz_cycle_budget=1000000,
                sources_SLOW_exceeding_reference_budget=sum(row['SLOW'] >= 1000000 for row in source_sums.values()),
                reference_budget_is_achieved_clock=False,
                retained_pre_fix_failure=dict(attempt=failure['attempt'], result_sha256=failure['result_sha256'],
                    regression=failure['expected_pre_fix_failure']),
                packed_scratch_RTL_implemented=True, packet_to_memory_to_dense_coefficients_connected=True,
                positive_memory_ACK_delay_and_abort_drain_tested=True,
                memory_controller_physically_calibrated=False,
                synchronous_packet_staging_RAM_ports_qualified=False,
                target_synthesis_route_frequency_or_fit_proven=False,
                complete_pixel_reference_HUD_hash_display_pipeline_qualified=False,
                live_ESP32_wifi_QSPI_concurrency_measured=False,
                sustained_hardware_distinct_30fps_proven=False,
                complete_validated_FPGA_decode_strictly_under10ms_proven=False,
                firmware_or_hardware_deployed=False)


def collect():
    alias = ROOT / read(RTL / 'historical-vector-storage.json')['alias']
    dirs = ('docs/cu66-v91d', 'scripts/cu66-v91d', 'experiments/python-gamebub-v91d', 'fpga/experiments/cu66-v91d')
    paths = [path for relative in dirs for path in (ROOT / relative).rglob('*')
             if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc'
             and path != alias and path != DOCS / 'bundle-manifest.json']
    paths.extend(ROOT / name for name in ('docs/gamebub-application-specific-codec-plan.md',
                 'docs/gamebub-v91-v110-development-plan.md', 'docs/literature-review-2026-11-06/README.md'))
    return {str(path.relative_to(ROOT)): sha(path) for path in sorted(paths)}


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
        print('V91D_BUNDLE_PASS', manifest['file_count'])
        return
    (AREA / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    if args.write_manifest:
        files = collect()
        (DOCS / 'bundle-manifest.json').write_text(json.dumps(dict(schema='cu66-v91d-bundle-v1',
            parent_commit=BASE, file_count=len(files), sha256=files,
            scope='Checkpoint tree integrity only; shared roadmap documents evolve at later commits.',
            excluded=['manifest itself', '__pycache__', '*.pyc', 'failed text fixture retained by exact serializer',
                      'unrelated marker-recovery experiment']), indent=2) + '\n')
    print(result['status'])


if __name__ == '__main__':
    main()
