"""Strict actual-byte/current-source RGB admission against a fitting shadow."""
CAP=49152
POLICIES=('control','hierarchy_full','hierarchy_select25')
SCENES=('mass-effect-2600','mass-effect-7200')

def choose(shadow,children):
    if shadow is not None:
        if type(shadow['complete_bytes'])is not int or not 0<shadow['complete_bytes']<=CAP:raise ValueError('fitting control shadow')
        error=shadow['hybrid']['active_squared_error']
        if type(error)is not int or error<0:raise ValueError('integer shadow SSE')
    for c in children:
        size,sse=c['complete_bytes'],c['hybrid']['active_squared_error']
        if type(size)is not int or size<=0 or type(sse)is not int or sse<0:raise ValueError('actual size/SSE')
        c['quality_eligible']=shadow is not None and sse<=error;c['cap_fit']=size<=CAP
        c['qualified']=shadow is not None and c['cap_fit'] and c['quality_eligible'] and size<shadow['complete_bytes']
    if shadow is None:return None
    return min([shadow]+[c for c in children if c['qualified']],key=lambda c:c['complete_bytes'])

def complete(cases):
    keys=[(c['scene'],c['policy']) for c in cases]
    expected={(s,p) for s in SCENES for p in POLICIES}
    if len(keys)!=6 or len(set(keys))!=6 or set(keys)!=expected:raise ValueError('exact six cohorts')
    for c in cases:
        if [r['id'] for r in c['rows']]!=list(range(48)):raise ValueError('exact ordered48 IDs')
