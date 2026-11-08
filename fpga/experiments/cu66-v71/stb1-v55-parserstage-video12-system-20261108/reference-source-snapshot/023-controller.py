"""Conservative same-history, current-source RGB residual admission."""

CAP = 49152
POLICIES = ('adaptive_control', 'band_strict', 'band_budget')


def select_tier(group, policy):
    if policy not in POLICIES or not group or group[0]['kind'] != 'zero':
        raise ValueError('declared policy with zero incumbent first')
    if len({a['kind'] for a in group}) != len(group):
        raise ValueError('unique candidates')
    for a in group:
        if type(a['complete_bytes']) is not int or a['complete_bytes'] <= 0:
            raise ValueError('actual complete bytes')
        sse = a['hybrid']['active_squared_error']
        if type(sse) is not int or sse < 0:
            raise ValueError('integer source SSE')
        a['cap_fit'] = a['complete_bytes'] <= CAP
    zero_sse = group[0]['hybrid']['active_squared_error']
    legacy = [a for a in group if not a['kind'].endswith('_band')]
    for a in legacy:
        a['quality_eligible'] = a['hybrid']['active_squared_error'] <= zero_sse
    eligible = [a for a in legacy if a['cap_fit'] and a['quality_eligible']]
    baseline = min(eligible, key=lambda a: a['complete_bytes']) if eligible else None
    alternatives = [a for a in group if a['kind'].endswith('_band')]
    if policy == 'adaptive_control' and alternatives:
        raise ValueError('control contains modified residuals')
    budget = 1 if policy == 'band_budget' else 0
    for a in alternatives:
        a['quality_eligible'] = baseline is not None and 100 * a['hybrid']['active_squared_error'] <= (100 + budget) * baseline['hybrid']['active_squared_error']
    # A shadow incumbent must fit before residual alternatives are admitted.
    # This intentionally declines potential rescue-only packets at this tier.
    if baseline is None:
        return None, None
    eligible = [baseline] + [a for a in alternatives if a['cap_fit'] and a['quality_eligible']]
    return min(eligible, key=lambda a: a['complete_bytes']), baseline
