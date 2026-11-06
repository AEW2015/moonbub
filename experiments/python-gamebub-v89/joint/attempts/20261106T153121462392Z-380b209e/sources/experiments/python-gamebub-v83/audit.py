"""Independent checks of retained, conditional DAG schedules; not RTL timing."""
from collections import defaultdict


def verify(jobs, timeline, capacities, windows=None, groups=(), group_slots=None):
    by_id = {job['id']: job for job in jobs}
    assert len(by_id) == len(jobs), 'duplicate job'
    rows = {row['id']: row for row in timeline}
    assert len(rows) == len(timeline) and rows.keys() == by_id.keys(), 'timeline membership'
    resources = defaultdict(list)
    total_work = defaultdict(int)
    for ident, job in by_id.items():
        row = rows[ident]
        start, finish = row['start'], row['finish']
        assert isinstance(start, int) and isinstance(finish, int) and start >= 0
        assert finish - start == job['duration'], ('duration', ident)
        assert row['resource'] == job['resource']
        assert all(rows[dep]['finish'] <= start for dep in job['deps']), ('dependency', ident)
        resource = job['resource']
        if resource is not None and finish > start:
            resources[resource].append((start, 1))
            resources[resource].append((finish, -1))
            total_work[resource] += finish - start
        if windows and resource == 'memory' and finish > start:
            period = windows['period']
            for cycle in range(start // period, (finish - 1) // period + 1):
                for low, high in windows['blocked']:
                    assert finish <= cycle * period + low or start >= cycle * period + high, ('reserved-window', ident)
    peaks = {}
    for resource, events in resources.items():
        live = peak = 0
        for _, delta in sorted(events):  # completion before admission on equal clock
            live += delta
            assert 0 <= live <= capacities[resource], ('capacity', resource)
            peak = max(peak, live)
        assert live == 0
        peaks[resource] = peak
    group_peak = 0
    if groups:
        assert isinstance(group_slots, int) and group_slots > 0
        events = []
        for group in groups:
            start = rows[group['start']]['start']
            finish = rows[group['release']]['finish']
            assert finish >= start
            if finish > start:
                events.extend(((start, 1), (finish, -1)))
        live = 0
        for _, delta in sorted(events):
            live += delta
            assert 0 <= live <= group_slots, 'group buffer capacity'
            group_peak = max(group_peak, live)
        assert live == 0
    return dict(jobs=len(jobs), finish_cycles=max((r['finish'] for r in timeline), default=0),
                resource_work_cycles=dict(sorted(total_work.items())),
                resource_peak=dict(sorted(peaks.items())), group_peak=group_peak)
