"""Deterministic causal DAG list scheduling, not an SDRAM/FPGA timing model.

Tasks are nonpreemptive. Each resource has a bounded number of identical lanes.
Task IDs break ready-queue ties. A resource's head task is never bypassed by a
later task merely because its duration fits a free interval. Group buffers are
bounded by explicit release-to-reuse dependencies supplied by the workload.
"""
from __future__ import annotations

import heapq


def _integer(value, label, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, int) or value < int(positive):
        raise ValueError(f"{label} must be a {'positive' if positive else 'nonnegative'} integer")
    return value


class PeriodicWindow:
    """Repeated half-open blocked intervals on one nonpreemptive resource."""

    def __init__(self, spec=None):
        self.period = 0
        self.blocked = []
        self.maximum_gap = None
        if spec is None:
            return
        self.period = _integer(spec['period'], 'window period', positive=True)
        raw = sorted(tuple(pair) for pair in spec.get('blocked', []))
        for start, end in raw:
            _integer(start, 'window start')
            _integer(end, 'window end')
            if not start < end <= self.period:
                raise ValueError('blocked windows require 0 <= start < end <= period')
            if self.blocked and start < self.blocked[-1][1]:
                raise ValueError('blocked windows may not overlap')
            if self.blocked and start == self.blocked[-1][1]:
                self.blocked[-1] = (self.blocked[-1][0], end)
            else:
                self.blocked.append((start, end))
        if self.blocked:
            gaps = [b[0] - a[1] for a, b in zip(self.blocked, self.blocked[1:])]
            gaps.append(self.period - self.blocked[-1][1] + self.blocked[0][0])
            self.maximum_gap = max(gaps)

    def earliest(self, start, duration):
        _integer(start, 'task start')
        _integer(duration, 'task duration')
        if not duration or not self.blocked:
            return start
        if duration > self.maximum_gap:
            raise ValueError('memory task cannot fit any contiguous periodic free interval')
        candidate = start
        # Deferring past a blocked interval monotonically increases candidate.
        # At most one cycle of intervals is needed after the first deferral,
        # because duration is bounded by the largest cyclic free gap.
        while True:
            epoch = candidate // self.period
            conflict = None
            for cycle in (epoch, epoch + 1):
                for left, right in self.blocked:
                    left += cycle * self.period
                    right += cycle * self.period
                    if candidate < right and candidate + duration > left:
                        conflict = right
                        break
                if conflict is not None:
                    break
            if conflict is None:
                return candidate
            candidate = conflict

    def overlaps(self, start, finish):
        return finish > start and self.earliest(start, finish - start) != start


def schedule(jobs, capacities, memory_windows=None, retain_timeline=False):
    """Schedule DAG tasks with data dependencies and independent resource lanes.

    jobs: dictionaries with unique integer ``id``, integer-ID ``deps``, named
    ``resource`` (or None for an unlimited control/delay task), and nonnegative
    integer ``duration``. Resources absent from capacities are rejected.

    A bounded group buffer must be expressed in the DAG, e.g. group i admission
    depends on release(i-N); the scheduler never invents early payload release.
    memory_windows: {period: positive cycles, blocked: [(start,end),...]}.
    Positive memory tasks are deferred whole across blocked intervals.
    """
    capacities = dict(capacities)
    if None in capacities:
        raise ValueError('None denotes unlimited controls, not a bounded resource')
    for resource, capacity in capacities.items():
        if not isinstance(resource, str) or not resource:
            raise ValueError('resource names must be nonempty strings')
        _integer(capacity, f'{resource} capacity', positive=True)
    window = PeriodicWindow(memory_windows)
    jobs = list(jobs)
    by_id = {}
    for job in jobs:
        ident = _integer(job['id'], 'task id')
        if ident in by_id:
            raise ValueError('duplicate task id')
        resource = job['resource']
        if resource is not None and resource not in capacities:
            raise ValueError(f'unknown task resource: {resource}')
        _integer(job['duration'], 'task duration')
        deps = list(job['deps'])
        if len(set(deps)) != len(deps):
            raise ValueError('duplicate dependency')
        for dep in deps:
            _integer(dep, 'dependency id')
        by_id[ident] = dict(job, deps=deps)
    outgoing = {ident: [] for ident in by_id}
    remaining = {}
    for ident, job in by_id.items():
        remaining[ident] = len(job['deps'])
        for dep in job['deps']:
            if dep not in by_id:
                raise ValueError('missing dependency')
            outgoing[dep].append(ident)
    # Validate acyclicity before execution, including disconnected cycles.
    check_remaining = dict(remaining)
    frontier = [ident for ident, n in check_remaining.items() if not n]
    checked = 0
    while frontier:
        ident = frontier.pop()
        checked += 1
        for child in outgoing[ident]:
            check_remaining[child] -= 1
            if check_remaining[child] == 0:
                frontier.append(child)
    if checked != len(jobs):
        raise ValueError('cyclic task graph')

    resources = [None] + sorted(capacities)
    ready = {resource: [] for resource in resources}
    for ident, n in remaining.items():
        if not n:
            heapq.heappush(ready[by_id[ident]['resource']], ident)
    active = []
    occupancy = {resource: 0 for resource in resources}
    maximum = {resource: 0 for resource in resources}
    work = {resource: 0 for resource in resources}
    count = {resource: 0 for resource in resources}
    timeline = [] if retain_timeline else None
    finish_by_id = {}
    now = 0
    done = 0
    memory_defer_events = 0
    memory_head_wait_cycles = 0
    while done < len(jobs):
        # Retire every completion at this clock before selecting new work.
        # In particular, a just-unblocked lower ID participates in the same
        # ready queue as tasks deferred by a periodic unavailable window.
        while active and active[0][0] == now:
            _, ident = heapq.heappop(active)
            occupancy[by_id[ident]['resource']] -= 1
            finish_by_id[ident] = now
            done += 1
            for child in outgoing[ident]:
                remaining[child] -= 1
                if remaining[child] == 0:
                    heapq.heappush(ready[by_id[child]['resource']], child)
        if done == len(jobs):
            break
        future_window = None
        for resource in resources:
            # Resolve instantaneous control fences before launching the next
            # resource's positive-duration work at this same clock.
            if active and active[0][0] == now:
                break
            limit = capacities.get(resource, len(jobs) + 1)
            while ready[resource] and occupancy[resource] < limit:
                ident = ready[resource][0]
                job = by_id[ident]
                if resource == 'memory':
                    permitted = window.earliest(now, job['duration'])
                    if permitted != now:
                        memory_defer_events += 1
                        # This sum is diagnostic head deferral, not a unique
                        # partition of wall time: another lane's completion can
                        # cause the same deferred head to be reconsidered.
                        memory_head_wait_cycles += permitted - now
                        future_window = permitted
                        break
                heapq.heappop(ready[resource])
                finish = now + job['duration']
                heapq.heappush(active, (finish, ident))
                occupancy[resource] += 1
                maximum[resource] = max(maximum[resource], occupancy[resource])
                work[resource] += job['duration']
                count[resource] += 1
                if timeline is not None:
                    timeline.append(dict(id=ident, start=now, finish=finish, resource=resource,
                                         kind=job.get('kind', 'unspecified')))
        if active and active[0][0] == now:
            continue
        events = [active[0][0]] if active else []
        if future_window is not None:
            events.append(future_window)
        if done < len(jobs):
            if not events:
                raise RuntimeError('scheduler deadlock after validated DAG')
            next_time = min(events)
            if next_time <= now:
                raise RuntimeError('scheduler did not advance')
            now = next_time
    result = dict(
        finish_cycles=now,
        tasks=len(jobs),
        policy='completion-first; instantaneous control fences; resource-name order; ready task ID priority; nonpreemptive; no head bypass',
        resources={resource: dict(capacity=capacities[resource], work_cycles=work[resource],
                                  task_count=count[resource], max_active=maximum[resource])
                   for resource in sorted(capacities)},
        controls=dict(task_count=count[None], work_cycles=work[None], max_active=maximum[None]),
        memory_window_defer_events=memory_defer_events,
        memory_head_deferral_sum_cycles=memory_head_wait_cycles,
        physical_timing_proven=False,
    )
    if timeline is not None:
        result['timeline'] = timeline
        result['finish_by_id'] = finish_by_id
    return result
