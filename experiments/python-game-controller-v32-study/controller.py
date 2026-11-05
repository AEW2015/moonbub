"""Admit small-AC alternatives against the whole v30 controller shadow."""
from pathlib import Path
import importlib.util

_s=importlib.util.spec_from_file_location('v32_shadow30',Path(__file__).resolve().parent.parent/'python-game-controller-v30-study/controller.py')
old=importlib.util.module_from_spec(_s);_s.loader.exec_module(old)
CAP=49152
POLICIES=('band_control','shrink_strict','shrink_budget')

def select_tier(group,policy):
    if policy not in POLICIES or not group:raise ValueError('declared policy and candidates')
    if len({a['kind'] for a in group})!=len(group):raise ValueError('unique candidates')
    previous=[a for a in group if not a['kind'].endswith('_shrink')]
    baseline,_=old.select_tier(previous,'band_strict')
    extra=[a for a in group if a['kind'].endswith('_shrink')]
    if policy=='band_control' and extra:raise ValueError('control cannot contain shrink trials')
    percent=1 if policy=='shrink_budget' else 0
    for a in extra:
        error=a['hybrid']['active_squared_error']
        if type(error) is not int or error<0 or type(a['complete_bytes']) is not int or a['complete_bytes']<=0:raise ValueError('actual bytes/source SSE')
        a['cap_fit']=a['complete_bytes']<=CAP
        a['quality_eligible']=baseline is not None and 100*error<=(100+percent)*baseline['hybrid']['active_squared_error']
    if baseline is None:return None,None
    eligible=[baseline]+[a for a in extra if a['cap_fit'] and a['quality_eligible']]
    return min(eligible,key=lambda a:a['complete_bytes']),baseline
