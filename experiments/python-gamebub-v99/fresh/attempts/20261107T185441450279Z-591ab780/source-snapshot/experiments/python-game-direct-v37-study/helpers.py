"""Pinned frozen dependencies and content-addressed direct-sender artifacts."""
from pathlib import Path
import hashlib,importlib.util,json,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
old=module('direct37_frozen36_helpers',HERE.parent/'python-game-canonical-v36-study/helpers.py')
m,n,p,entropy,HUD=old.m,old.n,old.p,old.entropy,old.HUD
canonical=module('direct37_frozen36_model',HERE.parent/'python-game-canonical-v36-study/model.py')
maskplan=module('direct37_maskplan36',HERE.parent/'python-game-maskplan-v36-study/model.py')
PLAN=maskplan.compile_plan((480,720),n.RECTS)
load,sha,digest=old.load,old.sha,old.digest
def raw(desc,folder=HERE):return old.raw(desc,folder)
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def pins():
    paths={ROOT/p for p in old.pins()}
    paths|={HERE/v for v in ('helpers.py','model.py','benchmark.py','test_model.py')}
    paths|={HERE.parent/'python-game-canonical-v36-study/results.json',HERE.parent/'python-game-canonical-v36-study/model.py',HERE.parent/'python-game-maskplan-v36-study/model.py'}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
