"""Strict source-visible RGB error and actual complete-byte candidate guard."""
CAP=49152
SCENES=('mass-effect-2600','mass-effect-7200')
POLICIES=('control','guarded_core8')

def choose(shadow,candidates):
    if shadow is not None:
        if type(shadow['complete_bytes'])is not int or not 0<shadow['complete_bytes']<=CAP:raise ValueError('fitting shadow')
        err=shadow['hybrid']['active_squared_error']
        if type(err)is not int or err<0:raise ValueError('integer source SSE')
    for c in candidates:
        size,sse=c['complete_bytes'],c['hybrid']['active_squared_error']
        if type(size)is not int or size<=0 or type(sse)is not int or sse<0:raise ValueError('actual size/SSE')
        c['cap_fit']=size<=CAP;c['quality_eligible']=shadow is not None and sse<=err
        c['qualified']=shadow is not None and c['cap_fit'] and c['quality_eligible'] and size<shadow['complete_bytes']
    return None if shadow is None else min([shadow]+[c for c in candidates if c['qualified']],key=lambda c:c['complete_bytes'])

def complete(cases):
    keys=[(c['scene'],c['policy']) for c in cases]
    if len(keys)!=4 or len(set(keys))!=4 or set(keys)!={(s,p) for s in SCENES for p in POLICIES}:raise ValueError('exact four cohorts')
    for case in cases:
        if [r['id'] for r in case['rows']]!=list(range(48)):raise ValueError('exact ordered48 IDs')
