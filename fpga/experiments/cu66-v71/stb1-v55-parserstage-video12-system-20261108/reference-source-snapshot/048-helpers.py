from pathlib import Path
import importlib.util,sys,json,hashlib,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);sys.modules[name]=obj;spec.loader.exec_module(obj)
    return obj

old=module('implicit37_frozen36_helpers',HERE.parent/'python-game-canonical-v36-study/helpers.py')
cn=module('implicit37_frozen36_model',HERE.parent/'python-game-canonical-v36-study/model.py')
m,n,entropy=old.m,old.n,old.entropy
load,sha,digest=old.load,old.sha,old.digest

def raw(desc,folder=HERE):return old.raw(desc,folder)

def blob(data):
    packed=zlib.compress(data,9);path='objects/'+digest(packed)+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True);(HERE/path).write_bytes(packed)
    return dict(path=path,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))

def pins():
    paths={ROOT/p for p in old.pins()}
    paths|={HERE/f for f in ('helpers.py','model.py','benchmark.py','test_model.py')}
    paths|={HERE.parent/'python-game-canonical-v36-study/model.py',HERE.parent/'python-game-canonical-v36-study/results.json'}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
