"""Frozen display preset/metrics and exact temporal custom/native inputs."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SOURCE=HERE.parent/'python-game-source-v40-study';CUSTOM=HERE.parent/'python-game-temporal-qual-v59-study'
FILTER=HERE.parent/'python-game-display-filter-v60-study'
NATIVE_SOURCES=(HERE.parent/'python-game-native-temporal-v61-study',HERE.parent/'python-game-native-temporal-cap-v61-study')
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
io=module('filter62_frozen57_IO',HERE.parent/'python-game-error-quality-v57-study/verify.py');h=io.h
filt=module('filter62_frozen60_model',FILTER/'model.py')
metric=module('filter62_frozen57_metrics',HERE.parent/'python-game-error-quality-v57-study/model.py')
load,raw,sha= h.load,h.raw,h.sha
def bound(name,path,helper):
    before=sys.modules.get('helpers')
    try:sys.modules['helpers']=helper;return module(name,path)
    finally:
        if before is None:sys.modules.pop('helpers',None)
        else:sys.modules['helpers']=before
def digest(data):return hashlib.sha256(data).hexdigest()
def planes_digest(planes):return digest(b''.join(p.astype('u1',copy=False).tobytes()for p in planes))
def canonical_digest(planes):return digest(b''.join(p.astype('<i2').tobytes()for p in planes))
def fixed_presets():
    calibration=load(FILTER/'calibration.json');selected=calibration['selected_preset']
    if selected!=dict(name='strong',alpha=24,beta=12,strength=3):raise ValueError('frozen strong calibration')
    if calibration['source_IDs']!=list(range(24)):raise ValueError('calibration uses only first24')
    for path,want in calibration['source_sha256'].items():assert sha(ROOT/path)==want,path
    return (filt.PRESETS[0],next(p for p in filt.PRESETS if p==selected))
def excluded():
    norm=h.f.f.normalize(tuple(np.zeros(shape,np.int16)for shape in((480,720),(240,360),(240,360))))
    mask=norm[0]==128;mask.setflags(write=False);return mask

def pins():
    paths={ROOT/p for p in load(CUSTOM/'results.json')['source_sha256']}
    for folder in(FILTER,*NATIVE_SOURCES):
        data=load(folder/'results.json');paths.add(folder/'results.json');paths|={ROOT/p for p in data['source_sha256']}
    paths|={FILTER/'model.py',FILTER/'calibration.json',FILTER/'calibrate.py',SOURCE/'manifest.json',CUSTOM/'results.json',
        HERE.parent/'python-game-error-quality-v57-study/model.py',HERE.parent/'python-game-error-quality-v57-study/verify.py'}
    paths|={HERE/name for name in('helpers.py','adapter.py','benchmark.py','test_model.py')}
    return {p.relative_to(ROOT).as_posix():sha(p)for p in sorted(paths)}
