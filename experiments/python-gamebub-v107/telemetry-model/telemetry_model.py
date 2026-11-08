#!/usr/bin/env python3
"""Bounded model-only comparison of resettable and validity-masked telemetry."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MASK = (1 << 32) - 1
BINS = 32
TAG_BITS = 3
TAG_MASK = (1 << TAG_BITS) - 1
SEEDS = (0x710701, 0x710702, 0x710703, 0x710704)
CYCLES_PER_SEED = 50_000


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def normalized(op: dict) -> dict:
    return {
        'reset': bool(op.get('reset', False)),
        'abort': bool(op.get('abort', False)),
        'sets': {int(k): int(v) & MASK for k, v in op.get('sets', {}).items()},
        'increments': {int(k): int(v) & MASK for k, v in op.get('increments', {}).items()},
        'capture': bool(op.get('capture', False)),
        'hold': bool(op.get('hold', False)),
    }


def reference_step(state: dict, raw_op: dict) -> dict:
    """Pure operation interpreter; returns a new semantic state each edge."""
    op = normalized(raw_op)
    counts = list(state['counts'])
    snapshot = list(state['snapshot'])
    snapshot_valid = state['snapshot_valid']
    next_tag = state['next_tag']
    snapshot_tag = state['snapshot_tag']
    if op['reset'] or op['abort']:
        return {'counts': [0] * BINS, 'snapshot': [0] * BINS,
                'snapshot_valid': False, 'next_tag': 0, 'snapshot_tag': None}

    # A set wins over an increment targeting the same bin. Distinct bins can
    # update on the same edge. Capture observes all accepted updates this edge.
    for i, value in op['sets'].items():
        if not 0 <= i < BINS:
            raise ValueError(f'set bin out of range: {i}')
        counts[i] = value
    for i, delta in op['increments'].items():
        if not 0 <= i < BINS:
            raise ValueError(f'increment bin out of range: {i}')
        if i not in op['sets']:
            counts[i] = (counts[i] + delta) & MASK
    if op['capture'] and not op['hold']:
        snapshot = list(counts)
        snapshot_valid = True
        snapshot_tag = next_tag
        next_tag = (next_tag + 1) & TAG_MASK
    return {'counts': counts, 'snapshot': snapshot,
            'snapshot_valid': snapshot_valid, 'next_tag': next_tag,
            'snapshot_tag': snapshot_tag}


class ResetDataBaseline:
    """Direct model of data registers synchronously cleared to zero."""
    def __init__(self) -> None:
        self.counts = [0] * BINS
        self.snapshot = [0] * BINS
        self.snapshot_valid = False
        self.next_tag = 0
        self.snapshot_tag = None

    def step(self, raw_op: dict) -> None:
        op = normalized(raw_op)
        if op['reset'] or op['abort']:
            self.counts = [0] * BINS
            self.snapshot = [0] * BINS
            self.snapshot_valid = False
            self.next_tag = 0
            self.snapshot_tag = None
            return
        for i, value in op['sets'].items():
            self.counts[i] = value
        for i, delta in op['increments'].items():
            if i not in op['sets']:
                self.counts[i] = (self.counts[i] + delta) & MASK
        if op['capture'] and not op['hold']:
            self.snapshot[:] = self.counts
            self.snapshot_valid = True
            self.snapshot_tag = self.next_tag
            self.next_tag = (self.next_tag + 1) & TAG_MASK

    def visible(self) -> list[int]:
        return list(self.counts)

    def visible_snapshot(self) -> list[int]:
        return list(self.snapshot) if self.snapshot_valid else [0] * BINS


class LazyValidCandidate:
    """Unreset data plus one resettable valid bit per counter and snapshot."""
    def __init__(self, seed: int) -> None:
        rng = random.Random(seed)
        self.data = [rng.getrandbits(32) for _ in range(BINS)]
        self.valid = [False] * BINS
        self.snapshot_data = [rng.getrandbits(32) for _ in range(BINS)]
        self.snapshot_valid = False
        self.next_tag = 0
        self.snapshot_tag = None

    def step(self, raw_op: dict) -> None:
        op = normalized(raw_op)
        if op['reset'] or op['abort']:
            self.valid = [False] * BINS
            self.snapshot_valid = False
            self.next_tag = 0
            self.snapshot_tag = None
            return
        for i, value in op['sets'].items():
            self.data[i] = value
            self.valid[i] = True
        for i, delta in op['increments'].items():
            if i in op['sets']:
                continue
            base = self.data[i] if self.valid[i] else 0
            self.data[i] = (base + delta) & MASK
            self.valid[i] = True
        if op['capture'] and not op['hold']:
            self.snapshot_data[:] = self.visible()
            self.snapshot_valid = True
            self.snapshot_tag = self.next_tag
            self.next_tag = (self.next_tag + 1) & TAG_MASK

    def visible(self) -> list[int]:
        return [self.data[i] if self.valid[i] else 0 for i in range(BINS)]

    def visible_snapshot(self) -> list[int]:
        return list(self.snapshot_data) if self.snapshot_valid else [0] * BINS


class OutputMaskOnlyNegativeControl(LazyValidCandidate):
    """Intentionally broken: hide all data at reset but retain stale valids."""
    def __init__(self, seed: int) -> None:
        super().__init__(seed)
        self.public_mask = False

    def step(self, raw_op: dict) -> None:
        op = normalized(raw_op)
        if op['reset'] or op['abort']:
            # Incorrectly clears only the public mask, not per-bin valids/data.
            self.public_mask = False
            self.snapshot_valid = False
            self.next_tag = 0
            self.snapshot_tag = None
            return
        super().step(op)
        if op['sets'] or op['increments']:
            self.public_mask = True

    def visible(self) -> list[int]:
        if not self.public_mask:
            return [0] * BINS
        return super().visible()


def directed_prefix() -> list[dict]:
    return [
        {'reset': True},
        {'reset': True, 'sets': {4: 77}, 'increments': {0: 9}, 'capture': True},
        {'increments': {i: 1 for i in range(BINS)}, 'capture': True},
        {'increments': {0: 2}, 'capture': True, 'hold': True},
        {'sets': {0: MASK}, 'capture': True},
        {'increments': {0: 1}, 'capture': True},  # u32 wrap to zero
        {'sets': {1: 0}, 'capture': True},         # capture explicit zero
        {'sets': {2: 7}, 'increments': {2: 9}},   # SET wins same-bin INC
        {'increments': {5: 3}, 'capture': True},   # includes last update
        {'abort': True, 'increments': {7: 4}, 'capture': True},
        {'increments': {7: 1}},
        {'increments': {7: 1}},                   # consecutive same-bin update
        *({'capture': True} for _ in range((1 << TAG_BITS) + 3)),  # tag wrap
        {'capture': True, 'hold': True, 'sets': {3: 91}},
        {'reset': True, 'increments': {31: 123}, 'capture': True},
        {'increments': {31: 1}, 'capture': True},
    ]


def random_op(rng: random.Random) -> dict:
    reset_draw = rng.random()
    reset = reset_draw < 0.00035
    abort = 0.00035 <= reset_draw < 0.00065
    sets: dict[int, int] = {}
    increments: dict[int, int] = {}
    if rng.random() < 0.025:
        for _ in range(1 + (rng.random() < 0.18)):
            sets[rng.randrange(BINS)] = rng.getrandbits(32)
    if rng.random() < 0.085:
        for _ in range(1 + (rng.random() < 0.25)):
            increments[rng.randrange(BINS)] = rng.choice((0, 1, 2, 3, MASK, rng.getrandbits(32)))
    return {'reset': reset, 'abort': abort, 'sets': sets, 'increments': increments,
            'capture': rng.random() < 0.075, 'hold': rng.random() < 0.035}


def state_view(ref: dict, baseline: ResetDataBaseline, candidate: LazyValidCandidate) -> dict:
    return {
        'reference_counts': ref['counts'], 'baseline_counts': baseline.visible(),
        'candidate_counts': candidate.visible(),
        'reference_snapshot': ref['snapshot'] if ref['snapshot_valid'] else [0] * BINS,
        'baseline_snapshot': baseline.visible_snapshot(),
        'candidate_snapshot': candidate.visible_snapshot(),
        'reference_snapshot_valid': ref['snapshot_valid'],
        'baseline_snapshot_valid': baseline.snapshot_valid,
        'candidate_snapshot_valid': candidate.snapshot_valid,
        'reference_snapshot_tag': ref['snapshot_tag'],
        'baseline_snapshot_tag': baseline.snapshot_tag,
        'candidate_snapshot_tag': candidate.snapshot_tag,
        'reference_next_tag': ref['next_tag'], 'baseline_next_tag': baseline.next_tag,
        'candidate_next_tag': candidate.next_tag,
    }


def run_seed(seed: int, cycles: int) -> dict:
    rng = random.Random(seed)
    ref = {'counts': [0] * BINS, 'snapshot': [0] * BINS,
           'snapshot_valid': False, 'next_tag': 0, 'snapshot_tag': None}
    baseline = ResetDataBaseline()
    candidate = LazyValidCandidate(seed ^ 0xA5A55A5A)
    ops = iter(directed_prefix())
    counts = {'cycles': 0, 'bin_visibility_compares': 0, 'accepted_set_events': 0,
        'accepted_increment_events': 0, 'reset_abort_edges': 0, 'reset_abort_update_conflicts': 0,
        'capture_requests': 0, 'effective_captures': 0, 'held_capture_requests': 0,
        'capture_after_update': 0, 'capture_all_zero': 0, 'captured_zero_bins': 0,
        'same_bin_consecutive_edges': 0, 'counter_wraps': 0, 'lazy_first_increment': 0,
        'same_bin_set_increment_conflicts': 0, 'tag_wraps': 0, 'all_bins_seen_valid': set()}
    prev_updated: set[int] = set()
    for cycle in range(cycles):
        try:
            raw_op = next(ops)
        except StopIteration:
            raw_op = random_op(rng)
        op = normalized(raw_op)
        counts['cycles'] += 1
        resetish = op['reset'] or op['abort']
        counts['capture_requests'] += int(op['capture'])
        if resetish:
            counts['reset_abort_edges'] += 1
            counts['reset_abort_update_conflicts'] += int(bool(op['sets'] or op['increments'] or op['capture']))
        else:
            counts['accepted_set_events'] += len(op['sets'])
            counts['accepted_increment_events'] += sum(i not in op['sets'] for i in op['increments'])
            counts['same_bin_set_increment_conflicts'] += len(set(op['sets']) & set(op['increments']))
            current_updates = set(op['sets']) | (set(op['increments']) - set(op['sets']))
            counts['same_bin_consecutive_edges'] += len(current_updates & prev_updated)
            counts['lazy_first_increment'] += sum(1 for i in op['increments'] if i not in op['sets'] and not candidate.valid[i])
            for i, delta in op['increments'].items():
                if i not in op['sets']:
                    old = candidate.data[i] if candidate.valid[i] else 0
                    counts['counter_wraps'] += int(old + delta > MASK)
            if op['capture'] and op['hold']:
                counts['held_capture_requests'] += 1
            if op['capture'] and not op['hold']:
                counts['effective_captures'] += 1
                counts['capture_after_update'] += int(bool(current_updates))
        before_next_tag = ref['next_tag']
        new_ref = reference_step(ref, op)
        baseline.step(op)
        candidate.step(op)
        if not resetish and op['capture'] and not op['hold'] and before_next_tag == TAG_MASK:
            counts['tag_wraps'] += 1
        ref = new_ref
        view = state_view(ref, baseline, candidate)
        for key in ('reference_counts', 'reference_snapshot', 'reference_snapshot_valid',
                    'reference_snapshot_tag', 'reference_next_tag'):
            refval = view[key]
            if key == 'reference_counts':
                if refval != view['baseline_counts'] or refval != view['candidate_counts']:
                    return mismatch_result(seed, cycle, op, view, counts)
                counts['bin_visibility_compares'] += 2 * BINS
                counts['all_bins_seen_valid'].update(i for i, value in enumerate(refval)
                    if (baseline.counts[i] != 0 or candidate.valid[i]))
            elif key == 'reference_snapshot':
                if refval != view['baseline_snapshot'] or refval != view['candidate_snapshot']:
                    return mismatch_result(seed, cycle, op, view, counts)
            elif key == 'reference_snapshot_valid':
                if refval != view['baseline_snapshot_valid'] or refval != view['candidate_snapshot_valid']:
                    return mismatch_result(seed, cycle, op, view, counts)
            elif key == 'reference_snapshot_tag':
                if refval != view['baseline_snapshot_tag'] or refval != view['candidate_snapshot_tag']:
                    return mismatch_result(seed, cycle, op, view, counts)
            else:
                if refval != view['baseline_next_tag'] or refval != view['candidate_next_tag']:
                    return mismatch_result(seed, cycle, op, view, counts)
        if op['capture'] and not resetish and not op['hold']:
            counts['captured_zero_bins'] += sum(v == 0 for v in ref['snapshot'])
            counts['capture_all_zero'] += int(all(v == 0 for v in ref['snapshot']))
        prev_updated = set() if resetish else set(op['sets']) | (set(op['increments']) - set(op['sets']))
    counts['all_bins_seen_valid'] = len(counts['all_bins_seen_valid'])
    directed_ok = all(counts[k] > 0 for k in ('reset_abort_update_conflicts', 'effective_captures',
        'held_capture_requests', 'capture_after_update', 'captured_zero_bins', 'same_bin_consecutive_edges',
        'counter_wraps', 'lazy_first_increment', 'same_bin_set_increment_conflicts', 'tag_wraps'))
    return {'seed': seed, 'status': 'PASS' if directed_ok else 'FAIL_DIRECTED_COVERAGE', 'counts': counts,
            'directed_coverage_pass': directed_ok}


def mismatch_result(seed: int, cycle: int, op: dict, view: dict, counts: dict) -> dict:
    return {'seed': seed, 'status': 'FAIL_MODEL_MISMATCH', 'mismatch': {
        'cycle': cycle, 'operation': op, 'state': view}, 'counts': counts}


def run_negative_control() -> dict:
    ref = {'counts': [0] * BINS, 'snapshot': [0] * BINS,
           'snapshot_valid': False, 'next_tag': 0, 'snapshot_tag': None}
    baseline = ResetDataBaseline()
    broken = OutputMaskOnlyNegativeControl(seed=0xBAD0)
    sequence = [
        {'sets': {0: 0xA0B0C0D0}},
        {'reset': True},
        {'increments': {0: 1}},
    ]
    for cycle, raw_op in enumerate(sequence):
        op = normalized(raw_op)
        ref = reference_step(ref, op)
        baseline.step(op)
        broken.step(op)
        if ref['counts'] != baseline.visible() or ref['counts'] != broken.visible():
            return {'status': 'EXPECTED_FAIL_OUTPUT_MASK_ONLY_STALE_INCREMENT',
                'expected_failure_observed': True,
                'counterexample': {'cycle': cycle, 'operation': op,
                    'expected_bin0': ref['counts'][0], 'broken_bin0': broken.visible()[0],
                    'output_mask_only': broken.public_mask,
                    'stale_private_data_bin0': broken.data[0], 'stale_valid_bin0': broken.valid[0]}}
    return {'status': 'ERROR_NEGATIVE_CONTROL_SURVIVED', 'expected_failure_observed': False}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, default=HERE / 'results.json')
    args = ap.parse_args()
    start = time.monotonic()
    runs = [run_seed(seed, CYCLES_PER_SEED) for seed in SEEDS]
    negative = run_negative_control()
    source_paths = {
        'telemetry_model': Path(__file__).resolve(),
        'fanout_attribution_summary': ROOT / 'experiments/python-gamebub-v107/fanout-attribution/20261108T075501402480Z/summary.json',
        'v106_child_telemetry_rtl': ROOT / 'fpga/experiments/cu66-v106-telemetry/br88_pipeline_v91h.sv',
    }
    source_hashes = {name: sha(path) for name, path in source_paths.items() if path.is_file()}
    passed = (all(x['status'] == 'PASS' for x in runs)
        and negative['expected_failure_observed'] is True
        and len(source_hashes) == len(source_paths))
    result = {
        'schema': 'v107-telemetry-reset-free-counter-model-v1',
        'status': 'PASS_MODEL_ONLY' if passed else 'FAIL',
        'scope': 'Pure-Python finite model only; not RTL, full current-source equivalence, synthesis, timing, resource gain, CDC, or hardware evidence.',
        'model': {'bins': BINS, 'counter_bits': 32, 'tag_bits': TAG_BITS,
            'cycles_per_seed': CYCLES_PER_SEED, 'seeds': list(SEEDS),
            'total_cycles': sum(x['counts']['cycles'] for x in runs),
            'arbitrary_initial_candidate_counter_and_snapshot_data': True,
            'candidate_counter_resettable_state': 'one valid bit per bin',
            'candidate_snapshot_resettable_state': 'snapshot_valid plus finite sequence control',
            'public_visibility': 'zero when per-bin valid is clear; snapshot zero when snapshot_valid is clear',
            'priority': ['reset or abort dominates every update, capture, and hold action',
                         'otherwise per-bin SET dominates same-bin INCREMENT',
                         'distinct bins may update on one edge',
                         'accepted update occurs before capture, so capture includes this edge event',
                         'hold dominates capture and preserves prior snapshot while live counters update'],
            'counter_wrap': 'modulo 2^32', 'first_increment_after_invalidation': 'zero_base + delta modulo 2^32',
            'snapshot_semantics': 'atomic copy of all publicly visible bins after accepted updates; captures advance a modulo-2^3 tag; reset/abort invalidates snapshot and resets next tag to zero; hold leaves snapshot and tag unchanged',
            'tag_wrap_limitation': 'tag is finite and can repeat after eight effective captures; consumers must use snapshot_valid and protocol ownership, not assume global uniqueness'},
        'runs': runs, 'negative_control': negative,
        'input_sha256': source_hashes,
        'elapsed_seconds': round(time.monotonic() - start, 3),
        'resource_bound': {'max_clock_edges': 200000, 'bins_compared_per_clock_per_candidate': BINS,
            'numpy_used': False, 'serialized_trace_storage': False},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': result['status'], 'runs': [
        {'seed': x['seed'], 'status': x['status'], 'counts': x['counts']} for x in runs],
        'negative_control': negative, 'elapsed_seconds': result['elapsed_seconds'],
        'output': str(args.output)}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
