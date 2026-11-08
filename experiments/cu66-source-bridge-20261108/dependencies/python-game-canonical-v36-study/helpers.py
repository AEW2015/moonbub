"""Pinned source and frozen codec imports for CN36 research."""
from pathlib import Path
import importlib.util, sys, json, hashlib, zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
old=module('canonical36_frozen35',HERE.parent/'python-game-controller-v35-study/helpers.py')
m,n,mask,p=old.m,old.n,old.mask,old.p
entropy=old.shared.entropy
HUD=old.HUD
load,sha,digest=old.load,old.sha,old.digest
def raw(desc,folder=HERE):return old.raw(desc,folder)
def blob(data):
    packed=zlib.compress(data,9);path='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/path).write_bytes(packed)
    return dict(path=path,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def pins():
    paths={ROOT/v for v in old.pins()};paths|={HERE/v for v in ('helpers.py','model.py','benchmark.py','test_model.py')}
    paths|={HERE.parent/'python-game-controller-v35-study/results.json',HERE.parent/'python-game-aligned-v35-study/results.json'}
    return {v.relative_to(ROOT).as_posix():sha(v) for v in sorted(paths)}
