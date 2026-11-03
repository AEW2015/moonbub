"""GBT1 bounded intra RGB565 tile-codec *Python research model*.

No RTL, hardware throughput, or temporal-reference protocol is implied.
Wire words are little endian; tiles are 16x16 raster order, clipped at edges.
Header <4sBBBBHHII> = magic,version,tile,quant_step,reserved,width,height,
  tile_count,payload_bytes; CRC32(header+payload) is appended as <I>.
Tile <BH> = mode,payload_bytes, followed by RAW/FILL/RLE/PALETTE/DPCM.
RLE pairs <HH> = nonzero count,value. PALETTE = u8 count, sorted u16 words,
  packed MSB-first indices of ceil(log2(count)) bits; zero trailing pad bits.
DPCM = three u8 Rice k values, then channel-planar MSB-first Rice codes.
  R5/G6/B5 left predictors reset to 0 at EVERY tile row. Signed residual maps
  x>=0 -> 2*x, x<0 -> -2*x-1. q<15 uses q zeros,one,k remainder bits;
  q>=15 uses 15 zeros then seven raw mapped-residual bits (no terminator).
  Final pad bits are zero. Decoder reconstructs channels, checking ranges.
Quantization happens before coding: (channel + step//2)//step*step, saturated
  to 31/63/31. This is a lossy prequantizer, not closed-loop temporal DPCM.
"""
from __future__ import annotations
import math
import struct
import zlib
from collections import Counter
import numpy as np

MAGIC = b'GBT1'
HEADER = struct.Struct('<4sBBBBHHII')
TILE_HEADER = struct.Struct('<BH')
RAW, FILL, RLE, PALETTE, DPCM = range(5)
MODE_NAMES = ('raw', 'fill', 'rle', 'palette', 'dpcm')
MAX_DIM = 2048
PREFIX_LIMIT = 15
_RICE_STRINGS = [[('0'*(u >> k)+'1'+(format(u & ((1<<k)-1), f'0{k}b') if k else ''))
                  if u >> k < PREFIX_LIMIT else '0'*PREFIX_LIMIT+format(u,'07b')
                  for u in range(127)] for k in range(7)]
_RICE_LENGTHS = np.array([[len(s) for s in row] for row in _RICE_STRINGS])


def _input(a):
    a = np.asarray(a)
    if a.dtype != np.uint16 or a.ndim != 2 or not all(1 <= x <= MAX_DIM for x in a.shape):
        raise ValueError('expected HxW uint16 RGB565, dimensions 1..2048')
    return a


def quantize(rgb565: np.ndarray, quant_step: int = 1) -> np.ndarray:
    a = _input(rgb565)
    if not isinstance(quant_step, int) or not 1 <= quant_step <= 32:
        raise ValueError('quant_step must be integer 1..32')
    q = quant_step
    r = np.minimum((((a >> 11).astype(np.int32)+q//2)//q)*q, 31)
    g = np.minimum(((((a >> 5)&63).astype(np.int32)+q//2)//q)*q, 63)
    b = np.minimum((((a&31).astype(np.int32)+q//2)//q)*q, 31)
    return ((r << 11)|(g << 5)|b).astype(np.uint16)


def _pack_bits_string(s):
    n = (len(s)+7)//8
    return (int(s,2) << (n*8-len(s))).to_bytes(n,'big') if s else b''


def _dpcm(tile):
    ks, codes = [], []
    for shift, mask in ((11,31),(5,63),(0,31)):
        channel = ((tile >> shift)&mask).astype(np.int16)
        residual = channel.copy()
        residual[:,1:] -= channel[:,:-1]
        mapped = np.where(residual >= 0, residual*2, -residual*2-1).ravel()
        k = int(np.argmin(_RICE_LENGTHS[:,mapped].sum(axis=1)))
        ks.append(k)
        table = _RICE_STRINGS[k]
        codes.extend(table[int(v)] for v in mapped)
    return bytes(ks)+_pack_bits_string(''.join(codes))


def _palette(flat):
    colors, inv = np.unique(flat, return_inverse=True)
    n = len(colors)
    if not 2 <= n <= 16:
        return None
    width = (n-1).bit_length()
    table = [format(v, f'0{width}b') for v in range(n)]
    return bytes([n])+colors.astype('<u2').tobytes()+_pack_bits_string(''.join(table[int(v)] for v in inv))


def encode(rgb565: np.ndarray, *, quant_step: int = 1, use_dpcm: bool = True,
           use_palette: bool = True) -> bytes:
    a = quantize(rgb565, quant_step)
    h,w = a.shape
    chunks = []
    for y in range(0,h,16):
        for x in range(0,w,16):
            tile = a[y:y+16,x:x+16]
            flat = tile.ravel()
            best = (RAW, flat.astype('<u2').tobytes())
            if np.all(flat == flat[0]):
                best = (FILL, struct.pack('<H',int(flat[0])))
            else:
                starts = np.r_[0,np.flatnonzero(flat[1:] != flat[:-1])+1]
                ends = np.r_[starts[1:],len(flat)]
                runs = np.column_stack((ends-starts,flat[starts])).astype('<u2').tobytes()
                if len(runs) < len(best[1]): best = (RLE,runs)
                if use_palette:
                    p = _palette(flat)
                    if p is not None and len(p) < len(best[1]): best = (PALETTE,p)
                if use_dpcm:
                    d = _dpcm(tile)
                    if len(d) < len(best[1]): best = (DPCM,d)
            chunks.append(TILE_HEADER.pack(best[0],len(best[1]))+best[1])
    payload = b''.join(chunks)
    header = HEADER.pack(MAGIC,1,16,quant_step,0,w,h,len(chunks),len(payload))
    body = header+payload
    return body+struct.pack('<I',zlib.crc32(body))


class _Bits:
    def __init__(self,data): self.data,self.bit = data,0
    def get(self,n):
        if self.bit+n > len(self.data)*8: raise ValueError('truncated bits')
        value = 0
        for _ in range(n):
            value = (value<<1)|((self.data[self.bit//8] >> (7-self.bit%8))&1)
            self.bit += 1
        return value
    def rice(self,k):
        q = 0
        while q < PREFIX_LIMIT:
            if self.get(1): return (q<<k)|self.get(k)
            q += 1
        value = self.get(7)
        if value >> k < PREFIX_LIMIT: raise ValueError('noncanonical Rice escape')
        return value
    def finish(self):
        remaining = len(self.data)*8-self.bit
        if remaining >= 8 or self.get(remaining): raise ValueError('extra/nonzero pad bits')


def _tiles(packet):
    if not isinstance(packet,(bytes,bytearray)) or len(packet) < HEADER.size+4:
        raise ValueError('truncated frame')
    magic,version,tile,q,reserved,w,h,count,size = HEADER.unpack_from(packet)
    if magic != MAGIC or version != 1 or tile != 16 or reserved or not 1 <= q <= 32:
        raise ValueError('invalid header/profile')
    if not 1 <= w <= MAX_DIM or not 1 <= h <= MAX_DIM:
        raise ValueError('invalid dimensions')
    if count != math.ceil(w/16)*math.ceil(h/16): raise ValueError('invalid tile count')
    if size > 2*w*h+TILE_HEADER.size*count: raise ValueError('frame expansion bound exceeded')
    if len(packet) != HEADER.size+size+4: raise ValueError('invalid frame length/trailing bytes')
    if zlib.crc32(packet[:-4]) != struct.unpack_from('<I',packet,len(packet)-4)[0]:
        raise ValueError('frame CRC mismatch')
    pos = HEADER.size
    tiles = []
    end = pos+size
    for y in range(0,h,16):
        for x in range(0,w,16):
            if pos+TILE_HEADER.size > end: raise ValueError('missing tile header')
            mode,n = TILE_HEADER.unpack_from(packet,pos)
            pos += TILE_HEADER.size
            th,tw = min(16,h-y),min(16,w-x)
            if mode > DPCM or n > th*tw*2 or pos+n > end: raise ValueError('invalid tile mode/length')
            tiles.append((x,y,tw,th,mode,packet[pos:pos+n]))
            pos += n
    if pos != end: raise ValueError('trailing tile payload')
    return w,h,q,tiles


def decode(packet: bytes) -> np.ndarray:
    w,h,q,tiles = _tiles(packet)
    out = np.empty((h,w),np.uint16)
    for x,y,tw,th,mode,data in tiles:
        n = tw*th
        if mode == RAW:
            if len(data) != 2*n: raise ValueError('RAW size')
            values = np.frombuffer(data,dtype='<u2').copy()
        elif mode == FILL:
            if len(data) != 2: raise ValueError('FILL size')
            values = np.full(n,struct.unpack('<H',data)[0],np.uint16)
        elif mode == RLE:
            if len(data)%4: raise ValueError('RLE size')
            values = np.empty(n,np.uint16)
            at = 0
            for run,value in struct.iter_unpack('<HH',data):
                if run == 0 or at+run > n: raise ValueError('RLE run')
                values[at:at+run] = value
                at += run
            if at != n: raise ValueError('short RLE')
        elif mode == PALETTE:
            if not data or not 2 <= data[0] <= 16: raise ValueError('palette count')
            count = data[0]
            if len(data) < 1+count*2: raise ValueError('palette size')
            colors = struct.unpack_from('<'+'H'*count,data,1)
            if any(a >= b for a,b in zip(colors,colors[1:])): raise ValueError('palette order')
            bits = _Bits(data[1+count*2:]); width = (count-1).bit_length()
            values = np.empty(n,np.uint16)
            for i in range(n):
                index = bits.get(width)
                if index >= count: raise ValueError('palette index')
                values[i] = colors[index]
            bits.finish()
        else:
            if len(data) < 3 or any(k > 6 for k in data[:3]): raise ValueError('DPCM Rice k')
            bits = _Bits(data[3:]); values = np.zeros(n,np.uint16)
            for k,(shift,maximum) in zip(data[:3],((11,31),(5,63),(0,31))):
                previous = 0
                for i in range(n):
                    if i%tw == 0: previous = 0
                    mapped = bits.rice(k)
                    residual = mapped//2 if mapped%2 == 0 else -(mapped//2)-1
                    value = previous+residual
                    if not 0 <= value <= maximum: raise ValueError('DPCM channel out of range')
                    values[i] |= value << shift
                    previous = value
            bits.finish()
        out[y:y+th,x:x+tw] = values.reshape(th,tw)
    return out


def stats(packet: bytes) -> dict:
    w,h,q,tiles = _tiles(packet)
    modes = Counter(MODE_NAMES[t[4]] for t in tiles)
    samples = sum(t[2]*t[3]*3 for t in tiles if t[4] == DPCM)
    return dict(width=w,height=h,quant_step=q,tiles=len(tiles),modes=dict(modes),
                bytes=len(packet),payload_bytes=len(packet)-HEADER.size-4,
                raw_bytes=w*h*2,raw_bound_bytes=w*h*2+3*len(tiles)+HEADER.size+4,
                dpcm_channel_residuals=samples,maximum_rice_unary_bits=PREFIX_LIMIT,
                reconstructed_rgb565_write_bytes=w*h*2,reference_read_bytes=0,
                timing_scope='Python reference model; no hardware cycle estimate')
