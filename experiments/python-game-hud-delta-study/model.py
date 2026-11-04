"""HD21: bounded exact RGB565 patch deltas, independent of AR03/YUV state.

This is a Python component/wire experiment. It is not installed target support.
All tags bind geometry and little-endian RGB565 words; delta references are exact
decoded display-cache objects, never the lossy YUV prediction bank.
"""
import hashlib
import struct
import zlib

import numpy as np

MAGIC = b"HD21"
VERSION = 1
RAW, COPY, SPAN_XOR = 0, 1, 2
MAX_WIDTH, MAX_HEIGHT, MAX_WORDS = 720, 480, 21120
HEADER = struct.Struct("<4sBBHHI16s16s")
CRC = struct.Struct("<I")
COUNT = struct.Struct("<H")
SPAN = struct.Struct("<HHH")
FIXED_BYTES = HEADER.size + CRC.size
MAX_PAYLOAD = 2 * MAX_WORDS
MAX_PACKET = FIXED_BYTES + MAX_PAYLOAD
ZERO_TAG = bytes(16)


def _geometry(width, height):
    if not (0 < width <= MAX_WIDTH and 0 < height <= MAX_HEIGHT
            and width * height <= MAX_WORDS):
        raise ValueError("patch geometry outside fixed bounds")


def _array(value):
    if not isinstance(value, np.ndarray) or value.ndim != 2 or value.dtype.kind != "u" or value.dtype.itemsize != 2:
        raise ValueError("a two-dimensional uint16 RGB565 array is required")
    height, width = value.shape
    _geometry(width, height)
    # Copy to a bounded, canonical little-endian representation. Noncontiguous
    # or big-endian source arrays are legal and cannot affect wire byte order.
    return np.array(value, dtype="<u2", order="C", copy=True)


def _tag(canonical):
    height, width = canonical.shape
    return hashlib.sha256(struct.pack("<HH", width, height) + canonical.tobytes()).digest()[:16]


def content_tag(value):
    """Return geometry-bound SHA256[:16] of exact little-endian display words."""
    return _tag(_array(value))


def _pack(mode, current, reference_tag, payload):
    height, width = current.shape
    head = HEADER.pack(MAGIC, VERSION, mode, width, height, len(payload), reference_tag, _tag(current))
    framed = head + payload
    return framed + CRC.pack(zlib.crc32(framed) & 0xFFFFFFFF)


def encode(current, reference=None):
    """Encode an exact patch, choosing actual smallest RAW/COPY/SPAN_XOR bytes.

    The encoder uses only the supplied current patch and acknowledged reference.
    It does not alter either array. Unknown/unacknowledged references belong in
    the caller's protocol and must be passed as None.
    """
    current = _array(current)
    raw_payload = current.tobytes()
    if reference is None:
        return _pack(RAW, current, ZERO_TAG, raw_payload)
    reference = _array(reference)
    if current.shape != reference.shape:
        raise ValueError("reference geometry mismatch")
    ref_tag = _tag(reference)
    if np.array_equal(current, reference):
        return _pack(COPY, current, ref_tag, b"")

    # At most one bounded XOR array plus a bounded payload under the RAW size.
    # Stop the losing candidate before allocating a long noisy sparse stream.
    xor = np.bitwise_xor(current, reference)
    payload = bytearray(COUNT.size)
    records = 0
    for row in range(current.shape[0]):
        changed = np.flatnonzero(xor[row])
        if not changed.size:
            continue
        starts = np.r_[0, np.flatnonzero(np.diff(changed) != 1) + 1]
        ends = np.r_[starts[1:], len(changed)]
        for first, end in zip(starts, ends):
            start = int(changed[first])
            words = int(end - first)
            if len(payload) + SPAN.size + 2 * words >= len(raw_payload):
                return _pack(RAW, current, ZERO_TAG, raw_payload)
            payload.extend(SPAN.pack(row, start, words))
            payload.extend(xor[row, start:start + words].astype("<u2", copy=False).tobytes())
            records += 1
    assert 0 < records <= MAX_WORDS
    COUNT.pack_into(payload, 0, records)
    return _pack(SPAN_XOR, current, ref_tag, bytes(payload))


def _parse(packet):
    if not isinstance(packet, bytes):
        raise ValueError("immutable packet bytes required")
    if not FIXED_BYTES <= len(packet) <= MAX_PACKET:
        raise ValueError("packet length outside fixed bounds")
    magic, version, mode, width, height, count, reference, current = HEADER.unpack_from(packet)
    _geometry(width, height)
    if magic != MAGIC or version != VERSION or mode not in (RAW, COPY, SPAN_XOR):
        raise ValueError("unknown format, version or mode")
    if count > MAX_PAYLOAD or len(packet) != FIXED_BYTES + count:
        raise ValueError("declared payload length mismatch")
    if CRC.unpack_from(packet, len(packet) - CRC.size)[0] != (zlib.crc32(packet[:-CRC.size]) & 0xFFFFFFFF):
        raise ValueError("packet CRC mismatch")
    payload = memoryview(packet)[HEADER.size:-CRC.size]
    spans = []
    if mode == RAW:
        if count != width * height * 2 or reference != ZERO_TAG:
            raise ValueError("invalid RAW length/reference")
    elif mode == COPY:
        if count:
            raise ValueError("COPY payload must be empty")
    else:
        if count < COUNT.size:
            raise ValueError("missing span count")
        records = COUNT.unpack_from(payload)[0]
        if not 0 < records <= width * height or records > (count - COUNT.size) // (SPAN.size + 2):
            raise ValueError("impossible span count")
        offset, previous_row, previous_end = COUNT.size, -1, -1
        for _ in range(records):
            if offset + SPAN.size > count:
                raise ValueError("truncated span header")
            row, start, words = SPAN.unpack_from(payload, offset)
            offset += SPAN.size
            if (not 0 <= row < height or not 0 < words <= width or start + words > width
                    or row < previous_row or (row == previous_row and start <= previous_end)):
                raise ValueError("unordered, adjacent, overlapping or out-of-bounds span")
            end = offset + words * 2
            if end > count:
                raise ValueError("truncated span words")
            values = np.frombuffer(payload[offset:end], dtype="<u2")
            if not np.all(values):
                raise ValueError("noncanonical zero XOR in changed span")
            spans.append((row, start, words, offset, end))
            previous_row, previous_end = row, start + words
            offset = end
        if offset != count:
            raise ValueError("trailing span bytes")
    return dict(mode=mode, width=width, height=height, words=width * height,
                reference_tag=reference.hex(), current_tag=current.hex(),
                payload_bytes=count, packet_bytes=len(packet), fixed_bytes=FIXED_BYTES,
                span_count=len(spans)), payload, spans


def inspect(packet):
    """Validate bounded framing/span grammar and return byte/count metadata.

    Complete current-content/tag validation is performed by decode, because a
    delta cannot be reconstructed without its exact acknowledged reference.
    """
    info, _, _ = _parse(packet)
    return info


def decode(packet, reference=None):
    """Validate fully and return a fresh exact RGB565 patch; no input mutation."""
    info, payload, spans = _parse(packet)
    shape = info["height"], info["width"]
    if info["mode"] == RAW:
        current = np.frombuffer(payload, dtype="<u2").reshape(shape).copy()
    else:
        if reference is None:
            raise ValueError("delta requires exact reference")
        current = _array(reference)
        if current.shape != shape or _tag(current).hex() != info["reference_tag"]:
            raise ValueError("reference geometry/content mismatch")
        if info["mode"] == SPAN_XOR:
            for row, start, words, offset, end in spans:
                current[row, start:start + words] ^= np.frombuffer(payload[offset:end], dtype="<u2")
    if _tag(current).hex() != info["current_tag"]:
        raise ValueError("reconstructed content tag mismatch")
    return current
