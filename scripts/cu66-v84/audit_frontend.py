#!/usr/bin/env python3
"""Independently aggregate V84 native primitives and assumed isolated costs."""
import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v84'
ENTROPY = AREA / 'entropy'
INDEX = ENTROPY / 'index.json'
DATA = ENTROPY / 'data.py'
RUNNER = ROOT / 'scripts/cu66-v84/prototype_pipeline.py'
OUT = AREA / 'frontend-audit.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def distribution(values):
    return {'min': min(values), 'median': statistics.median(values), 'max': max(values)}


def main():
    index = json.loads(INDEX.read_text())
    runner = load('cu84_frontend_runner', RUNNER)
    data = load('cu84_frontend_entropy_data', DATA)
    totals = {field: 0 for field in data.FIELDS}
    calculated = {'LOW': [], 'HIGH': []}
    frame_records = []
    for n, frame in enumerate(data.iter_frames()):
        meta = index['frames'][n]
        assert (frame['cohort'], frame['ordinal'], frame['fid']) == (meta['cohort'], meta['ordinal'], meta['fid'])
        frame_totals = {field: sum(tile[field] for tile in frame['tile_work']) for field in data.FIELDS}
        assert frame_totals == meta['totals']
        assert frame_totals['raw_bits'] == frame_totals['renorm'] + 216
        assert frame_totals['header_bytes'] == 84
        assert frame_totals['prob_init'] == 1056
        assert frame_totals['emits'] == 8100
        for field, value in frame_totals.items():
            totals[field] += value
        frame_records.append({'cohort': frame['cohort'], 'ordinal': frame['ordinal'],
                              'fid': frame['fid'], 'totals': frame_totals})
        for label, weights in (('LOW', runner.LOW), ('HIGH', runner.HIGH)):
            cycles = sum(tile[field] * weight for tile in frame['tile_work']
                         for field, weight in weights.items())
            calculated[label].append(cycles / 100_000)  # assumed 100 MHz => ms
    assert len(frame_records) == index['record_count'] == 457
    assert totals == index['totals']

    slots = {}
    for count in (64, 8, 2):
        current = 4096 + count * (64 + 192 + 128)
        v83 = 4096 + count * (64 + 192)
        slots[str(count)] = {
            'v84_bytes': current,
            'v83_reference_plus_inverse_bytes': v83,
            'v84_added_coefficient_reservation_bytes': current - v83,
            'v84_formula': '4096 + slots * (64 + 192 + 128)',
            'v83_fair_comparison_formula': '4096 + slots * (64 + 192); coefficient reservation excluded',
        }
    weights = {}
    for label, values in calculated.items():
        weights[label] = {
            'isolated_work_ms': distribution(values),
            'frames_under_10ms': sum(value < 10 for value in values),
            'frames': len(values),
            'clock_mhz_assumption': 100,
            'interpretation': 'Counter-weight sum converted to milliseconds; assumed isolated entropy work, not measured or end-to-end timing.',
        }
    hashes = {
        'experiments/python-gamebub-v84/entropy/index.json': sha(INDEX),
        'experiments/python-gamebub-v84/entropy/data.py': sha(DATA),
        'scripts/cu66-v84/prototype_pipeline.py': sha(RUNNER),
        'scripts/cu66-v84/audit_frontend.py': sha(Path(__file__)),
    }
    report = {
        'schema': 'cu66-v84-frontend-audit-v1',
        'status': 'PASS',
        'records': len(frame_records),
        'native_primitive_totals': totals,
        'checks': {
            'raw_bits_equals_renorm_plus_216_per_frame': True,
            'header_bytes_84_per_frame': True,
            'prob_init_1056_per_frame': True,
            'emits_8100_per_frame': True,
            'rice_values': 'omitted; not independently derivable from the frame index alone',
        },
        'assumed_isolated_entropy_work': weights,
        'logical_stage_allocation': slots,
        'source_sha256': hashes,
        'scope': 'Counts are independently summed from retained per-tile observations and checked against the native frame index. Weighted times are isolated model estimates under runner LOW/HIGH cycle assumptions at 100 MHz; they are not measurements or end-to-end completion claims.',
    }
    OUT.write_text(json.dumps(report, indent=2) + '\n')
    print(f"V84_FRONTEND_AUDIT_PASS frames={len(frame_records)} under10_low={weights['LOW']['frames_under_10ms']} under10_high={weights['HIGH']['frames_under_10ms']}")


if __name__ == '__main__':
    main()
