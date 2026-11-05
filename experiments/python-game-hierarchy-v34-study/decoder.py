"""HM34/v1 bounded syntax-only motion component decoder.

This module imports no encoder and does no canonical/minimum-size re-encoding.
The returned field is published only after every syntax/domain/padding check.
"""
import struct
import zlib
import numpy as np

MAGIC, VERSION, LIMIT = b'HM34', 1, 18
HEADER = struct.Struct('<4sBBHHHH')
CRC = struct.Struct('<I')
MODE_NAMES = ('flat_child', 'sparse_gap', 'parent_masks')


def geometry(width, height):
    if type(width) is not int or type(height) is not int or not 1 <= width <= 720 or not 1 <= height <= 480:
        raise ValueError('HM34 bounded geometry')
    return ((height+31)//32, (width+31)//32), ((height+15)//16, (width+15)//16)


class Reader:
    def __init__(self, data):
        self.data, self.pos, self.size = data, 0, len(data)*8

    def get(self, n):
        if not 0 <= n <= 16 or self.pos+n > self.size:
            raise ValueError('HM34 truncated bits')
        out = 0
        for _ in range(n):
            out = (out << 1) | ((self.data[self.pos >> 3] >> (7-(self.pos & 7))) & 1)
            self.pos += 1
        return out

    def end(self):
        remaining = self.size-self.pos
        if remaining >= 8 or self.get(remaining):
            raise ValueError('HM34 padding/exact bit length')


def rice(bits, k, maximum, escape_bits):
    q = 0
    while q < 7 and bits.get(1):
        q += 1
    if q == 7:
        value = bits.get(escape_bits)
        if value >> k < 7:
            raise ValueError('HM34 unnecessary Rice escape')
    else:
        value = (q << k) | bits.get(k)
    if value > maximum:
        raise ValueError('HM34 Rice domain')
    return value


def _predict(flat, i, mw, axis, mode):
    x, y = i % mw, i // mw
    left = int(flat[i-1, axis]) if x else 0
    if mode == 5:
        return left
    top = int(flat[i-mw, axis]) if y else 0
    right = int(flat[i-mw+(x+1 < mw), axis]) if y else 0
    return left+top+right-min(left, top, right)-max(left, top, right)


def unpack_gm27(data, mw, mh):
    """Standalone syntax-only GM27 vector grammar (modes 0 through 6)."""
    n = mw*mh
    if type(data) is not bytes or not 1 <= len(data) <= 1+2*n:
        raise ValueError('GM27 motion length')
    mode = data[0]
    if mode == 0:
        if len(data) != 3:
            raise ValueError('GM27 global length')
        flat = np.tile(np.frombuffer(data[1:], np.int8), (n, 1))
    elif mode == 1:
        if len(data) != 1+2*n:
            raise ValueError('GM27 dense length')
        flat = np.frombuffer(data[1:], np.int8).reshape(n, 2).copy()
    elif mode == 2:
        if (len(data)-1) % 4:
            raise ValueError('GM27 run length')
        flat = np.empty((n, 2), np.int8)
        count = 0
        for offset in range(1, len(data), 4):
            run, dx, dy = struct.unpack_from('<Hbb', data, offset)
            if not run or count+run > n:
                raise ValueError('GM27 run bounds')
            flat[count:count+run] = dx, dy
            count += run
        if count != n:
            raise ValueError('GM27 incomplete runs')
    elif mode == 3:
        if len(data) < 3 or (len(data)-3) % 4:
            raise ValueError('GM27 sparse length')
        default = np.frombuffer(data[1:3], np.int8)
        flat = np.tile(default, (n, 1))
        previous = -1
        for offset in range(3, len(data), 4):
            index, dx, dy = struct.unpack_from('<Hbb', data, offset)
            if not previous < index < n or (dx == default[0] and dy == default[1]):
                raise ValueError('GM27 sparse order/redundancy')
            flat[index] = dx, dy
            previous = index
    elif mode == 4:
        bits = Reader(data[1:])
        flat = np.empty((n, 2), np.int16)
        for i in range(n):
            for axis in (0, 1):
                code = bits.get(6)
                if code > 36:
                    raise ValueError('GM27 packed vector domain')
                flat[i, axis] = code-18
        bits.end()
    elif mode in (5, 6):
        if len(data) < 3 or data[1] > 6 or data[2] > 6:
            raise ValueError('GM27 Rice parameters')
        bits = Reader(data[3:])
        flat = np.zeros((n, 2), np.int16)
        for axis, k in enumerate(data[1:3]):
            for i in range(n):
                code = rice(bits, k, 72, 7)
                delta = code//2 if code % 2 == 0 else -(code//2)-1
                value = _predict(flat, i, mw, axis, mode)+delta
                if not -18 <= value <= 18:
                    raise ValueError('GM27 reconstructed vector domain')
                flat[i, axis] = value
        bits.end()
    else:
        raise ValueError('GM27 mode')
    if np.any(flat < -18) or np.any(flat > 18):
        raise ValueError('GM27 vector domain')
    return flat.reshape(mh, mw, 2).astype(np.int8)


def _delta(bits, k):
    z = rice(bits, k, 72, 7)
    return z//2 if z % 2 == 0 else -(z//2)-1


def _set_delta(child, parent, index, bits, ks):
    mw = child.shape[1]
    y, x = divmod(index, mw)
    dx, dy = _delta(bits, ks[0]), _delta(bits, ks[1])
    if dx == 0 and dy == 0:
        raise ValueError('HM34 redundant child refinement')
    value = parent[y//2, x//2].astype(np.int16)+[dx, dy]
    if np.any(value < -18) or np.any(value > 18):
        raise ValueError('HM34 child vector domain')
    child[y, x] = value


def unpack(data, width, height, *, return_info=False):
    """Return child int8 field; optional info includes parent (None for flat).

    Geometry arguments are checked against the self-described header. All
    failures raise ValueError before any caller-owned state is modified.
    """
    (ph, pw), (ch, cw) = geometry(width, height)
    n = ch*cw
    if type(data) is not bytes or not HEADER.size+CRC.size+1 <= len(data) <= HEADER.size+CRC.size+1+2*n:
        raise ValueError('HM34 component length')
    magic, version, mode, w, h, parent_len, payload_len = HEADER.unpack_from(data)
    if magic != MAGIC or version != VERSION or mode >= len(MODE_NAMES) or (w, h) != (width, height):
        raise ValueError('HM34 header/profile/geometry')
    if HEADER.size+parent_len+payload_len+CRC.size != len(data):
        raise ValueError('HM34 exact component lengths')
    if zlib.crc32(data[:-CRC.size]) != CRC.unpack_from(data, len(data)-CRC.size)[0]:
        raise ValueError('HM34 CRC')
    payload = data[HEADER.size+parent_len:-CRC.size]
    parent = None
    refinements = 0
    if mode == 0:
        if parent_len:
            raise ValueError('HM34 flat parent length')
        child = unpack_gm27(payload, cw, ch)
    else:
        parent = unpack_gm27(data[HEADER.size:HEADER.size+parent_len], pw, ph)
        child = np.repeat(np.repeat(parent, 2, axis=0), 2, axis=1)[:ch, :cw].copy()
        if mode == 1:
            if len(payload) < 5:
                raise ValueError('HM34 sparse header')
            count, kg, kx, ky = struct.unpack_from('<HBBB', payload)
            if count > n or kg > 10 or kx > 6 or ky > 6:
                raise ValueError('HM34 sparse parameters')
            bits = Reader(payload[5:])
            previous = -1
            for _ in range(count):
                gap = rice(bits, kg, n-1, max(1, (n-1).bit_length()))
                index = previous+1+gap
                if index >= n:
                    raise ValueError('HM34 refinement index bounds')
                _set_delta(child, parent, index, bits, (kx, ky))
                previous = index
            refinements = count
            bits.end()
        else:
            if len(payload) < 2 or payload[0] > 6 or payload[1] > 6:
                raise ValueError('HM34 mask parameters')
            bits = Reader(payload[2:])
            for py in range(ph):
                for px in range(pw):
                    if not bits.get(1):
                        continue
                    mask = bits.get(4)
                    if not mask:
                        raise ValueError('HM34 empty parent split mask')
                    for local in range(4):
                        if not (mask & (1 << local)):
                            continue
                        y, x = 2*py+local//2, 2*px+local%2
                        if y >= ch or x >= cw:
                            raise ValueError('HM34 partial parent mask')
                        _set_delta(child, parent, y*cw+x, bits, payload[:2])
                        refinements += 1
            bits.end()
    info = dict(mode=mode, mode_name=MODE_NAMES[mode], parent=parent,
                component_bytes=len(data), header_bytes=HEADER.size, crc_bytes=CRC.size,
                parent_bytes=parent_len, refinement_bytes=payload_len,
                decoded_child_vectors=n, refinement_vectors=refinements)
    return (child, info) if return_info else child
