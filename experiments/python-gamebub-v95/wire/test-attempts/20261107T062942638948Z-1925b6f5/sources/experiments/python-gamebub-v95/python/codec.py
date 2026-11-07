"""Independent, strict V95 U8 8x8 pixel-palette reader.

This module imports no encoder or native implementation. Records contain exact
canonical-plane samples, not transform coefficients. Palette history is an
explicit argument: callers must reset it at every plane and frame boundary.
``parse_plane`` always starts a new history and leaves the EC92 residual opaque.
"""

import struct

SAMPLES = 64
MAX_RECORD = 138


def _palette(values):
    if (type(values) is not tuple or not 1 <= len(values) <= 8 or
            any(type(v) is not int or not 0 <= v <= 255 for v in values) or
            any(a >= b for a, b in zip(values, values[1:]))):
        raise ValueError('V95 palette must be 1..8 sorted unique U8 values')
    return values


class _Bits:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def read(self, width):
        if self.pos + width > len(self.data) * 8:
            raise ValueError('V95 truncated index/literal bits')
        value = 0
        for _ in range(width):
            value = value * 2 + ((self.data[self.pos // 8] >> (7 - self.pos % 8)) & 1)
            self.pos += 1
        return value

    def finish(self):
        if (self.pos + 7) // 8 != len(self.data):
            raise ValueError('V95 trailing index/literal bytes')
        if self.pos % 8 and self.data[-1] & ((1 << (8 - self.pos % 8)) - 1):
            raise ValueError('V95 nonzero index/literal padding')


def decode(record, previous=None):
    """Return ``(64 decoded bytes, next_palette)`` or raise ``ValueError``.

    A supplied previous palette must be a sorted unique U8 tuple. RAW clears
    history; own-palette records replace it; REUSE keeps it. Unused palette
    entries are valid in both own and reused palettes.
    """
    if type(record) is not bytes or not 2 <= len(record) <= MAX_RECORD:
        raise ValueError('V95 record bounds/type')
    if previous is not None:
        _palette(previous)
    kind, count = record[:2]
    if kind == 3:
        if count != 0 or len(record) != 66:
            raise ValueError('V95 RAW reserved byte/exact length')
        return record[2:], None
    if kind == 4:
        if count not in (0, 1, 2) or len(record) < 3 or record[2] != 0:
            raise ValueError('V95 REUSE subkind/palette ID')
        if previous is None:
            raise ValueError('V95 REUSE missing previous palette')
        kind, palette, offset = count, previous, 3
    elif kind in (0, 1, 2):
        if not 1 <= count <= 8 or len(record) < 2 + count:
            raise ValueError('V95 own palette count/extent')
        palette, offset = _palette(tuple(record[2:2 + count])), 2 + count
    else:
        raise ValueError('V95 unknown record kind')
    count = len(palette)
    width = (count - 1).bit_length()
    body = record[offset:]
    output = bytearray()

    def index(reader):
        value = reader.read(width)
        if value >= count:
            raise ValueError('V95 unused index code')
        return palette[value]

    if kind == 0:
        reader = _Bits(body)
        output.extend(index(reader) for _ in range(SAMPLES))
        reader.finish()
    elif kind == 1:
        cursor = 0
        while len(output) < SAMPLES:
            if cursor >= len(body):
                raise ValueError('V95 PRED truncated instruction')
            instruction = body[cursor]
            cursor += 1
            op, run = instruction >> 6, (instruction & 63) + 1
            position = len(output)
            if position + run > SAMPLES:
                raise ValueError('V95 PRED output overrun')
            if op == 0:
                if position < 8:
                    raise ValueError('V95 TOP before first row')
                for _ in range(run):
                    output.append(output[-8])
            elif op == 1:
                if position % 8 == 0 or run > 8 - position % 8:
                    raise ValueError('V95 LEFT row boundary')
                output.extend([output[-1]] * run)
            elif op == 2:
                extent = (run * width + 7) // 8
                reader = _Bits(body[cursor:cursor + extent])
                output.extend(index(reader) for _ in range(run))
                reader.finish()
                cursor += extent
            else:
                raise ValueError('V95 PRED reserved operation')
        if cursor != len(body):
            raise ValueError('V95 PRED trailing bytes')
    else:
        reader = _Bits(body)
        escape_width = count.bit_length()
        for _ in range(SAMPLES):
            value = reader.read(escape_width)
            if value > count:
                raise ValueError('V95 ESC unused index code')
            output.append(reader.read(8) if value == count else palette[value])
        reader.finish()
    return bytes(output), palette


def parse_plane(packet, active_positions=None):
    """Read a complete V95 plane; return palette entries and opaque EC92 bytes.

    ``active_positions`` supplies original mode-2 positions in ascending order.
    When supplied, every palette entry must belong to that set and its count
    minus palette records must equal the residual block count. The caller owns
    the original mode map and full residual coefficient/pixel reconstruction.
    """
    if type(packet) is not bytes or len(packet) < 12:
        raise ValueError('V95 plane bounds/type')
    if active_positions is not None:
        active_positions = tuple(active_positions)
        if (any(type(p) is not int or not 0 <= p <= 65535 for p in active_positions) or
                any(a >= b for a, b in zip(active_positions, active_positions[1:]))):
            raise ValueError('V95 active positions must be ascending unique U16')
        active = set(active_positions)
    else:
        active = None
    count = struct.unpack_from('>I', packet)[0]
    if count > (len(packet) - 12) // 6 or (active is not None and count > len(active)):
        raise ValueError('V95 palette directory count')
    cursor, last_position, previous, entries = 4, -1, None, []
    for _ in range(count):
        if cursor + 4 > len(packet) - 8:
            raise ValueError('V95 truncated palette directory')
        position, length = struct.unpack_from('>HH', packet, cursor)
        cursor += 4
        if (position <= last_position or (active is not None and position not in active) or
                not 2 <= length <= MAX_RECORD or cursor + length > len(packet) - 8):
            raise ValueError('V95 palette position/record extent')
        record = packet[cursor:cursor + length]
        pixels, next_palette = decode(record, previous)
        entries.append(dict(position=position, record=record, pixels=pixels,
                            palette_before=previous, palette_after=next_palette))
        previous, last_position, cursor = next_palette, position, cursor + length
    if cursor + 8 > len(packet):
        raise ValueError('V95 missing residual directory')
    residual_blocks, entropy_length = struct.unpack_from('>II', packet, cursor)
    cursor += 8
    if (entropy_length != len(packet) - cursor or
            (residual_blocks == 0) != (entropy_length == 0) or
            residual_blocks > 65536 or
            (active is not None and residual_blocks != len(active) - count)):
        raise ValueError('V95 residual count/exact extent')
    entropy = packet[cursor:]
    if residual_blocks and not entropy.startswith(b'EC92'):
        raise ValueError('V95 residual must use EC92')
    return dict(palettes=entries, residual_blocks=residual_blocks, entropy=entropy)
