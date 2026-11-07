#!/usr/bin/env python3
"""Independent brute-force oracle for V95's six-profile plane selector."""
import datetime
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / 'scripts/cu66-v95/run_wire.py'
WIRE_AREA = ROOT / 'experiments/python-gamebub-v95/wire'
SELECTION_AREA = ROOT / 'experiments/python-gamebub-v95/selection'
RECEIPT_POINTER = SELECTION_AREA / 'results.json'
PROFILES = range(6)
POLICIES = ('control', 'P2', 'P4', 'P8', 'E8', 'W8',
            'byte_min', 'work5', 'work15')
STRICT_CAP = 49152


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_runner():
    spec = importlib.util.spec_from_file_location('v95_runner_selection_target', RUNNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def brute_force(frame, common_bytes, baseline_bytes):
    combos = list(itertools.product(PROFILES, repeat=3))
    sizes = {
        combo: common_bytes + sum(len(frame['plane_variants'][axis][combo[axis]])
                                  for axis in range(3))
        for combo in combos
    }
    avoided = {
        combo: sum(frame['palette_stats'][axis][combo[axis]]['avoided_tiles']
                   for axis in range(3))
        for combo in combos
    }
    selected = {
        'control': (0, 0, 0),
        'P2': (1, 1, 1),
        'P4': (2, 2, 2),
        'P8': (3, 3, 3),
        'E8': (4, 4, 4),
        'W8': (5, 5, 5),
        'byte_min': min(combos, key=lambda c: (sizes[c], -avoided[c], c)),
    }
    for policy, percent in (('work5', 105), ('work15', 115)):
        budget = min(STRICT_CAP, baseline_bytes * percent // 100)
        feasible = [combo for combo in combos if sizes[combo] <= budget]
        assert feasible, ('test fixture has no feasible control', baseline_bytes, budget)
        selected[policy] = min(feasible, key=lambda c: (-avoided[c], sizes[c], c))
    return selected, sizes, avoided


def make_frame(rng, scenario):
    # The first fixtures pin boundary and tie behavior; remaining fixtures use
    # seeded varied per-plane costs and gains while keeping the control feasible.
    if scenario == 0:
        lengths = [[1] * 6 for _ in range(3)]
        gains = [[0, 1, 1, 2, 2, 3] for _ in range(3)]
        common = STRICT_CAP - 3
    elif scenario == 1:
        lengths = [[7, 7, 7, 7, 7, 7] for _ in range(3)]
        gains = [[0] * 6 for _ in range(3)]
        common = STRICT_CAP - 21
    elif scenario == 2:  # work5's exact cap threshold: floor(105% * 46811) = 49151
        lengths = [[1, 1, 1, 1, 1, 1] for _ in range(3)]
        gains = [[0, 4, 3, 2, 1, 0] for _ in range(3)]
        common = 46808
    elif scenario == 3:  # work15 threshold immediately below strict cap
        lengths = [[1, 1, 1, 1, 1, 1] for _ in range(3)]
        gains = [[0, 0, 5, 5, 5, 5] for _ in range(3)]
        common = 42738
    elif scenario == 4:  # all palette profiles more expensive than the strict budget
        lengths = [[2, 30000, 30001, 30002, 30003, 30004] for _ in range(3)]
        gains = [[0, 10, 20, 30, 40, 50] for _ in range(3)]
        common = STRICT_CAP - 6
    else:
        lengths = []
        gains = []
        for axis in range(3):
            control = rng.randint(1, 2000)
            lengths.append([control] + [rng.randint(1, 60000) for _ in range(5)])
            gains.append([rng.randint(0, 12000) for _ in range(6)])
        # Keep the exact control baseline in range; spans near both ends of
        # the cap to exercise truncated work budgets and the cap clamp.
        if scenario % 4 == 0:
            upper = STRICT_CAP - sum(x[0] for x in lengths)
            common = rng.randint(max(0, upper - 5000), upper)
        else:
            common = rng.randint(0, STRICT_CAP - sum(x[0] for x in lengths))
    frame = {
        'plane_variants': [[bytes([axis * 17 + profile]) * lengths[axis][profile]
                            for profile in PROFILES] for axis in range(3)],
        'palette_stats': [[{'avoided_tiles': gains[axis][profile],
                            'residual_blocks': max(0, 12000 - gains[axis][profile])}
                           for profile in PROFILES] for axis in range(3)],
    }
    baseline = common + sum(lengths[axis][0] for axis in range(3))
    assert baseline <= STRICT_CAP
    return frame, common, baseline


def compare_campaign():
    pointer_path = WIRE_AREA / 'results.json'
    pointer = json.loads(pointer_path.read_text())
    attempt_path = ROOT / pointer['selected_report']
    attempt = json.loads(attempt_path.read_text())
    frames_path = attempt_path.with_name('frames.jsonl')
    records = [json.loads(line) for line in frames_path.read_text().splitlines()]
    groups = {}
    for row in records:
        groups.setdefault((row['cohort'], row['fid']), {})[row['policy']] = row
    assert len(groups) == attempt['frames'] == 457
    byte_deltas = []
    byte_nonzero = 0
    byte_rate_wins = 0
    work5_deltas, work15_deltas = [], []
    work5_avoided = work15_avoided = 0
    work5_nonzero = work15_nonzero = 0
    for ident, policies in groups.items():
        control = policies['control']
        byte_min = policies['byte_min']
        work5 = policies['work5']
        work15 = policies['work15']
        delta = byte_min['wire_bytes'] - control['wire_bytes']
        byte_deltas.append(delta)
        byte_rate_wins += delta < 0
        byte_nonzero += any(byte_min['profile_indices'])
        work5_deltas.append(work5['wire_bytes'] - control['wire_bytes'])
        work15_deltas.append(work15['wire_bytes'] - control['wire_bytes'])
        work5_avoided += work5['transforms_avoided']
        work15_avoided += work15['transforms_avoided']
        work5_nonzero += any(work5['profile_indices'])
        work15_nonzero += any(work15['profile_indices'])
    summaries = {row['policy']: row for row in attempt['summaries']}
    control_total = summaries['control']['wire_bytes']['total']
    control_blocks = summaries['control']['residual_blocks']
    return dict(selected_attempt=str(attempt_path.relative_to(ROOT)),
                selected_results_sha256=sha(attempt_path),
                selected_frames_sha256=sha(frames_path), frames=len(groups),
                byte_min=dict(rate_win_frames=byte_rate_wins,
                              palette_selected_frames=byte_nonzero,
                              total_delta_bytes=sum(byte_deltas),
                              equal_to_control_frames=sum(delta == 0 for delta in byte_deltas),
                              worse_frames=sum(delta > 0 for delta in byte_deltas)),
                work5=dict(total_delta_bytes=sum(work5_deltas),
                           delta_percent=100 * sum(work5_deltas) / control_total,
                           transforms_avoided=work5_avoided,
                           transforms_avoided_percent=100 * work5_avoided / control_blocks,
                           palette_selected_frames=work5_nonzero,
                           fits_strict_frames=summaries['work5']['fits_49152']),
                work15=dict(total_delta_bytes=sum(work15_deltas),
                            delta_percent=100 * sum(work15_deltas) / control_total,
                            transforms_avoided=work15_avoided,
                            transforms_avoided_percent=100 * work15_avoided / control_blocks,
                            palette_selected_frames=work15_nonzero,
                            fits_strict_frames=summaries['work15']['fits_49152']))


def main():
    runner = load_runner()
    rng = random.Random(0xC06695)
    checks = 0
    for index in range(128):
        frame, common, baseline = make_frame(rng, index)
        expected = brute_force(frame, common, baseline)
        actual = runner.select_policies(frame, common, baseline)
        assert actual == expected, ('selection differs from brute force', index)
        checks += len(expected[1]) + len(expected[0]) + len(expected[2])

    campaign = compare_campaign()
    # A no-rate-win finding is asserted directly from all 457 full-frame rows.
    assert campaign['byte_min']['rate_win_frames'] == 0
    assert campaign['byte_min']['palette_selected_frames'] == 0
    assert campaign['byte_min']['total_delta_bytes'] == 0
    assert campaign['work5']['transforms_avoided'] > 0
    assert campaign['work15']['transforms_avoided'] > campaign['work5']['transforms_avoided']

    source_sha256 = {str(path.relative_to(ROOT)): sha(path)
                     for path in (RUNNER, Path(__file__).resolve())}
    receipt = dict(schema='cu66-v95-selection-oracle-v1', status='PASS_V95_SELECTION_ORACLE',
                   source_sha256=source_sha256,
                   oracle='Enumerate all six-profile x six-profile x six-profile combinations independently; compare exact selections and full size/gain maps.',
                   seed='0xC06695', scenarios=128, combinations_per_scenario=216,
                   assertion_checks=checks, deterministic_edge_cases=5,
                   campaign=campaign)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    immutable_receipt = SELECTION_AREA / 'attempts' / stamp / 'receipt.json'
    immutable_receipt.parent.mkdir(parents=True, exist_ok=False)
    immutable_receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    pointer = dict(receipt, selected_report=str(immutable_receipt.relative_to(ROOT)))
    RECEIPT_POINTER.write_text(json.dumps(pointer, indent=2) + '\n')
    print('V95_SELECTION_PASS', immutable_receipt, 'scenarios=128', 'combinations=27648')


if __name__ == '__main__':
    main()
