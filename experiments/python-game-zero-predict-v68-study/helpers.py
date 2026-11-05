from pathlib import Path
import importlib.util,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
old=module('zero68_helpers66',HERE.parent/'python-game-canonical-tag-v66-study/helpers.py')
m,rx,f=old.m,old.oldrx,old.f
raw,sha,digest,load=old.raw,old.sha,old.digest,old.load
SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
def pins():
 paths={ROOT/p for p in old.pins()};paths|={HERE/n for n in ('helpers.py','model.py','benchmark.py','test_model.py')}
 return {p.relative_to(ROOT).as_posix():sha(p)for p in sorted(paths)}
