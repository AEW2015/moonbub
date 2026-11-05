"""Conditional banked block schedule using measured v31 RTL stage cycles.

This is a dependency/resource model, not a simulated or synthesized new RTL.
Input, compute, and output have independent service resources; each bank is
reserved from first input until final output. All stages remain ordered.
"""

PAYLOAD_BITS_PER_BANK = 64 * (20 + 8 + 24 + 24)
COMPUTE_CYCLES = (0, 4, 132)
MAX_BLOCKS = 8100
MIN_SAMPLE_SERVICE_CYCLES = 64


def schedule(kinds, banks=1, *, load_cycles=64, output_cycles=64):
    if type(banks) is not int or not 1 <= banks <= 3:
        raise ValueError('one to three declared banks')
    if (type(load_cycles) is not int or type(output_cycles) is not int
            or min(load_cycles, output_cycles) < MIN_SAMPLE_SERVICE_CYCLES):
        raise ValueError('bounded non-overlapped sample services')
    kinds = list(kinds)
    if not kinds or len(kinds) > MAX_BLOCKS:
        raise ValueError('block count outside bounded frame geometry')
    if any(type(kind) is not int or kind not in (0, 1, 2) for kind in kinds):
        raise ValueError('nonempty zero/DC/general kinds')

    release = [0] * banks
    load_free = compute_free = out_free = 0
    rows = []
    for block_id, kind in enumerate(kinds):
        bank = block_id % banks
        load_start = max(load_free, release[bank])
        load_end = load_start + load_cycles
        compute_start = max(load_end, compute_free)
        compute_end = compute_start + COMPUTE_CYCLES[kind]
        out_start = max(compute_end, out_free)
        out_end = out_start + output_cycles
        rows.append(dict(id=block_id, kind=kind, bank=bank,
                         load_start=load_start, load_end=load_end,
                         compute_start=compute_start, compute_end=compute_end,
                         out_start=out_start, out_end=out_end))
        release[bank] = out_end
        load_free, compute_free, out_free = load_end, compute_end, out_end
    return dict(blocks=len(rows), banks=banks, done_cycles=out_free,
                payload_storage_bits=banks * PAYLOAD_BITS_PER_BANK, rows=rows)


def validate(result):
    """Validate bounded schedule structure, resources, bank lifetime and totals."""
    if not isinstance(result, dict):
        raise ValueError('schedule result must be a mapping')
    rows = result.get('rows')
    banks = result.get('banks')
    blocks = result.get('blocks')
    done_cycles = result.get('done_cycles')
    payload_bits = result.get('payload_storage_bits')
    if type(banks) is not int or not 1 <= banks <= 3:
        raise ValueError('one to three declared banks')
    if (not isinstance(rows, list) or not 1 <= len(rows) <= MAX_BLOCKS
            or type(blocks) is not int or blocks != len(rows)):
        raise ValueError('bounded block count must match schedule rows')
    if (type(done_cycles) is not int or done_cycles < 0
            or type(payload_bits) is not int
            or payload_bits != banks * PAYLOAD_BITS_PER_BANK):
        raise ValueError('invalid completion or payload accounting')

    release = [0] * banks
    stage_ends = [0, 0, 0]
    for block_id, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError('schedule row must be a mapping')
        fields = ('id', 'kind', 'bank', 'load_start', 'load_end',
                  'compute_start', 'compute_end', 'out_start', 'out_end')
        if any(type(row.get(field)) is not int for field in fields):
            raise ValueError('schedule fields must be integers')
        kind, bank = row['kind'], row['bank']
        if kind not in (0, 1, 2) or not 0 <= bank < banks:
            raise ValueError('schedule kind or bank outside declared range')
        if row['id'] != block_id or bank != block_id % banks:
            raise ValueError('ordered bank assignment')
        if min(row[name] for name in ('load_start', 'load_end', 'compute_start',
                                      'compute_end', 'out_start', 'out_end')) < 0:
            raise ValueError('negative schedule cycle')
        if not (release[bank] <= row['load_start']
                and row['load_start'] < row['load_end']
                and row['load_end'] <= row['compute_start']
                and row['compute_start'] <= row['compute_end']
                and row['compute_end'] <= row['out_start']
                and row['out_start'] < row['out_end']):
            raise ValueError('bank/dependency overlap')
        if (row['load_end'] - row['load_start'] < MIN_SAMPLE_SERVICE_CYCLES
                or row['out_end'] - row['out_start'] < MIN_SAMPLE_SERVICE_CYCLES):
            raise ValueError('sample service below declared minimum')
        for stage_index, name in enumerate(('load', 'compute', 'out')):
            if row[name + '_start'] < stage_ends[stage_index]:
                raise ValueError('shared stage overlap')
            stage_ends[stage_index] = row[name + '_end']
        if row['compute_end'] - row['compute_start'] != COMPUTE_CYCLES[kind]:
            raise ValueError('wrong measured stage work')
        release[bank] = row['out_end']

    if done_cycles != rows[-1]['out_end']:
        raise ValueError('frame completion mismatch')
    return True
