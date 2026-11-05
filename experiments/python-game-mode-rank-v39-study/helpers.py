"""Frozen SP38 geometry/arithmetic and AB38 bit coder dependencies."""
from pathlib import Path
import importlib.util,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
old=module('rank39_spatial38_helpers',HERE.parent/'python-game-spatial-v38-study/helpers.py')
m,n,p,entropy,HUD,canonical=old.m,old.n,old.p,old.entropy,old.HUD,old.canonical
f=module('rank39_frozen_spatial38_decoder',HERE.parent/'python-game-spatial-v38-study/verify.py')
spatial=module('rank39_frozen_spatial38_predictor',HERE.parent/'python-game-spatial-v38-study/model.py')
binary=module('rank39_frozen_binary38',HERE.parent/'python-game-binary-v38-study/model.py')
load,sha,digest=old.load,old.sha,old.digest
def raw(desc,folder=HERE):return old.raw(desc,folder)
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def pins():
    paths={ROOT/path for path in old.pins()}
    paths|={HERE/name for name in('helpers.py','model.py','benchmark.py','test_model.py')}
    paths|={HERE.parent/'python-game-spatial-v38-study/model.py',HERE.parent/'python-game-spatial-v38-study/verify.py',
            HERE.parent/'python-game-spatial-v38-study/results.json',HERE.parent/'python-game-binary-v38-study/model.py'}
    return {path.relative_to(ROOT).as_posix():sha(path) for path in sorted(paths)}
