from pathlib import Path
import hashlib,importlib.util,json,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value

old=module('binary38_frozen37_helpers',HERE.parent/'python-game-implicit-v37-study/helpers.py')
f=module('binary38_frozen37_decoder',HERE.parent/'python-game-implicit-v37-study/verify.py')
load,sha,digest=old.load,old.sha,old.digest

def raw(desc,folder=HERE):return old.raw(desc,folder)

def blob(data):
    stored=zlib.compress(data,9);name='objects/'+digest(stored)+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(stored)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(stored))

def pins():
    paths={ROOT/p for p in old.pins()}
    paths|={HERE/p for p in ('helpers.py','model.py','decoder.py','frame_verify.py','benchmark.py','test_model.py')}
    paths|={HERE.parent/'python-game-implicit-v37-study/verify.py',HERE.parent/'python-game-implicit-v37-study/results.json'}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
