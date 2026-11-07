#!/usr/bin/env python3
"""Independent bounded-search checks for the V93 four-method selector."""
import datetime
import hashlib
import importlib.util
import itertools
import json
import platform
from pathlib import Path
import random
import signal
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
WIRE_PATH = ROOT / 'scripts/cu66-v93/run_wire.py'
OUT_ROOT = ROOT / 'experiments/python-gamebub-v93/selection/attempts'
ACTIVE = 12
METHODS = 4


def load_wire():
    name = 'cu66_v93_wire_selection_test'
    spec = importlib.util.spec_from_file_location(name, WIRE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_choices(choices):
    assert len(choices) == ACTIVE
    for context, options in enumerate(choices):
        assert len(options) == METHODS, (context, len(options))
        for method, cost in enumerate(options):
            assert len(cost) == 4, (context, method, cost)
            assert all(isinstance(v, int) and v >= 0 for v in cost), (context, method, cost)


def exhaustive(choices, fixed, budget):
    """Direct Cartesian-product reference, independent of the beam pruning."""
    rows = []
    for selector in itertools.product(range(METHODS), repeat=ACTIVE):
        costs = [choices[i][method] for i, method in enumerate(selector)]
        state = (
            fixed + sum(c[0] for c in costs),
            sum(c[1] for c in costs),
            sum(c[2] for c in costs),
            sum(c[3] for c in costs),
            sum(method << (2 * i) for i, method in enumerate(selector)),
        )
        if state[0] <= budget:
            rows.append(state)
    return rows


def oracle_pick(states, work_key):
    return min(states, key=work_key) if states else None


def sparse_choices(seed):
    """Four active contexts and eight zero-identical contexts: 4**4 choices."""
    rng = random.Random(seed)
    choices = []
    for context in range(ACTIVE):
        if context >= 4:
            choices.append([(0, 0, 0, 0)] * METHODS)
            continue
        options = []
        for method in range(METHODS):
            # Deliberate ties and dominated alternatives exercise stable tie
            # breaking without making the generated arrays negative.
            if method == 3:
                cost = (0, 9, 9, 9)
            elif method == 1:
                cost = (rng.randrange(0, 8), 0, rng.randrange(0, 5), rng.randrange(0, 9))
            elif method == 2:
                cost = (rng.randrange(0, 8), rng.randrange(0, 6), 0, rng.randrange(0, 9))
            else:
                cost = (rng.randrange(0, 8), rng.randrange(0, 6), rng.randrange(0, 5), rng.randrange(0, 9))
            options.append(cost)
        choices.append(options)
    return choices


def full_choices(seed):
    rng = random.Random(seed)
    result = []
    for _ in range(ACTIVE):
        options = []
        for _ in range(METHODS):
            options.append((rng.randrange(0, 20), rng.randrange(0, 12),
                            rng.randrange(0, 8), rng.randrange(0, 24)))
        result.append(options)
    return result


def record_exact(wire, seed):
    choices = sparse_choices(seed)
    validate_choices(choices)
    fixed = 13 + seed % 11
    all_states = exhaustive(choices, fixed, 1 << 60)
    assert len(all_states) == 4 ** 4
    byte_values = sorted({s[0] for s in all_states})
    budgets = sorted({byte_values[0] - 1, byte_values[0], byte_values[-1],
                      byte_values[-1] + 1, *(v for x in byte_values for v in (x - 1, x, x + 1))})
    checks = []
    expanded_max = peak_max = 0
    for budget in budgets:
        reference = exhaustive(choices, fixed, budget)
        expected = oracle_pick(reference, wire.work_key)
        try:
            actual, search = wire.beam(choices, fixed, budget, width=256)
        except ValueError:
            actual, search = None, None
        assert actual == expected, (seed, budget, actual, expected)
        if search:
            expanded_max = max(expanded_max, search['expanded'])
            peak_max = max(peak_max, search['peak'])
        checks.append(dict(budget=budget, feasible=expected is not None,
                           selected=list(actual) if actual is not None else None,
                           expanded=search['expanded'] if search else 0,
                           peak=search['peak'] if search else 0,
                           truncations=search['truncations'] if search else 0))
    return dict(seed=seed, mode='exact_sparse', active_contexts=4,
                cartesian_candidates=4 ** 4, width=256, fixed_bytes=fixed,
                budgets_checked=len(budgets), expanded_max=expanded_max,
                peak_max=peak_max, checks=checks)


def record_approx(wire, seed):
    choices = full_choices(seed)
    validate_choices(choices)
    fixed = 29 + seed % 13
    minima = fixed + sum(min(c[0] for c in opts) for opts in choices)
    maxima = fixed + sum(max(c[0] for c in opts) for opts in choices)
    # Includes impossible, exact minimum, interior, and unconstrained budgets.
    budgets = (minima - 1, minima, (minima + maxima) // 2, maxima)
    checks = []
    for budget in budgets:
        expected = exhaustive(choices, fixed, budget)
        try:
            first, s1 = wire.beam(choices, fixed, budget, width=128)
            second, s2 = wire.beam(choices, fixed, budget, width=128)
        except ValueError:
            first = second = s1 = s2 = None
        if not expected:
            assert first is second is s1 is s2 is None, (seed, budget)
            checks.append(dict(budget=budget, feasible=False))
            continue
        assert first is not None and second == first, (seed, budget, first, second)
        assert s1 == s2
        assert first[0] <= budget, (seed, budget, first)
        assert s1['expanded'] <= 6144, (seed, budget, s1)
        assert s1['peak'] <= 512, (seed, budget, s1)
        assert s1['truncations'] >= 0
        # A bounded beam is not asserted to equal the global exhaustive optimum.
        checks.append(dict(budget=budget, feasible=True, selected=list(first),
                           exhaustive_best=list(oracle_pick(expected, wire.work_key)),
                           optimality_claim=False, expanded=s1['expanded'],
                           peak=s1['peak'], truncations=s1['truncations']))
    return dict(seed=seed, mode='bounded_full', active_contexts=12,
                cartesian_candidates=4 ** 12, width=128, fixed_bytes=fixed,
                budgets_checked=len(budgets), checks=checks)


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

    report = dict(schema='cu66-v93-selection-bounded-v1', status='FAIL',
                  source_sha256=source_pins, python=platform.python_version(),
                  exact_seeds=list(range(9300, 9350)), stress_seeds=list(range(9400, 9450)),
                  exact_cases=50, stress_cases=50, contexts=12, methods_per_context=4,
                  exact_active_contexts=4, exact_candidates_per_case=256,
                  stress_candidates_per_case=4 ** 12, exact_width=256, stress_width=128,
                  max_expanded=6144, max_peak=512, global_optimality_claim=False,
                  latency_claim=False)
    rows = []
    previous = signal.getsignal(signal.SIGALRM)
    started = time.monotonic()
    signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('V93 selection watchdog')))
    signal.setitimer(signal.ITIMER_REAL, 90)
    try:
        for seed in report['exact_seeds']:
            rows.append(record_exact(wire, seed))
        for seed in report['stress_seeds']:
            rows.append(record_approx(wire, seed))
        assert source_pins == {str(path.relative_to(ROOT)): sha(path) for path in source_paths}, \
            'selection sources changed during execution'
        report.update(status='PASS', total_exact_candidates=50 * 256,
                      total_stress_budget_checks=50 * 4,
                      elapsed_seconds=round(time.monotonic() - started, 6),
                      bounded_expanded_max=max(
                          (x.get('expanded', 0) for c in rows if c['mode'] == 'bounded_full'
                           for x in c['checks']), default=0),
                      bounded_peak_max=max(
                          (x.get('peak', 0) for c in rows if c['mode'] == 'bounded_full'
                           for x in c['checks']), default=0),
                      exact_expanded_max=max((c['expanded_max'] for c in rows if c['mode'] == 'exact_sparse'), default=0),
                      exact_peak_max=max((c['peak_max'] for c in rows if c['mode'] == 'exact_sparse'), default=0),
                      rows_file='cases.json')
    except BaseException as exc:
        report['failure'] = repr(exc)
        report['elapsed_seconds'] = round(time.monotonic() - started, 6)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        (out / 'cases.json').write_text(json.dumps(rows, indent=2) + '\n')
        report['artifact_sha256'] = {
            str(path.relative_to(out)): sha(path)
            for path in out.rglob('*') if path.is_file() and path.name != 'results.json'
        }
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        pointer = dict(report, selected_report=str((out / 'results.json').relative_to(ROOT)),
                       report_copy=report)
        (OUT_ROOT.parent / 'results.json').write_text(json.dumps(pointer, indent=2) + '\n')
        print('V93_SELECTION_REPORT', out / 'results.json', report['status'], flush=True)


if __name__ == '__main__':
    run()
