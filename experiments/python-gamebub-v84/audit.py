"""Independent lifetime and semantic-fence checks of V84 credit schedules."""
from collections import defaultdict


def highwater(intervals):
    points = []
    for start, finish, size in intervals:
        assert 0 <= start <= finish and size >= 0
        if start != finish:
            points.extend(((start, size), (finish, -size)))
    live = maximum = 0
    for _, delta in sorted(points):
        live += delta
        assert live >= 0
        maximum = max(maximum, live)
    assert live == 0
    return maximum


def verify(work, timeline, *, ref_slots, inverse_slots, coefficient_slots, tile_count=8100):
    jobs = work['jobs']
    by_id = {j['id']:j for j in jobs}
    timing = {r['id']:r for r in timeline}
    assert len(by_id) == len(timing) == len(jobs)
    kinds = defaultdict(dict)
    for job in jobs:
        if 'tile' in job:
            assert job['tile'] not in kinds[job['kind']], ('duplicate tile stage', job['kind'])
            kinds[job['kind']][job['tile']] = job
    entropy = sorted(kinds['entropy_tile'].values(), key=lambda j:j['tile'])
    assert len(entropy) == tile_count
    assert [j['tile'] for j in entropy] == list(range(tile_count))
    for index, job in enumerate(entropy):
        assert job['resource'] == 'entropy'
        assert work['groups'][job['group']]['start'] in job['deps']
        if index:
            assert entropy[index-1]['id'] in job['deps']
        assert job['id'] in kinds['map_lookup'][job['tile']]['deps']
    # The final publication fence must include every operation, not just happen
    # to execute later under the selected scheduler policy.
    ancestors, frontier = set(), [work['complete']]
    while frontier:
        ident = frontier.pop()
        if ident not in ancestors:
            ancestors.add(ident)
            frontier.extend(by_id[ident]['deps'])
    assert ancestors == by_id.keys()
    categories = {}
    for name, producer_kind, capacity, size in (
        ('reference', 'reference_read', ref_slots, 64),
        ('inverse', 'inverse', inverse_slots, 192),
        ('coefficient', 'entropy_tile', coefficient_slots, 128),
    ):
        producers = sorted(kinds[producer_kind].values(), key=lambda j:j['tile'])
        consumers = []
        intervals = []
        for index, producer in enumerate(producers):
            tile = producer['tile']
            if name == 'coefficient':
                consumer = kinds['inverse'].get(tile, kinds['map_lookup'][tile])
            else:
                consumer = kinds['reconstruct'].get(tile, kinds['copy_ready'].get(tile))
                assert consumer is not None
            consumers.append(consumer)
            if index >= capacity:
                assert consumers[index-capacity]['id'] in producer['deps'], (name, 'credit reuse')
            start = timing[producer['id']]['start']
            finish = timing[consumer['id']]['finish']
            assert finish >= timing[producer['id']]['finish'] >= start
            intervals.append((start, finish, size))
        peak_bytes = highwater(intervals)
        assert peak_bytes <= capacity * size, (name, peak_bytes, capacity * size)
        categories[name] = dict(peak_bytes=peak_bytes, peak_slots=peak_bytes//size,
                                capacity_slots=capacity, bytes_per_slot=size, producers=len(producers), intervals=intervals)
    group_sizes = defaultdict(int)
    for job in kinds['map_lookup'].values():
        group_sizes[job['group']] += 1
    output = [(timing[g['start']]['start'], timing[g['release']]['finish'], group_sizes[i]*64)
              for i,g in enumerate(work['groups'])]
    assert highwater(output) <= 4096
    combined = highwater(output + [v for c in categories.values() for v in c['intervals']])
    static = 4096 + ref_slots*64 + inverse_slots*192 + coefficient_slots*128
    assert combined <= static
    return dict(stages={k:{f:v for f,v in c.items() if f!='intervals'} for k,c in categories.items()},
                output_peak_bytes=highwater(output), combined_peak_bytes=combined,
                conservative_logical_capacity_bytes=static,
                scope='Reserved from producer admission through consumer completion; excludes all other decoder/transport state and RAM rounding.')
