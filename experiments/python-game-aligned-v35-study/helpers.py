from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import zlib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
V34=HERE.parent/'python-game-controller-v34-study'
HUD=HERE.parent/'python-game-hud-runs-v33-study'


def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m


root=module('aligned35_root_helpers',V34/'helpers.py')
m,n,adaptive,shared,select30,p=root.m,root.n,root.adaptive,root.shared,root.select30,root.p
mask=module('aligned35_mask',HERE/'model.py')
standard=module('aligned35_native',HERE.parent/'python-game-standard-v24-study/model.py')
load,sha,digest,raw=root.load,root.sha,root.digest,root.raw


def blob(data):
    packed=zlib.compress(data,9);path='objects/'+digest(packed)+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True);(HERE/path).write_bytes(packed)
    return dict(path=path,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))


def pins():
    paths={ROOT/path for path in root.pins()}
    paths|=set(HERE.glob('*.py'))
    paths.add(HERE.parent/'python-game-standard-v24-study/model.py')
    paths.add(V34/'results.json')
    return {v.relative_to(ROOT).as_posix():sha(v) for v in sorted(paths)}


def producer_pins():
    # Replay-only verifier/tests can be repaired without changing a producer.
    return {path:sha for path,sha in pins().items()
            if not Path(path).name.startswith(('test_', 'verify'))}


def source(src):
    import numpy as np
    original=n.source(src)
    masked=mask.mask_source(original,n.RECTS,policy='core8')
    words=n.original(src)
    patches=tuple(words[y:y+hh,x:x+w] for x,y,w,hh in n.RECTS)
    rgb=m.ft.planes_to_rgb(original);changed=m.ft.planes_to_rgb(masked)
    outside=~mask.coverage(rgb.shape[:2],n.RECTS)
    np.testing.assert_array_equal(rgb[outside],changed[outside])
    np.testing.assert_array_equal(n.overlay(m.C.corpus.rgb565(rgb),patches),n.overlay(m.C.corpus.rgb565(changed),patches))
    return original,masked,words,patches
