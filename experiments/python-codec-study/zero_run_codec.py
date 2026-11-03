"""ZR01 research: compact-channel spatial residuals with bounded zero runs.

Header <4sBBHHII> = ZR01,version1,quant_step,width,height,tile_count,payload_len;
then raster-order <BH> mode,length tiles and CRC32(header+payload) as <I>.
Modes0..4 retain GBT1 tile syntax over compact RGB565 channel *indices*.
Mode5 (ZR) contains3 channel Rice k bytes followed by one MSB-first bitstream.
R5/G6/B5 channels use left prediction, reset to zero at EVERY tile row.
For each channel exactly tile_width*tile_height residuals are reconstructed:
  zero residual run: 0 + u8(run-1), run1..256 (may span rows);
  nonzero residual: 1 + bounded_Rice(zigzag(residual)-1,k).
Bounded Rice is exactly GBT1's15-zero-prefix/7-bit-escape syntax. Final bit pad
is zero. Compact indices reconstruct min(index*q,31/63/31); unused terminal
levels and out-of-range values are rejected. RAW fallback bounds tile payload
at2bytes/pixel. This is independent intra research, not a production protocol,
FPGA decoder, or hardware performance result.
"""
from __future__ import annotations
import math
import struct
import zlib
import numpy as np
import codec

HEADER = struct.Struct('<4sBBHHII')
MAGIC = b'ZR01'
ZERO_RUN = 5


def _indices(words,q):
    quantized=codec.quantize(words,q)
    virtual=np.zeros(quantized.shape,np.uint16)
    for shift,maximum in ((11,31),(5,63),(0,31)):
        value=((quantized>>shift)&maximum).astype(np.uint16)
        virtual|=((value+q-1)//q)<<shift
    return virtual


def _zr(tile):
    ks,codes=[],[]
    for shift,maximum in ((11,31),(5,63),(0,31)):
        channel=((tile>>shift)&maximum).astype(np.int16)
        residual=channel.copy();residual[:,1:]-=channel[:,:-1]
        mapped=np.where(residual>=0,residual*2,-residual*2-1).ravel()
        nonzero=mapped[mapped!=0]-1
        k=int(np.argmin(codec._RICE_LENGTHS[:,nonzero].sum(axis=1))) if len(nonzero) else 0
        ks.append(k);table=codec._RICE_STRINGS[k]
        i=0
        while i<len(mapped):
            if mapped[i]==0:
                end=i+1
                while end<len(mapped) and mapped[end]==0 and end-i<256: end+=1
                codes.append('0'+format(end-i-1,'08b'));i=end
            else:
                codes.append('1'+table[int(mapped[i])-1]);i+=1
    return bytes(ks)+codec._pack_bits_string(''.join(codes))


def encode(words: np.ndarray,quant_step: int=2)->bytes:
    virtual=_indices(words,quant_step)
    # Retain every existing bounded tile mode; ZR must win its actual byte cost.
    base=codec.encode(virtual,quant_step=1)
    w,h,_,tiles=codec._tiles(base)
    chunks=[]
    for x,y,tw,th,mode,data in tiles:
        candidate=_zr(virtual[y:y+th,x:x+tw])
        if len(candidate)<len(data):mode,data=ZERO_RUN,candidate
        chunks.append(codec.TILE_HEADER.pack(mode,len(data))+data)
    payload=b''.join(chunks)
    body=HEADER.pack(MAGIC,1,quant_step,w,h,len(tiles),len(payload))+payload
    return body+struct.pack('<I',zlib.crc32(body))


def _decode_zr(data,tw,th):
    if len(data)<3 or any(k>6 for k in data[:3]): raise ValueError('ZR Rice k')
    bits=codec._Bits(data[3:]);n=tw*th;out=np.zeros(n,np.uint16)
    for k,(shift,maximum) in zip(data[:3],((11,31),(5,63),(0,31))):
        i=0;previous=0
        while i<n:
            if bits.get(1)==0:
                run=bits.get(8)+1
                if i+run>n: raise ValueError('ZR run exceeds channel')
                for _ in range(run):
                    if i%tw==0: previous=0
                    out[i]|=previous<<shift;i+=1
            else:
                mapped=bits.rice(k)+1
                residual=mapped//2 if mapped%2==0 else -(mapped//2)-1
                if i%tw==0: previous=0
                value=previous+residual
                if not 0<=value<=maximum: raise ValueError('ZR channel out of range')
                out[i]|=value<<shift;previous=value;i+=1
    bits.finish()
    return out.reshape(th,tw)


def decode(packet: bytes)->np.ndarray:
    if not isinstance(packet,(bytes,bytearray)) or len(packet)<HEADER.size+4:
        raise ValueError('truncated ZR01 packet')
    magic,version,q,w,h,count,size=HEADER.unpack_from(packet)
    if magic!=MAGIC or version!=1 or not 1<=q<=32: raise ValueError('invalid ZR01 profile')
    if not 1<=w<=codec.MAX_DIM or not 1<=h<=codec.MAX_DIM: raise ValueError('invalid ZR01 dimensions')
    if count!=math.ceil(w/16)*math.ceil(h/16): raise ValueError('invalid ZR01 tile count')
    if size>2*w*h+3*count or len(packet)!=HEADER.size+size+4:
        raise ValueError('invalid ZR01 frame length/bound')
    if zlib.crc32(packet[:-4])!=struct.unpack_from('<I',packet,len(packet)-4)[0]:
        raise ValueError('ZR01 CRC mismatch')
    virtual=np.empty((h,w),np.uint16);pos=HEADER.size;end=pos+size
    for y in range(0,h,16):
        for x in range(0,w,16):
            tw,th=min(16,w-x),min(16,h-y)
            if pos+3>end: raise ValueError('missing ZR01 tile header')
            mode,length=codec.TILE_HEADER.unpack_from(packet,pos);pos+=3
            if mode>ZERO_RUN or length>tw*th*2 or pos+length>end:
                raise ValueError('invalid ZR01 tile mode/length')
            data=packet[pos:pos+length];pos+=length
            if mode==ZERO_RUN:
                tile=_decode_zr(data,tw,th)
            else:
                payload=codec.TILE_HEADER.pack(mode,length)+data
                body=codec.HEADER.pack(codec.MAGIC,1,16,1,0,tw,th,1,len(payload))+payload
                tile=codec.decode(body+struct.pack('<I',zlib.crc32(body)))
            virtual[y:y+th,x:x+tw]=tile
    if pos!=end: raise ValueError('trailing ZR01 tile bytes')
    out=np.zeros((h,w),np.uint16)
    for shift,maximum in ((11,31),(5,63),(0,31)):
        index=((virtual>>shift)&maximum).astype(np.uint16)
        if np.any(index>(maximum+q-1)//q):raise ValueError('ZR01 index out of range')
        value=np.minimum(index*q,maximum).astype(np.uint16)
        if np.any(np.minimum(((value+q//2)//q)*q,maximum)!=value):
            raise ValueError('ZR01 unused terminal level')
        out|=value<<shift
    return out
