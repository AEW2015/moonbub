"""CP02 encoder optimization, requiring byte-for-byte compatibility.

Python token-list variant; same coefficients, Rice selection, DC reset, AC syntax,
RAW decision and CRC. It batches sparse AC discovery and skips zero blocks
without repeatedly scanning each remaining block. The frozen decoder is used
unchanged; no wire capability or hardware-speed claim is introduced.
"""
from pathlib import Path
import sys
import zlib
import struct

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'python-coefficient-study'))
import coeff_codec as frozen


def encode_coefficients(coefficients, blocks_w):
    a = frozen._check(coefficients, blocks_w)
    zig = a.reshape(-1, 64)[:, frozen.frozen.ZIGZAG].astype(np.int32)
    dc = zig[:, 0]
    delta = dc.copy()
    delta[1:] -= dc[:-1]
    delta[::blocks_w] = dc[::blocks_w]
    mapped_dc = frozen._mapped(delta)
    kd = frozen._best_k(mapped_dc, 13, 14)
    table_dc = {int(v): frozen._rice(int(v), kd, 14) for v in np.unique(mapped_dc)}
    dc_data = bytes([kd])+frozen._pack(''.join(table_dc[v] for v in mapped_dc.tolist()))

    block_indices, ac_indices = np.nonzero(zig[:, 1:])
    positions = ac_indices+1
    values = zig[block_indices, positions]
    mapped = frozen._mapped(values)-1
    bands = np.where(positions <= 5, 0, np.where(positions <= 20, 1, 2))
    ks = [frozen._best_k(mapped[bands == band], 11, 12) for band in range(3)]
    tables = [{int(v): frozen._rice(int(v), ks[band], 12)
               for v in np.unique(mapped[bands == band])} for band in range(3)]
    positions_list = positions.tolist()
    mapped_list = mapped.tolist()
    bands_list = bands.tolist()
    blocks_list = block_indices.tolist()
    prefixes = tuple('1'+format(run, '04b') for run in range(16))
    zero_runs = ('', '01', '0101', '010101')
    tokens = []
    previous_block_end = 0
    starts = np.r_[0, np.flatnonzero(block_indices[1:] != block_indices[:-1])+1]
    ends = np.r_[starts[1:], len(block_indices)]
    # np.r_[0] on an empty sequence is not a block; handle the all-zero case.
    if len(block_indices):
        for start, end in zip(starts.tolist(), ends.tolist()):
            block = blocks_list[start]
            if block > previous_block_end:
                tokens.append('00'*(block-previous_block_end))
            position = 1
            for index in range(start, end):
                target = positions_list[index]
                run = target-position
                if run >= 16:
                    zrl = run//16
                    tokens.append(zero_runs[zrl])
                    position += zrl*16
                tokens.append(prefixes[target-position]+tables[bands_list[index]][mapped_list[index]])
                position = target+1
            if position < 64:
                tokens.append('00')
            previous_block_end = block+1
    if previous_block_end < len(a):
        tokens.append('00'*(len(a)-previous_block_end))
    ac_data = bytes(ks)+frozen._pack(''.join(tokens))
    raw = a.astype('<i2').tobytes()
    mode = 1
    if len(dc_data)+len(ac_data) >= len(raw):
        mode, dc_data, ac_data = 0, raw, b''
    body = frozen.COEFF.pack(b'CP02', 1, mode, len(a), blocks_w, 0, len(dc_data), len(ac_data))+dc_data+ac_data
    return body+struct.pack('<I', zlib.crc32(body))


def encode(rgb, quant_scale=16):
    ft = frozen.frozen
    a = ft._check_rgb(rgb)
    coeffs = ft.quantized_coefficients(a, quant_scale)
    h, w = a.shape[:2]
    chunks = []
    for i, coeff in enumerate(coeffs):
        pw, ph = (w, h) if i == 0 else (w//2, h//2)
        payload = encode_coefficients(coeff, (pw+7)//8)
        chunks.append(frozen.PLANE.pack(pw, ph, len(coeff), len(payload))+payload)
    payload = b''.join(chunks)
    body = frozen.FRAME.pack(b'FT02', 1, quant_scale, w, h, len(payload))+payload
    return body+struct.pack('<I', zlib.crc32(body))
