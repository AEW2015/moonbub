#!/usr/bin/env python3
"""Deterministic brute-force checks for the bounded V92 selector."""
import datetime
import hashlib
import importlib.util
import itertools
import json
import platform
from pathlib import Path
import random
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
WIRE_PATH = ROOT / 'scripts/cu66-v92/run_wire.py'
OUT_ROOT = ROOT / 'experiments/python-gamebub-v92/selection/attempts'


def load_wire():
    spec = importlib.util.spec_from_file_location('cu66_v92_wire_selection_test', WIRE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exhaustive(planes, fixed):
    """Independent direct Cartesian-product oracle; tuple layout matches wire API."""
    result = []
    for choice in itertools.product(*planes):
        result.append((
            fixed + sum(c['bytes'] for c in choice),
            sum(c['ab_decisions'] for c in choice),
            sum(c['ab_renorm'] for c in choice),
            sum(c['br_bits'] for c in choice),
            sum(c['requested_mask'] << (4 * axis) for axis, c in enumerate(choice)),
        ))
    return result


def oracle_pick(states, budget, byte_min):
    feasible = [state for state in states if state[0] <= budget]
    if not feasible:
        return None
    if byte_min:
        return min(feasible, key=lambda s: (s[0], s[1], s[2], s[3], s[4]))
    return min(feasible, key=lambda s: (s[1], s[2], s[3], s[4], s[0]))


def synthetic_planes(seed):
    rng = random.Random(seed)
    planes = []
    for axis in range(3):
        choices = []
        base = (axis + 1) * 3
        # Masks 0 and 1 are an intentional exact tie; the selector mask is the
        # final deterministic tie-break field in the work objective.
        for mask in range(16):
            if mask in (0, 1):
                byte_count, decisions, renorm, br_bits = base + 10, 4, 2, 7
            elif mask == 15:
                # Strictly dominated by mask 0 in every additive cost.
                byte_count, decisions, renorm, br_bits = base + 50, 40, 20, 70
            else:
                byte_count = base + rng.randint(0, 35)
                decisions = rng.randint(0, 18)
                renorm = rng.randint(0, 12)
                br_bits = rng.randint(0, 30)
            choices.append(dict(bytes=byte_count, ab_decisions=decisions,
                                ab_renorm=renorm, br_bits=br_bits,
                                requested_mask=mask))
        planes.append(choices)
    return planes


def budgets_for(states):
    sizes = sorted({state[0] for state in states})
    if len(sizes) > 12:
        indexes = {round(i * (len(sizes) - 1) / 11) for i in range(12)}
        sizes = [sizes[i] for i in sorted(indexes)]
    # Exercise infeasible, exact-fit, just-below/above, and broad-cap cases.
    budgets = {sizes[0] - 1, sizes[-1], sizes[-1] + 1}
    for size in sizes:
        budgets.update((size - 1, size, size + 1))
    return sorted(budgets)


def run():
    wire = load_wire()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = OUT_ROOT / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    source_paths = [Path(__file__).resolve(), WIRE_PATH]
    source_pins = {str(path.relative_to(ROOT)): sha(path) for path in source_paths}
    for path in source_paths:
        dest = out / 'sources' / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())

    report = dict(schema='cu66-v92-selection-bruteforce-v1', status='FAIL',
                  source_sha256=source_pins, python=platform.python_version(),
                  deterministic_seeds=list(range(9200, 9250)), cases=50,
                  planes_per_case=3, options_per_plane=16,
                  cartesian_candidates_per_case=4096,
                  objective_work=['ab_decisions', 'ab_renorm', 'br_bits', 'mask', 'bytes'],
                  objective_byte_min=['bytes', 'ab_decisions', 'ab_renorm', 'br_bits', 'mask'],
                  expanded_state_bound=4368, peak_state_bound=4096,
                  latency_claim=False)
    rows = []
    try:
        for seed in report['deterministic_seeds']:
            planes = synthetic_planes(seed)
            fixed = 11 + (seed % 7)
            all_states = exhaustive(planes, fixed)
            frontier, expanded, peak = wire.pareto(planes, fixed)
            assert len(all_states) == 4096
            assert expanded <= 4368, (seed, expanded)
            assert peak <= 4096, (seed, peak)
            budgets = budgets_for(all_states)
            seed_rows = []
            for budget in budgets:
                for byte_min in (False, True):
                    expected = oracle_pick(all_states, budget, byte_min)
                    if expected is None:
                        try:
                            wire.pick(frontier, budget, byte_min)
                        except AssertionError:
                            selected = None
                        else:
                            raise AssertionError(('selector accepted infeasible cap', seed, budget, byte_min))
                    else:
                        selected = wire.pick(frontier, budget, byte_min)
                        assert selected == expected, (seed, budget, byte_min, selected, expected)
                    seed_rows.append(dict(budget=budget, byte_min=byte_min,
                                          selected=list(selected) if selected is not None else None))
            # Explicitly assert the work and byte-min winners at a tight cap
            # equal to the smallest complete candidate size.
            tight = min(state[0] for state in all_states)
            for byte_min in (False, True):
                expected = oracle_pick(all_states, tight, byte_min)
                selected = wire.pick(frontier, tight, byte_min)
                assert selected == expected, (seed, 'tight', byte_min, selected, expected)
            rows.append(dict(seed=seed, fixed_bytes=fixed, exhaustive_count=len(all_states),
                             frontier_count=len(frontier), expanded_states=expanded,
                             peak_states=peak, budgets_checked=len(budgets),
                             objective_comparisons=len(budgets) * 2,
                             tight_cap=tight, checks=seed_rows))

        assert source_pins == {str(path.relative_to(ROOT)): sha(path) for path in source_paths}, \
            'selection sources changed during execution'
        report.update(status='PASS', total_candidates=50 * 4096,
                      total_budget_objective_comparisons=sum(r['objective_comparisons'] for r in rows),
                      total_budget_checks=sum(r['budgets_checked'] for r in rows),
                      expanded_states_max=max(r['expanded_states'] for r in rows),
                      peak_states_max=max(r['peak_states'] for r in rows),
                      rows_file='cases.json')
        (out / 'cases.json').write_text(json.dumps(rows, indent=2) + '\n')
    except BaseException as exc:
        report['failure'] = repr(exc)
        (out / 'cases.json').write_text(json.dumps(rows, indent=2) + '\n')
        raise
    finally:
        report['artifact_sha256'] = {
            str(path.relative_to(out)): sha(path)
            for path in out.rglob('*') if path.is_file() and path.name != 'results.json'
        }
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        print('V92_SELECTION_REPORT', out / 'results.json', report['status'], flush=True)


if __name__ == '__main__':
    run()
