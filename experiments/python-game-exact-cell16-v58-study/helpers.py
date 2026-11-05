"""Frozen32-cell source proposals, new16/8-cell exact mixture geometry."""
from pathlib import Path
import importlib.util,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
old=module('exactcell58_frozen56_helpers',HERE.parent/'python-game-exact-motion-v56-study/helpers.py')
m,n,rx,analysis,global_search,base,producer,AB,fine=old.m,old.n,old.rx,old.analysis,old.global_search,old.base,old.producer,old.AB,old.fine
SOURCE,CONTROL,GOLDEN=old.SOURCE,old.CONTROL,old.GOLDEN
load,sha,digest=old.load,old.sha,old.digest
def bound(name,path,helper):return old.bound(name,path,helper)
def raw(desc,folder=HERE):return old.raw(desc,folder)
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def geometry(axis):
    height,width=(480,720)if axis==0 else(240,360);size=16 if axis==0 else 8
    yy,xx=np.mgrid[:height,:width];pixels=(yy//size)*45+xx//size
    by,bx=np.mgrid[:height//8,:width//8];blocks=(by//(size//8))*45+bx//(size//8)
    return pixels.reshape(-1),blocks.reshape(-1)
def pins():
    paths={ROOT/p for p in old.pins()};paths|={HERE/name for name in('helpers.py','model.py','benchmark.py','test_model.py')}
    paths|={HERE.parent/'python-game-exact-motion-v56-study/results.json'}
    return {path.relative_to(ROOT).as_posix():sha(path)for path in sorted(paths)}
