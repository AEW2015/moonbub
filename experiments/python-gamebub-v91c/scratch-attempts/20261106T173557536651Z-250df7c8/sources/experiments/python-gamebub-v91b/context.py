"""V91b sparse context/reference transaction, with one coefficient credit.

This is a Python functional integration model, not a cycle or resource model.
Packet CRC and metadata are checked before opening its four contexts. Context
writes are provisional; only finish() publishes a completely accepted chunk.
The caller supplies the independently qualified Rice primitive.
"""
from array import array
from dataclasses import dataclass
import struct
import zlib


LIMITS = (1, 6, 21, 64)
ORDER = tuple(sorted(range(64), key=lambda n: (
    n // 8 + n % 8, n // 8 if (n // 8 + n % 8) % 2 else -(n // 8))))


@dataclass(frozen=True)
class Context:
    blocks: int
    band: int
    k0: int
    k1: int
    event_count: int
    bit_size: int
    data: bytes

    def validate(self):
        if not 1 <= self.blocks <= 65536 or not 0 <= self.band <= 3:
            raise ValueError('context geometry')
        if self.band == 0:
            if self.k0 > 13 or self.k0 < 0 or self.k1 != 255 or self.event_count != self.blocks:
                raise ValueError('DC metadata')
        else:
            width = LIMITS[self.band] - LIMITS[self.band - 1]
            if (not 0 <= self.k0 <= 19 or not 0 <= self.k1 <= 11 or
                    not 0 <= self.event_count <= self.blocks * width):
                raise ValueError('AC metadata')
        if self.bit_size < 0 or len(self.data) != (self.bit_size + 7) // 8:
            raise ValueError('context exact bytes')
        if self.bit_size % 8 and self.data[-1] & ((1 << (8 - self.bit_size % 8)) - 1):
            raise ValueError('context padding')


def parse_chunk(packet, blocks):
    """Return validated four contexts, or validated raw coefficients.

    Complete packet binding/CRC is software work here; the RTL accepts extracted
    context metadata and does not execute this packet parser.
    """
    if not 1 <= blocks <= 65536 or not 46 <= len(packet) <= 46 + blocks * 128:
        raise ValueError('packet bounds')
    if packet[:5] != b'BR88\x01' or packet[5] not in (0, 1):
        raise ValueError('packet profile')
    if zlib.crc32(packet[:-4]) != int.from_bytes(packet[-4:], 'little'):
        raise ValueError('packet CRC')
    if struct.unpack_from('<IHH', packet, 6) != (blocks, 1, 0):
        raise ValueError('packet binding')
    lengths = struct.unpack_from('<4I', packet, 14)
    counts = struct.unpack_from('<3I', packet, 30)
    if sum(lengths) != len(packet) - 46:
        raise ValueError('packet lengths')
    if packet[5]:
        if lengths != (blocks * 128, 0, 0, 0) or counts != (0, 0, 0):
            raise ValueError('raw metadata')
        raw = struct.unpack_from('<' + str(blocks * 64) + 'h', packet, 42)
        if any(not -2048 <= value <= 2048 for value in raw):
            raise ValueError('raw range')
        return (), raw
    contexts = []
    offset = 42
    for band, length in enumerate(lengths):
        if length < 6:
            raise ValueError('context header')
        k0, k1, bit_size = struct.unpack_from('<BBI', packet, offset)
        context = Context(blocks, band, k0, k1,
                          blocks if band == 0 else counts[band - 1],
                          bit_size, packet[offset + 6:offset + length])
        context.validate()
        contexts.append(context)
        offset += length
    if offset != len(packet) - 4:
        raise ValueError('packet end')
    return tuple(contexts), None


def signed(value):
    return -(value // 2) - 1 if value & 1 else value // 2


def writes(context, reader_type):
    """Decode lazily: no next event is requested until caller returns credit.

    Yields sparse (block,raster_index,value), including all DC values. Exact
    stream-end validation occurs when the generator completes, after its last
    provisional write has been consumed. Unmentioned coefficients are zero.
    """
    context.validate()
    reader = reader_type(context.data, context.bit_size)
    position = -1
    for event in range(context.event_count):
        if context.band == 0:
            block, index = event, 0
            value = signed(reader.value(context.k0, 14))
        else:
            width = LIMITS[context.band] - LIMITS[context.band - 1]
            position += reader.value(context.k0, 24) + 1
            if position >= context.blocks * width:
                raise ValueError('AC run range')
            block, within = divmod(position, width)
            index = ORDER[LIMITS[context.band - 1] + within]
            value = signed(reader.value(context.k1, 12) + 1)
            if value == 0:
                raise ValueError('AC zero')
        if not -2048 <= value <= 2048:
            raise ValueError('coefficient range')
        yield block, index, value
    reader.end()


class Transaction:
    """Bounded scratch and one pending output; failed/aborted epochs never commit.

    Scratch here is a dense Python array plus a duplicate-write bitmap, not an
    FPGA memory-fit claim. There is no unbounded FIFO. Epoch wrap is intentionally
    disallowed in this reference; a system owner must define wrap/drain policy.
    """
    def __init__(self):
        self.epoch = -1
        self.active = False
        self.pending = None
        self.high_water = 0
        self.accepted = 0
        self.published = None

    def begin(self, epoch, blocks):
        if not 0 <= epoch <= 0xffffffff or epoch <= self.epoch or not 1 <= blocks <= 65536:
            raise ValueError('epoch or geometry')
        self.epoch, self.blocks, self.active = epoch, blocks, True
        self.pending = None
        self.scratch = array('h', [0]) * (blocks * 64)
        self.seen = bytearray(blocks * 64)
        self.completed = set()
        self.high_water = 0
        self.accepted = 0
        self.published = None

    def offer(self, epoch, band, item):
        if not self.active or epoch != self.epoch:
            raise ValueError('stale coefficient')
        if self.pending is not None:
            raise BufferError('no coefficient credit')
        if not 0 <= band <= 3 or band in self.completed:
            raise ValueError('closed context')
        block, index, value = item
        if not 0 <= block < self.blocks or not 0 <= index < 64 or not -2048 <= value <= 2048:
            raise ValueError('write range')
        valid_indices = (0,) if band == 0 else ORDER[LIMITS[band - 1]:LIMITS[band]]
        if index not in valid_indices or (band != 0 and value == 0):
            raise ValueError('write band')
        if self.seen[block * 64 + index]:
            raise ValueError('duplicate coefficient')
        self.pending = (epoch, block, index, value)
        self.high_water = 1

    def consume(self, ready):
        if not ready or self.pending is None:
            return False
        epoch, block, index, value = self.pending
        if not self.active or epoch != self.epoch:
            raise ValueError('stale pending write')
        address = block * 64 + index
        self.scratch[address], self.seen[address] = value, 1
        self.pending = None
        self.accepted += 1
        return True

    def complete(self, epoch, band):
        if not self.active or epoch != self.epoch or self.pending is not None:
            raise ValueError('premature context completion')
        if not 0 <= band <= 3 or band in self.completed:
            raise ValueError('duplicate context completion')
        self.completed.add(band)

    def finish(self, epoch):
        if (not self.active or epoch != self.epoch or self.pending is not None or
                self.completed != {0, 1, 2, 3}):
            raise ValueError('incomplete transaction')
        self.published = tuple(self.scratch)
        self.active = False
        return self.published

    def abort(self):
        self.active = False
        self.pending = None
        self.published = None


def decode(packet, blocks, reader_type, *, epoch=0, stalls=None):
    """Functional packet adapter; stalls is an optional finite boolean iterator.

    A False consumer sample holds the only pending write, with no advancement
    of the entropy generator. These samples are not FPGA clock counts.
    """
    contexts, raw = parse_chunk(packet, blocks)
    transaction = Transaction()
    transaction.begin(epoch, blocks)
    blocked = 0
    try:
        if raw is not None:
            # Bypass is qualified in software only, separate from context RTL.
            transaction.scratch = array('h', raw)
            for band in range(4):
                transaction.complete(epoch, band)
        else:
            for context in contexts:
                for item in writes(context, reader_type):
                    transaction.offer(epoch, context.band, item)
                    held = transaction.pending
                    while not transaction.consume(True if stalls is None else next(stalls)):
                        blocked += 1
                        assert transaction.pending == held
                transaction.complete(epoch, context.band)
        result = transaction.finish(epoch)
        return result, dict(writes=transaction.accepted, held_samples=blocked,
                           pending_high_water=transaction.high_water,
                           scratch_int16_values=blocks * 64,
                           raw=raw is not None)
    except BaseException:
        transaction.abort()
        raise
