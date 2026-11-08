"""Frozen43 decode primitives and577 retained CS38 input packets."""
from pathlib import Path
import hashlib,importlib.util,json,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
BASE=HERE.parent/'python-game-direct-rx-v43-study'
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
def bound(name,path,helper):
    before=sys.modules.get('helpers')
    try:sys.modules['helpers']=helper;return module(name,path)
    finally:
        if before is None:sys.modules.pop('helpers',None)
        else:sys.modules['helpers']=before
old=module('canonical66_frozen43_helpers',BASE/'helpers.py');m,f,arithmetic=old.m,old.f,old.arithmetic
oldrx=bound('canonical66_frozen43_receiver',BASE/'receiver.py',old)
FOLDERS=old.FOLDERS
load,sha,digest=old.load,old.sha,old.digest
def raw(desc,folder=HERE):return old.raw(desc,folder)
def blob(data):
    stored=zlib.compress(data,9);name='objects/'+digest(stored)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(stored)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(stored))
def pins():
    paths={ROOT/p for p in old.pins()};paths|={HERE/name for name in('helpers.py','protocol.py','receiver.py','benchmark.py','test_model.py')}
    paths|={HERE.parent/'python-game-recent-reference-study/recent_codec.py'}
    return {path.relative_to(ROOT).as_posix():sha(path)for path in sorted(paths)}
