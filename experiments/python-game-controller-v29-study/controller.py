"""Bounded host decision shared by causal campaign and offline verification."""

CAP = 49152


def select_group(group):
    """Choose smallest cap-fitting candidate no worse than current zero motion.

    Entries must already contain actual serialized bytes and measured RGB565
    active squared error. Every attempted entry is retained and paid, including
    rejected motion candidates. This is not a perceptual quality guarantee.
    """
    if not group or group[0]['kind'] != 'zero':
        raise ValueError('zero reference candidate required first')
    if len({v['kind'] for v in group}) != len(group):
        raise ValueError('unique candidate kinds')
    baseline = group[0]['hybrid']['active_squared_error']
    for item in group:
        if type(item['complete_bytes']) is not int or item['complete_bytes'] <= 0:
            raise ValueError('actual positive complete bytes')
        error = item['hybrid']['active_squared_error']
        if type(error) is not int or error < 0:
            raise ValueError('integer source SSE')
        item['cap_fit'] = item['complete_bytes'] <= CAP
        item['quality_eligible'] = error <= baseline
    eligible = [v for v in group if v['cap_fit'] and v['quality_eligible']]
    return min(eligible, key=lambda v: v['complete_bytes']) if eligible else None
