"""Independent strict BR88 decoder with a bounded, MSB-first word reservoir.

``decode(packet, blocks, bw=1, stats=None)`` accepts the existing BR88 profile,
including its raw fallback, and returns coefficients in block/raster order.
It imports no previous reader or encoder. ``WordRice(data, size, stats=None,
refill_bits=32)`` also exposes ``value(k, escape)``, ``bit()``, ``end()``,
``at`` (consumed logical bits), and ``size`` (declared logical bits).
Standalone value() accepts integer k in 0..19 and escape width in 0..24;
packet decoding further enforces each DC/run/level field's BR88 parameters.

Refills fetch whole 16- or 32-bit words in wire/MSB order, with a short final
word when necessary. No fetch crosses the supplied byte string. Padding is
validated before reading and never enters the logical reservoir. The reservoir
holds at most 63 bits; a BR88 symbol consumes at most 15 + 24 = 39 bits.
The last short symbol only needs its available prefix bits, not 15 bits of
unavailable lookahead. The 15-zero escape has no terminating one bit.

Counters accumulate in a caller-supplied mutable mapping; missing keys start at
zero. ``symbols`` counts completed value() calls, ``logical_bits`` counts bits
consumed by value() and bit(), ``prefix_queries`` counts leading-zero queries,
``suffix_extracts`` counts suffix requests (including zero-width suffixes),
``refill_words`` counts fetches (including a short final word), and
``fetched_bytes`` counts bytes fetched. ``max_reservoir_bits`` is a high-water
mark across all readers sharing the mapping. Raw packets add no reader work.
These are software operation counts, not hardware cycles or latency estimates.
"""

import struct
import zlib


COUNTERS = (
    "symbols", "logical_bits", "prefix_queries", "suffix_extracts",
    "refill_words", "fetched_bytes", "max_reservoir_bits",
)


def _counters(stats):
    if stats is None:
        stats = {}
    for name in COUNTERS:
        stats.setdefault(name, 0)
    return stats


class Reader:
    """Checked byte-field cursor, independent of entropy bit buffering."""

    def __init__(self, data):
        self.data = data
        self.at = 0

    def take(self, count):
        if count < 0 or self.at + count > len(self.data):
            raise ValueError("BR88 truncated byte fields")
        result = self.data[self.at:self.at + count]
        self.at += count
        return result

    def byte(self):
        return self.take(1)[0]

    def u16(self):
        return int.from_bytes(self.take(2), "little")

    def u32(self):
        return int.from_bytes(self.take(4), "little")

    def end(self):
        if self.at != len(self.data):
            raise ValueError("BR88 trailing fields")


class WordRice:
    def __init__(self, data, size, stats=None, refill_bits=32):
        if refill_bits not in (16, 32):
            raise ValueError("BR88 refill width must be 16 or 32")
        if size < 0 or len(data) != (size + 7) // 8:
            raise ValueError("BR88 exact bit bytes")
        if size % 8 and data[-1] & ((1 << (8 - size % 8)) - 1):
            raise ValueError("BR88 padding")
        self.data = data
        self.size = size
        self.at = 0
        self.stats = _counters(stats)
        self.refill_bits = refill_bits
        self._next_byte = 0
        self._reservoir = 0
        self._available = 0

    def _ensure(self, count):
        # Every extraction chunk is <=32 bits, so appending a word while
        # available<count can retain at most 31+32=63 reservoir bits.
        if count > self.size - self.at:
            raise ValueError("BR88 truncated coded bits")
        while self._available < count:
            byte_count = min(self.refill_bits // 8,
                             len(self.data) - self._next_byte)
            if not byte_count:
                raise ValueError("BR88 truncated coded bits")
            stop = self._next_byte + byte_count
            word = int.from_bytes(self.data[self._next_byte:stop], "big")
            valid = byte_count * 8
            if stop == len(self.data) and self.size % 8:
                padding = 8 - self.size % 8
                word >>= padding
                valid -= padding
            self._reservoir = (self._reservoir << valid) | word
            self._available += valid
            self._next_byte = stop
            self.stats["refill_words"] += 1
            self.stats["fetched_bytes"] += byte_count
            self.stats["max_reservoir_bits"] = max(
                self.stats["max_reservoir_bits"], self._available)

    def _extract(self, count):
        if count < 0:
            raise ValueError("BR88 negative bit width")
        value = 0
        while count:
            chunk = min(count, 32)
            self._ensure(chunk)
            self._available -= chunk
            value = ((value << chunk) |
                     (self._reservoir >> self._available))
            self._reservoir &= (1 << self._available) - 1
            self.at += chunk
            self.stats["logical_bits"] += chunk
            count -= chunk
        return value

    def bit(self):
        return self._extract(1)

    def value(self, k, escape):
        if (not isinstance(k, int) or not 0 <= k <= 19 or
                not isinstance(escape, int) or not 0 <= escape <= 24):
            raise ValueError("BR88 Rice bit width")
        self.stats["prefix_queries"] += 1
        window = min(15, self.size - self.at)
        if not window:
            raise ValueError("BR88 truncated coded bits")
        self._ensure(window)
        prefix = self._reservoir >> (self._available - window)
        quotient = window - prefix.bit_length()
        if not prefix and window < 15:
            self._extract(window)
            raise ValueError("BR88 truncated coded bits")
        self._extract(15 if quotient == 15 else quotient + 1)
        width = escape if quotient == 15 else k
        self.stats["suffix_extracts"] += 1
        suffix = self._extract(width)
        self.stats["symbols"] += 1
        return suffix if quotient == 15 else (quotient << k) | suffix

    def end(self):
        if self.at != self.size:
            raise ValueError("BR88 unused coded bits")


def signed(value):
    return -(value // 2) - 1 if value & 1 else value // 2


def decode(packet, blocks, bw=1, stats=None):
    stats = _counters(stats)
    if (not 1 <= blocks <= 65536 or bw != 1 or
            not 46 <= len(packet) <= 46 + 128 * blocks):
        raise ValueError("BR88 bounds")
    if zlib.crc32(packet[:-4]) != int.from_bytes(packet[-4:], "little"):
        raise ValueError("BR88 CRC")
    reader = Reader(packet[:-4])
    if reader.take(4) != b"BR88" or reader.byte() != 1:
        raise ValueError("BR88 profile")
    flags = reader.byte()
    if (flags > 1 or reader.u32() != blocks or reader.u16() != 1 or
            reader.u16() != 0):
        raise ValueError("BR88 binding")
    lengths = [reader.u32() for _ in range(4)]
    counts = [reader.u32() for _ in range(3)]
    if sum(lengths) != len(packet) - 46:
        raise ValueError("BR88 lengths")
    result = [0] * (blocks * 64)
    if flags:
        if lengths != [128 * blocks, 0, 0, 0] or counts != [0, 0, 0]:
            raise ValueError("BR88 raw fields")
        result = list(struct.unpack("<" + "h" * (blocks * 64),
                                    reader.take(128 * blocks)))
        if any(not -2048 <= value <= 2048 for value in result):
            raise ValueError("BR88 raw range")
        reader.end()
        return result
    streams = []
    for length in lengths:
        if length < 6:
            raise ValueError("BR88 stream header")
        fields = Reader(reader.take(length))
        k0, k1, size = fields.byte(), fields.byte(), fields.u32()
        streams.append((k0, k1, WordRice(fields.take(length - 6), size, stats)))
        fields.end()
    reader.end()
    k0, k1, dc = streams[0]
    if k0 > 13 or k1 != 255:
        raise ValueError("BR88 DC parameters")
    for block in range(blocks):
        value = signed(dc.value(k0, 14))
        if not -2048 <= value <= 2048:
            raise ValueError("BR88 DC range")
        result[block * 64] = value
    dc.end()
    order = sorted(range(64), key=lambda i: (
        i // 8 + i % 8,
        (i // 8) if (i // 8 + i % 8) % 2 else -(i // 8)))
    limits = (1, 6, 21, 64)
    for band, count in enumerate(counts):
        k0, k1, bits = streams[band + 1]
        width = limits[band + 1] - limits[band]
        if k0 > 19 or k1 > 11 or count > blocks * width:
            raise ValueError("BR88 AC parameters")
        position = -1
        for _ in range(count):
            position += bits.value(k0, 24) + 1
            if position >= blocks * width:
                raise ValueError("BR88 run range")
            value = signed(bits.value(k1, 12) + 1)
            if value == 0 or not -2048 <= value <= 2048:
                raise ValueError("BR88 level range")
            block, index = divmod(position, width)
            result[block * 64 + order[limits[band] + index]] = value
        bits.end()
    return result
