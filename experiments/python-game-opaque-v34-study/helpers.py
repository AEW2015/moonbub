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


root=module('opaque34_root_helpers',V34/'helpers.py')
m,n,adaptive,shared,select30,p=root.m,root.n,root.adaptive,root.shared,root.select30,root.p
mask=module('opaque34_mask',HERE/'model.py')
standard=module('opaque34_native',HERE.parent/'python-game-standard-v24-study/model.py')
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
    original=n.source(src)
    masked=mask.mask_source(original,n.RECTS)
    words=n.original(src)
    patches=tuple(words[y:y+hh,x:x+w] for x,y,w,hh in n.RECTS)
    before=m.C.corpus.rgb565(m.ft.planes_to_rgb(original))
    after=m.C.corpus.rgb565(m.ft.planes_to_rgb(masked))
    import numpy as np
    np.testing.assert_array_equal(n.overlay(before,patches),n.overlay(after,patches))
    for axis,(a,b) in enumerate(zip(original,masked)):
        changed=np.zeros(a.shape,bool);scale=1 if axis==0 else 2
        for x,y,w,hh in n.RECTS:changed[y//scale:(y+hh)//scale,x//scale:(x+w)//scale]=True
        np.testing.assert_array_equal(a[~changed],b[~changed])
        inner=np.zeros(a.shape,bool);border=0 if axis==0 else 1
        for x,y,w,hh in n.RECTS:inner[y//scale+border:(y+hh)//scale,x//scale+border:(x+w)//scale]=True
        assert np.all(b[inner]==128)
    return original,masked,words,patches


def requested_full_mask_audit(source,patches):
    import numpy as np
    full=mask.mask_source(source,n.RECTS,preserve_chroma_border=False)
    before=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(source)),patches)
    after=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(full)),patches)
    changed=before!=after
    return dict(visible_precodec_equal=not bool(changed.any()),changed_visible_rgb565_words=int(changed.sum()),
                full_masked_source_sha256=digest(b''.join(v.astype('u1').tobytes() for v in full)))
