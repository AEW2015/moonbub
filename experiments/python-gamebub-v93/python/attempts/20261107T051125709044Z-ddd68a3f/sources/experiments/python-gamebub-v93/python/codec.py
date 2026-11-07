"""Independent strict EC93 coefficient reader; no encoder imports.

Frozen AB38/BR88 arithmetic and Rice primitives below are copied from the
independent EC92 reader in experiments/python-gamebub-v92/python/codec.py.
The selector carries two bits per context: AB, BR, HY, SG32. Every context,
and each SG32 group, resets its entropy model. DC prediction is frozen at zero.
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
            raise ValueError('EC93 Rice exact bit length')
        if size % 8 and data[-1] & ((1 << (8 - size % 8)) - 1):
            raise ValueError('EC93 Rice padding')
        self.data, self.size, self.pos = data, size, 0

    def raw(self):
        if self.pos >= self.size:
            raise ValueError('EC93 Rice truncation')
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
            raise ValueError('EC93 Rice unused bits')


class ArithmeticReader:
    def __init__(self, data, size):
        if size < 18 or len(data) != (size + 7) // 8:
            raise ValueError('EC93 arithmetic exact bit length')
        if size % 8 and data[-1] & ((1 << (8 - size % 8)) - 1):
            raise ValueError('EC93 arithmetic padding')
        self.data, self.size, self.pos = data, size, 0
        self.start, self.end, self.code = 0, 65535, 0
        self.probabilities = [128] * 88
        for _ in range(16):
            self.code = (self.code << 1) | self.raw()

    def raw(self):
        if self.pos >= self.size:
            raise ValueError('EC93 arithmetic truncation')
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
            raise ValueError('EC93 arithmetic interval')
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
            raise ValueError('EC93 arithmetic exact termination')



class HybridReader(ArithmeticReader):
    """Arithmetic unary prefixes, separately padded plain MSB-first suffixes."""
    def __init__(self, prefix, prefix_size, suffix, suffix_size):
        super().__init__(prefix, prefix_size)
        self.suffix = RiceReader(suffix, suffix_size)

    def rice(self, k, escape, level=False):
        base = 48 if level else 0
        quotient = 0
        while quotient < 15:
            if self.bit(base + quotient):
                break
            quotient += 1
        value = 0
        for _ in range(escape if quotient == 15 else k):
            value = (value << 1) | self.suffix.raw()
        return value if quotient == 15 else (quotient << k) | value

    def finish(self):
        super().finish()
        self.suffix.finish()


def signed(value):
    return -(value // 2) - 1 if value & 1 else value // 2


def parse_header(packet, blocks, bw=1):
    """Validate framing/CRC; return flags, selector, four streams, AC counts."""
    if type(blocks) is not int or not 1 <= blocks <= 65536 or type(bw) is not int or bw != 1:
        raise ValueError('EC93 requested geometry')
    if type(packet) is not bytes or not 48 <= len(packet) <= 48 + 128 * blocks:
        raise ValueError('EC93 packet bounds')
    if zlib.crc32(packet[:-4]) != int.from_bytes(packet[-4:], 'little'):
        raise ValueError('EC93 CRC')
    magic, version, flags, selector, reserved, n, predictor, reserved16, *tail = FRAME.unpack_from(packet)
    if ((magic, version, reserved, n, predictor, reserved16) !=
            (b'EC93', 1, 0, blocks, 1, 0) or flags not in (0, 1)):
        raise ValueError('EC93 profile/binding')
    lengths, counts = tail[:4], tail[4:]
    if sum(lengths) != len(packet) - 48:
        raise ValueError('EC93 exact lengths')
    if not flags and sum(lengths) >= 128 * blocks:
        raise ValueError('EC93 coded payload requires raw fallback')
    if flags and (selector or lengths != [128 * blocks, 0, 0, 0] or any(counts)):
        raise ValueError('EC93 raw fields')
    if any(count > blocks * width for count, width in zip(counts, (5, 15, 43))):
        raise ValueError('EC93 AC count bound')
    streams, offset = [], FRAME.size
    for length in lengths:
        streams.append(packet[offset:offset + length])
        offset += length
    return flags, selector, streams, counts


def parameters(k0, k1, context):
    if context == 0:
        if k0 > 13 or k1 != 255:
            raise ValueError('EC93 DC parameters')
    elif k0 > 19 or k1 > 11:
        raise ValueError('EC93 AC parameters')


def decode_context(stream, context, count, blocks, method):
    """Decode one context into its block-major zigzag-band sequence.

    method is 0=AB, 1=BR, 2=HY, 3=SG32. AC count means nonzero events;
    SG32 partitions events, with the AC position continuing across groups.
    """
    if (type(context) is not int or context not in range(4) or
            type(blocks) is not int or not 1 <= blocks <= 65536 or
            type(method) is not int or method not in range(4) or
            type(count) is not int or type(stream) is not bytes):
        raise ValueError('EC93 context geometry')
    width = 1 if context == 0 else LIMITS[context] - LIMITS[context - 1]
    if not 0 <= count <= blocks * width:
        raise ValueError('EC93 context event count')
    events = blocks if context == 0 else count
    result = [0] * (blocks * width)
    position = -1

    def consume(reader, k0, k1, amount):
        nonlocal position
        parameters(k0, k1, context)
        for _ in range(amount):
            if context == 0:
                position += 1
                value = signed(reader.rice(k0, 14))
                if not -2048 <= value <= 2048:
                    raise ValueError('EC93 DC range')
            else:
                position += reader.rice(k0, 24) + 1
                if position >= len(result):
                    raise ValueError('EC93 run range')
                value = signed(reader.rice(k1, 12, True) + 1)
                if not value or not -2048 <= value <= 2048:
                    raise ValueError('EC93 level range')
            result[position] = value
        reader.finish()

    if method == 3:
        if len(stream) < 6:
            raise ValueError('EC93 SG32 descriptor')
        group_size, reserved, groups = struct.unpack_from('<BBI', stream)
        if group_size != 32 or reserved or groups != (events + 31) // 32:
            raise ValueError('EC93 SG32 group count/header')
        offset = 6
        for group in range(groups):
            if len(stream) - offset < 6:
                raise ValueError('EC93 SG32 group descriptor')
            k0, k1, size = struct.unpack_from('<BBI', stream, offset)
            offset += 6
            length = (size + 7) // 8
            if length > len(stream) - offset:
                raise ValueError('EC93 SG32 group length')
            reader = RiceReader(stream[offset:offset + length], size)
            offset += length
            consume(reader, k0, k1, min(32, events - group * 32))
        if offset != len(stream):
            raise ValueError('EC93 SG32 trailing bytes')
    elif method == 2:
        if len(stream) < 10:
            raise ValueError('EC93 HY descriptor')
        k0, k1, prefix_size, suffix_size = struct.unpack_from('<BBII', stream)
        prefix_length = (prefix_size + 7) // 8
        suffix_length = (suffix_size + 7) // 8
        if 10 + prefix_length + suffix_length != len(stream):
            raise ValueError('EC93 HY exact lengths')
        reader = HybridReader(stream[10:10 + prefix_length], prefix_size,
                              stream[10 + prefix_length:], suffix_size)
        consume(reader, k0, k1, events)
    else:
        if len(stream) < 6:
            raise ValueError('EC93 stream descriptor')
        k0, k1, size = struct.unpack_from('<BBI', stream)
        reader = (ArithmeticReader if method == 0 else RiceReader)(stream[6:], size)
        consume(reader, k0, k1, events)
    return result


def decode(packet, blocks, bw=1):
    flags, selector, streams, counts = parse_header(packet, blocks, bw)
    if flags:
        result = list(struct.unpack('<' + 'h' * (blocks * 64), streams[0]))
        if any(not -2048 <= value <= 2048 for value in result):
            raise ValueError('EC93 raw range')
        return result
    result = [0] * (blocks * 64)
    result[::64] = decode_context(streams[0], 0, blocks, blocks, selector & 3)
    for context in range(1, 4):
        values = decode_context(streams[context], context, counts[context - 1], blocks,
                                (selector >> (2 * context)) & 3)
        lo, hi = LIMITS[context - 1:context + 1]
        width = hi - lo
        for block in range(blocks):
            for index in range(width):
                result[block * 64 + ORDER[lo + index]] = values[block * width + index]
    return result
