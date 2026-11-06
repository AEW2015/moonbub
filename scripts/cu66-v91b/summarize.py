#!/usr/bin/env python3
"""Bind selected V91b audits/results; optionally write/check the bundle manifest."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91b'
DOCS = ROOT / 'docs/cu66-v91b'
PARENT = '42f84090d0f93ea2711270e29b3d5e38791a8612'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(relative):
    return json.loads((ROOT / relative).read_text())


def summary():
    spec = importlib.util.spec_from_file_location('v91b_retained_vectors', Path(__file__).with_name('retain_vectors.py'))
    retained = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(retained)
    storage = retained.verify()
    model = read('experiments/python-gamebub-v91b/results.json')
    packet = read('experiments/python-gamebub-v91b/packet-checks.json')
    rtl = read('fpga/experiments/cu66-v91b/results.json')
    audit = read('experiments/python-gamebub-v91b/audit.json')
    assert model['status'] == 'PASS_FULL_CORPUS_SPARSE_CONTEXT_MODEL'
    assert packet['status'] == audit['status'] == 'PASS'
    assert rtl['status'] == 'PASS_CONTEXT_SIMULATION'
    assert audit['model']['public_result_sha256'] == sha(AREA / 'results.json')
    assert audit['rtl']['selected']['result_sha256'] == sha(ROOT / rtl['selected_report'])
    assert audit['packet_checks']['details_sha256'] == packet['details_sha256']
    seed_runs = [audit['rtl']['selected'], *audit['rtl']['repeated_seed_runs']]
    assert {run['seed'] for run in seed_runs} == {910132, 910133}
    for run in seed_runs:
        result = read(run['path'])
        assert run['result_sha256'] == sha(ROOT / run['path'])
        assert result['source_sha256'] == rtl['source_sha256']
        assert result['verdict']['directed_checks'] == 172
        for path, digest in result['source_sha256'].items():
            assert sha(ROOT / path) == digest
    for evidence in (model, packet):
        for path, digest in evidence['source_sha256'].items():
            assert sha(ROOT / path) == digest
    comparisons = [row for row in rtl['population_comparisons'] if row['population'] == 'actual']
    assert len(comparisons) == 4
    for row in comparisons:
        row['cycle_reduction_percent'] = 100 * (1 - row['fast_cycles'] / row['serial_cycles'])
    v91 = read('fpga/experiments/cu66-v91/results.json')
    old = next(row for row in v91['population_comparisons']
               if row['population'] == 'actual' and row['word_bits'] == 32 and row['stalls'] == 0)
    new = next(row for row in comparisons if row['word_bits'] == 32 and row['stalls'] == 0)
    report_paths = ('experiments/python-gamebub-v91b/results.json',
                    'experiments/python-gamebub-v91b/packet-checks.json',
                    'experiments/python-gamebub-v91b/audit.json',
                    'experiments/python-gamebub-v91b/context-vectors/index.json',
                    'fpga/experiments/cu66-v91b/results.json',
                    'fpga/experiments/cu66-v91/results.json',
                    'fpga/experiments/cu66-v91b/historical-vector-storage.json')
    return dict(schema='cu66-v91b-combined-evidence-v1',
                status='PASS_FULL_CORPUS_AND_CLOCKED_CONTEXT_COMPONENT', parent_commit=PARENT,
                evidence_sha256={path: sha(ROOT / path) for path in report_paths},
                source_sha256={str(path.relative_to(ROOT)): sha(path) for path in
                    (Path(__file__).resolve(), AREA / 'verify_results.py', Path(__file__).with_name('retain_vectors.py'))},
                historical_text_vectors_reconstructible=len(storage['aliases']),
                model_totals=model['totals'], model_directed_checks=model['directed_checks'],
                packet_checks={key: packet[key] for key in ('cases', 'accepted', 'rejected')},
                rtl_seeds=[{key: run[key] for key in ('seed', 'path', 'result_sha256', 'directed_checks')}
                           for run in sorted(seed_runs, key=lambda row: row['seed'])],
                rtl_contexts=rtl['vector_cases'], actual_rtl_contexts=rtl['actual_contexts'],
                actual_rtl_source_frames=4, rtl_configurations_per_seed=8,
                rtl_output_comparisons_per_seed=rtl['verdict']['outputs_per_configuration'] * 8,
                real_context_comparisons=comparisons,
                explicit_adapter_cost_32_ready=dict(
                    v91_parser_cycles=old['fast_cycles'], v91b_context_cycles=new['fast_cycles'],
                    added_cycles=new['fast_cycles'] - old['fast_cycles'],
                    added_percent=100 * (new['fast_cycles'] / old['fast_cycles'] - 1)),
                unchanged_wire_format=True, new_quantization=False,
                full_pixel_HUD_publication_pipeline_executed=False,
                packet_CRC_and_raw_RTL_implemented=False,
                actual_ESP32_wifi_QSPI_concurrency_measured=False,
                routed_frequency_and_memory_fit_proven=False,
                sustained_hardware_30fps_proven=False,
                complete_validated_FPGA_decode_under10ms_proven=False,
                firmware_or_bitstream_deployed=False)


def collect():
    storage = read('fpga/experiments/cu66-v91b/historical-vector-storage.json')
    aliases = {ROOT / path for path in storage['aliases']}
    directories = ('docs/cu66-v91b', 'scripts/cu66-v91b',
                   'experiments/python-gamebub-v91b', 'fpga/experiments/cu66-v91b')
    paths = [path for relative in directories for path in (ROOT / relative).rglob('*')
             if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc'
             and path != DOCS / 'bundle-manifest.json' and path not in aliases]
    paths.extend(ROOT / relative for relative in (
        'docs/gamebub-application-specific-codec-plan.md',
        'docs/gamebub-v91-v110-development-plan.md',
        'docs/literature-review-2026-11-06/README.md'))
    return {str(path.relative_to(ROOT)): sha(path) for path in sorted(paths)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-manifest', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    report = summary()
    destination = AREA / 'summary.json'
    if args.check:
        assert json.loads(destination.read_text()) == report
        manifest = json.loads((DOCS / 'bundle-manifest.json').read_text())
        assert manifest['parent_commit'] == PARENT and manifest['sha256'] == collect()
        assert manifest['file_count'] == len(manifest['sha256'])
        print('V91B_BUNDLE_PASS', manifest['file_count'])
        return
    destination.write_text(json.dumps(report, indent=2) + '\n')
    if args.write_manifest:
        files = collect()
        (DOCS / 'bundle-manifest.json').write_text(json.dumps(dict(
            schema='cu66-v91b-bundle-v1', parent_commit=PARENT, file_count=len(files), sha256=files,
            scope='Checkpoint tree integrity, not a hardware or performance verdict; shared roadmap documents may evolve on later commits.',
            excluded=['manifest itself', '__pycache__', '*.pyc',
                      'two duplicate failed-attempt text vectors retained by exact serializer aliases',
                      'unrelated marker-recovery experiment']), indent=2) + '\n')
    print(report['status'])


if __name__ == '__main__':
    main()
