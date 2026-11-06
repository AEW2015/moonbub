"""Bounded intermediate credits and entropy admission for frozen V83 DAGs.

This transforms a software scheduling workload, not an RTL implementation.
Every credit is reserved before its producer starts and released only when the
named consumer finishes. FIFO-order dependencies enforce capacity independently
of the scheduler's resource selection policy.
"""
from __future__ import annotations

import copy


def _capacity(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(f'{name} must be a positive integer')
    return value


def _acyclic(jobs):
    by_id = {j['id']: j for j in jobs}
    if len(by_id) != len(jobs):
        raise ValueError('duplicate job identity')
    outgoing = {i: [] for i in by_id}
    degree = {}
    for ident, job in by_id.items():
        deps = job['deps']
        if len(set(deps)) != len(deps):
            raise ValueError('duplicate dependency')
        degree[ident] = len(deps)
        for dep in deps:
            if dep not in by_id:
                raise ValueError('missing dependency')
            outgoing[dep].append(ident)
    ready = [i for i, count in degree.items() if not count]
    seen = 0
    while ready:
        ident = ready.pop()
        seen += 1
        for child in outgoing[ident]:
            degree[child] -= 1
            if not degree[child]:
                ready.append(child)
    if seen != len(jobs):
        raise ValueError('cyclic credit/admission workload')


def augment(work, tile_costs, *, ref_slots=8, inverse_slots=8,
            coefficient_slots=8):
    """Add serial entropy work, mode-arrival fences and finite staging credits.

    ``tile_costs`` supplies one nonnegative integer work duration per physical
    tile in Y/Cb/Cr order. Its relation to real entropy hardware is the caller's
    explicit model assumption. Hidden and COPY records still reserve coefficient
    capacity before classification; their reservation is released by map lookup.
    The function copies its input and preserves all original task IDs and priced
    V83 memory/hash/map operations. New entropy jobs use IDs above the old DAG.
    """
    capacities = dict(reference=_capacity(ref_slots, 'ref_slots'),
                      inverse=_capacity(inverse_slots, 'inverse_slots'),
                      coefficients=_capacity(coefficient_slots, 'coefficient_slots'))
    result = copy.deepcopy(work)
    jobs = result['jobs']
    by_id = {j['id']: j for j in jobs}
    if len(by_id) != len(jobs) or not jobs:
        raise ValueError('missing/duplicate workload jobs')
    if any(type(j['id']) is not int or j['id'] < 0 for j in jobs):
        raise ValueError('invalid job identity')
    original_complete = result['complete']
    if original_complete not in by_id:
        raise ValueError('missing completion fence')
    modes = {}
    for job in jobs:
        if job['kind'] in ('map_lookup', 'reference_read', 'inverse', 'reconstruct',
                           'copy_ready', 'const_generate'):
            tile = job['tile']
            if type(tile) is not int or tile < 0:
                raise ValueError('invalid tile identity')
            entry = modes.setdefault(tile, {})
            if job['kind'] in entry:
                raise ValueError('duplicate tile operation')
            entry[job['kind']] = job
    count = len(modes)
    if set(modes) != set(range(count)):
        raise ValueError('noncontiguous tile coverage')
    costs = list(tile_costs)
    if len(costs) != count or any(type(v) is not int or v < 0 for v in costs):
        raise ValueError('tile_costs must cover every tile with nonnegative integer durations')
    if not result.get('groups'):
        raise ValueError('missing group ownership')
    for tile, entry in modes.items():
        if 'map_lookup' not in entry:
            raise ValueError('missing map admission')
        if sum(kind in entry for kind in ('reconstruct', 'copy_ready', 'const_generate')) != 1:
            raise ValueError('ambiguous tile mode')
        if ('inverse' in entry) != ('reconstruct' in entry):
            raise ValueError('inverse/reconstruction coverage disagreement')
        group = entry['map_lookup']['group']
        if type(group) is not int or not 0 <= group < len(result['groups']):
            raise ValueError('invalid group identity')
    next_id = max(by_id) + 1
    entropy = []
    # The sequential stream cannot classify future tiles before a group is
    # admitted. Reserving coefficient credits before production makes response
    # storage available even when downstream inverse/reference work stalls.
    for tile in range(count):
        entry = modes[tile]
        group = entry['map_lookup']['group']
        deps = [result['groups'][group]['start']]
        if entropy:
            deps.append(entropy[-1]['id'])
        job = dict(id=next_id, deps=sorted(set(deps)), resource='entropy',
                   duration=costs[tile], kind='entropy_tile', tile=tile, group=group)
        next_id += 1
        entropy.append(job)
        jobs.append(job)
        by_id[job['id']] = job
        entry['map_lookup']['deps'] = sorted(set(entry['map_lookup']['deps'] + [job['id']]))

    constraints = dict(reference=[], inverse=[], coefficients=[])
    for tile in range(count):
        entry = modes[tile]
        if 'reference_read' in entry:
            consumer = entry.get('reconstruct', entry.get('copy_ready'))
            if consumer is None:
                raise ValueError('reference lacks a consumer')
            constraints['reference'].append(dict(tile=tile, producer=entry['reference_read']['id'],
                                                 consumer=consumer['id'], bytes=64))
        if 'inverse' in entry:
            constraints['inverse'].append(dict(tile=tile, producer=entry['inverse']['id'],
                                               consumer=entry['reconstruct']['id'], bytes=192))
        consumer = entry.get('inverse', entry['map_lookup'])
        constraints['coefficients'].append(dict(tile=tile, producer=entropy[tile]['id'],
                                                consumer=consumer['id'], bytes=128))
    for kind, records in constraints.items():
        capacity = capacities[kind]
        for i, record in enumerate(records):
            release = None if i < capacity else records[i-capacity]['consumer']
            record['release_before_production'] = release
            if release is not None:
                producer = by_id[record['producer']]
                producer['deps'] = sorted(set(producer['deps'] + [release]))
    # Existing map/store/leaf fences transitively include all arrivals; an
    # explicit final entropy edge documents the complete coefficient stream.
    by_id[original_complete]['deps'] = sorted(set(by_id[original_complete]['deps'] + [entropy[-1]['id']]))
    _acyclic(jobs)
    output_bytes = result['counts']['group_payload_buffer_bytes']
    static = dict(reference=capacities['reference']*64,
                  inverse=capacities['inverse']*192,
                  coefficients=capacities['coefficients']*128,
                  output_groups=output_bytes)
    result['credits'] = dict(capacities=capacities, constraints=constraints,
                             reserved_bytes=static,
                             total_logical_stage_reservations_bytes=sum(static.values()),
                             lifetime='Producer start through consumer finish; half-open clock intervals.')
    result['counts']['task_count'] = len(jobs)
    result['counts']['entropy_tiles'] = count
    result['counts']['entropy_work_cycles'] = sum(costs)
    result['assumptions'] = dict(result.get('assumptions', {}),
        producer='Encoded input is available at epoch start, but tile modes/coefficients are produced by the sequential entropy tasks and group/credit admission.',
        entropy='One sequential nonpreemptive resource; explicit per-tile cost supplied by caller; backpressured by group and coefficient admission.',
        staging='Reference64B, signed24 inverse-result192B, coefficient128B credits reserved at producer start; consumed through consumer finish.',
        COPY='Reference bytes become group output at copy_ready, with no separately priced copy-port transfer.',
        timing_is_physical=False,
        unpriced='Physical RAM/ports, dequant staging, inverse working registers, compressed transport buffers, descriptor/control and CDC remain outside this DAG.')
    return result


def audit_lifetimes(work, timeline):
    """Independently measure reserved slots from producer/consumer timestamps.

    This does not infer the correct consumers from native pixels. Construction
    tests separately check those bindings. Reservations include producer runtime,
    not only the interval after a result has already arrived.
    """
    rows = {row['id']: row for row in timeline}
    if len(rows) != len(timeline) or set(rows) != {j['id'] for j in work['jobs']}:
        raise ValueError('timeline coverage')
    result = {}
    for kind, records in work['credits']['constraints'].items():
        events = []
        for record in records:
            start = rows[record['producer']]['start']
            finish = rows[record['consumer']]['finish']
            if start > finish:
                raise ValueError('consumer precedes reservation')
            prior = record['release_before_production']
            if prior is not None and rows[prior]['finish'] > start:
                raise ValueError('credit reused before consumer completion')
            if finish > start:
                events.extend(((start, 1), (finish, -1)))
        live = maximum = 0
        for _, delta in sorted(events):
            live += delta
            if not 0 <= live <= work['credits']['capacities'][kind]:
                raise ValueError('staging credit capacity exceeded: ' + kind)
            maximum = max(maximum, live)
        if live:
            raise ValueError('credit leak')
        size = {'reference':64, 'inverse':192, 'coefficients':128}[kind]
        result[kind] = dict(peak_reserved_slots=maximum, peak_reserved_bytes=maximum*size,
                            capacity=work['credits']['capacities'][kind], slot_bytes=size,
                            reservations=len(records))
    return result
