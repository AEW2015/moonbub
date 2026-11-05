"""Isolated frozen primitives; source40 and owned-history motion comparison."""
from pathlib import Path
import hashlib,importlib.util,json,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SOURCE=HERE.parent/'python-game-source-v40-study';CONTROL=HERE.parent/'python-game-control-qual-v40-study';GOLDEN=HERE.parent/'python-game-binary-qual-v40-study'
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
def bound(name,path,helper):
    before=sys.modules.get('helpers')
    try:sys.modules['helpers']=helper;return module(name,path)
    finally:
        if before is None:sys.modules.pop('helpers',None)
        else:sys.modules['helpers']=before
base=module('motion47_integrated38_helpers',HERE.parent/'python-game-integrated-v38-study/helpers.py')
m,n=base.m,base.n
analysis=bound('motion47_analysis37',HERE.parent/'python-game-analysis-v37-study/model.py',base)
global_search=module('motion47_global33',HERE.parent/'python-game-global-v33-study/model.py')
AB=module('motion47_frozen_AB38_encoder',HERE.parent/'python-game-binary-v38-study/model.py')
rxh=module('motion47_rx43_helpers',HERE.parent/'python-game-direct-rx-v43-study/helpers.py')
rx=bound('motion47_direct43',HERE.parent/'python-game-direct-rx-v43-study/receiver.py',rxh)
load,sha,digest=base.load,base.sha,base.digest
def raw(desc,folder=HERE):return base.raw(desc,folder)
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def pins():
    paths={ROOT/p for p in base.pins()};paths|={ROOT/p for p in rxh.pins()}
    paths|={HERE/name for name in('helpers.py','model.py','benchmark.py','test_model.py')}
    paths|={SOURCE/'manifest.json',CONTROL/'results.json',GOLDEN/'results.json',HERE.parent/'python-game-global-v33-study/model.py',HERE.parent/'python-game-adaptive-v29-study/model.py',HERE.parent/'python-game-binary-v38-study/model.py'}
    return {path.relative_to(ROOT).as_posix():sha(path)for path in sorted(paths)}
