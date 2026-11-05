"""Explicit frozen direct-sender dependencies for fast zero-map analysis."""
from pathlib import Path
import importlib.util,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
old=module('analysis37_direct_helpers',HERE.parent/'python-game-direct-v37-study/helpers.py')
m,n,p,entropy,HUD,canonical,maskplan,PLAN=old.m,old.n,old.p,old.entropy,old.HUD,old.canonical,old.maskplan,old.PLAN
load,sha,digest=old.load,old.sha,old.digest
def raw(desc,folder=HERE):return old.raw(desc,folder)
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def pins():
    paths={ROOT/p for p in old.pins()}
    paths|={HERE/v for v in ('helpers.py','model.py','benchmark.py','test_model.py')}
    paths|={HERE.parent/'python-game-direct-v37-study/model.py',HERE.parent/'python-game-direct-v37-study/results.json'}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
