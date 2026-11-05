"""Frozen AB38 imports; own extended-campaign artifact storage."""
from pathlib import Path
import sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];BASE=HERE.parent/'python-game-binary-v38-study'
sys.path.insert(0,str(BASE))
import helpers as old
f=old.f
decoder=old.module('binary_full39_frozen_decoder',BASE/'decoder.py')
frame=old.module('binary_full39_frozen_frame_proof',BASE/'frame_verify.py')
load,sha,digest=old.load,old.sha,old.digest
def raw(desc,folder=HERE):return old.raw(desc,folder)
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def pins():
    paths={ROOT/p for p in old.pins()};paths|={HERE/'bridge.py',HERE/'benchmark.py'}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
