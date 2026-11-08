"""Explicit path imports and bounded retained-artifact access for v34."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

frame=module('controller34_frame',HERE/'model.py');m=frame.runtime
p=module('controller34_protocol',HERE/'protocol.py')
old=module('controller34_shared_helpers',HERE.parent/'python-game-shared-v33-study/helpers.py')
n,adaptive,shared=old.n,old.adaptive,old.shared
full=module('controller34_full33',HERE.parent/'python-game-split-v33-study/model.py')
selective=module('controller34_selective',HERE.parent/'python-game-selective-v34-study/model.py')
select30=module('controller34_select30',HERE.parent/'python-game-controller-v30-study/controller.py')
POLICIES=('control','hierarchy_full','hierarchy_select25')

def load(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(data):return hashlib.sha256(data).hexdigest()

def raw(desc,folder=HERE):
    path=Path(desc['path']);assert not path.is_absolute() and '..' not in path.parts
    packed=(folder/path).read_bytes();assert digest(packed)==desc['stored_sha256']
    dc=zlib.decompressobj();out=dc.decompress(packed,desc['raw_bytes']+1)
    assert dc.eof and not dc.unused_data and not dc.unconsumed_tail and len(out)==desc['raw_bytes'] and digest(out)==desc['raw_sha256']
    return out

def blob(data):
    packed=zlib.compress(data,9);path='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/path).write_bytes(packed)
    return dict(path=path,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))

def pins():
    paths={ROOT/path for path in load(HERE.parent/'python-game-global-v33-study/results.json')['source_sha256']}
    for folder in ('python-game-shared-v33-study','python-game-hud-runs-v33-study','python-game-hierarchy-v34-study','python-game-selective-v34-study'):
        result=HERE.parent/folder/'results.json'
        if result.exists():
            paths.add(result);paths|={ROOT/path for path in load(result)['source_sha256']}
        paths|=set((HERE.parent/folder).glob('*.py'))
    paths|=set(HERE.glob('*.py'));paths.add(HERE.parent/'python-game-global-v33-study/results.json')
    hud=load(HERE.parent/'python-game-hud-runs-v33-study/results.json')
    for case in hud['cases']:
        paths|={HERE.parent/'python-game-hud-runs-v33-study'/r['packet']['path'] for r in case['rows']}
    return {q.relative_to(ROOT).as_posix():sha(q) for q in sorted(paths)}
