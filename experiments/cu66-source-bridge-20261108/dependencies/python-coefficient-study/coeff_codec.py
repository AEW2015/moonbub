"""CP02/FT02 coefficient research profile, preserving FT01 pixels exactly.

CP02 <4sBBIHHII> = magic,version1,mode,blocks,blocks_w,reserved0,DCbytes,ACbytes,
then payload and little-endian CRC32(header+payload). RAW mode0 stores int16
block-raster coefficients, ACbytes0. Mode1 has separate byte-padded DC and AC.
DC: u8 k0..13 and bounded Rice codes for signed zigzag row-reset DC deltas;
prefix15 escapes to14 raw bits (positive delta4096 maps8192). AC:3 u8 k0..11
for zigzag positions1..5,6..20,21..63; tokens 00=EOB,01=16zeros,
1+u4 zero_count+bounded Rice(zigzag(nonzero)-1,k), escape12 bits. EOB may not
follow a completed block; ZRL/run may not cross63 AC positions. Bit padding0.
RAW fallback bounds complete payload to128*blocks+26 bytes. Header/CRC and
all context bytes are charged. No arithmetic, quantization or color changes.

FT02 uses FT01's RGB/Q14 helpers, but new frame/plane lengths wrapping CP02.
Neither format is a production Sunshine/ESP32/FPGA codec or hardware proof.
"""
from pathlib import Path
import math
import struct
import sys
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'python-transform-study'))
import fixed_codec as frozen

COEFF = struct.Struct('<4sBBIHHII')
FRAME = struct.Struct('<4sBBHHI')
PLANE = struct.Struct('<HHII')
MAX_BLOCKS = 65536
MAX_COEFF = 2048
PAYLOAD_OVERHEAD = COEFF.size + 4


def _check(coefficients, blocks_w):
    a = np.asarray(coefficients)
    if (a.dtype != np.int16 or a.ndim != 3 or a.shape[1:] != (8, 8)
            or not 1 <= len(a) <= MAX_BLOCKS or type(blocks_w) is not int
            or not 1 <= blocks_w <= 256 or len(a) % blocks_w
            or np.any(np.abs(a.astype(np.int32)) > MAX_COEFF)):
        raise ValueError('bounded int16 coefficient blocks and integral rows required')
    return a


def _mapped(values):
    values = np.asarray(values, np.int32)
    return np.where(values >= 0, values*2, -values*2-1)


def _rice(value, k, escape):
    quotient = value >> k
    if quotient >= 15:
        if value >= 1 << escape:
            raise ValueError('Rice value beyond escape')
        return '0'*15+format(value, f'0{escape}b')
    return '0'*quotient+'1'+(format(value & ((1 << k)-1), f'0{k}b') if k else '')


def _best_k(values, maximum, escape):
    values = np.asarray(values, np.int32)
    if not len(values):
        return 0
    costs = [np.where((values >> k) < 15, (values >> k)+1+k, 15+escape).sum()
             for k in range(maximum+1)]
    return int(np.argmin(costs))


def _pack(bits):
    n = (len(bits)+7)//8
    return (int(bits, 2) << (n*8-len(bits))).to_bytes(n, 'big') if bits else b''


def _band(position):
    return 0 if position <= 5 else (1 if position <= 20 else 2)


def encode_coefficients(coefficients, blocks_w):
    a = _check(coefficients, blocks_w)
    zig = a.reshape(-1, 64)[:, frozen.ZIGZAG].astype(np.int32)
    dc = zig[:, 0].copy()
    delta = dc.copy()
    for i in range(len(dc)):
        if i % blocks_w:
            delta[i] -= dc[i-1]
    mapped_dc = _mapped(delta)
    kd = _best_k(mapped_dc, 13, 14)
    dc_data = bytes([kd])+_pack(''.join(_rice(int(v), kd, 14) for v in mapped_dc))
    samples = [[], [], []]
    for position in range(1, 64):
        nonzero = zig[:, position][zig[:, position] != 0]
        samples[_band(position)].extend((_mapped(nonzero)-1).tolist())
    ks = [_best_k(v, 11, 12) for v in samples]
    bits = []
    for block in zig:
        position = 1
        while position < 64:
            found = np.flatnonzero(block[position:] != 0)
            if not len(found):
                bits.append('00')
                break
            target = position+int(found[0])
            while target-position >= 16:
                bits.append('01')
                position += 16
            value = int(block[target])
            mapped = 2*value if value >= 0 else -2*value-1
            bits.append('1'+format(target-position, '04b')+_rice(mapped-1, ks[_band(target)], 12))
            position = target+1
    ac_data = bytes(ks)+_pack(''.join(bits))
    raw = a.astype('<i2').tobytes()
    mode = 1
    if len(dc_data)+len(ac_data) >= len(raw):
        mode, dc_data, ac_data = 0, raw, b''
    body = COEFF.pack(b'CP02', 1, mode, len(a), blocks_w, 0, len(dc_data), len(ac_data))+dc_data+ac_data
    return body+struct.pack('<I', zlib.crc32(body))


class _Bits:
    def __init__(self, data):
        self.data, self.position = data, 0

    def get(self, count):
        if count < 0 or self.position+count > len(self.data)*8:
            raise ValueError('truncated coefficient bits')
        value = 0
        for _ in range(count):
            value = (value << 1) | ((self.data[self.position//8] >> (7-self.position % 8)) & 1)
            self.position += 1
        return value

    def rice(self, k, escape):
        quotient = 0
        while quotient < 15:
            if self.get(1):
                return (quotient << k) | self.get(k)
            quotient += 1
        value = self.get(escape)
        if value >> k < 15:
            raise ValueError('noncanonical coefficient escape')
        return value

    def finish(self):
        left = len(self.data)*8-self.position
        if left >= 8 or self.get(left):
            raise ValueError('extra/nonzero coefficient padding')


def _unmap(value):
    return value//2 if value % 2 == 0 else -(value//2)-1


def decode_coefficients(packet, blocks, blocks_w):
    if (type(blocks) is not int or not 1 <= blocks <= MAX_BLOCKS
            or type(blocks_w) is not int or not 1 <= blocks_w <= 256 or blocks % blocks_w):
        raise ValueError('invalid expected coefficient geometry')
    if (not isinstance(packet, (bytes, bytearray)) or not PAYLOAD_OVERHEAD <= len(packet) <= 128*blocks+PAYLOAD_OVERHEAD):
        raise ValueError('coefficient payload bound')
    magic, version, mode, count, width, reserved, ndc, nac = COEFF.unpack_from(packet)
    if ((magic, version, count, width, reserved) != (b'CP02', 1, blocks, blocks_w, 0)
            or mode not in (0, 1) or len(packet) != PAYLOAD_OVERHEAD+ndc+nac):
        raise ValueError('coefficient header/length')
    if zlib.crc32(packet[:-4]) != struct.unpack_from('<I', packet, len(packet)-4)[0]:
        raise ValueError('coefficient CRC')
    dc_data = packet[COEFF.size:COEFF.size+ndc]
    ac_data = packet[COEFF.size+ndc:-4]
    if mode == 0:
        if ndc != blocks*128 or nac:
            raise ValueError('RAW coefficient lengths')
        out = np.frombuffer(dc_data, '<i2').copy().reshape(blocks, 8, 8)
        if np.any(np.abs(out.astype(np.int32)) > MAX_COEFF):
            raise ValueError('RAW coefficient range')
        return out
    if not dc_data or dc_data[0] > 13 or len(ac_data) < 3 or any(k > 11 for k in ac_data[:3]):
        raise ValueError('coefficient Rice parameters')
    dcbits, acbits = _Bits(dc_data[1:]), _Bits(ac_data[3:])
    zig = np.zeros((blocks, 64), np.int16)
    previous = 0
    for i in range(blocks):
        if i % blocks_w == 0:
            previous = 0
        difference = _unmap(dcbits.rice(dc_data[0], 14))
        value = previous+difference
        if not -MAX_COEFF <= value <= MAX_COEFF:
            raise ValueError('reconstructed DC range')
        zig[i, 0] = previous = value
        position = 1
        while position < 64:
            if acbits.get(1) == 0:
                if acbits.get(1) == 0:
                    break
                if position+16 > 64:
                    raise ValueError('AC ZRL overrun')
                position += 16
            else:
                target = position+acbits.get(4)
                if target >= 64:
                    raise ValueError('AC run overrun')
                mapped = acbits.rice(ac_data[_band(target)], 12)+1
                value = _unmap(mapped)
                if value == 0 or not -MAX_COEFF <= value <= MAX_COEFF:
                    raise ValueError('AC coefficient range')
                zig[i, target] = value
                position = target+1
    dcbits.finish()
    acbits.finish()
    out = np.empty((blocks, 64), np.int16)
    out[:, frozen.ZIGZAG] = zig
    return out.reshape(blocks, 8, 8)


def encode(rgb, quant_scale=16):
    a = frozen._check_rgb(rgb)
    coefficients = frozen.quantized_coefficients(a, quant_scale)
    h, w = a.shape[:2]
    chunks = []
    for i, c in enumerate(coefficients):
        pw, ph = (w, h) if i == 0 else (w//2, h//2)
        data = encode_coefficients(c, math.ceil(pw/8))
        chunks.append(PLANE.pack(pw, ph, len(c), len(data))+data)
    payload = b''.join(chunks)
    body = FRAME.pack(b'FT02', 1, quant_scale, w, h, len(payload))+payload
    return body+struct.pack('<I', zlib.crc32(body))


def decode(packet):
    if not isinstance(packet, (bytes, bytearray)) or len(packet) < FRAME.size+4+3*PLANE.size:
        raise ValueError('truncated FT02')
    magic, version, scale, w, h, size = FRAME.unpack_from(packet)
    if magic != b'FT02' or version != 1 or not 1 <= scale <= 128:
        raise ValueError('FT02 profile')
    if (not 2 <= w <= frozen.MAX_DIM or not 2 <= h <= frozen.MAX_DIM
            or w % 2 or h % 2 or w*h > frozen.MAX_PIXELS):
        raise ValueError('FT02 dimensions')
    bound = sum(math.ceil((w if i == 0 else w//2)/8)*math.ceil((h if i == 0 else h//2)/8)*128+PAYLOAD_OVERHEAD+PLANE.size for i in range(3))
    if len(packet) != FRAME.size+4+size or size > bound:
        raise ValueError('FT02 payload bound')
    if zlib.crc32(packet[:-4]) != struct.unpack_from('<I', packet, len(packet)-4)[0]:
        raise ValueError('FT02 CRC')
    pos, end, planes = FRAME.size, FRAME.size+size, []
    for i in range(3):
        pw, ph = (w, h) if i == 0 else (w//2, h//2)
        expected = math.ceil(pw/8)*math.ceil(ph/8)
        if pos+PLANE.size > end:
            raise ValueError('FT02 plane missing')
        sw, sh, blocks, length = PLANE.unpack_from(packet, pos)
        pos += PLANE.size
        if (sw, sh, blocks) != (pw, ph, expected) or pos+length > end:
            raise ValueError('FT02 plane geometry/length')
        c = decode_coefficients(packet[pos:pos+length], blocks, math.ceil(pw/8))
        planes.append(frozen._reconstruct_plane(c, pw, ph, scale, i != 0))
        pos += length
    if pos != end:
        raise ValueError('FT02 trailing plane data')
    return frozen.planes_to_rgb(planes)
