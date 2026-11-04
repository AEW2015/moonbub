"""HD25 exact RGB565 residuals with bounded integer-motion prediction.

All candidate bytes are constructed and charged. This is a host Python and
bounded decoder reference, not native endpoint/FPGA resource or timing proof.
"""
from pathlib import Path
import hashlib
import importlib.util
import struct
import sys
import time
import zlib
import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('hd25_gap22', HERE.parent / 'python-game-gap-span-study/model.py')
old = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = old
spec.loader.exec_module(old)

MAGIC, VERSION = b'HD25', 1
RAW, COPY, SPAN_XOR, BYTE_XOR, GLOBAL, TILED, INTRA_BYTE, INTRA_LEFT, COMPONENT, INTRA_COMPONENT = range(10)
NAMES = ('raw', 'copy', 'span_xor', 'byte_xor', 'global_motion', 'tile_motion', 'intra_byte', 'intra_left', 'component_delta', 'intra_component')
HEADER, CRC = old.HEADER, old.CRC
FIXED_BYTES, MAX_WORDS, MAX_PACKET = old.FIXED_BYTES, old.MAX_WORDS, old.MAX_PACKET
ZERO = bytes(16)
TW, TH, RADIUS = 16, 8, 4
TILE = struct.Struct('<BBBBH')
RUN = struct.Struct('<Hbb')
LENGTHS = struct.Struct('<II')
RICE = struct.Struct('<BBBIII')


def _components(words):
    return ((words >> 11).astype(np.int16), ((words >> 5) & 63).astype(np.int16), (words & 31).astype(np.int16))


def _rice_encode(current, prediction=None, *, left=False):
    components = _components(current)
    predicted = _components(prediction) if prediction is not None else None
    ks, counts, streams = [], [], []
    for index, values in enumerate(components):
        if left:
            delta = values.copy(); delta[:, 1:] -= values[:, :-1]
        else:
            delta = values - predicted[index]
        flat = delta.reshape(-1).astype(np.int32)
        zig = np.where(flat >= 0, 2 * flat, -2 * flat - 1).astype(np.uint16)
        sizes = [int(np.sum((zig >> k).astype(np.int64) + 1 + k)) for k in range(6)]
        k = min(range(6), key=lambda k: sizes[k])
        quotient = (zig >> k).astype(np.int64)
        lengths = quotient + 1 + k
        starts = np.cumsum(lengths) - lengths
        bits = np.zeros(sizes[k], np.uint8)
        bits[starts + quotient] = 1
        for bit in range(k):
            bits[starts + quotient + 1 + bit] = ((zig >> (k - 1 - bit)) & 1).astype(np.uint8)
        ks.append(k); counts.append(sizes[k]); streams.append(np.packbits(bits, bitorder='big').tobytes())
    return RICE.pack(*ks, *counts) + b''.join(streams)


def _rice_decode(payload, h, w, prediction=None, *, left=False, validate_range=True):
    if len(payload) < RICE.size: raise ValueError('Rice header')
    k0, k1, k2, b0, b1, b2 = RICE.unpack_from(payload)
    ks, counts = (k0, k1, k2), (b0, b1, b2)
    n = h * w
    if any(k > 5 for k in ks) or any(not n <= count <= 127 * n for count in counts):
        raise ValueError('Rice parameter/bit count')
    if len(payload) != RICE.size + sum((count + 7) // 8 for count in counts):
        raise ValueError('Rice exact length')
    predicted = _components(prediction) if prediction is not None else None
    out, offset = [], RICE.size
    for channel, (k, count, maximum) in enumerate(zip(ks, counts, (31, 63, 31))):
        length = (count + 7) // 8
        stream = payload[offset:offset + length]; offset += length
        if count % 8 and stream[-1] & ((1 << (8 - count % 8)) - 1): raise ValueError('Rice padding')
        values, pos = [], 0
        for _ in range(n):
            quotient = 0
            while True:
                if pos >= count: raise ValueError('Rice truncated unary')
                bit = (stream[pos // 8] >> (7 - pos % 8)) & 1; pos += 1
                if bit: break
                quotient += 1
                if (quotient << k) > 2 * maximum: raise ValueError('Rice unary domain')
            remainder = 0
            for _ in range(k):
                if pos >= count: raise ValueError('Rice truncated remainder')
                remainder = (remainder << 1) | ((stream[pos // 8] >> (7 - pos % 8)) & 1); pos += 1
            zig = (quotient << k) | remainder
            if zig > 2 * maximum: raise ValueError('Rice component delta domain')
            values.append(zig // 2 if not zig & 1 else -(zig // 2) - 1)
        if pos != count: raise ValueError('Rice trailing bits')
        delta = np.asarray(values, np.int32).reshape(h, w)
        result = np.cumsum(delta, axis=1) if left else predicted[channel].astype(np.int32) + delta
        if validate_range and (np.any(result < 0) or np.any(result > maximum)):
            raise ValueError('Rice reconstructed component range')
        if not validate_range: result &= maximum
        out.append(result.astype(np.uint16))
    return (out[0] << 11) | (out[1] << 5) | out[2]


def _array(a): return old._array(a)
def _tag(a): return old._tag(a)
def content_tag(a): return _tag(_array(a))


def rle_encode(data):
    """Bounded byte literal/zero/repeat runs; no entropy dictionaries."""
    if type(data) is not bytes or not 0 < len(data) <= MAX_WORDS:
        raise ValueError('bounded byte plane')
    out, i, n = bytearray(), 0, len(data)
    while i < n:
        j = i + 1
        while j < n and data[j] == data[i] and j - i < 64:
            j += 1
        run = j - i
        if run >= 3:
            out.append((128 if data[i] == 0 else 192) + run - 1)
            if data[i]: out.append(data[i])
            i = j
            continue
        start = i
        i += run
        while i < n and i - start < 128:
            j = i + 1
            while j < n and data[j] == data[i] and j - i < 3: j += 1
            if j - i >= 3: break
            i += min(j - i, 128 - (i - start))
        out.append(i - start - 1)
        out.extend(data[start:i])
    return bytes(out)


def rle_decode(data, count):
    if type(data) is not bytes or type(count) is not int or not 0 < count <= MAX_WORDS:
        raise ValueError('bounded RLE input')
    if not 0 < len(data) <= count + (count + 127) // 128:
        raise ValueError('bounded encoded byte plane')
    out, i = bytearray(), 0
    while i < len(data):
        token = data[i]; i += 1
        if token < 128:
            n = token + 1
            if i + n > len(data): raise ValueError('short literal')
            value = data[i:i + n]; i += n
        elif token < 192:
            n = (token & 63) + 1
            value = bytes(n)
        else:
            n = (token & 63) + 1
            if i >= len(data) or data[i] == 0: raise ValueError('repeat value')
            value = bytes([data[i]]) * n; i += 1
        if len(out) + n > count: raise ValueError('RLE output overflow')
        out.extend(value)
    if len(out) != count: raise ValueError('RLE output short')
    return bytes(out)


def _planes_encode(words):
    a = np.asarray(words, dtype='<u2').reshape(-1)
    lo = rle_encode((a & 255).astype(np.uint8).tobytes())
    hi = rle_encode((a >> 8).astype(np.uint8).tobytes())
    return LENGTHS.pack(len(lo), len(hi)) + lo + hi


def _planes_decode(payload, h, w):
    if len(payload) < LENGTHS.size: raise ValueError('byte-plane lengths')
    low, high = LENGTHS.unpack_from(payload)
    if len(payload) != 8 + low + high: raise ValueError('byte-plane exact lengths')
    n = h * w
    lo = np.frombuffer(rle_decode(payload[8:8 + low], n), np.uint8).astype(np.uint16)
    hi = np.frombuffer(rle_decode(payload[8 + low:], n), np.uint8).astype(np.uint16)
    return (lo | (hi << 8)).reshape(h, w)


def _span_encode(xor):
    out, count = bytearray(2), 0
    for y in range(xor.shape[0]):
        for start, end in old.optimal_row_spans(xor[y]):
            out.extend(old.SPAN.pack(y, start, end - start))
            out.extend(xor[y, start:end].astype('<u2', copy=False).tobytes())
            count += 1
    old.COUNT.pack_into(out, 0, count)
    return bytes(out)


def _span_decode(payload, h, w):
    if len(payload) < 2: raise ValueError('span count')
    count = old.COUNT.unpack_from(payload)[0]
    if count > h * w or count > (len(payload) - 2) // 8: raise ValueError('span count bound')
    out = np.zeros((h, w), np.uint16)
    pos, last_y, last_end = 2, -1, -1
    for _ in range(count):
        if pos + 6 > len(payload): raise ValueError('short span')
        y, x, n = old.SPAN.unpack_from(payload, pos); pos += 6
        if y >= h or not 0 < n <= w or x + n > w or y < last_y or (y == last_y and x - last_end < 3):
            raise ValueError('span location/order')
        if pos + 2 * n > len(payload): raise ValueError('short XOR values')
        values = np.frombuffer(payload[pos:pos + 2 * n], dtype='<u2')
        if not values[0] or not values[-1] or np.any(np.diff(np.flatnonzero(values)) >= 4):
            raise ValueError('noncanonical span')
        out[y, x:x + n] = values
        last_y, last_end, pos = y, x + n, pos + 2 * n
    if pos != len(payload): raise ValueError('trailing span')
    return out


def _residual_encode(xor, current, prediction):
    span, planes = _span_encode(xor), _planes_encode(xor)
    rice = _rice_encode(current, prediction)
    return min((b'\0' + span, b'\1' + planes, b'\2' + rice), key=len)


def _residual_decode(payload, h, w, prediction, *, validate_range=True):
    if not payload: raise ValueError('residual grammar missing')
    if payload[0] == 0: return _span_decode(payload[1:], h, w)
    if payload[0] == 1: return _planes_decode(payload[1:], h, w)
    if payload[0] == 2: return prediction ^ _rice_decode(payload[1:], h, w, prediction, validate_range=validate_range)
    raise ValueError('unknown residual grammar')


def predict(reference, dx, dy):
    h, w = reference.shape
    return reference[np.ix_(np.clip(np.arange(h) + dy, 0, h - 1),
                            np.clip(np.arange(w) + dx, 0, w - 1))]


def _vector_bytes(vectors):
    raw = b''.join(struct.pack('<bb', dx, dy) for dx, dy in vectors)
    runs = []
    for vector in vectors:
        if runs and runs[-1][1:] == vector:
            runs[-1] = (runs[-1][0] + 1, *vector)
        else: runs.append((1, *vector))
    encoded = b''.join(RUN.pack(*run) for run in runs)
    return (0, raw) if len(raw) <= len(encoded) else (1, encoded)


def _motion_search(current, reference):
    h, w = current.shape
    padded = np.pad(reference, RADIUS, mode='edge')
    windows = np.lib.stride_tricks.sliding_window_view(padded, (h, w))
    ordered = sorted(((dx, dy) for dy in range(-RADIUS, RADIUS + 1) for dx in range(-RADIUS, RADIUS + 1)),
                     key=lambda q: (abs(q[0]) + abs(q[1]), q[1], q[0]))
    ys = np.asarray([dy + RADIUS for dx, dy in ordered])
    xs = np.asarray([dx + RADIUS for dx, dy in ordered])
    # A declared cheap coding-length proxy ranks vectors. It is not a future
    # image/quality oracle, and is not claimed to minimize actual Rice bytes.
    # Component deltas preserve small color changes that packed-word equality
    # misses. The same finite per-pixel costs serve global and tile searches.
    pixel_cost = np.zeros(windows.shape, np.uint16)
    table = np.asarray([2 * ((v + 1).bit_length() - 1) + 1 for v in range(127)], np.uint8)
    for shift, mask in ((11, 31), (5, 63), (0, 31)):
        delta = ((current >> shift) & mask).astype(np.int16)[None, None] - ((windows >> shift) & mask).astype(np.int16)
        zig = np.where(delta >= 0, 2 * delta, -2 * delta - 1)
        pixel_cost += table[zig]
    costs_global = np.sum(pixel_cost, axis=(2, 3))
    ranked = sorted(ordered, key=lambda q: (int(costs_global[q[1] + RADIUS, q[0] + RADIUS]), abs(q[0]) + abs(q[1]), q[1], q[0]))
    globals_ = [q for q in ranked if q != (0, 0)][:3]
    prediction, vectors = np.empty_like(reference), []
    for y in range(0, h, TH):
        for x in range(0, w, TW):
            hh, ww = min(TH, h - y), min(TW, w - x)
            costs = np.sum(pixel_cost[:, :, y:y + hh, x:x + ww], axis=(2, 3))
            index = int(np.argmin(costs[ys, xs]))
            dx, dy = ordered[index]
            vectors.append((dx, dy))
            prediction[y:y + hh, x:x + ww] = windows[dy + RADIUS, dx + RADIUS, y:y + hh, x:x + ww]
    return globals_, prediction, vectors


def _pack(mode, current, ref, payload):
    body = HEADER.pack(MAGIC, VERSION, mode, current.shape[1], current.shape[0], len(payload), ref, _tag(current)) + payload
    return body + CRC.pack(zlib.crc32(body))


def encode_with_info(current, reference=None, *, motion=True):
    start = time.perf_counter_ns()
    current = _array(current)
    candidates = [(RAW, _pack(RAW, current, ZERO, current.tobytes()))]
    candidates.append((INTRA_BYTE, _pack(INTRA_BYTE, current, ZERO, _planes_encode(current))))
    left = current.copy(); left[:, 1:] ^= current[:, :-1]
    candidates.append((INTRA_LEFT, _pack(INTRA_LEFT, current, ZERO, _planes_encode(left))))
    candidates.append((INTRA_COMPONENT, _pack(INTRA_COMPONENT, current, ZERO, _rice_encode(current, left=True))))
    globals_, vectors = [], []
    if reference is not None:
        reference = _array(reference)
        if reference.shape != current.shape: raise ValueError('reference geometry')
        ref = _tag(reference)
        if np.array_equal(reference, current):
            candidates.append((COPY, _pack(COPY, current, ref, b'')))
        else:
            xor = current ^ reference
            candidates.append((SPAN_XOR, _pack(SPAN_XOR, current, ref, _span_encode(xor))))
            candidates.append((BYTE_XOR, _pack(BYTE_XOR, current, ref, _planes_encode(xor))))
            candidates.append((COMPONENT, _pack(COMPONENT, current, ref, _rice_encode(current, reference))))
            if motion:
                globals_, prediction, vectors = _motion_search(current, reference)
                for dx, dy in globals_:
                    p = predict(reference, dx, dy)
                    data = struct.pack('<bb', dx, dy) + _residual_encode(current ^ p, current, p)
                    candidates.append((GLOBAL, _pack(GLOBAL, current, ref, data)))
                field, data = _vector_bytes(vectors)
                tiled = TILE.pack(TW, TH, RADIUS, field, len(vectors)) + struct.pack('<I', len(data)) + data
                candidates.append((TILED, _pack(TILED, current, ref, tiled + _residual_encode(current ^ prediction, current, prediction))))
    # Actual complete sizes are authoritative; an expensive losing candidate is
    # still paid, but cannot force an oversized accepted packet.
    best = min(candidates, key=lambda item: (len(item[1]), item[0]))
    if len(best[1]) > MAX_PACKET: raise AssertionError('RAW fallback bound')
    info = dict(mode=NAMES[best[0]], packet_bytes=len(best[1]),
                candidates=[dict(mode=NAMES[mode], bytes=len(data)) for mode, data in candidates],
                motion_search_vectors=(2 * RADIUS + 1) ** 2 * (1 + len(vectors)) if vectors else 0,
                motion_compared_words=(2 * RADIUS + 1) ** 2 * current.size if vectors else 0,
                motion_search_metric='component_exp_golomb_length_proxy',
                selected_global_candidates=len(globals_), tile_vectors=len(vectors),
                nonzero_tile_vectors=sum(q != (0, 0) for q in vectors),
                encode_ms=(time.perf_counter_ns() - start) / 1e6)
    return best[1], info


def encode(current, reference=None):
    return encode_with_info(current, reference)[0]


def _decode_parts(packet, reference=None, *, structural=False):
    if type(packet) is not bytes or not FIXED_BYTES <= len(packet) <= MAX_PACKET:
        raise ValueError('bounded HD25 bytes')
    magic, version, mode, w, h, size, ref, tag = HEADER.unpack_from(packet)
    old._geometry(w, h)
    if magic != MAGIC or version != VERSION or mode not in range(10) or len(packet) != FIXED_BYTES + size or size > 2 * MAX_WORDS:
        raise ValueError('HD25 header')
    if zlib.crc32(packet[:-4]) != CRC.unpack_from(packet, len(packet) - 4)[0]: raise ValueError('HD25 CRC')
    data = packet[HEADER.size:-4]
    independent = mode in (RAW, INTRA_BYTE, INTRA_LEFT, INTRA_COMPONENT)
    if independent:
        if ref != ZERO: raise ValueError('independent reference tag')
        base = None
    else:
        if reference is None:
            if not structural: raise ValueError('exact acknowledged reference required')
            base = np.zeros((h, w), np.uint16)
        else:
            base = _array(reference)
            if base.shape != (h, w) or _tag(base) != ref: raise ValueError('reference binding')
    vector_count = 0
    if mode == RAW:
        if size != 2 * h * w: raise ValueError('RAW size')
        output = np.frombuffer(data, dtype='<u2').reshape(h, w).copy()
    elif mode == COPY:
        if size: raise ValueError('COPY payload')
        output = base.copy()
    elif mode in (SPAN_XOR, BYTE_XOR):
        output = base ^ (_span_decode(data, h, w) if mode == SPAN_XOR else _planes_decode(data, h, w))
    elif mode in (INTRA_BYTE, INTRA_LEFT):
        output = _planes_decode(data, h, w)
        if mode == INTRA_LEFT:
            output = np.bitwise_xor.accumulate(output, axis=1)
    elif mode == INTRA_COMPONENT:
        output = _rice_decode(data, h, w, left=True)
    elif mode == COMPONENT:
        output = _rice_decode(data, h, w, base, validate_range=not (structural and reference is None))
    elif mode == GLOBAL:
        if size < 3: raise ValueError('global motion payload')
        dx, dy = struct.unpack_from('<bb', data)
        if abs(dx) > RADIUS or abs(dy) > RADIUS: raise ValueError('global vector domain')
        prediction = predict(base, dx, dy)
        output = prediction ^ _residual_decode(data[2:], h, w, prediction, validate_range=not (structural and reference is None))
        vector_count = 1
    else:
        if size < TILE.size + 4: raise ValueError('tile field')
        tw, th, radius, field, n = TILE.unpack_from(data)
        count = ((w + TW - 1) // TW) * ((h + TH - 1) // TH)
        if (tw, th, radius) != (TW, TH, RADIUS) or field not in (0, 1) or n != count:
            raise ValueError('tile geometry/count')
        nb = struct.unpack_from('<I', data, TILE.size)[0]
        begin = TILE.size + 4
        if begin + nb >= size or not 0 < nb <= 4 * count: raise ValueError('tile field length')
        field_data = data[begin:begin + nb]
        vectors = []
        if field == 0:
            if nb != 2 * count: raise ValueError('raw vector length')
            vectors = [struct.unpack_from('<bb', field_data, 2 * i) for i in range(count)]
        else:
            if nb % RUN.size: raise ValueError('run vector length')
            for i in range(0, nb, RUN.size):
                length, dx, dy = RUN.unpack_from(field_data, i)
                if not length or len(vectors) + length > count or (vectors and vectors[-1] == (dx, dy)):
                    raise ValueError('vector run coverage/canonicality')
                vectors.extend([(dx, dy)] * length)
            if len(vectors) != count: raise ValueError('short vector coverage')
        if any(abs(dx) > RADIUS or abs(dy) > RADIUS for dx, dy in vectors): raise ValueError('tile vector domain')
        prediction = np.empty_like(base)
        index = 0
        for y in range(0, h, TH):
            for x in range(0, w, TW):
                dx, dy = vectors[index]; index += 1
                hh, ww = min(TH, h - y), min(TW, w - x)
                ys = np.clip(np.arange(y, y + hh) + dy, 0, h - 1)
                xs = np.clip(np.arange(x, x + ww) + dx, 0, w - 1)
                prediction[y:y + hh, x:x + ww] = base[np.ix_(ys, xs)]
        output = prediction ^ _residual_decode(data[begin + nb:], h, w, prediction, validate_range=not (structural and reference is None))
        vector_count = count
    if not (structural and not independent and reference is None) and _tag(output.astype('<u2', copy=False)) != tag:
        raise ValueError('decoded content tag')
    return output, dict(mode=mode, mode_name=NAMES[mode], width=w, height=h, words=w*h,
                        payload_bytes=size, packet_bytes=len(packet), vector_count=vector_count,
                        reference_tag=ref.hex(), current_tag=tag.hex(), independent=independent)


def decode(packet, reference=None): return _decode_parts(packet, reference)[0]


def inspect(packet, reference=None):
    """Bounded grammar metadata; pass reference for full content validation."""
    return _decode_parts(packet, reference, structural=reference is None)[1]
