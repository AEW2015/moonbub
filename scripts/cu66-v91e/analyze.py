#!/usr/bin/env python3
"""Analyze reconciled V91e occupancy without claiming full decode latency."""
import hashlib
import json
from pathlib import Path

import telemetry

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91e'
RTL = ROOT / 'fpga/experiments/cu66-v91e'
SEEDS = (910432, 910433)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected(seed):
    choices = []
    for path in (RTL / 'pipeline-attempts').glob('*/results.json'):
        result = json.loads(path.read_text())
        if result.get('seed') == seed and result['status'] == 'PASS_RECONCILED_TELEMETRY_WITH_FROZEN_V91D_PARITY':
            choices.append((path, result))
    assert choices
    return sorted(choices, key=lambda pair: pair[0].parent.name)[-1]


def analyze():
    vector_rows = telemetry.cases()
    contract = json.loads(telemetry.CONTRACT_PATH.read_text())
    reports = []
    pins = {str(path.relative_to(ROOT)): sha(path) for path in (
        Path(__file__).resolve(), Path(__file__).with_name('telemetry.py'), telemetry.CONTRACT_PATH,
        AREA / 'vectors/index.json', AREA / 'vectors/coefficients.jsonl.gz')}
    source_set = None
    for seed in SEEDS:
        path, report = selected(seed)
        if source_set is None:
            source_set = report['source_sha256']
        assert source_set == report['source_sha256']
        for relative, digest in report['source_sha256'].items():
            assert sha(ROOT / relative) == digest
        for relative, digest in report['artifacts_sha256'].items():
            assert sha(path.parent / relative) == digest
        rows = [json.loads(line) for line in path.with_name('simulation.jsonl').read_text().splitlines()]
        records = telemetry.validate_rows(rows, vector_rows)
        assert telemetry.compare_v91d(records, seed) == report['baseline_v91d']
        groups = telemetry.aggregate(records)
        assert groups == report['population_totals']
        tile_summary = telemetry.validate_tiles(path.parent / report['tile_trace']['path'], records, vector_rows)
        assert tile_summary == json.loads(path.with_name('tile-summary.json').read_text())
        sources = {}
        for row in records:
            if not row['id'].startswith('actual:') or row['serial_clear']:
                continue
            identity = ':'.join(row['id'].split(':')[:3])
            key = identity, row['memory_profile']
            target = sources.setdefault(key, dict(source=identity, memory_profile=row['memory_profile'], chunks=0,
                request_to_coefficient_done_cycles=0, post_chunk_last_byte_coefficient_done_cycles=0,
                write_ack_wait_cycles=0, read_ack_wait_cycles=0, dense_accepted_cycles=0, dense_hold_cycles=0))
            target['chunks'] += 1
            target['request_to_coefficient_done_cycles'] += row['cycles']
            target['post_chunk_last_byte_coefficient_done_cycles'] += row['cycles'] - row['observability']['timestamps']['last_input']
            target['write_ack_wait_cycles'] += row['observability']['scratch_state_cycles'][9]
            target['read_ack_wait_cycles'] += row['observability']['scratch_state_cycles'][11]
            target['dense_accepted_cycles'] += row['dense_coefficients']
            target['dense_hold_cycles'] += row['output_stalls']
        for target in sources.values():
            assert target['chunks'] == 3
            target['fixed_other_work_delete_write_ACK_sensitivity_cycles'] = (
                target['request_to_coefficient_done_cycles'] - target['write_ack_wait_cycles'])
            target['sensitivity_is_achievable_or_certified_bound'] = False
        slow = [target for target in sources.values() if target['memory_profile'] == 1]
        assert len(slow) == 5
        worst = max((row for row in records if row['id'].startswith('actual:') and not row['serial_clear']
                     and row['memory_profile'] == 1), key=lambda row: row['cycles'])
        reports.append(dict(seed=seed, result_path=str(path.relative_to(ROOT)), result_sha256=sha(path),
                            baseline=report['baseline_v91d'], population_totals=groups,
                            source_services=list(sources.values()),
                            slow_source_sums_at_or_above_reference_1M=sum(target['request_to_coefficient_done_cycles'] >= 1000000 for target in slow),
                            worst_actual_slow_packet=dict(id=worst['id'], cycles=worst['cycles'], used_bytes=worst['used_bytes']),
                            tile_trace=report['tile_trace'], tile_delivery_summary=tile_summary))
    return dict(schema='cu66-v91e-stage-and-fence-analysis-v1', status='PASS_RECONCILED_IDENTIFIED_STAGE_WORK',
                source_sha256=pins, seed_runs=reports,
                current_endpoint=contract['current_endpoint'],
                full_frame_publication_timestamp=None, full_frame_decode_latency_measured=False,
                primary_findings=[
                    'Original17 case/config metrics are exactly unchanged at each matched seed; instrumentation is not a scheduling speedup.',
                    'Scratch state occupancy is an exclusive partition. Packet state occupancy is a separate partition of the same interval; stall counters overlap both.',
                    'Dense delivery/consumer hold, ACK waits and merge/control all contribute. V91f assembler overlap alone must not be assumed to close the full-frame budget.',
                    'C3/f28 extends the memory/sparse-write stress selection without adding an independent game/source family.',
                    'Deleting measured WRITE_WAIT edges while fixing all other work is sensitivity arithmetic only; it is neither an achievable schedule nor a certified architectural bound.'
                ],
                achieved_frequency_or_physical_memory_service=False,
                hardware_30fps_or_complete_under10ms_proven=False)


if __name__ == '__main__':
    result = analyze()
    (AREA / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'])
