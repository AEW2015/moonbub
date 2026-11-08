"""Explicit imports of the frozen v32 controller's source/search/codec helpers.

Unlike importing its benchmark by basename, this never binds generic `model`,
`protocol`, `benchmark` or `controller` names in sys.modules.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V32 = HERE.parent/'python-game-controller-v32-study'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


m = module('shared33_runtime28', HERE.parent/'python-game-runtime-v28-study/model.py')
n = module('shared33_native25_helpers', HERE.parent/'python-game-native-motion-v25-study/benchmark.py')
adaptive = module('shared33_adaptive29', HERE.parent/'python-game-adaptive-v29-study/model.py')
band = module('shared33_frozen_band30', HERE.parent/'python-game-band-v30-study/model.py')
shared = module('shared33_implementation', HERE/'model.py')


def load(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(data): return hashlib.sha256(data).hexdigest()


def raw(desc, folder=HERE):
    path = Path(desc['path'])
    assert not path.is_absolute() and '..' not in path.parts
    packed = (folder/path).read_bytes()
    assert digest(packed) == desc['stored_sha256']
    dc = zlib.decompressobj()
    data = dc.decompress(packed, desc['raw_bytes']+1)
    assert dc.eof and not dc.unconsumed_tail and not dc.unused_data
    assert len(data) == desc['raw_bytes'] and digest(data) == desc['raw_sha256']
    return data


def blob(data):
    packed = zlib.compress(data, 9)
    path = 'objects/'+digest(packed)+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True)
    (HERE/path).write_bytes(packed)
    return dict(path=path, raw_bytes=len(data), raw_sha256=digest(data), stored_sha256=digest(packed))


def pins():
    inherited = load(V32/'results.json')['source_sha256']
    paths = {ROOT/path for path in inherited}
    paths |= {V32/'results.json', V32/'benchmark.py', HERE/'model.py', HERE/'helpers.py',
              HERE/'benchmark.py', HERE/'verify.py', HERE/'test_model.py'}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}


def cases():
    inputs = load(n.V24/'results.json')['inputs']
    for case in load(V32/'results.json')['cases']:
        if case['policy'] == 'band_control':
            inp = next(i for i in inputs if i['scene'] == case['scene'])
            yield case, inp


def prepare(source, ref, row, kind):
    return adaptive.analyze_with(m.base, source, ref, search_policy='adaptive_zero2',
        epoch=25, frame_id=row['id'], reference_id=row['reference_id'], block_size=32,
        motion_mode='zero' if kind == 'zero' else 'block', motion_precision='half', penalty=0)


def old_pair(prepared, q):
    return m.encode_prepared(prepared, q), band.encode_with(m, prepared, q, policy='band_strict')


def packet_planes(packet):
    meta = m.parse_metadata(packet)
    pos = m.HEADER.size + meta['qmap_bytes'] + meta['vector_bytes']
    result = []
    for length in meta['plane_lengths']:
        result.append(packet[pos:pos+length]); pos += length
    return result
