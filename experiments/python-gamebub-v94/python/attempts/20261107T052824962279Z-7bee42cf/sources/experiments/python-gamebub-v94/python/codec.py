"""Independent strict EC94 coefficient decoder; no encoder imports.

AB38/BR88 primitives are frozen copies of the independent EC93 reader.
Only inline rANS models are accepted. There is no shared model cache.
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
            raise ValueError('EC94 Rice exact bit length')
        if size % 8 and data[-1] & ((1 << (8 - size % 8)) - 1):
            raise ValueError('EC94 Rice padding')
        self.data, self.size, self.pos = data, size, 0

    def raw(self):
        if self.pos >= self.size:
            raise ValueError('EC94 Rice truncation')
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
            raise ValueError('EC94 Rice unused bits')


class ArithmeticReader:
    def __init__(self, data, size):
        if size < 18 or len(data) != (size + 7) // 8:
            raise ValueError('EC94 arithmetic exact bit length')
        if size % 8 and data[-1] & ((1 << (8 - size % 8)) - 1):
            raise ValueError('EC94 arithmetic padding')
        self.data, self.size, self.pos = data, size, 0
        self.start, self.end, self.code = 0, 65535, 0
        self.probabilities = [128] * 88
        for _ in range(16):
            self.code = (self.code << 1) | self.raw()

    def raw(self):
        if self.pos >= self.size:
            raise ValueError('EC94 arithmetic truncation')
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
            raise ValueError('EC94 arithmetic interval')
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
            raise ValueError('EC94 arithmetic exact termination')



RANS_L = 1 << 23
RANS_DESCRIPTOR = struct.Struct('<BBBBIIII')


class RansReader:
    """Byte rANS category reader with independently tracked literal suffixes."""
    def __init__(self, stream, context, method, expected_symbols=None):
        if context not in range(4) or method not in (2, 3) or type(stream) is not bytes:
            raise ValueError('EC94 rANS context/method')
        if len(stream) < RANS_DESCRIPTOR.size:
            raise ValueError('EC94 rANS descriptor')
        (self.k0, self.k1, self.scale, table_mode, self.model_id,
         rans_bytes, literal_bits, self.symbol_count) = RANS_DESCRIPTOR.unpack_from(stream)
        parameters(self.k0, self.k1, context)
        if self.scale not in (8, 9, 10) or table_mode != 0:
            raise ValueError('EC94 rANS scale/inline model required')
        if expected_symbols is not None and self.symbol_count != expected_symbols:
            raise ValueError('EC94 rANS symbol count')
        self.context, self.lanes = context, 2 if method == 2 else 4
        model_count = 1 if context == 0 else 2
        tables_end = 20 + model_count * 32
        if (rans_bytes < 4 * self.lanes or
                tables_end + rans_bytes + (literal_bits + 7) // 8 != len(stream)):
            raise ValueError('EC94 rANS exact lengths')
        table_bytes = stream[20:tables_end]
        if zlib.crc32(table_bytes) != self.model_id:
            raise ValueError('EC94 rANS model CRC')
        self.models = []
        for model in range(model_count):
            freq = list(struct.unpack_from('<16H', table_bytes, model * 32))
            if sum(freq) != 1 << self.scale:
                raise ValueError('EC94 rANS frequency sum')
            cdf, total = [], 0
            lookup = []
            for q, f in enumerate(freq):
                cdf.append(total)
                total += f
                lookup.extend([q] * f)
            self.models.append(dict(freq=freq, cdf=cdf, lookup=lookup))
        self.states = list(struct.unpack_from('<' + 'I' * self.lanes, stream, tables_end))
        if any(not RANS_L <= state < 1 << 31 for state in self.states):
            raise ValueError('EC94 rANS initial state')
        self.initial_states = list(self.states)
        self.renorm = stream[tables_end + 4 * self.lanes:tables_end + rans_bytes]
        self.literal = RiceReader(stream[tables_end + rans_bytes:], literal_bits)
        self.cursor, self.field = 0, 0
        self.trace = []
        self.values = []

    def rice(self, k, escape, level=False):
        if self.field >= self.symbol_count:
            raise ValueError('EC94 rANS too many fields')
        model_index = self.field % 2 if self.context else 0
        model = self.models[model_index]
        lane = self.field % self.lanes
        before, cursor_before = self.states[lane], self.cursor
        slot = before & ((1 << self.scale) - 1)
        q = model['lookup'][slot]
        state = model['freq'][q] * (before >> self.scale) + slot - model['cdf'][q]
        state_unrenormalized = state
        while state < RANS_L:
            if self.cursor >= len(self.renorm) or self.cursor - cursor_before >= 2:
                raise ValueError('EC94 rANS renormalization extent/bound')
            state = (state << 8) | self.renorm[self.cursor]
            self.cursor += 1
        self.states[lane] = state
        literal_before = self.literal.pos
        value = 0
        for _ in range(escape if q == 15 else k):
            value = (value << 1) | self.literal.raw()
        if q != 15:
            value |= q << k
        self.trace.append(dict(index=self.field, model=model_index, lane=lane, q=q,
                               slot=slot, state_before=before,
                               state_unrenormalized=state_unrenormalized,
                               state_after=state, cursor_before=cursor_before,
                               cursor=self.cursor, renorm_count=self.cursor - cursor_before,
                               literal_before=literal_before, literal_after=self.literal.pos,
                               value=value))
        self.values.append(value)
        self.field += 1
        return value

    def finish(self):
        if (self.field != self.symbol_count or self.cursor != len(self.renorm) or
                any(state != RANS_L for state in self.states)):
            raise ValueError('EC94 rANS exact terminal consumption/state')
        self.literal.finish()


def inspect_rans(stream, context, method, expected_symbols=None):
    """Decode every category/literal and return a complete independent trace."""
    reader = RansReader(stream, context, method, expected_symbols)
    if context and reader.symbol_count % 2:
        raise ValueError('EC94 rANS odd AC field count')
    for field in range(reader.symbol_count):
        level = bool(context and field % 2)
        k = reader.k1 if level else reader.k0
        reader.rice(k, 12 if level else 24 if context else 14, level)
    reader.finish()
    return dict(k0=reader.k0, k1=reader.k1, scale=reader.scale,
                lanes=reader.lanes, model_id=reader.model_id,
                models=[dict(freq=m['freq'], cdf=m['cdf']) for m in reader.models],
                symbol_count=reader.symbol_count, initial_states=reader.initial_states,
                final_states=reader.states, renorm_bytes=list(reader.renorm),
                literal_bits=reader.literal.size, fields=reader.trace, values=reader.values)


def signed(value):
    return -(value // 2) - 1 if value & 1 else value // 2


def parse_header(packet, blocks, bw=1):
    """Validate framing/CRC; return flags, selector, four streams, AC counts."""
    if type(blocks) is not int or not 1 <= blocks <= 65536 or type(bw) is not int or bw != 1:
        raise ValueError('EC94 requested geometry')
    if type(packet) is not bytes or not 48 <= len(packet) <= 48 + 128 * blocks:
        raise ValueError('EC94 packet bounds')
    if zlib.crc32(packet[:-4]) != int.from_bytes(packet[-4:], 'little'):
        raise ValueError('EC94 CRC')
    magic, version, flags, selector, reserved, n, predictor, reserved16, *tail = FRAME.unpack_from(packet)
    if ((magic, version, reserved, n, predictor, reserved16) !=
            (b'EC94', 1, 0, blocks, 1, 0) or flags not in (0, 1)):
        raise ValueError('EC94 profile/binding')
    lengths, counts = tail[:4], tail[4:]
    if sum(lengths) != len(packet) - 48:
        raise ValueError('EC94 exact lengths')
    if not flags and sum(lengths) >= 128 * blocks:
        raise ValueError('EC94 coded payload requires raw fallback')
    if flags and (selector or lengths != [128 * blocks, 0, 0, 0] or any(counts)):
        raise ValueError('EC94 raw fields')
    if any(count > blocks * width for count, width in zip(counts, (5, 15, 43))):
        raise ValueError('EC94 AC count bound')
    streams, offset = [], FRAME.size
    for length in lengths:
        streams.append(packet[offset:offset + length])
        offset += length
    return flags, selector, streams, counts


def parameters(k0, k1, context):
    if context == 0:
        if k0 > 13 or k1 != 255:
            raise ValueError('EC94 DC parameters')
    elif k0 > 19 or k1 > 11:
        raise ValueError('EC94 AC parameters')


def decode_context(stream, context, count, blocks, method):
    """Decode a context: AB=0, BR=1, rANS two lanes=2, four lanes=3."""
    if (type(context) is not int or context not in range(4) or
            type(blocks) is not int or not 1 <= blocks <= 65536 or
            type(method) is not int or method not in range(4) or
            type(count) is not int or type(stream) is not bytes):
        raise ValueError('EC94 context geometry')
    width = 1 if context == 0 else LIMITS[context] - LIMITS[context - 1]
    if not 0 <= count <= blocks * width:
        raise ValueError('EC94 context event count')
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
                    raise ValueError('EC94 DC range')
            else:
                position += reader.rice(k0, 24) + 1
                if position >= len(result):
                    raise ValueError('EC94 run range')
                value = signed(reader.rice(k1, 12, True) + 1)
                if not value or not -2048 <= value <= 2048:
                    raise ValueError('EC94 level range')
            result[position] = value
        reader.finish()

    if method in (2, 3):
        reader = RansReader(stream, context, method, events if context == 0 else 2 * events)
        consume(reader, reader.k0, reader.k1, events)
    else:
        if len(stream) < 6:
            raise ValueError('EC94 stream descriptor')
        k0, k1, size = struct.unpack_from('<BBI', stream)
        reader = (ArithmeticReader if method == 0 else RiceReader)(stream[6:], size)
        consume(reader, k0, k1, events)
    return result


def decode(packet, blocks, bw=1):
    flags, selector, streams, counts = parse_header(packet, blocks, bw)
    if flags:
        result = list(struct.unpack('<' + 'h' * (blocks * 64), streams[0]))
        if any(not -2048 <= value <= 2048 for value in result):
            raise ValueError('EC94 raw range')
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
