"""Bounded constant-line scheduling and explicit bank leases, not FPGA timing."""
import hashlib

COUNTS = (5400, 1350, 1350)
BASES = (0, 345600, 432000)
WIDTHS = (720, 360, 360)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def raster_sha(tiles):
    digest = hashlib.sha256()
    start = 0
    for width, count in zip(WIDTHS, COUNTS):
        across = width // 8
        for ty in range(count // across):
            for row in range(8):
                digest.update(b''.join(tiles[start + ty * across + tx][row * 8:row * 8 + 8]
                                       for tx in range(across)))
        start += count
    return digest.hexdigest()


def constant_scan(frame, generated_bytes_per_clock):
    """One 16B line slot, fixed hidden mask, same tiled addresses and source lease.

    Visible data is supplied by a fixture memory read. Generation clocks are
    charged separately; they cannot be added to/mixed with unmeasured controller
    or full-frame latency. This is not the raster-reader RTL's request schedule.
    """
    require(generated_bytes_per_clock in (1, 4, 16), 'generator width')
    require(len(frame['hidden_mask']) == len(frame['tiles']) == 8100, 'shape')
    result, memory_lines, generated_lines, clocks = [], 0, 0, 0
    address_digest = hashlib.sha256()
    offset = 0
    for base, count in zip(BASES, COUNTS):
        for tile in range(count):
            chunks = []
            for line in range(4):
                address = base + tile * 64 + line * 16
                require(address % 16 == 0 and address + 16 <= 518400, 'address')
                if frame['hidden_mask'][offset + tile]:
                    require(frame['tiles'][offset + tile] == bytes([128]) * 64, 'hidden profile data')
                    data = bytes([128]) * 16
                    generated_lines += 1
                    clocks += (16 + generated_bytes_per_clock - 1) // generated_bytes_per_clock
                else:
                    data = frame['tiles'][offset + tile][line * 16:line * 16 + 16]
                    memory_lines += 1
                require(len(data) == 16, 'line extent')
                chunks.append(data)
                address_digest.update(address.to_bytes(4, 'little'))
            result.append(b''.join(chunks))
        offset += count
    require(result == frame['tiles'], 'constant consumer pixel parity')
    require(raster_sha(result) == frame['canonical_sha256'], 'canonical SHA')
    return dict(memory_bl8_commands=memory_lines, memory_read_words16=memory_lines * 8,
                generated_lines=generated_lines, generated_bytes=generated_lines * 16,
                generator_clocks=clocks, generator_bytes_per_clock=generated_bytes_per_clock,
                scheduled_line_count=memory_lines + generated_lines,
                address_order_sha256=address_digest.hexdigest(), canonical_sha256=frame['canonical_sha256'])


class Banks:
    """Three physical materialized banks; no aliases or payload indirection.

    Behavioral lifecycle oracle. One display lease captures a full identity and
    survives accepted-reference advancement. Canceled candidates cannot publish;
    outstanding writes and two observations of consumer drain block reuse.
    """
    def __init__(self):
        self.accepted = self.front = self.pending = self.display = self.candidate = None
        self.outstanding = 0
        self.faulted = False
        self.display_terminal = False
        self.display_drain = 0

    def protected(self):
        return {item[0] for item in (self.accepted, self.front, self.pending, self.display)
                if item is not None}

    def start(self, bank, fid, generation):
        require(self.candidate is None and not self.outstanding, 'candidate busy')
        require(bank in range(3) and bank not in self.protected(), 'protected destination')
        require(0 <= fid < 0xffffffff and 0 < generation < 1 << 64, 'identity bounds')
        require(self.accepted is None or (fid > self.accepted[1] and generation > self.accepted[2]), 'stale identity')
        self.candidate = (bank, fid, generation)
        self.faulted = False

    def issue(self):
        require(self.candidate is not None and not self.faulted, 'no live candidate')
        self.outstanding += 1

    def acknowledge(self):
        require(self.outstanding > 0, 'unowned response')
        self.outstanding -= 1

    def cancel(self):
        require(self.candidate is not None, 'no candidate to cancel')
        self.faulted = True

    def discard(self):
        require(self.candidate is not None and self.faulted and not self.outstanding, 'discard before drain')
        self.candidate = None

    def commit(self, valid):
        require(self.candidate is not None and not self.outstanding and not self.faulted and valid, 'commit fence')
        require(self.pending is None, 'pending occupied')
        self.accepted = self.pending = self.candidate
        self.candidate = None

    def present(self, vblank):
        require(vblank and self.pending is not None and self.display is None, 'presentation fence')
        self.front = self.pending
        self.pending = None

    def open_display(self):
        require(self.display is None and self.front is not None, 'display start')
        self.display = self.front
        self.display_terminal = False
        self.display_drain = 0

    def close_display(self, terminal, physical_busy, held_response):
        require(self.display is not None, 'display missing')
        self.display_terminal |= terminal
        self.display_drain = (self.display_drain + 1 if self.display_terminal and not physical_busy and not held_response else 0)
        if self.display_drain >= 2:
            self.display = None
