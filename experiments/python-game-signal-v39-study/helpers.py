"""Frozen predictor/rank grammar plus exact source fixtures for fine RDO pilot."""
from pathlib import Path
import importlib.util,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
bootstrap=module('signal39_spatial_bootstrap',HERE.parent/'python-game-spatial-v38-study/helpers.py')
m,n,p,entropy,HUD,canonical=bootstrap.m,bootstrap.n,bootstrap.p,bootstrap.entropy,bootstrap.HUD,bootstrap.canonical
old=module('signal39_rank_helpers',HERE.parent/'python-game-mode-rank-v39-study/helpers.py')
m,n,p,entropy,HUD,canonical,f,spatial,binary=old.m,old.n,old.p,old.entropy,old.HUD,old.canonical,old.f,old.spatial,old.binary
rank=module('signal39_frozen_rank39',HERE.parent/'python-game-mode-rank-v39-study/model.py')
load,sha,digest=old.load,old.sha,old.digest
def raw(desc,folder=HERE):return old.raw(desc,folder)
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def pins():
    paths={ROOT/path for path in old.pins()};paths|={HERE/name for name in('helpers.py','model.py','benchmark.py','test_model.py')}
    paths|={HERE.parent/'python-game-mode-rank-v39-study/model.py',HERE.parent/'python-game-mode-rank-v39-study/results.json',HERE.parent/'python-game-mode-rank-v39-study/verify.py'}
    return {path.relative_to(ROOT).as_posix():sha(path)for path in sorted(paths)}
