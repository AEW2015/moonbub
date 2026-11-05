"""Unchanged v30 strict admission for a new motion search operating point."""
from pathlib import Path
import importlib.util
_s=importlib.util.spec_from_file_location('camera33_controller30',Path(__file__).resolve().parent.parent/'python-game-controller-v30-study/controller.py')
old=importlib.util.module_from_spec(_s);_s.loader.exec_module(old)
SCENES=('mass-effect-2600','mass-effect-7200')
POLICIES=('band_control','global_cross','global_grid')

def complete_cases(cases):
    keys=[(c['scene'],c['policy']) for c in cases]
    expected={(s,k) for s in SCENES for k in POLICIES}
    if len(keys)!=6 or len(set(keys))!=6 or set(keys)!=expected:raise ValueError('exact six cohorts required')
    for c in cases:
        if [r['id'] for r in c['rows']]!=list(range(48)):raise ValueError('ordered complete frame IDs required')

def select_tier(group,policy='band_control'):
    if policy!='band_control':raise ValueError('strict tier policy only')
    return old.select_tier(group,'band_strict')
