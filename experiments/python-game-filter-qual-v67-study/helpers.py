"""Namespaced frozen sources, decoder and fixed display-only filter."""
from pathlib import Path
import hashlib, importlib.util, json, sys
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=HERE.parent/'python-game-source-v40-study'
PACKETS=HERE.parent/'python-game-binary-qual-v40-study'
FILTER=HERE.parent/'python-game-display-filter-v60-study'

def module(name,path):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s)
    sys.modules[name]=m; s.loader.exec_module(m); return m

def bound(name,path,helper):
    old=sys.modules.get('helpers')
    try:
        sys.modules['helpers']=helper
        return module(name,path)
    finally:
        if old is None: sys.modules.pop('helpers',None)
        else: sys.modules['helpers']=old

h=module('qual67_direct43_helpers',HERE.parent/'python-game-direct-rx-v43-study/helpers.py')
direct=bound('qual67_direct43_receiver',HERE.parent/'python-game-direct-rx-v43-study/receiver.py',h)
filt=module('qual67_frozen60_filter',FILTER/'model.py')
load,raw,sha=h.load,h.raw,h.sha

def digest(data): return hashlib.sha256(data).hexdigest()

def preset():
    c=load(FILTER/'calibration.json')
    assert c['source_IDs']==list(range(24))
    assert c['selected_preset']==dict(name='strong',alpha=24,beta=12,strength=3)
    for p,want in c['source_sha256'].items(): assert sha(ROOT/p)==want,p
    return dict(c['selected_preset'])

def excluded():
    z=tuple(np.zeros(s,np.int16) for s in ((480,720),(240,360),(240,360)))
    mask=h.f.f.normalize(z)[0]==128; mask.setflags(write=False); return mask

def pins():
    source=load(PACKETS/'results.json'); paths={ROOT/p for p in source['source_pins_sha256']}
    paths|={PACKETS/'results.json',SOURCE/'manifest.json',FILTER/'calibration.json',FILTER/'model.py',
            HERE.parent/'python-game-direct-rx-v43-study/helpers.py',HERE.parent/'python-game-direct-rx-v43-study/receiver.py'}
    paths|={HERE/p for p in ('helpers.py','model.py','benchmark.py','test_model.py')}
    for c in source['cases']:
        paths|={PACKETS/r['packet']['path'] for r in c['rows']}
    for c in load(SOURCE/'manifest.json')['cases']:
        paths|={SOURCE/r['canvas_rgb24']['path'] for r in c['frames']}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
