"""Explicit imports and immutable retained source access for guarded masking."""
from pathlib import Path
import hashlib,importlib.util,json,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

old=module('guard35_frozen34_helpers',HERE.parent/'python-game-controller-v34-study/helpers.py')
m,n,adaptive,shared,p,select30=old.m,old.n,old.adaptive,old.shared,old.p,old.select30
mask=module('guard35_core_mask',HERE.parent/'python-game-aligned-v35-study/model.py')
standard=module('guard35_native24',HERE.parent/'python-game-standard-v24-study/model.py')
load,sha,digest,raw=old.load,old.sha,old.digest,old.raw
HUD=HERE.parent/'python-game-hud-runs-v33-study'
POLICIES=('control','guarded_core8')

def raw(desc,folder=HERE):return old.raw(desc,folder)

def blob(data):
    packed=zlib.compress(data,9);path='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/path).write_bytes(packed)
    return dict(path=path,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))

def pins():
    paths={ROOT/path for path in old.pins()};paths|=set(HERE.glob('*.py'))
    paths|={HERE.parent/'python-game-aligned-v35-study/model.py',HERE.parent/'python-game-standard-v24-study/model.py',
            HERE.parent/'python-game-controller-v34-study/results.json'}
    return {q.relative_to(ROOT).as_posix():sha(q) for q in sorted(paths)}
