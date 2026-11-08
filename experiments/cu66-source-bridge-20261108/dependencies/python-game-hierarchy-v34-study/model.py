"""Host-side minimum actual-byte HM34 motion component encoder."""
from pathlib import Path
import importlib.util
import struct
import sys
import zlib
import numpy as np

HERE = Path(__file__).resolve().parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


decoder = _load('hierarchy34_syntax_decoder', HERE/'decoder.py')
frozen = _load('hierarchy34_host_gm27_encoder', HERE.parent/'python-game-prediction-v26-study/model.py')
unpack, HEADER, CRC = decoder.unpack, decoder.HEADER, decoder.CRC
MAGIC, VERSION = decoder.MAGIC, decoder.VERSION


class Bits:
    def __init__(self):
        self.bits = []

    def put(self, value, n):
        self.bits.extend((value >> i) & 1 for i in range(n-1, -1, -1))

    def finish(self):
        result = bytearray((len(self.bits)+7)//8)
        for i, bit in enumerate(self.bits):
            result[i >> 3] |= bit << (7-(i & 7))
        return bytes(result)


def _rice(bits, value, k, escape_bits):
    q = value >> k
    if q >= 7:
        bits.put(127, 7)
        bits.put(value, escape_bits)
    else:
        bits.put((1 << q)-1, q)
        bits.put(0, 1)
        bits.put(value & ((1 << k)-1), k)


def _cost(values, k, escape_bits):
    return sum(7+escape_bits if v >> k >= 7 else (v >> k)+1+k for v in values)


def _choose(values, maximum_k, escape_bits):
    return min(range(maximum_k+1), key=lambda k: _cost(values, k, escape_bits))


def _zig(v):
    return 2*v if v >= 0 else -2*v-1


def _seal(mode, width, height, parent, payload):
    body = HEADER.pack(MAGIC, VERSION, mode, width, height, len(parent), len(payload))+parent+payload
    return body+CRC.pack(zlib.crc32(body))


def pack(parent, child, width, height, *, return_info=False):
    """Preserve exact child vectors; choose min actual complete bytes, ties flat.

    Both fields must be owned/int8-compatible arrays of exact 32/16 grid shape
    with components bounded to [-18,18]. Encoder search never runs in unpack.
    """
    pshape, cshape = decoder.geometry(width, height)
    p, c = np.asarray(parent), np.asarray(child)
    for a, shape in ((p, pshape), (c, cshape)):
        if a.dtype != np.int8 or a.shape != shape+(2,) or np.any(np.abs(a.astype(np.int16)) > 18):
            raise ValueError('HM34 bounded int8 vector field')
    seed = np.repeat(np.repeat(p, 2, axis=0), 2, axis=1)[:cshape[0], :cshape[1]]
    delta = c.astype(np.int16)-seed.astype(np.int16)
    indices = np.flatnonzero(np.any(delta != 0, axis=2).reshape(-1))
    values = delta.reshape(-1, 2)[indices]
    axes = [[_zig(int(v)) for v in values[:, axis]] for axis in (0, 1)]
    ks = [_choose(axis, 6, 7) for axis in axes]
    parent_bytes = frozen.pack_vectors(p)
    flat_bytes = frozen.pack_vectors(c)
    candidates = [_seal(0, width, height, b'', flat_bytes)]
    gaps = [int(index)-(int(indices[i-1]) if i else -1)-1 for i, index in enumerate(indices)]
    escape_bits = max(1, (cshape[0]*cshape[1]-1).bit_length())
    kg = _choose(gaps, min(10, escape_bits), escape_bits)
    bits = Bits()
    for i, gap in enumerate(gaps):
        _rice(bits, gap, kg, escape_bits)
        for axis in (0, 1):
            _rice(bits, axes[axis][i], ks[axis], 7)
    payload = struct.pack('<HBBB', len(indices), kg, *ks)+bits.finish()
    candidates.append(_seal(1, width, height, parent_bytes, payload))
    bits = Bits()
    for py in range(pshape[0]):
        for px in range(pshape[1]):
            cells = []
            for local in range(4):
                y, x = 2*py+local//2, 2*px+local%2
                if y < cshape[0] and x < cshape[1] and np.any(delta[y, x]):
                    cells.append((local, y, x))
            bits.put(bool(cells), 1)
            if not cells:
                continue
            bits.put(sum(1 << cell[0] for cell in cells), 4)
            for _, y, x in cells:
                for axis in (0, 1):
                    _rice(bits, _zig(int(delta[y, x, axis])), ks[axis], 7)
    candidates.append(_seal(2, width, height, parent_bytes, bytes(ks)+bits.finish()))
    selected = min(range(len(candidates)), key=lambda mode: len(candidates[mode]))
    packet = candidates[selected]
    info = dict(selected_mode=selected, selected_mode_name=decoder.MODE_NAMES[selected],
                candidates=[dict(mode=mode, name=decoder.MODE_NAMES[mode], bytes=len(data))
                            for mode, data in enumerate(candidates)],
                parent_gm27_bytes=len(parent_bytes), flat_child_gm27_bytes=len(flat_bytes),
                refinement_vectors=len(indices), child_vectors=cshape[0]*cshape[1],
                component_bytes=len(packet), sparse_rice_parameters=[kg]+ks,
                header_bytes=HEADER.size, crc_bytes=CRC.size,
                stable_tie_order=list(decoder.MODE_NAMES))
    return (packet, info) if return_info else packet
