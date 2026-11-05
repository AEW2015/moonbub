"""Frozen CS38 wire/arithmetic/legacy receive primitives and retained packets."""
from pathlib import Path
import hashlib,importlib.util,json,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
FOLDERS=('python-game-binary-v38-study','python-game-binary-full-v39-study','python-game-binary-qual-v40-study')
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
old=module('directrx43_binary38_helpers',HERE.parent/'python-game-binary-v38-study/helpers.py')
f,m=old.f,old.f.m
arithmetic=module('directrx43_frozen_AB38_decoder',HERE.parent/'python-game-binary-v38-study/decoder.py')
# The frozen adapter uses an absolute ``import helpers``. Bind that import to
# its OWN frozen helper only while loading, then restore the caller's alias.
previous_helpers=sys.modules.get('helpers')
try:
    sys.modules['helpers']=old
    adapter=module('directrx43_frozen_CS38_adapter',HERE.parent/'python-game-binary-v38-study/frame_verify.py')
finally:
    if previous_helpers is None:sys.modules.pop('helpers',None)
    else:sys.modules['helpers']=previous_helpers
load,sha,digest=old.load,old.sha,old.digest
def raw(desc,folder=HERE):return old.raw(desc,folder)
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def pins():
    paths={ROOT/path for path in old.pins()};paths|={HERE/name for name in('helpers.py','receiver.py','benchmark.py','test_model.py')}
    paths|={HERE.parent/'python-game-binary-v38-study/decoder.py',HERE.parent/'python-game-binary-v38-study/frame_verify.py'}
    for name in FOLDERS:
        path=HERE.parent/name/'results.json';data=load(path);paths.add(path)
        paths|={ROOT/p for p in data.get('source_sha256',data.get('source_pins_sha256',{}))}
    return {path.relative_to(ROOT).as_posix():sha(path)for path in sorted(paths)}
