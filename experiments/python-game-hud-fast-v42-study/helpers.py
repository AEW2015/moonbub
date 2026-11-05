"""Explicit frozen HUD codec imports and qualified packet fixture access."""
from pathlib import Path
import hashlib,importlib.util,json,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
QUAL=HERE.parent/'python-game-control-qual-v40-study'
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
hud32=module('fast42_frozen_hud32',HERE.parent/'python-game-hud-v32-study/model.py')
baseline=module('baseline',HERE.parent/'python-game-hud-runs-v33-study/baseline.py')
decoder=module('decoder',HERE.parent/'python-game-hud-runs-v33-study/decoder.py')
hud33=module('fast42_frozen_hud33',HERE.parent/'python-game-hud-runs-v33-study/model.py')
p,h=baseline.p,baseline.h
def load(path):return json.loads(Path(path).read_text())
def digest(data):return hashlib.sha256(data).hexdigest()
def sha(path):return digest(Path(path).read_bytes())
def raw(desc,folder=HERE):
    stored=(folder/desc['path']).read_bytes()
    if digest(stored)!=desc['stored_sha256']:raise ValueError('stored fixture hash')
    data=zlib.decompress(stored)
    if len(data)!=desc['raw_bytes']or digest(data)!=desc['raw_sha256']:raise ValueError('raw fixture hash/length')
    return data
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def pins():
    qual=load(QUAL/'results.json');paths={ROOT/path for path in qual['source_pins_sha256']}
    paths|={HERE/name for name in('helpers.py','model.py','benchmark.py','test_model.py')}
    paths|={QUAL/'results.json',HERE.parent/'python-game-hud-v32-study/model.py',HERE.parent/'python-game-hud-runs-v33-study/model.py',
        HERE.parent/'python-game-hud-runs-v33-study/baseline.py',HERE.parent/'python-game-hud-runs-v33-study/decoder.py'}
    return {path.relative_to(ROOT).as_posix():sha(path)for path in sorted(paths)}
