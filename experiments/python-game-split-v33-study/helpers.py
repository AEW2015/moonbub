from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import zlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);sys.modules[name]=obj;spec.loader.exec_module(obj);return obj


h=module('split33_source_helpers',HERE.parent/'python-game-shared-v33-study/helpers.py')
m,n,adaptive,band=h.m,h.n,h.adaptive,h.band
split=module('split33_motion_model',HERE/'model.py')
protocol=module('split33_cp27',HERE.parent/'python-game-runtime-v28-study/protocol.py')
load,sha,digest,raw,cases=h.load,h.sha,h.digest,h.raw,h.cases


def blob(data):
    packed=zlib.compress(data,9);path='objects/'+digest(packed)+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True);(HERE/path).write_bytes(packed)
    return dict(path=path,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))


def pins():
    paths={ROOT/p for p in h.pins()}
    paths|=set(HERE.glob('*.py'))
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
