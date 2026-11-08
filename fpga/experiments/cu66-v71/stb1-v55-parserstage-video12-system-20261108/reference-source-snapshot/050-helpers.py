"""Frozen inputs and primitive dependencies for integrated CS37 sender."""
from pathlib import Path
import importlib.util,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);obj=importlib.util.module_from_spec(spec);sys.modules[name]=obj;spec.loader.exec_module(obj);return obj
old=module('integrated38_analysis37_helpers',HERE.parent/'python-game-analysis-v37-study/helpers.py')
m,n,p,entropy,HUD,canonical,maskplan,PLAN=old.m,old.n,old.p,old.entropy,old.HUD,old.canonical,old.maskplan,old.PLAN
cn=canonical
load,sha,digest=old.load,old.sha,old.digest
def raw(desc,folder=HERE):return old.raw(desc,folder)
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def pins():
    paths={ROOT/path for path in old.pins()}
    paths|={HERE/name for name in ('helpers.py','model.py','benchmark.py','test_model.py')}
    paths|={HERE.parent/'python-game-analysis-v37-study/model.py',HERE.parent/'python-game-analysis-v37-study/results.json',
            HERE.parent/'python-game-implicit-v37-study/model.py',HERE.parent/'python-game-implicit-v37-study/results.json'}
    return {path.relative_to(ROOT).as_posix():sha(path) for path in sorted(paths)}
