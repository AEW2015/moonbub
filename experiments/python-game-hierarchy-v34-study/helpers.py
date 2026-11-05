from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SPLIT = HERE.parent/'python-game-split-v33-study'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


old = module('hierarchy34_frozen_split_helpers', SPLIT/'helpers.py')
m, n = old.m, old.n
model = module('hierarchy34_encoder', HERE/'model.py')
decoder = model.decoder
load, sha, digest, raw = old.load, old.sha, old.digest, old.raw


def blob(data):
    packed = zlib.compress(data, 9)
    path = 'objects/'+digest(packed)+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True)
    (HERE/path).write_bytes(packed)
    return dict(path=path, raw_bytes=len(data), raw_sha256=digest(data), stored_sha256=digest(packed))


def pins():
    paths = {ROOT/p for p in load(SPLIT/'results.json')['source_sha256']}
    paths |= {SPLIT/'results.json'} | set(HERE.glob('*.py'))
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}


def vectors(packet, block_size):
    meta = m.parse_metadata(packet)
    assert meta['block_size'] == block_size
    offset = m.HEADER.size+meta['qmap_bytes']
    payload = packet[offset:offset+meta['vector_bytes']]
    # Frame keys carry no motion component, and HM34 keys remain zero bytes.
    if meta['key']:
        assert not payload
        import numpy as np
        return np.zeros(((meta['height']+block_size-1)//block_size,
                         (meta['width']+block_size-1)//block_size, 2), np.int8), payload
    return decoder.unpack_gm27(payload, (meta['width']+block_size-1)//block_size,
                              (meta['height']+block_size-1)//block_size), payload


def guard(control, trials, size_key):
    qualifying = [t for t in trials if t[size_key] <= 49152 and t[size_key] < control['complete_bytes']
                  and t['hybrid']['active_squared_error'] <= control['hybrid']['active_squared_error']]
    choices = [('v32_control', control['complete_bytes'], control['hybrid'])]
    choices.extend((t['kind'], t[size_key], t['hybrid']) for t in qualifying)
    kind, size, metric = min(choices, key=lambda value: value[1])
    return dict(selected_kind=kind, complete_bytes=size, hybrid=metric,
                qualified_trial_kinds=[t['kind'] for t in qualifying])
