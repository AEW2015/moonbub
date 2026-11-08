"""FT01 fixed-Q14 intra transform Python reference; no FPGA speed/fit claim.

Arithmetic/color helpers are adapted from local GBD1 src/codec.py SHA256
4fc49e333f2629ca54de600ee43297ff5aadf1bb7bdf2c21735587aa9748a3c4.
This self-contained NumPy model needs no SciPy or native entropy library.
It differs from GBD1: fixed-point forward DCT, intra-only, bounded plane-wide
Rice/zero-run coding and a distinct wire format; no compatibility is implied.

RGB->YUV is integer full-range BT.601 approximation. Chroma is 2x2 box averaged
with +2 rounding (support center .5,.5), then assigned to even output pixel
coordinates by the upsampling convention below. This explicit phase choice
is not a claim of standard JPEG chroma siting. 8x8 blocks edge-pad each
plane, then subtract128. Forward Q14 DCT rounds after each MAC pass by
(x+8192)>>14, i.e. ties toward +infinity. Coefficient quantization uses
sign(x)*floor((abs(x)+q//2)/q), i.e. nearest ties away from zero for even q.
Inverse uses two Q14 MAC passes with the same +8192 rounding, adds128 and
clips0..255. Chroma display upsampling is the explicitly defined bilinear
co-sited interpolation below, followed by integer YUV->RGB and clipping.

Frame <4sBBHHI> = FT01,version1,quant_scale1..128,width,height,payload_len;
3planes each <HHIIBI> = plane_width,height,blocks,coeff_count,mode,length.
Mode0: little-endian signed16 coefficients in block-raster/zigzag order.
Mode1: u8 Rice k0..11 then MSB-first tokens over the same sequence:
  0+u8(run-1) for1..256 zeros; 1+Rice(zigzag_signed(value)-1,k) fornonzero.
Rice q<15: qzeros,1,k remainder; q>=15:15zeros,12-bit raw value, no terminator.
Final bits pad zero; full frame CRC32(header+payload) appended little-endian.
No coefficient predictor or temporal state; runs may cross block boundaries.
"""
from __future__ import annotations

import math
import struct
import zlib

import numpy as np

MAGIC = b'FT01'
HEADER = struct.Struct('<4sBBHHI')
PLANE = struct.Struct('<HHIIBI')
MAX_PIXELS = 720*480
MAX_DIM = 2048
MAX_COEFF = 2048
SOURCE_REFERENCE_SHA256 = '4fc49e333f2629ca54de600ee43297ff5aadf1bb7bdf2c21735587aa9748a3c4'
Q14 = np.array([
    [5793,5793,5793,5793,5793,5793,5793,5793],
    [8035,6811,4551,1598,-1598,-4551,-6811,-8035],
    [7568,3135,-3135,-7568,-7568,-3135,3135,7568],
    [6811,-1598,-8035,-4551,4551,8035,1598,-6811],
    [5793,-5793,-5793,5793,5793,-5793,-5793,5793],
    [4551,-8035,1598,6811,-6811,-1598,8035,-4551],
    [3135,-7568,7568,-3135,-3135,7568,-7568,3135],
    [1598,-4551,6811,-8035,8035,-6811,4551,-1598]],np.int64)
QY = np.array([
    [16,11,10,16,24,40,51,61],[12,12,14,19,26,58,60,55],
    [14,13,16,24,40,57,69,56],[14,17,22,29,51,87,80,62],
    [18,22,37,56,68,109,103,77],[24,35,55,64,81,104,113,92],
    [49,64,78,87,103,121,120,101],[72,92,95,98,112,100,103,99]],np.int64)
QC = np.array([
    [17,18,24,47,99,99,99,99],[18,21,26,66,99,99,99,99],
    [24,26,56,99,99,99,99,99],[47,66,99,99,99,99,99,99],
    [99]*8,[99]*8,[99]*8,[99]*8],np.int64)
ZIGZAG = np.array(sorted(range(64), key=lambda n:
    (n//8+n%8, n//8 if (n//8+n%8)%2 else -(n//8))))


def qtable(scale, chroma=False):
    if type(scale) is not int or not 1 <= scale <= 128:
        raise ValueError('quant_scale must be integer1..128')
    return np.clip(((QC if chroma else QY)*scale+8)//16,1,255)


def round_quantize(values, table):
    """Nearest integer quotient, ties away from zero; q positive integer."""
    values = np.asarray(values,dtype=np.int64)
    return np.sign(values)*((np.abs(values)+table//2)//table)


def forward(blocks):
    a = np.asarray(blocks,dtype=np.int64)
    return ((((Q14@a+8192)>>14)@Q14.T)+8192)>>14


def inverse(coefficients):
    a = np.asarray(coefficients,dtype=np.int64)
    return (Q14.T@((a@Q14+8192)>>14)+8192)>>14


def _check_rgb(rgb):
    a = np.asarray(rgb)
    if (a.dtype != np.uint8 or a.ndim != 3 or a.shape[2] != 3
            or not 2 <= a.shape[0] <= MAX_DIM or not 2 <= a.shape[1] <= MAX_DIM
            or a.shape[0]%2 or a.shape[1]%2 or a.shape[0]*a.shape[1] > MAX_PIXELS):
        raise ValueError('expected bounded even-size HxWx3 uint8 RGB')
    return a


def rgb_to_planes(rgb):
    a = _check_rgb(rgb).astype(np.int32)
    r,g,b = a[...,0],a[...,1],a[...,2]
    y = np.clip((77*r+150*g+29*b+128)>>8,0,255)
    cb = np.clip(((-43*r-85*g+128*b+128)>>8)+128,0,255)
    cr = np.clip(((128*r-107*g-21*b+128)>>8)+128,0,255)
    h,w = y.shape
    def down(p):
        return ((p.reshape(h//2,2,w//2,2).sum(axis=(1,3))+2)//4).astype(np.int16)
    return [y.astype(np.int16),down(cb),down(cr)]


def planes_to_rgb(planes):
    y = planes[0].astype(np.int32)
    def up(p):
        p = p.astype(np.int32)
        right = np.concatenate((p[:,1:],p[:,-1:]),axis=1)
        horizontal = np.empty((p.shape[0],p.shape[1]*2),np.int32)
        horizontal[:,::2],horizontal[:,1::2] = p,(p+right+1)//2
        below = np.concatenate((horizontal[1:],horizontal[-1:]),axis=0)
        full = np.empty((p.shape[0]*2,p.shape[1]*2),np.int32)
        full[::2],full[1::2] = horizontal,(horizontal+below+1)//2
        return full-128
    cb,cr = up(planes[1]),up(planes[2])
    r = y+((359*cr+128)>>8)
    g = y-((88*cb+183*cr+128)>>8)
    b = y+((454*cb+128)>>8)
    return np.clip(np.stack((r,g,b),axis=-1),0,255).astype(np.uint8)


def _blocks(plane):
    h,w = plane.shape
    padded = np.pad(plane,((0,(-h)%8),(0,(-w)%8)),mode='edge').astype(np.int64)-128
    ph,pw = padded.shape
    return padded.reshape(ph//8,8,pw//8,8).transpose(0,2,1,3).reshape(-1,8,8)


def _reconstruct_plane(coefficients, width, height, scale, chroma):
    samples = np.clip(inverse(coefficients.astype(np.int64)*qtable(scale,chroma))+128,0,255)
    ph,pw = math.ceil(height/8)*8,math.ceil(width/8)*8
    return samples.reshape(ph//8,pw//8,8,8).transpose(0,2,1,3).reshape(ph,pw)[:height,:width].astype(np.int16)


def quantized_coefficients(rgb, quant_scale=16):
    """Host-side coefficients; exact decoder reconstruction defines the golden."""
    planes = rgb_to_planes(rgb)
    result = []
    for i,p in enumerate(planes):
        coeff = round_quantize(forward(_blocks(p)),qtable(quant_scale,i != 0))
        if np.any(np.abs(coeff) > MAX_COEFF):
            raise ValueError('transform coefficient outside wire bound')
        result.append(coeff.astype(np.int16))
    return result


def reconstruct(rgb, quant_scale=16):
    """Independent of packet parsing: return RGB golden for this lossy profile."""
    a = _check_rgb(rgb)
    h,w = a.shape[:2]
    coefficients = quantized_coefficients(a,quant_scale)
    return planes_to_rgb([_reconstruct_plane(c,w if i==0 else w//2,h if i==0 else h//2,quant_scale,i!=0)
                          for i,c in enumerate(coefficients)])


def _pack_bits(s):
    size = (len(s)+7)//8
    return (int(s,2) << (size*8-len(s))).to_bytes(size,'big') if s else b''


def _rice_string(value,k):
    quotient = value >> k
    if quotient >= 15:
        return '0'*15+format(value,'012b')
    return '0'*quotient+'1'+(format(value&((1<<k)-1),f'0{k}b') if k else '')


def _entropy(values):
    mapped = np.where(values >= 0,values*2,-values*2-1)
    nonzero = mapped[mapped != 0]-1
    if len(nonzero):
        costs = [np.where((nonzero>>k)<15,(nonzero>>k)+1+k,27).sum() for k in range(12)]
        k = int(np.argmin(costs))
    else:
        k = 0
    codes = []
    i = 0
    while i < len(mapped):
        if mapped[i] == 0:
            end = i+1
            while end < len(mapped) and mapped[end] == 0 and end-i < 256:
                end += 1
            codes.append('0'+format(end-i-1,'08b'))
            i = end
        else:
            codes.append('1'+_rice_string(int(mapped[i])-1,k))
            i += 1
    return bytes([k])+_pack_bits(''.join(codes))


def encode(rgb, quant_scale=16):
    a = _check_rgb(rgb)
    qtable(quant_scale)
    h,w = a.shape[:2]
    coefficients = quantized_coefficients(a,quant_scale)
    chunks = []
    for i,c in enumerate(coefficients):
        pw,ph = (w,h) if i==0 else (w//2,h//2)
        values = c.reshape(-1,64)[:,ZIGZAG].reshape(-1).astype(np.int32)
        raw = values.astype('<i2').tobytes()
        coded = _entropy(values)
        mode,data = (1,coded) if len(coded) < len(raw) else (0,raw)
        chunks.append(PLANE.pack(pw,ph,len(c),len(values),mode,len(data))+data)
    payload = b''.join(chunks)
    body = HEADER.pack(MAGIC,1,quant_scale,w,h,len(payload))+payload
    return body+struct.pack('<I',zlib.crc32(body))


class _Bits:
    def __init__(self,data):
        self.data,self.bit = data,0
    def get(self,n):
        if n < 0 or self.bit+n > len(self.data)*8:
            raise ValueError('truncated transform bits')
        value = 0
        for _ in range(n):
            value = value*2+((self.data[self.bit//8]>>(7-self.bit%8))&1)
            self.bit += 1
        return value
    def rice(self,k):
        quotient = 0
        while quotient < 15:
            if self.get(1):
                return (quotient<<k)|self.get(k)
            quotient += 1
        value = self.get(12)
        if value >> k < 15:
            raise ValueError('noncanonical transform Rice escape')
        return value
    def finish(self):
        remaining = len(self.data)*8-self.bit
        if remaining >= 8 or self.get(remaining):
            raise ValueError('extra/nonzero transform padding')


def _decode_entropy(data,count):
    if not data or data[0] > 11:
        raise ValueError('invalid transform Rice k')
    bits = _Bits(data[1:])
    out = np.zeros(count,np.int16)
    i = 0
    while i < count:
        if bits.get(1) == 0:
            run = bits.get(8)+1
            if i+run > count:
                raise ValueError('transform run exceeds coefficient count')
            i += run
        else:
            mapped = bits.rice(data[0])+1
            value = mapped//2 if mapped%2==0 else -(mapped//2)-1
            if not -MAX_COEFF <= value <= MAX_COEFF:
                raise ValueError('transform coefficient out of range')
            out[i] = value
            i += 1
    bits.finish()
    return out


def _parse(packet):
    if not isinstance(packet,(bytes,bytearray)) or len(packet) < HEADER.size+3*PLANE.size+4:
        raise ValueError('truncated FT01 frame')
    magic,version,scale,w,h,size = HEADER.unpack_from(packet)
    if magic != MAGIC or version != 1 or not 1 <= scale <= 128:
        raise ValueError('invalid FT01 profile')
    if (not 2 <= w <= MAX_DIM or not 2 <= h <= MAX_DIM or w%2 or h%2 or w*h > MAX_PIXELS):
        raise ValueError('invalid FT01 dimensions')
    if len(packet) != HEADER.size+size+4:
        raise ValueError('invalid FT01 payload length')
    if zlib.crc32(packet[:-4]) != struct.unpack_from('<I',packet,len(packet)-4)[0]:
        raise ValueError('FT01 CRC mismatch')
    pos,end,planes = HEADER.size,HEADER.size+size,[]
    for i in range(3):
        pw,ph = (w,h) if i==0 else (w//2,h//2)
        expected = math.ceil(pw/8)*math.ceil(ph/8)
        if pos+PLANE.size > end:
            raise ValueError('missing FT01 plane descriptor')
        sw,sh,blocks,count,mode,length = PLANE.unpack_from(packet,pos)
        pos += PLANE.size
        if ((sw,sh) != (pw,ph) or blocks != expected or count != expected*64
                or mode not in (0,1) or length > count*2 or pos+length > end):
            raise ValueError('invalid FT01 plane descriptor')
        data = packet[pos:pos+length]
        pos += length
        planes.append((pw,ph,blocks,count,mode,data))
    if pos != end:
        raise ValueError('trailing FT01 plane data')
    return w,h,scale,planes


def decode(packet):
    """Return uint8 RGB; parse bytes independently then apply frozen arithmetic."""
    w,h,scale,descriptors = _parse(packet)
    planes = []
    for i,(pw,ph,blocks,count,mode,data) in enumerate(descriptors):
        if mode == 0:
            if len(data) != count*2:
                raise ValueError('RAW coefficient size')
            values = np.frombuffer(data,'<i2').copy()
            if np.any(np.abs(values.astype(np.int32)) > MAX_COEFF):
                raise ValueError('RAW coefficient out of range')
        else:
            values = _decode_entropy(data,count)
        coefficients = np.empty((blocks,64),np.int16)
        coefficients[:,ZIGZAG] = values.reshape(blocks,64)
        planes.append(_reconstruct_plane(coefficients.reshape(-1,8,8),pw,ph,scale,i!=0))
    return planes_to_rgb(planes)


def stats(packet):
    w,h,scale,planes = _parse(packet)
    count = sum(p[2] for p in planes)
    return {'width':w,'height':h,'quant_scale':scale,'blocks':count,
            'bytes':len(packet),'plane_modes':[p[4] for p in planes],
            'naive_forward_macs':count*1024,'naive_inverse_macs':count*1024,
            'raw_bound_bytes':HEADER.size+4+3*PLANE.size+sum(p[3]*2 for p in planes),
            'arithmetic':'frozen integer Q14; two8-termMACpasses pertransform',
            'scope':'Python research model; no FPGA schedule/resource/throughput measurement'}
