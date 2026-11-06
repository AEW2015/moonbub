#!/usr/bin/env python3
"""Paired conditional-work comparisons; not measured speedups or throughput."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v83'
INDEX = ROOT / 'experiments/python-gamebub-v82/native/index.json'
CONTROL = ROOT / 'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'
PAIRS = [
    ('group_buffers_1_to_4', 'serial_groups_current', 'bounded_groups_current_hash1'),
    ('hash_lanes_1_to_4', 'bounded_groups_current_hash1', 'bounded_groups_current'),
    ('add_20_percent_reservation', 'bounded_groups_current', 'bounded_groups_current_reserved20'),
    ('service_current_to_12', 'bounded_groups_current_reserved20', 'bounded_groups_target12_reserved20'),
    ('service_12_to_payload_ideal8', 'bounded_groups_target12_reserved20', 'bounded_groups_target8_reserved20'),
    ('inverse_cost_64_to_256', 'bounded_groups_target8_reserved20', 'bounded_groups_target8_inverse256_reserved20'),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    return dict(min=min(values), median=statistics.median(values), max=max(values), total=sum(values))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--verify', action='store_true')
    args = p.parse_args()
    summary_path = AREA / 'summary.json'
    summary = json.loads(summary_path.read_text())
    assert summary['status'] == 'PASS_CONDITIONAL_MODEL_EVIDENCE'
    reports = [ROOT / name for name in summary['evidence_sha256'] if name.endswith('/results.json')]
    rows = {}
    row_pins = {}
    for report_path in reports:
        assert sha(report_path) == summary['evidence_sha256'][str(report_path.relative_to(ROOT))]
        report = json.loads(report_path.read_text())
        path = report_path.parent / 'frames.jsonl'
        assert sha(path) == report['artifacts_sha256']['frames.jsonl']
        row_pins[str(path.relative_to(ROOT))] = sha(path)
        for line in path.read_text().splitlines():
            r = json.loads(line)
            key = (r['cohort'], r['fid'], r['configuration'])
            assert key not in rows
            rows[key] = r
    assert len(rows) == 3656
    native = json.loads(INDEX.read_text())['frames']
    pairs = []
    for label, before, after in PAIRS:
        values = []
        for frame in native:
            key = frame['cohort'], frame['fid']
            a, b = rows[(*key, before)], rows[(*key, after)]
            for field in ('root', 'seal'):
                assert a[field] == b[field]
            for field in ('reference_read_BL8', 'canonical_write_BL8', 'HUD_read_BL8', 'HUD_write_BL8',
                          'tree_r_words32', 'tree_w_words32', 'map_r_entries', 'map_w_entries',
                          'hash_compression_blocks'):
                assert a['counts'].get(field, 0) == b['counts'].get(field, 0)
            values.append((a['finish_cycles'] - b['finish_cycles']) * 1e-5)
        pairs.append(dict(comparison=label, before=before, after=after, sources=len(values),
                          model_ms_reduction=stats(values),
                          improved=sum(v > 0 for v in values), equal=sum(v == 0 for v in values),
                          regressed=sum(v < 0 for v in values)))
    control = [json.loads(line) for line in CONTROL.read_text().splitlines()]
    cold = max((r for r in control if not r['key']), key=lambda r:r['logical_BL8']['total'])
    commands = cold['logical_BL8']['total']
    assert commands == 68904
    occupied = {}
    for config in summary['configurations']:
        selected = [r for r in rows.values() if r['configuration'] == config['name']]
        occupied[config['name']] = stats([r['audit']['resource_work_cycles']['memory']/r['finish_cycles'] for r in selected])
    result = dict(schema='cu66-v83-paired-tradeoffs-v1', status='PASS',
                  source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),
                                 str(summary_path.relative_to(ROOT)):sha(summary_path),
                                 str(INDEX.relative_to(ROOT)):sha(INDEX), str(CONTROL.relative_to(ROOT)):sha(CONTROL)},
                  frame_artifacts_sha256=row_pins, comparisons=pairs,
                  memory_busy_fraction_by_configuration=occupied,
                  cold_service_requirement=dict(BL8_commands=commands, example_cohort=cold['cohort'], example_fid=cold['fid'],
                                                assumed_clock_mhz=100, budget_cycles=1_000_000,
                                                illustrative_reserved_fraction=0.2, available_cycles=800_000,
                                                strict_necessary_mean_cycles_per_BL8_less_than=800_000/commands,
                                                scope='Necessary service budget only, before fragmentation or unhidden computation.'),
                  old_wire_packet_bytes=stats([f['packet_bytes'] for f in native]),
                  scope=['Paired schedules use identical native content, memory command counts and SHA work.',
                         'Model_ms_reduction positive means a shorter conditional schedule; it is not a physical speedup.',
                         'Memory busy fraction is priced service occupancy, not measured SDRAM utilization.',
                         'Packet sizes describe frozen CU66 input only, not a finished new-profile envelope or ESP32 simulation.'])
    dest = AREA / 'tradeoffs.json'
    if args.verify:
        assert json.loads(dest.read_text()) == result
    else:
        if dest.exists():
            raise FileExistsError(dest)
        dest.write_text(json.dumps(result, indent=2)+'\n')
    print('V83_TRADEOFFS_PASS paired_sources=457 comparisons=6')


if __name__ == '__main__':
    main()
