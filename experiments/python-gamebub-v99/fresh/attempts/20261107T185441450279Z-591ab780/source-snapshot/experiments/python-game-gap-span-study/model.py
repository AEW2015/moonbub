"""HD22: exact RGB565 XOR spans with minimum-cost short-gap merging.

Experimental incompatible HD22 framing. This is not a native endpoint codec.
The envelope/RAW/COPY conventions follow the frozen HD21 component.
"""
import hashlib
import struct
import zlib
import numpy as np

MAGIC = b'HD22'
VERSION = 1
RAW, COPY, SPAN_XOR = 0, 1, 2
MAX_WIDTH, MAX_HEIGHT, MAX_WORDS = 720, 480, 21120
HEADER = struct.Struct('<4sBBHHI16s16s')
CRC = struct.Struct('<I')
COUNT = struct.Struct('<H')
SPAN = struct.Struct('<HHH')
FIXED_BYTES = HEADER.size + CRC.size
MAX_PAYLOAD = 2 * MAX_WORDS
MAX_PACKET = FIXED_BYTES + MAX_PAYLOAD
ZERO_TAG = bytes(16)


def _geometry(w, h):
    if not 0 < w <= MAX_WIDTH or not 0 < h <= MAX_HEIGHT or w * h > MAX_WORDS:
        raise ValueError('bounded patch geometry')


def _array(a):
    if not isinstance(a, np.ndarray) or a.ndim != 2 or a.dtype.kind != 'u' or a.dtype.itemsize != 2:
        raise ValueError('2D uint16 patch required')
    _geometry(a.shape[1], a.shape[0])
    return np.array(a, dtype='<u2', order='C', copy=True)


def _tag(a):
    return hashlib.sha256(struct.pack('<HH', a.shape[1], a.shape[0]) + a.tobytes()).digest()[:16]


def content_tag(a):
    return _tag(_array(a))


def optimal_row_spans(row):
    """Linear scan after finding nonzeros; gap=3 ties are canonically split.

    Each decision crosses one zero gap g. Merging pays 2*g extra bytes and
    removes exactly one 6-byte header, independently of every other gap.
    Thus merge iff g<3 is globally minimum for ordered row-local spans.
    """
    if not isinstance(row, np.ndarray) or row.ndim != 1 or row.dtype.kind != 'u' or row.dtype.itemsize != 2 or not 0 < row.size <= MAX_WIDTH:
        raise ValueError('bounded uint16 row')
    changed = np.flatnonzero(row)
    if not len(changed):
        return []
    cuts = np.flatnonzero(np.diff(changed) >= 4) + 1
    starts = np.r_[0, cuts]
    ends = np.r_[cuts, len(changed)]
    return [(int(changed[a]), int(changed[b - 1]) + 1) for a, b in zip(starts, ends)]


def _pack(mode, current, reference_tag, payload):
    header = HEADER.pack(MAGIC, VERSION, mode, current.shape[1], current.shape[0], len(payload), reference_tag, _tag(current))
    body = header + payload
    return body + CRC.pack(zlib.crc32(body))


def encode(current, reference=None):
    current = _array(current)
    raw = current.tobytes()
    if reference is None:
        return _pack(RAW, current, ZERO_TAG, raw)
    reference = _array(reference)
    if reference.shape != current.shape:
        raise ValueError('reference geometry')
    if np.array_equal(current, reference):
        return _pack(COPY, current, _tag(reference), b'')
    xor = current ^ reference
    payload = bytearray(COUNT.size)
    count = 0
    for y in range(current.shape[0]):
        for start, end in optimal_row_spans(xor[y]):
            n = end - start
            if len(payload) + SPAN.size + 2 * n >= len(raw):
                return _pack(RAW, current, ZERO_TAG, raw)
            payload.extend(SPAN.pack(y, start, n))
            payload.extend(xor[y, start:end].astype('<u2', copy=False).tobytes())
            count += 1
    COUNT.pack_into(payload, 0, count)
    return _pack(SPAN_XOR, current, _tag(reference), bytes(payload))


def _parse(packet):
    if type(packet) is not bytes or not FIXED_BYTES <= len(packet) <= MAX_PACKET:
        raise ValueError('bounded immutable HD22 packet')
    magic, version, mode, w, h, size, ref, tag = HEADER.unpack_from(packet)
    _geometry(w, h)
    if (magic, version) != (MAGIC, VERSION) or mode not in (RAW, COPY, SPAN_XOR):
        raise ValueError('HD22 version/mode')
    if size > MAX_PAYLOAD or len(packet) != FIXED_BYTES + size:
        raise ValueError('HD22 exact payload length')
    if zlib.crc32(packet[:-4]) != CRC.unpack_from(packet, len(packet) - 4)[0]:
        raise ValueError('HD22 CRC')
    payload = memoryview(packet)[HEADER.size:-4]
    spans = []
    changed_words = transmitted_words = zero_words = 0
    if mode == RAW:
        if size != 2 * w * h or ref != ZERO_TAG:
            raise ValueError('RAW framing')
    elif mode == COPY:
        if size:
            raise ValueError('COPY payload')
    else:
        if size < COUNT.size:
            raise ValueError('missing span count')
        n = COUNT.unpack_from(payload)[0]
        if not 0 < n <= w * h or n > (size - COUNT.size) // (SPAN.size + 2):
            raise ValueError('bounded span count')
        offset, last_y, last_end = COUNT.size, -1, -1
        for _ in range(n):
            if offset + SPAN.size > size:
                raise ValueError('truncated span')
            y, x, words = SPAN.unpack_from(payload, offset)
            offset += SPAN.size
            if y >= h or not 0 < words <= w or x + words > w or y < last_y or (y == last_y and x - last_end < 3):
                raise ValueError('unordered/overlap/noncanonical gap')
            end = offset + 2 * words
            if end > size:
                raise ValueError('truncated XOR words')
            values = np.frombuffer(payload[offset:end], dtype='<u2')
            if not values[0] or not values[-1]:
                raise ValueError('zero endpoint')
            # Interior gaps of3+words must be split even on a byte-cost tie.
            nonzero = np.flatnonzero(values)
            if np.any(np.diff(nonzero) >= 4):
                raise ValueError('noncanonical internal gap')
            changed_words += len(nonzero)
            transmitted_words += words
            zero_words += words - len(nonzero)
            spans.append((y, x, words, offset, end))
            last_y, last_end, offset = y, x + words, end
        if offset != size:
            raise ValueError('trailing span bytes')
    info = dict(mode=mode, width=w, height=h, words=w*h, payload_bytes=size,
                packet_bytes=len(packet), fixed_bytes=FIXED_BYTES,
                reference_tag=ref.hex(), current_tag=tag.hex(), span_count=len(spans),
                changed_words=changed_words, transmitted_span_words=transmitted_words,
                merged_zero_words=zero_words)
    return info, payload, spans


def inspect(packet):
    return _parse(packet)[0]


def decode(packet, reference=None):
    info, payload, spans = _parse(packet)
    shape = info['height'], info['width']
    if info['mode'] == RAW:
        result = np.frombuffer(payload, dtype='<u2').reshape(shape).copy()
    else:
        if reference is None:
            raise ValueError('missing acknowledged reference')
        result = _array(reference)
        if result.shape != shape or _tag(result).hex() != info['reference_tag']:
            raise ValueError('wrong exact reference')
        for y, x, n, begin, end in spans:
            result[y, x:x+n] ^= np.frombuffer(payload[begin:end], dtype='<u2')
    if _tag(result).hex() != info['current_tag']:
        raise ValueError('reconstruction tag')
    return result
