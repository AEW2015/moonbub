#!/usr/bin/env python3
"""Bind audited V91c results and check the retained checkpoint bundle."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91c'
RTL = ROOT / 'fpga/experiments/cu66-v91c'
DOCS = ROOT / 'docs/cu66-v91c'
PARENT = '9073cd7c99fc7d7f0fd75bc1e3c186be4c935c88'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def retained_vectors():
    spec = importlib.util.spec_from_file_location('v91c_retained_vectors', Path(__file__).with_name('retain_vectors.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify()


def pins(result, attempt):
    for relative, digest in result['source_sha256'].items():
        assert sha(ROOT / relative) == digest, relative
    for relative, digest in result['artifacts_sha256'].items():
        assert sha(attempt / relative) == digest, relative


def summary():
    retained_vectors()
    scratch = read(AREA / 'scratch-results.json')
    rtl = read(RTL / 'results.json')
    audit = read(AREA / 'audit.json')
    assert scratch['status'] == 'PASS_FULL_CORPUS_PACKED_SCRATCH'
    assert rtl['status'] == 'PASS_PACKET_SIMULATION'
    assert audit['status'] == 'PASS_VECTORS_RTL_AND_PACKED_SCRATCH'
    scratch_path = ROOT / scratch['selected_report']
    assert audit['checks']['scratch']['selected_result_sha256'] == sha(scratch_path)
    assert {key: value for key, value in scratch.items() if key != 'selected_report'} == read(scratch_path)
    pins(scratch, scratch_path.parent)
    seeds = audit['checks']['rtl']['seed_receipts']
    assert {run['seed'] for run in seeds} == {910232, 910233}
    for run in seeds:
        path = RTL / 'attempts' / run['attempt'] / 'results.json'
        result = read(path)
        assert run['result_sha256'] == sha(path)
        assert result['source_sha256'] == run['source_sha256'] == rtl['source_sha256']
        assert result['artifacts_sha256'] == run['artifact_sha256']
        assert result['vectors_sha256'] == audit['checks']['vectors']['fixture_sha256']
        pins(result, path.parent)
    assert rtl['seed'] == 910233
    assert sha(ROOT / rtl['selected_report']) == next(run['result_sha256'] for run in seeds if run['seed'] == 910233)
    comparisons = [dict(row, cycle_reduction_percent=100 * (1 - row['fast_cycles'] / row['serial_cycles']))
                   for row in rtl['population_comparisons'] if row['population'] == 'actual']
    assert len(comparisons) == 4
    old = read(ROOT / 'fpga/experiments/cu66-v91b/results.json')
    old32 = next(row for row in old['population_comparisons']
                 if row['population'] == 'actual' and row['word_bits'] == 32 and row['stalls'] == 0)
    new32 = next(row for row in comparisons if row['word_bits'] == 32 and row['stalls'] == 0)
    peak_packed = scratch['maxima']['used_bytes']['value']
    peak_dense = scratch['maxima']['dense_reservation_bytes']['value']
    evidence = [AREA / 'scratch-results.json', AREA / 'packet-vectors/index.json',
                AREA / 'audit.json', RTL / 'results.json', RTL / 'historical-vector-storage.json',
                ROOT / 'fpga/experiments/cu66-v91b/results.json']
    sources = [Path(__file__).resolve(), Path(__file__).with_name('retain_vectors.py'), AREA / 'verify_results.py']
    return dict(schema='cu66-v91c-combined-evidence-v1',
                status='PASS_PACKET_RTL_AND_PACKED_SCRATCH_MODEL', parent_commit=PARENT,
                evidence_sha256={str(path.relative_to(ROOT)): sha(path) for path in evidence},
                source_sha256={str(path.relative_to(ROOT)): sha(path) for path in sources},
                scratch_totals=scratch['totals'], scratch_maxima=scratch['maxima'],
                scratch_budget_sweep=scratch['budget_sweep'], scratch_directed_campaigns=scratch['directed_checks'],
                peak_to_peak_capacity_reduction_percent=100 * (1 - peak_packed / peak_dense),
                rtl_packets=16, actual_rtl_packets=12, actual_rtl_source_frames=4,
                rtl_output_comparisons_per_seed=rtl['verdict']['outputs_per_configuration'] * 8,
                rtl_seed_runs=[{key: run[key] for key in ('seed', 'attempt', 'result_sha256', 'directed_checks')} for run in seeds],
                actual_packet_comparisons=comparisons,
                packet_over_context_cost_32_ready=dict(
                    context_cycles=old32['fast_cycles'], packet_cycles=new32['fast_cycles'],
                    additional_cycles=new32['fast_cycles'] - old32['fast_cycles']),
                wire_format_changed=False, quantization_changed=False,
                BR88_chunk_CRC_raw_and_context_control_RTL=True,
                packed_scratch_implemented_in_RTL=False,
                packet_and_scratch_connected_in_one_RTL_top=False,
                synchronous_1R1W_packet_RAM_schedule_qualified=False,
                physical_memory_fit_or_routed_clock_proven=False,
                full_reconstruction_HUD_reference_publication_pipeline_qualified=False,
                live_ESP32_wifi_QSPI_concurrency_measured=False,
                sustained_hardware_30fps_proven=False,
                complete_validated_FPGA_decode_strictly_under10ms_proven=False,
                hardware_or_firmware_deployed=False)


def collect():
    alias = ROOT / read(RTL / 'historical-vector-storage.json')['alias']
    directories = ('docs/cu66-v91c', 'scripts/cu66-v91c',
                   'experiments/python-gamebub-v91c', 'fpga/experiments/cu66-v91c')
    files = [path for relative in directories for path in (ROOT / relative).rglob('*')
             if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc'
             and path != DOCS / 'bundle-manifest.json' and path != alias]
    files.extend(ROOT / path for path in ('docs/gamebub-application-specific-codec-plan.md',
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
        assert manifest['parent_commit'] == PARENT
        assert manifest['sha256'] == collect() and manifest['file_count'] == len(manifest['sha256'])
        print('V91C_BUNDLE_PASS', manifest['file_count'])
        return
    (AREA / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    if args.write_manifest:
        files = collect()
        (DOCS / 'bundle-manifest.json').write_text(json.dumps(dict(
            schema='cu66-v91c-bundle-v1', parent_commit=PARENT, file_count=len(files), sha256=files,
            scope='Checkpoint tree integrity; shared roadmap documents evolve at later commits. Functional/hardware verdicts are separate.',
            excluded=['manifest itself', '__pycache__', '*.pyc',
                      'early failed-run text fixture retained by exact serializer alias',
                      'unrelated marker-recovery experiment']), indent=2) + '\n')
    print(result['status'])


if __name__ == '__main__':
    main()
