"""Frozen shared analysis, exact sender and unrounded block cost primitives."""
from pathlib import Path
import importlib.util,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
old=module('quantmotion53_frozen47_helpers',HERE.parent/'python-game-motion-v47-study/helpers.py')
producer=old.bound('quantmotion53_frozen47_sender',HERE.parent/'python-game-motion-v47-study/model.py',old)
m,n,rx,analysis,global_search,base=old.m,old.n,old.rx,old.analysis,old.global_search,old.base
SOURCE,CONTROL,GOLDEN=old.SOURCE,old.CONTROL,old.GOLDEN
load,sha,digest=old.load,old.sha,old.digest
def bound(name,path,helper):return old.bound(name,path,helper)
def raw(desc,folder=HERE):return old.raw(desc,folder)
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def pins():
    paths={ROOT/p for p in old.pins()};paths|={HERE/name for name in('helpers.py','model.py','benchmark.py','test_model.py')}
    paths|={HERE.parent/'python-game-signal-v39-study/model.py',HERE.parent/'python-game-motion-v47-study/results.json',HERE.parent/'python-game-guarded-motion-v50-study/results.json'}
    return {path.relative_to(ROOT).as_posix():sha(path)for path in sorted(paths)}
