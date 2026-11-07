"""Q87 quantizer block prototype. Exact needed values; no image-quality change."""
import struct
import zlib

HEAD = struct.Struct('>4sBBHHH')
CELLS = 1350


def needed_cells(operations):
    if len(operations) != 8100 or any(v not in (0, 1, 2) for v in operations):
        raise ValueError('operation coverage')
    result = [False] * CELLS
    for tile, mode in enumerate(operations):
        if mode != 2:
            continue
        if tile < 5400:
            row, col = divmod(tile, 90)
            cell = row // 2 * 45 + col // 2
        else:
            cell = (tile - 5400) % 1350
        result[cell] = True
    return result


def packed(values):
    out = bytearray((len(values) + 3) // 4)
    for i, value in enumerate(values):
        if value not in (0, 1, 2):
            raise ValueError('quantizer code')
        out[i // 4] |= value << (6 - 2 * (i % 4))
    return bytes(out)


def unpacked(body, count):
    if len(body) != (count + 3) // 4:
        raise ValueError('packed length')
    result = []
    for i in range(len(body) * 4):
        value = (body[i // 4] >> (6 - 2 * (i % 4))) & 3
        if i < count:
            if value == 3:
                raise ValueError('reserved quantizer')
            result.append(value)
        elif value:
            raise ValueError('packed padding')
    return result


def runs(values):
    result = bytearray()
    i = 0
    while i < len(values):
        j = i + 1
        while j < min(i + 64, len(values)) and values[j] == values[i]:
            j += 1
        result.append(values[i] * 64 + j - i - 1)
        i = j
    return bytes(result)


def encode(values, operations, previous=None):
    if len(values) != CELLS or any(v not in (0, 1, 2) for v in values):
        raise ValueError('quantizer coverage')
    needed = needed_cells(operations)
    active = [v for v, need in zip(values, needed) if need]
    candidates = [(0, packed(values)), (2, runs(values)),
                  (4, packed(active)), (5, runs(active))]
    if len(set(values)) == 1:
        candidates.append((1, bytes([values[0]])))
    if active and len(set(active)) == 1:
        candidates.append((3, bytes([active[0]])))
    if previous is not None:
        if len(previous) != CELLS or any(v not in (0, 1, 2) for v in previous):
            raise ValueError('previous quantizer coverage')
        if all(not need or a == b for need, a, b in zip(needed, values, previous)):
            candidates.append((6, b''))
    method, body = min(candidates, key=lambda pair: (len(pair[1]), pair[0]))
    header = HEAD.pack(b'QM87', 1, method, CELLS, len(body), sum(needed))
    content = header + body
    return content + struct.pack('>I', zlib.crc32(content))


def decode(block, operations, previous=None):
    """Strict reader, independently walking run and bit streams."""
    if len(block) < 16:
        raise ValueError('short quantizer block')
    magic, version, method, cells, length, required = HEAD.unpack(block[:12])
    if magic != b'QM87' or version != 1 or cells != CELLS or method > 6:
        raise ValueError('quantizer profile')
    if len(block) != 16 + length or zlib.crc32(block[:-4]) != int.from_bytes(block[-4:], 'big'):
        raise ValueError('quantizer length/CRC')
    needed = needed_cells(operations)
    if required != sum(needed):
        raise ValueError('required-cell count')
    body = block[12:-4]
    if method == 6:
        if body or previous is None or len(previous) != CELLS or any(v not in (0, 1, 2) for v in previous):
            raise ValueError('missing/invalid inherited map')
        return list(previous)
    count = required if method in (3, 4, 5) else CELLS
    if method in (1, 3):
        if not count or len(body) != 1 or body[0] > 2:
            raise ValueError('uniform map')
        values = [body[0]] * count
    elif method in (2, 5):
        values = []
        for byte in body:
            value, n = byte >> 6, (byte & 63) + 1
            if value == 3 or len(values) + n > count:
                raise ValueError('run code/overrun')
            values.extend([value] * n)
        if len(values) != count:
            raise ValueError('run underrun')
    else:
        values = unpacked(body, count)
    if method < 3:
        return values
    result, cursor = [0] * CELLS, 0
    for i, need in enumerate(needed):
        if need:
            result[i] = values[cursor]
            cursor += 1
    assert cursor == len(values)
    return result
