#!/usr/bin/env python3
"""Independent timeline and cycle-tick checks for the V83 causal scheduler."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'experiments/python-gamebub-v83/scheduler.py'
DEST = ROOT / 'experiments/python-gamebub-v83/scheduler-tests.json'
spec = importlib.util.spec_from_file_location('cu83_scheduler_under_test', SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def job(ident, duration, resource='memory', deps=()):
    return dict(id=ident, duration=duration, resource=resource, deps=list(deps))


def check_timeline(jobs, caps, result, windows=None):
    entries = {entry['id']: entry for entry in result['timeline']}
    assert len(entries) == len(jobs) == result['tasks']
    assert result['finish_cycles'] == max((e['finish'] for e in entries.values()), default=0)
    for task in jobs:
        entry = entries[task['id']]
        assert entry['finish'] - entry['start'] == task['duration']
        assert entry['resource'] == task['resource']
        assert all(entries[dep]['finish'] <= entry['start'] for dep in task['deps'])
        if task['resource'] == 'memory' and windows and task['duration']:
            # Brute per-cycle blocked check, independent from PeriodicWindow.
            for cycle in range(entry['start'], entry['finish']):
                offset = cycle % windows['period']
                assert all(not left <= offset < right for left, right in windows['blocked'])
    for resource, cap in caps.items():
        events = []
        for entry in entries.values():
            if entry['resource'] == resource and entry['finish'] > entry['start']:
                events.extend([(entry['start'], 1), (entry['finish'], -1)])
        active = peak = 0
        for _, delta in sorted(events):
            active += delta
            peak = max(peak, active)
            assert 0 <= active <= cap
        assert active == 0
        assert result['resources'][resource]['work_cycles'] == sum(
            task['duration'] for task in jobs if task['resource'] == resource)
        if all(task['duration'] for task in jobs if task['resource'] == resource):
            assert result['resources'][resource]['max_active'] == peak


def tick_oracle(jobs, caps, windows=None):
    """Slow independent clock-by-clock scheduler for positive-duration jobs."""
    by_id = {j['id']: j for j in jobs}
    launched, completed = set(), set()
    running = {}
    clock = 0
    resources = [None] + sorted(caps)
    while len(completed) < len(jobs):
        while True:
            # Drain same-clock completion events before any positive launches.
            newly_done = {i for i, end in running.items() if end == clock}
            for i in newly_done:
                del running[i]
            completed |= newly_done
            changed = bool(newly_done)
            for resource in resources:
                candidates = sorted(j['id'] for j in jobs if j['id'] not in launched
                                    and j['resource'] == resource
                                    and set(j['deps']) <= completed)
                used = sum(by_id[i]['resource'] == resource for i in running)
                cap = caps.get(resource, len(jobs) + 1)
                for i in candidates:
                    if used >= cap:
                        break
                    if resource == 'memory' and windows:
                        fits = all(not left <= t % windows['period'] < right
                                   for t in range(clock, clock + by_id[i]['duration'])
                                   for left, right in windows['blocked'])
                        if not fits:
                            break
                    launched.add(i)
                    running[i] = clock + by_id[i]['duration']
                    used += 1
                    changed = True
            if not newly_done:
                break
        if len(completed) == len(jobs):
            return clock
        clock += 1
        assert clock < 100000, 'tick oracle timeout'


def main():
    checks = []
    report = dict(schema='cu83-scheduler-tests-v1', status='FAIL',
                  source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    try:
        cases = [
            ('empty', [], {'memory': 1}, None, 0),
            ('serial', [job(0, 10), job(1, 3)], {'memory': 1}, None, 13),
            ('parallel_lanes', [job(i, 5, 'hash') for i in range(4)], {'hash': 2}, None, 10),
            ('causal_hash', [job(0, 12), job(1, 8, 'inverse', [0]),
                             job(2, 7, 'hash', [1]), job(3, 3, 'memory', [1]),
                             job(4, 0, None, [2, 3])],
             {'memory': 1, 'inverse': 1, 'hash': 1}, None, 27),
            ('periodic_boundaries', [job(i, 40) for i in range(3)], {'memory': 1},
             dict(period=100, blocked=[(0, 10), (50, 60)]), 150),
            ('wraparound_gap', [job(0, 20)], {'memory': 1},
             dict(period=30, blocked=[(10, 20)]), 40),
            ('zero_time_fence', [job(0, 0, None), job(1, 0, None, [0]),
                                 job(2, 9, 'memory', [1])], {'memory': 1}, None, 9),
        ]
        for label, tasks, caps, windows, expected in cases:
            result = module.schedule(tasks, caps, windows, retain_timeline=True)
            assert result['finish_cycles'] == expected, (label, result['finish_cycles'], expected)
            check_timeline(tasks, caps, result, windows)
            assert result == module.schedule(tasks, caps, windows, retain_timeline=True)
            checks.append(dict(name=label, status='PASS', finish_cycles=expected))
        tasks = [job(0, 5, 'inverse'), job(1, 2, 'memory', [0]), job(10, 3)]
        windows = dict(period=10, blocked=[(0, 5)])
        result = module.schedule(tasks, {'memory': 1, 'inverse': 1}, windows, retain_timeline=True)
        entries = {x['id']: x for x in result['timeline']}
        assert entries[1]['start'] == 5 and entries[10]['start'] == 7
        check_timeline(tasks, {'memory': 1, 'inverse': 1}, result, windows)
        checks.append(dict(name='completion_before_window_relaunch', status='PASS', finish_cycles=10))
        tasks = [job(0, 0, None), job(1, 2, 'memory', [0]), job(10, 3)]
        result = module.schedule(tasks, {'memory': 1}, retain_timeline=True)
        entries = {x['id']: x for x in result['timeline']}
        assert entries[1]['start'] == 0 and entries[10]['start'] == 2
        check_timeline(tasks, {'memory': 1}, result)
        checks.append(dict(name='control_fence_before_positive_launch', status='PASS', finish_cycles=5))
        for slots, expected in ((1, 30), (2, 20), (3, 20)):
            tasks = []
            for group in range(3):
                i = group * 4
                tasks += [job(i, 0, None, [4*(group-slots)+3] if group >= slots else []),
                          job(i+1, 5, 'memory', [i]), job(i+2, 5, 'hash', [i+1]),
                          job(i+3, 0, None, [i+2])]
            result = module.schedule(tasks, {'memory': 1, 'hash': 1}, retain_timeline=True)
            assert result['finish_cycles'] == expected
            check_timeline(tasks, {'memory': 1, 'hash': 1}, result)
            entries = {x['id']: x for x in result['timeline']}
            intervals = [(entries[g*4]['start'], entries[g*4+3]['finish']) for g in range(3)]
            for clock in range(expected):
                assert sum(start <= clock < end for start, end in intervals) <= slots
            checks.append(dict(name=f'bounded_groups_{slots}', status='PASS', finish_cycles=expected))
        rejects = [
            ('duplicate_id', [job(0, 1), job(0, 2)], {'memory': 1}, None),
            ('missing_dependency', [job(0, 1, deps=[9])], {'memory': 1}, None),
            ('cycle', [job(0, 1, deps=[1]), job(1, 1, deps=[0])], {'memory': 1}, None),
            ('disconnected_cycle', [job(0, 1), job(1, 1, deps=[2]), job(2, 1, deps=[1])], {'memory': 1}, None),
            ('duplicate_dependency', [job(0, 1), job(1, 1, deps=[0, 0])], {'memory': 1}, None),
            ('unknown_resource', [job(0, 1, 'unknown')], {'memory': 1}, None),
            ('negative_duration', [job(0, -1)], {'memory': 1}, None),
            ('bool_duration', [job(0, True)], {'memory': 1}, None),
            ('zero_capacity', [job(0, 1)], {'memory': 0}, None),
            ('full_block', [job(0, 1)], {'memory': 1}, dict(period=10, blocked=[(0, 10)])),
            ('oversized_task', [job(0, 6)], {'memory': 1}, dict(period=10, blocked=[(0, 5)])),
            ('overlap_windows', [job(0, 1)], {'memory': 1}, dict(period=10, blocked=[(0, 6), (5, 9)])),
            ('bad_window_endpoint', [job(0, 1)], {'memory': 1}, dict(period=10, blocked=[(5, 11)])),
        ]
        for label, tasks, caps, windows in rejects:
            try:
                module.schedule(tasks, caps, windows)
            except (ValueError, KeyError, TypeError):
                pass
            else:
                raise AssertionError(f'{label}: invalid input accepted')
            checks.append(dict(name=label, status='PASS_REJECT'))
        for seed in range(12):
            rng = random.Random(seed)
            caps = dict(memory=1, hash=rng.randint(1, 3), inverse=1)
            tasks = []
            for ident in range(35):
                deps = [earlier for earlier in range(ident) if rng.random() < .055]
                resource = rng.choice(list(caps))
                tasks.append(job(ident, rng.randint(1, 7), resource, deps))
            windows = dict(period=29, blocked=[(0, 3), (14, 17)]) if seed % 2 else None
            result = module.schedule(tasks, caps, windows, retain_timeline=True)
            check_timeline(tasks, caps, result, windows)
            expected = tick_oracle(tasks, caps, windows)
            assert result['finish_cycles'] == expected, (seed, result['finish_cycles'], expected)
            checks.append(dict(name=f'random_tick_oracle_{seed}', status='PASS', finish_cycles=expected))
        report.update(status='PASS', checks=checks, count=len(checks),
                      scope='DAG scheduler semantics and finite synthetic resources only; not physical timing.')
    except Exception as exc:
        report.update(failure=repr(exc), traceback=traceback.format_exc(), checks=checks)
        raise
    finally:
        DEST.write_text(json.dumps(report, indent=2) + '\n')
        print('V83_SCHEDULER_TESTS', report['status'], len(checks))


if __name__ == '__main__':
    main()
