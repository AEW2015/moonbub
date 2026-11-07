"""GM27 bounded syntax-only motion decoder; frozen GM26 is read-only oracle.

No re-encoding is performed while parsing. GM26 replay adapters are explicitly
qualification-only: deployed GM26 still requires its frozen minimal grammar.
"""
from pathlib import Path
import importlib.util
import sys
import struct
import zlib
import numpy as np

HERE = Path(__file__).resolve().parent
V26 = HERE.parent / 'python-game-prediction-v26-study'

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

frozen = load('decoder27_frozen26', V26 / 'model.py')
LIMIT = 18
HEADER = frozen.HEADER
MAGIC, VERSION = b'GM27', 1


def _geometry(mw, mh):
    # Any grid possible for bounded even YUV geometry and 16/32 blocks. The
    # smallest even source giving a grid is 16*(grid-1)+2 per axis.
    if (type(mw) is not int or type(mh) is not int or not 1 <= mw <= 128
            or not 1 <= mh <= 128 or (16*(mw-1)+2)*(16*(mh-1)+2) > 720*480):
        raise ValueError('bounded motion geometry')
    return mw * mh


class _Reader:
    def __init__(self, data):
        self.data, self.pos, self.size = data, 0, len(data)*8

    def get(self, n):
        if self.pos+n > self.size:
            raise ValueError('motion bitstream truncated')
        value = 0
        for _ in range(n):
            value = (value << 1) | ((self.data[self.pos >> 3] >> (7-(self.pos & 7))) & 1)
            self.pos += 1
        return value

    def end(self):
        remaining = self.size-self.pos
        if remaining >= 8 or self.get(remaining):
            raise ValueError('motion padding/exact length')


def _predict(flat, i, mw, axis, mode):
    x, y = i % mw, i // mw
    left = int(flat[i-1, axis]) if x else 0
    if mode == 5:
        return left
    top = int(flat[i-mw, axis]) if y else 0
    right = int(flat[i-mw+(x+1 < mw), axis]) if y else 0
    return left+top+right-min(left, top, right)-max(left, top, right)


def unpack_vectors(data, mw, mh):
    """Parse bounded MV syntax without optimal mode/k selection or re-encoding.

    Accepts structurally valid nonminimal modes, split adjacent equal RLE runs,
    and nonmodal sparse defaults. Redundant sparse entries remain forbidden.
    Components are signed half-luma units, -18 through +18 inclusive.
    """
    n = _geometry(mw, mh)
    if type(data) is not bytes or not 1 <= len(data) <= 1+2*n:
        raise ValueError('motion map length')
    mode = data[0]
    if mode == 0:
        if len(data) != 3:
            raise ValueError('global map length')
        flat = np.tile(np.frombuffer(data[1:], np.int8), (n, 1))
    elif mode == 1:
        if len(data) != 1+2*n:
            raise ValueError('dense map length')
        flat = np.frombuffer(data[1:], np.int8).reshape(n, 2).copy()
    elif mode == 2:
        if (len(data)-1) % 4:
            raise ValueError('RLE length')
        flat = np.empty((n, 2), np.int8)
        count = 0
        for offset in range(1, len(data), 4):
            run, dx, dy = struct.unpack_from('<Hbb', data, offset)
            if not run or count+run > n:
                raise ValueError('RLE coverage')
            flat[count:count+run] = dx, dy
            count += run
        if count != n:
            raise ValueError('RLE incomplete')
    elif mode == 3:
        if len(data) < 3 or (len(data)-3) % 4:
            raise ValueError('sparse length')
        default = np.frombuffer(data[1:3], np.int8)
        flat = np.tile(default, (n, 1))
        previous = -1
        for offset in range(3, len(data), 4):
            index, dx, dy = struct.unpack_from('<Hbb', data, offset)
            if not previous < index < n or (dx == default[0] and dy == default[1]):
                raise ValueError('sparse index/redundant value')
            flat[index] = dx, dy
            previous = index
    elif mode == 4:
        bits = _Reader(data[1:])
        flat = np.empty((n, 2), np.int16)
        for i in range(n):
            for axis in (0, 1):
                value = bits.get(6)
                if value > 36:
                    raise ValueError('packed motion code')
                flat[i, axis] = value-18
        bits.end()
    elif mode in (5, 6):
        if len(data) < 3 or data[1] > 6 or data[2] > 6:
            raise ValueError('Rice motion parameters')
        bits = _Reader(data[3:])
        flat = np.zeros((n, 2), np.int16)
        for axis, k in enumerate(data[1:3]):
            for i in range(n):
                q = 0
                while q < 7 and bits.get(1):
                    q += 1
                if q == 7:
                    z = bits.get(7)
                    if z > 72 or z >> k < 7:
                        raise ValueError('Rice escape/domain')
                else:
                    z = (q << k) | bits.get(k)
                if z > 72:
                    raise ValueError('Rice motion delta')
                delta = z//2 if z % 2 == 0 else -(z//2)-1
                value = _predict(flat, i, mw, axis, mode)+delta
                if not -18 <= value <= 18:
                    raise ValueError('Rice reconstructed vector')
                flat[i, axis] = value
        bits.end()
    else:
        raise ValueError('motion map mode')
    if np.any(flat < -LIMIT) or np.any(flat > LIMIT):
        raise ValueError('bounded half-luma motion vectors')
    return flat.reshape(mh, mw, 2).astype(np.int8)


def parse_frame(packet, *, expected_epoch=None, magic=MAGIC, version=VERSION,
                map_decoder=None, allowed_modes=range(7)):
    """Profile-explicit frame parser, reusable with a supplied MV decoder.

    Defaults to new GM27/v1. It never monkeypatches any frozen module.
    """
    m = frozen
    if type(packet) is not bytes or not HEADER.size+7 <= len(packet) <= m.MAX_PACKET:
        raise ValueError('bounded frame length')
    if zlib.crc32(packet[:-4]) != struct.unpack('<I', packet[-4:])[0]:
        raise ValueError('frame CRC')
    (got_magic, got_version, flags, epoch, frame, refid, w, h, bs, limit,
     reftag, outtag, nq, nv, ny, ncb, ncr) = HEADER.unpack_from(packet)
    m.roi.geometry(w, h)
    mw, mh = m._grid(w, h, bs)
    key = bool(flags)
    if ((got_magic, got_version) != (magic, version) or flags not in (0, 1)
            or limit != LIMIT or not m._id(epoch) or not m._id(frame)):
        raise ValueError('frame profile/identity')
    if expected_epoch is not None and epoch != expected_epoch:
        raise ValueError('frame wrong epoch')
    if key:
        if refid != m.NO_REF or reftag != m.ZERO_TAG or nv:
            raise ValueError('independent key reference')
    elif not m._id(refid) or refid >= frame or reftag == m.ZERO_TAG or not 1 <= nv <= 1+2*mw*mh:
        raise ValueError('P reference/map')
    if outtag == m.ZERO_TAG or nq != (((w+15)//16)*((h+15)//16)+3)//4:
        raise ValueError('output tag/quant-map length')
    lengths = (ny, ncb, ncr)
    for plane, size in enumerate(lengths):
        pw, ph = (w, h) if plane == 0 else (w//2, h//2)
        n = ((pw+7)//8)*((ph+7)//8)
        if not 1 <= size <= 132*n+256:
            raise ValueError('plane bound')
    if len(packet) != HEADER.size+nq+nv+sum(lengths)+4:
        raise ValueError('exact frame length')
    pos = HEADER.size
    mapped = m.roi.unpack_map(packet[pos:pos+nq], (w+15)//16, (h+15)//16)
    pos += nq
    data = packet[pos:pos+nv]
    if not key and data[0] not in allowed_modes:
        raise ValueError('profile motion mode')
    vectors = np.zeros((mh, mw, 2), np.int8) if key else (map_decoder or unpack_vectors)(data, mw, mh)
    pos += nv
    coefficients = []
    for plane, size in enumerate(lengths):
        pw, ph = (w, h) if plane == 0 else (w//2, h//2)
        n, bw = ((pw+7)//8)*((ph+7)//8), (pw+7)//8
        coefficients.append(m._decode_plane(packet[pos:pos+size], n, bw))
        pos += size
    return dict(epoch=epoch, frame_id=frame, reference_id=refid, key=key, width=w, height=h,
                block_size=bs, vectors=vectors, scale_map=mapped, coefficients=tuple(coefficients),
                reference_tag=reftag, reconstructed_tag=outtag)


def decode_frame(packet, reference=None, *, expected_reference_id=None, **parse_options):
    m = frozen
    meta = parse_frame(packet, **parse_options)
    w, h = meta['width'], meta['height']
    if meta['key']:
        prediction = tuple(np.full(shape, 128, np.int16) for shape in ((h,w),(h//2,w//2),(h//2,w//2)))
    else:
        if expected_reference_id is None or expected_reference_id != meta['reference_id']:
            raise ValueError('exact reference ID required')
        ref = m._planes(reference, (w, h))
        if m.C.reference_tag(ref) != meta['reference_tag']:
            raise ValueError('exact reconstructed reference tag')
        prediction = m.predict(ref, meta['vectors'], meta['block_size'])
    rebuilt = m.gm.reconstruct(meta['coefficients'], prediction, meta['scale_map'], w, h)
    if m.C.reference_tag(rebuilt) != meta['reconstructed_tag']:
        raise ValueError('reconstructed output tag')
    return rebuilt, meta


def replay_parse_gm26(packet, *, early=False, **options):
    """Qualification only. Not a replacement for normative GM26 validation."""
    return parse_frame(packet, magic=b'GM26', version=1 if early else 2,
                       allowed_modes=range(4) if early else range(7), **options)


def replay_decode_gm26(packet, reference=None, *, early=False, **options):
    """Qualification only. Early GM26/v1 has only modes 0..3."""
    return decode_frame(packet, reference, magic=b'GM26', version=1 if early else 2,
                        allowed_modes=range(4) if early else range(7), **options)
