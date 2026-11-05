"""Namespaced frozen AB38/CS38 imports and local artifact paths."""
from pathlib import Path
import importlib.util,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
BASE=HERE.parent/'python-game-binary-v38-study'
CONTROL=HERE.parent/'python-game-control-qual-v40-study'

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);sys.modules[name]=obj;spec.loader.exec_module(obj);return obj
old=module('binary_qual_v40_frozen_helpers',BASE/'helpers.py')
# `frame_verify.py` imports its helper by this module name; use the already
# loaded frozen helper under the expected import alias, with no encoder loaded.
sys.modules['helpers']=old
f=old.f
decoder=old.module('binary_qual_v40_independent_ab38_decoder',BASE/'decoder.py')
frame=module('binary_qual_v40_frame_proof',BASE/'frame_verify.py')
load,sha,digest=old.load,old.sha,old.digest

def raw(desc,folder=HERE):return old.raw(desc,folder)
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def pins():
    paths={ROOT/p for p in old.pins()}
    paths|={HERE/p for p in ('bridge.py','benchmark.py','verify.py','README.md')}
    paths|={CONTROL/'results.json',CONTROL/'prepare.py',CONTROL/'verify.py',CONTROL/'README.md'}
    paths|={ROOT/'experiments/python-game-source-v40-study/manifest.json',ROOT/'experiments/python-game-source-v40-study/prepare.py'}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
