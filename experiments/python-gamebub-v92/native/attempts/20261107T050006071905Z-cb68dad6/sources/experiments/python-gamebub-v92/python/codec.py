"""Independent, strict EC92 reader; imports neither encoder nor prior decoder.

decode(packet, blocks, bw=1) returns a flat block/raster-order coefficient list.
Each selector bit chooses BR88 (one) or AB38 (zero) for DC, [1,6),
[6,21), [21,64), respectively. Each arithmetic model resets independently.
The frozen predictor width is one, so every DC value starts from zero.
"""

import struct
import zlib

FRAME = struct.Struct('<4sBBBBIHH4I3I')
LIMITS = (1, 6, 21, 64)
ORDER = tuple(sorted(range(64), key=lambda n: (
    n // 8 + n % 8, n // 8 if (n // 8 + n % 8) % 2 else -(n // 8))))


class RiceReader:
    def __init__(self, data, size):
        if len(data) != (size + 7) // 8:
            raise ValueError('EC92 Rice exact bit length')
        if size % 8 and data[-1] & ((1 << (8 - size % 8)) - 1):
            raise ValueError('EC92 Rice padding')
        self.data, self.size, self.pos = data, size, 0

    def raw(self):
        if self.pos >= self.size:
            raise ValueError('EC92 Rice truncation')
        value = (self.data[self.pos // 8] >> (7 - self.pos % 8)) & 1
        self.pos += 1
        return value

    def rice(self, k, escape, level=False):
        quotient = 0
        while quotient < 15:
            if self.raw():
                break
            quotient += 1
        value = 0
        for _ in range(escape if quotient == 15 else k):
            value = (value << 1) | self.raw()
        return value if quotient == 15 else (quotient << k) | value

    def finish(self):
        if self.pos != self.size:
            raise ValueError('EC92 Rice unused bits')


class ArithmeticReader:
    def __init__(self, data, size):
        if size < 18 or len(data) != (size + 7) // 8:
            raise ValueError('EC92 arithmetic exact bit length')
        if size % 8 and data[-1] & ((1 << (8 - size % 8)) - 1):
            raise ValueError('EC92 arithmetic padding')
        self.data, self.size, self.pos = data, size, 0
        self.start, self.end, self.code = 0, 65535, 0
        self.probabilities = [128] * 88
        for _ in range(16):
            self.code = (self.code << 1) | self.raw()

    def raw(self):
        if self.pos >= self.size:
            raise ValueError('EC92 arithmetic truncation')
        value = (self.data[self.pos // 8] >> (7 - self.pos % 8)) & 1
        self.pos += 1
        return value

    def bit(self, index):
        probability = self.probabilities[index]
        partition = ((self.end - self.start + 1) * probability) // 256
        boundary = self.start + max(1, min(self.end - self.start, partition)) - 1
        value = int(self.code > boundary)
        if value:
            self.start = boundary + 1
            probability = max(1, probability - max(1, probability // 32))
        else:
            self.end = boundary
            probability = min(255, probability + max(1, (256 - probability) // 32))
        self.probabilities[index] = probability
        while True:
            if self.end < 32768:
                offset = 0
            elif self.start >= 32768:
                offset = 32768
            elif self.start >= 16384 and self.end < 49152:
                offset = 16384
            else:
                break
            self.start = (self.start - offset) * 2
            self.end = (self.end - offset) * 2 + 1
            self.code = (self.code - offset) * 2 + self.raw()
        if not self.start <= self.code <= self.end:
            raise ValueError('EC92 arithmetic interval')
        return value

    def rice(self, k, escape, level=False):
        base = 48 if level else 0
        quotient = 0
        while quotient < 15:
            if self.bit(base + quotient):
                break
            quotient += 1
        value = 0
        for bit in range((escape if quotient == 15 else k) - 1, -1, -1):
            value = (value << 1) | self.bit(base + 16 + min(bit, 23))
        return value if quotient == 15 else (quotient << k) | value

    def finish(self):
        if self.size - self.pos != 2 or self.raw() or self.raw():
            raise ValueError('EC92 arithmetic exact termination')


def signed(value):
    return -(value // 2) - 1 if value & 1 else value // 2


def parse_header(packet, blocks, bw=1):
    """Validate framing/CRC and return flags, mask, four streams, AC counts."""
    if type(blocks) is not int or not 1 <= blocks <= 65536 or type(bw) is not int or bw != 1:
        raise ValueError('EC92 requested geometry')
    if type(packet) is not bytes or not 48 <= len(packet) <= 48 + 128 * blocks:
        raise ValueError('EC92 packet bounds')
    if zlib.crc32(packet[:-4]) != int.from_bytes(packet[-4:], 'little'):
        raise ValueError('EC92 CRC')
    magic, version, flags, mask, reserved, n, predictor, reserved16, *tail = FRAME.unpack_from(packet)
    if ((magic, version, reserved, n, predictor, reserved16) !=
            (b'EC92', 1, 0, blocks, 1, 0) or flags not in (0, 1) or mask & 0xf0):
        raise ValueError('EC92 profile/binding')
    lengths, counts = tail[:4], tail[4:]
    if sum(lengths) != len(packet) - 48:
        raise ValueError('EC92 exact lengths')
    if not flags and sum(lengths) >= 128 * blocks:
        raise ValueError('EC92 coded payload requires raw fallback')
    if flags and (mask or lengths != [128 * blocks, 0, 0, 0] or any(counts)):
        raise ValueError('EC92 raw fields')
    streams, offset = [], FRAME.size
    for length in lengths:
        streams.append(packet[offset:offset + length])
        offset += length
    return flags, mask, streams, counts


def decode_context(stream, context, count, blocks, br):
    """Decode one context into its block-major zigzag-band sequence."""
    if context not in range(4) or not 1 <= blocks <= 65536:
        raise ValueError('EC92 context geometry')
    if len(stream) < (6 if br else 9):
        raise ValueError('EC92 stream header')
    k0, k1, size = struct.unpack_from('<BBI', stream)
    if context == 0:
        if k0 > 13 or k1 != 255:
            raise ValueError('EC92 DC parameters')
        width = 1
    else:
        width = LIMITS[context] - LIMITS[context - 1]
        if k0 > 19 or k1 > 11 or not 0 <= count <= blocks * width:
            raise ValueError('EC92 AC parameters/count')
    reader = (RiceReader if br else ArithmeticReader)(stream[6:], size)
    result = [0] * (blocks * width)
    if context == 0:
        for block in range(blocks):
            value = signed(reader.rice(k0, 14))
            if not -2048 <= value <= 2048:
                raise ValueError('EC92 DC range')
            result[block] = value
    else:
        position = -1
        for _ in range(count):
            position += reader.rice(k0, 24) + 1
            if position >= len(result):
                raise ValueError('EC92 run range')
            value = signed(reader.rice(k1, 12, True) + 1)
            if not value or not -2048 <= value <= 2048:
                raise ValueError('EC92 level range')
            result[position] = value
    reader.finish()
    return result


def decode(packet, blocks, bw=1):
    flags, mask, streams, counts = parse_header(packet, blocks, bw)
    if flags:
        result = list(struct.unpack('<' + 'h' * (blocks * 64), streams[0]))
        if any(not -2048 <= value <= 2048 for value in result):
            raise ValueError('EC92 raw range')
        return result
    result = [0] * (blocks * 64)
    dc = decode_context(streams[0], 0, blocks, blocks, bool(mask & 1))
    result[::64] = dc
    for context in range(1, 4):
        values = decode_context(streams[context], context, counts[context - 1], blocks, bool(mask & (1 << context)))
        lo, hi = LIMITS[context - 1:context + 1]
        width = hi - lo
        for block in range(blocks):
            for index in range(width):
                result[block * 64 + ORDER[lo + index]] = values[block * width + index]
    return result
