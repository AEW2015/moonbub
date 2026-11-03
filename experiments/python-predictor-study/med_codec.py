"""MP01 Python research: compact RGB565 indices with tile-local prediction.

Header <4sBBBHHII>: MP01, version1, quant_step, predictor_id, width,height,
tile_count,payload_length; raster <BH> tiles and CRC32(header+payload).
Predictor0='above': left except first column uses above; first pixel zero.
Predictor1='med': median-edge from left/above/upper-left, top row left,
first column above, first pixel zero. Each tile resets all predictor state.
Modes0..4 are GBT1 tile modes over compact quantized indices. Mode5 contains
three Rice k bytes, then channel-planar zero/nonzero tokens: 0+u8(run-1)
for1..256 zero residuals, 1+bounded Rice(zigzag(residual)-1,k) otherwise.
Zero runs may cross rows; the selected predictor is still evaluated per pixel.
The residual syntax inherits GBT1's15-zero-prefix,7-bit escape and zero padding.
No hardware throughput, physical memory, FPGA resource or synthesis claim.
"""
from __future__ import annotations

from collections import Counter
import math
from pathlib import Path
import struct
import sys
import zlib

import numpy as np

CODEC_STUDY = Path(__file__).resolve().parent.parent / 'python-codec-study'
if str(CODEC_STUDY) not in sys.path:
    sys.path.insert(0, str(CODEC_STUDY))
import codec

HEADER = struct.Struct('<4sBBBHHII')
MAGIC = b'MP01'
PREDICTORS = {'above': 0, 'med': 1}
PREDICTED_ZERO_RUN = 5


def _indices(words, q):
    quantized = codec.quantize(words, q)
    out = np.zeros(quantized.shape, np.uint16)
    for shift, maximum in ((11,31), (5,63), (0,31)):
        value = (quantized >> shift) & maximum
        out |= ((value + q - 1) // q) << shift
    return out


def _predict_all(channel, predictor):
    """Encoder-only vectorized predictor; decoder independently reconstructs."""
    result = np.zeros(channel.shape, np.int16)
    result[:, 1:] = channel[:, :-1]
    result[1:, 0] = channel[:-1, 0]
    if predictor == 1 and min(channel.shape) > 1:
        a, b, c = channel[1:, :-1], channel[:-1, 1:], channel[:-1, :-1]
        low, high = np.minimum(a,b), np.maximum(a,b)
        result[1:, 1:] = np.where(c >= high, low, np.where(c <= low, high, a+b-c))
    return result


def _predicted(tile, predictor):
    ks, codes = [], []
    for shift, maximum in ((11,31), (5,63), (0,31)):
        channel = ((tile >> shift) & maximum).astype(np.int16)
        residual = channel - _predict_all(channel, predictor)
        mapped = np.where(residual >= 0, residual*2, -residual*2-1).ravel()
        nonzero = mapped[mapped != 0] - 1
        k = int(np.argmin(codec._RICE_LENGTHS[:, nonzero].sum(axis=1))) if len(nonzero) else 0
        ks.append(k)
        table = codec._RICE_STRINGS[k]
        i = 0
        while i < len(mapped):
            if mapped[i] == 0:
                end = i + 1
                while end < len(mapped) and mapped[end] == 0 and end-i < 256:
                    end += 1
                codes.append('0' + format(end-i-1, '08b'))
                i = end
            else:
                codes.append('1' + table[int(mapped[i])-1])
                i += 1
    return bytes(ks) + codec._pack_bits_string(''.join(codes))


def encode(words: np.ndarray, quant_step: int = 2, predictor: str = 'med') -> bytes:
    """Encode exactly codec.quantize(words,q), retaining bounded RAW fallback."""
    if predictor not in PREDICTORS:
        raise ValueError('predictor must be above or med')
    identifier = PREDICTORS[predictor]
    virtual = _indices(words, quant_step)
    base = codec.encode(virtual, quant_step=1)
    w,h,_,tiles = codec._tiles(base)
    chunks = []
    for x,y,tw,th,mode,data in tiles:
        candidate = _predicted(virtual[y:y+th, x:x+tw], identifier)
        if len(candidate) < len(data):
            mode, data = PREDICTED_ZERO_RUN, candidate
        chunks.append(codec.TILE_HEADER.pack(mode, len(data)) + data)
    payload = b''.join(chunks)
    body = HEADER.pack(MAGIC,1,quant_step,identifier,w,h,len(tiles),len(payload)) + payload
    return body + struct.pack('<I', zlib.crc32(body))


def _parse(packet):
    if not isinstance(packet, (bytes,bytearray)) or len(packet) < HEADER.size+4:
        raise ValueError('truncated MP01 frame')
    magic,version,q,predictor,w,h,count,size = HEADER.unpack_from(packet)
    if magic != MAGIC or version != 1 or not 1 <= q <= 32 or predictor not in (0,1):
        raise ValueError('invalid MP01 profile')
    if not 1 <= w <= codec.MAX_DIM or not 1 <= h <= codec.MAX_DIM:
        raise ValueError('invalid MP01 dimensions')
    if count != math.ceil(w/16)*math.ceil(h/16):
        raise ValueError('invalid MP01 tile count')
    if size > 2*w*h+3*count or len(packet) != HEADER.size+size+4:
        raise ValueError('invalid MP01 length/bound')
    if zlib.crc32(packet[:-4]) != struct.unpack_from('<I', packet, len(packet)-4)[0]:
        raise ValueError('MP01 CRC mismatch')
    pos, end, tiles = HEADER.size, HEADER.size+size, []
    for y in range(0,h,16):
        for x in range(0,w,16):
            tw,th = min(16,w-x), min(16,h-y)
            if pos+3 > end:
                raise ValueError('missing MP01 tile header')
            mode,length = codec.TILE_HEADER.unpack_from(packet,pos)
            pos += 3
            if mode > PREDICTED_ZERO_RUN or length > tw*th*2 or pos+length > end:
                raise ValueError('invalid MP01 tile mode/length')
            tiles.append((x,y,tw,th,mode,packet[pos:pos+length]))
            pos += length
    if pos != end:
        raise ValueError('trailing MP01 tile bytes')
    return w,h,q,predictor,tiles


def _decode_predicted(data, tw, th, predictor):
    if len(data) < 3 or any(k > 6 for k in data[:3]):
        raise ValueError('invalid predictor Rice k')
    bits = codec._Bits(data[3:])
    out = np.zeros((th,tw), np.uint16)
    for k,(shift,maximum) in zip(data[:3], ((11,31),(5,63),(0,31))):
        channel = np.zeros((th,tw), np.int16)
        i = 0
        while i < tw*th:
            zero = bits.get(1) == 0
            run = bits.get(8)+1 if zero else 1
            if i+run > tw*th:
                raise ValueError('predictor run exceeds channel')
            if zero:
                residual = 0
            else:
                mapped = bits.rice(k)+1
                residual = mapped//2 if mapped%2 == 0 else -(mapped//2)-1
            for _ in range(run):
                y,x = divmod(i,tw)
                if not y:
                    pred = int(channel[y,x-1]) if x else 0
                elif not x:
                    pred = int(channel[y-1,x])
                elif predictor == 0:
                    pred = int(channel[y,x-1])
                else:
                    a,b,c = int(channel[y,x-1]),int(channel[y-1,x]),int(channel[y-1,x-1])
                    if c >= max(a,b):
                        pred = min(a,b)
                    elif c <= min(a,b):
                        pred = max(a,b)
                    else:
                        pred = a+b-c
                value = pred + residual
                if not 0 <= value <= maximum:
                    raise ValueError('predictor channel out of range')
                channel[y,x] = value
                i += 1
        out |= channel.astype(np.uint16) << shift
    bits.finish()
    return out


def decode(packet: bytes) -> np.ndarray:
    """Parse complete bytes and independently reconstruct compact indices."""
    w,h,q,predictor,tiles = _parse(packet)
    virtual = np.empty((h,w),np.uint16)
    for x,y,tw,th,mode,data in tiles:
        if mode == PREDICTED_ZERO_RUN:
            tile = _decode_predicted(data,tw,th,predictor)
        else:
            payload = codec.TILE_HEADER.pack(mode,len(data))+data
            body = codec.HEADER.pack(codec.MAGIC,1,16,1,0,tw,th,1,len(payload))+payload
            tile = codec.decode(body+struct.pack('<I',zlib.crc32(body)))
        virtual[y:y+th,x:x+tw] = tile
    out = np.zeros((h,w),np.uint16)
    for shift,maximum in ((11,31),(5,63),(0,31)):
        index = (virtual >> shift) & maximum
        if np.any(index > (maximum+q-1)//q):
            raise ValueError('MP01 index out of range')
        value = np.minimum(index*q, maximum).astype(np.uint16)
        if np.any(np.minimum(((value+q//2)//q)*q,maximum) != value):
            raise ValueError('MP01 unused terminal level')
        out |= value << shift
    return out


def stats(packet: bytes) -> dict:
    w,h,q,predictor,tiles = _parse(packet)
    modes = Counter(('predicted_zero_run' if t[4] == 5 else codec.MODE_NAMES[t[4]]) for t in tiles)
    return {'width':w,'height':h,'quant_step':q,
            'predictor':next(name for name,value in PREDICTORS.items() if value == predictor),
            'modes':dict(modes),'bytes':len(packet),
            'raw_bound_bytes':HEADER.size+4+2*w*h+3*len(tiles),
            'predicted_pixels':sum(t[2]*t[3] for t in tiles if t[4] == 5),
            'predicted_channel_samples':sum(3*t[2]*t[3] for t in tiles if t[4] == 5),
            'max_zero_run':256,'max_rice_prefix':15,
            'scope':'Python intra reference; no hardware resource/throughput measurement'}
