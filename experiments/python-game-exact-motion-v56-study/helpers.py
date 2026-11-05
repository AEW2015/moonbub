"""Frozen post-RDO proposals, exact fine-bit cost and direct receive primitives."""
from pathlib import Path
import importlib.util,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
old=module('exactmotion56_frozen53_helpers',HERE.parent/'python-game-quantized-motion-v53-study/helpers.py')
proxy=old.bound('exactmotion56_frozen53_model',HERE.parent/'python-game-quantized-motion-v53-study/model.py',old)
m,n,rx,analysis,global_search,base,producer=old.m,old.n,old.rx,old.analysis,old.global_search,old.base,old.producer
AB=old.old.AB;fine=proxy.fine;geometry=proxy.geometry
SOURCE,CONTROL,GOLDEN=old.SOURCE,old.CONTROL,old.GOLDEN
load,sha,digest=old.load,old.sha,old.digest
def bound(name,path,helper):return old.bound(name,path,helper)
def raw(desc,folder=HERE):return old.raw(desc,folder)
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def pins():
    paths={ROOT/p for p in old.pins()};paths|={HERE/name for name in('helpers.py','model.py','benchmark.py','test_model.py')}
    paths|={HERE.parent/'python-game-quantized-motion-v53-study/results.json'}
    return {path.relative_to(ROOT).as_posix():sha(path)for path in sorted(paths)}
