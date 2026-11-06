"""Bounded packed coefficient scratch: functional Python architecture model.

This changes scratch representation only, not BR88 bytes or quantization. It
does not implement an SDRAM controller or establish cycle-level timing/fit.
"""
import struct

LIMITS = (1, 6, 21, 64)
ORDER = tuple(sorted(range(64), key=lambda i: (
    i // 8 + i % 8, i // 8 if (i // 8 + i % 8) % 2 else -(i // 8))))
INVERSE = {raster: at for at, raster in enumerate(ORDER)}
MAX_BLOCKS = 8192
HEADER = 32
BURST = 16


def aligned(value):
    return (value + BURST - 1) // BURST * BURST


def layout(blocks, counts, raw=False):
    if not 1 <= blocks <= MAX_BLOCKS or len(counts) != 3:
        raise ValueError('scratch profile geometry')
    if any(not 0 <= count <= blocks * (LIMITS[b + 1] - LIMITS[b])
           for b, count in enumerate(counts)):
        raise ValueError('scratch event counts')
    if raw and any(counts):
        raise ValueError('raw scratch counts')
    sizes = [blocks * 128] if raw else [blocks * 2, *(count * 4 for count in counts)]
    starts, at = [], HEADER
    for size in sizes:
        starts.append(at)
        at += aligned(size)
    return dict(starts=starts, sizes=sizes, used_bytes=at,
                padding_bytes=sum(aligned(size) - size for size in sizes))


class PackedScratch:
    """One transaction, one pending coefficient, one 16-byte write assembler.

    Complete contexts in order DC, AC1, AC2, AC3. RAW has one dense context.
    13 signed coefficient bits plus a 19-bit linear AC band position fit32bits.
    The <=8192-block profile makes every supported position fit19bits.

    The line-epoch instrumentation is a host proof aid, not proposed RAM tags.
    Memory starts poisoned, is reused without clearing and can be read only
    after every context has completed and seal() has written the descriptor.
    """
    def __init__(self, capacity=256 * 1024):
        if capacity < HEADER or capacity % BURST:
            raise ValueError('scratch capacity alignment')
        self.capacity = capacity
        self.memory = bytearray([0xa5]) * capacity
        self.line_epochs = [-1] * (capacity // BURST)
        self.epoch = -1
        self.active = self.sealed = False
        self.pending = None

    def begin(self, epoch, blocks, counts, raw=False):
        if not 0 <= epoch <= 0xffffffff or epoch <= self.epoch:
            raise ValueError('scratch epoch')
        self.abort()
        self.epoch = epoch
        plan = layout(blocks, counts, raw)
        if plan['used_bytes'] > self.capacity:
            raise BufferError('scratch capacity exceeded')
        self.plan, self.blocks, self.counts, self.raw = plan, blocks, tuple(counts), bool(raw)
        self.targets = [blocks * 64] if raw else [blocks, *counts]
        self.phase, self.written, self.previous = 0, [0] * len(self.targets), [-1] * len(self.targets)
        self.line = bytearray()
        self.line_address = HEADER
        self.caches = {}
        self.stats = dict(accepted=0, held_samples=0, pending_high_water=0,
                          write_bursts=0, read_bursts=0, logical_read_bytes=0,
                          write_assembler_high_water=0, read_cache_high_water=0,
                          tile_coefficients=64, ac_lookahead_records=3)
        self.active = True

    def abort(self):
        self.active = self.sealed = False
        self.pending = None

    def _active(self, epoch):
        if not self.active or epoch != self.epoch:
            raise ValueError('inactive or stale scratch epoch')

    def offer(self, epoch, band, item):
        self._active(epoch)
        if self.pending is not None:
            raise BufferError('coefficient credit exhausted')
        if band != self.phase or band >= len(self.targets) or self.written[band] >= self.targets[band]:
            raise ValueError('scratch context/count')
        block, index, value = item
        if not 0 <= block < self.blocks or not 0 <= index < 64 or not -2048 <= value <= 2048:
            raise ValueError('scratch coefficient bounds')
        if self.raw:
            position = block * 64 + index
            if position != self.written[band]:
                raise ValueError('raw raster order')
            data = struct.pack('<h', value)
        elif band == 0:
            if index != 0 or block != self.written[band]:
                raise ValueError('DC order')
            position = block
            data = struct.pack('<h', value)
        else:
            width = LIMITS[band] - LIMITS[band - 1]
            zigzag = INVERSE[index]
            if not LIMITS[band - 1] <= zigzag < LIMITS[band] or value == 0:
                raise ValueError('AC band/value')
            position = block * width + zigzag - LIMITS[band - 1]
            if position <= self.previous[band] or position >= 1 << 19:
                raise ValueError('AC order/packed position')
            data = struct.pack('<I', (position << 13) | (value & 0x1fff))
        self.pending = epoch, band, position, data
        self.stats['pending_high_water'] = 1

    def _write_burst(self, address, data):
        if address % BURST or len(data) != BURST or not 0 <= address <= self.capacity - BURST:
            raise ValueError('burst write bounds')
        self.memory[address:address + BURST] = data
        self.line_epochs[address // BURST] = self.epoch
        self.stats['write_bursts'] += 1

    def consume(self, epoch, ready):
        self._active(epoch)
        if self.pending is None:
            return False
        if not ready:
            self.stats['held_samples'] += 1
            return False
        pending_epoch, band, position, data = self.pending
        if pending_epoch != epoch:
            raise ValueError('stale pending coefficient')
        self.line.extend(data)
        self.stats['write_assembler_high_water'] = max(self.stats['write_assembler_high_water'], len(self.line))
        if len(self.line) == BURST:
            self._write_burst(self.line_address, self.line)
            self.line_address += BURST
            self.line.clear()
        self.written[band] += 1
        self.previous[band] = position
        self.pending = None
        self.stats['accepted'] += 1
        return True

    def complete(self, epoch, band):
        self._active(epoch)
        if (self.pending is not None or band != self.phase or band >= len(self.targets) or
                self.written[band] != self.targets[band]):
            raise ValueError('premature scratch context completion')
        if self.line:
            self.line.extend(bytes(BURST - len(self.line)))
            self._write_burst(self.line_address, self.line)
            self.line_address += BURST
            self.line.clear()
        expected = self.plan['starts'][band] + aligned(self.plan['sizes'][band])
        assert self.line_address == expected
        self.phase += 1

    def seal(self, epoch):
        self._active(epoch)
        if self.pending is not None or self.phase != len(self.targets):
            raise ValueError('incomplete scratch transaction')
        header = struct.pack('<8I', 0x43393150, self.blocks, int(self.raw),
                             *self.counts, self.plan['used_bytes'], 0)
        self._write_burst(0, header[:16])
        self._write_burst(16, header[16:])
        assert self.stats['write_bursts'] * BURST == self.plan['used_bytes']
        self.active, self.sealed = False, True

    def _readable(self, epoch):
        if not self.sealed or epoch != self.epoch:
            raise ValueError('unsealed or stale scratch read')

    def _fetch(self, address):
        if address % BURST or address + BURST > self.plan['used_bytes']:
            raise ValueError('burst read bounds')
        assert self.line_epochs[address // BURST] == self.epoch, 'unwritten current-epoch line'
        self.stats['read_bursts'] += 1
        return bytes(self.memory[address:address + BURST])

    def _read(self, segment, address, count):
        base = address // BURST * BURST
        if segment not in self.caches or self.caches[segment][0] != base:
            self.caches[segment] = base, self._fetch(base)
            self.stats['read_cache_high_water'] = max(self.stats['read_cache_high_water'], len(self.caches))
        offset = address - base
        assert offset + count <= BURST
        self.stats['logical_read_bytes'] += count
        return self.caches[segment][1][offset:offset + count]

    def tiles(self, epoch):
        """One dense 64-coefficient tile at a time, with at most three AC heads.

        This is an algorithmic merge, not a clocked datapath. It charges actual
        16-byte cache fills, including header and unused segment tail bytes.
        Dense tile initialization/selection and delivery still need RTL cycles.
        """
        self._readable(epoch)
        self.caches = {}
        header = self._fetch(0) + self._fetch(16)
        self.stats['logical_read_bytes'] += HEADER
        assert struct.unpack('<8I', header) == (0x43393150, self.blocks, int(self.raw),
                                                *self.counts, self.plan['used_bytes'], 0)
        starts = self.plan['starts']
        if self.raw:
            for block in range(self.blocks):
                self._readable(epoch)
                tile = [struct.unpack('<h', self._read(0, starts[0] + (block * 64 + index) * 2, 2))[0]
                        for index in range(64)]
                yield block, tuple(tile)
            return
        cursors = [0, 0, 0]
        heads = [None, None, None]

        def advance(band):
            cursor = cursors[band - 1]
            if cursor == self.counts[band - 1]:
                heads[band - 1] = None
                return
            word = struct.unpack('<I', self._read(band, starts[band] + cursor * 4, 4))[0]
            position, value = word >> 13, word & 0x1fff
            value = value - 8192 if value & 4096 else value
            width = LIMITS[band] - LIMITS[band - 1]
            assert position < self.blocks * width and value != 0 and -2048 <= value <= 2048
            block, within = divmod(position, width)
            heads[band - 1] = block, ORDER[LIMITS[band - 1] + within], value
            cursors[band - 1] += 1

        for band in range(1, 4):
            advance(band)
        for block in range(self.blocks):
            self._readable(epoch)
            tile = [0] * 64
            tile[0] = struct.unpack('<h', self._read(0, starts[0] + block * 2, 2))[0]
            for band in range(1, 4):
                while heads[band - 1] is not None and heads[band - 1][0] == block:
                    _, index, value = heads[band - 1]
                    tile[index] = value
                    advance(band)
            yield block, tuple(tile)
        assert all(head is None for head in heads)
        assert self.stats['read_cache_high_water'] <= 4
