"""RG01 independent-frame ROI quantization experiment; not installed firmware.

A 16x16 luma / 8x8 chroma macroblock map chooses scale8/16/32. Map entries
are2bit MSB-first codes0/1/2, four per byte; unused low bits must be zero.
The complete map and CP02 planes are length-bounded and covered by CRC32.
All color, DCT, inverse and rounding helpers are the frozen FT01 arithmetic.
"""
from pathlib import Path
import math
import struct
import sys
import zlib
import numpy as np

HERE=Path(__file__).resolve().parent
for directory in ('python-transform-study','python-coefficient-study','python-token-entropy-study'):
    sys.path.insert(0,str(HERE.parent/directory))
import fixed_codec as ft
import coeff_codec as cc
import token_coeff

HEADER=struct.Struct('<4sBBHHHHIIII')
MAGIC=b'RG01'
SCALES=(8,16,32)


def geometry(w,h):
    if (type(w) is not int or type(h) is not int or not 2<=w<=ft.MAX_DIM or not 2<=h<=ft.MAX_DIM
            or w%2 or h%2 or w*h>ft.MAX_PIXELS):
        raise ValueError('bounded even geometry required')
    return (w+15)//16,(h+15)//16


def check_map(scale_map,w,h):
    mw,mh=geometry(w,h)
    a=np.asarray(scale_map)
    if a.dtype!=np.uint8 or a.shape!=(mh,mw) or not np.isin(a,SCALES).all():
        raise ValueError('uint8 scale map shape/domain')
    return a


def pack_map(scale_map):
    a=np.asarray(scale_map)
    codes=np.searchsorted(SCALES,a.reshape(-1)).astype(np.uint8)
    padded=np.pad(codes,(0,(-len(codes))%4))
    return ((padded[::4]<<6)|(padded[1::4]<<4)|(padded[2::4]<<2)|padded[3::4]).tobytes()


def unpack_map(data,mw,mh):
    n=mw*mh
    if len(data)!=(n+3)//4:
        raise ValueError('map byte count')
    raw=np.frombuffer(data,np.uint8)
    codes=np.stack(((raw>>6)&3,(raw>>4)&3,(raw>>2)&3,raw&3),axis=1).reshape(-1)
    if np.any(codes[:n]>2) or np.any(codes[n:]):
        raise ValueError('map invalid code or nonzero padding')
    return np.array(SCALES,np.uint8)[codes[:n]].reshape(mh,mw)


def block_scales(scale_map,w,h,plane):
    pw,ph=(w,h) if plane==0 else (w//2,h//2)
    bh,bw=(ph+7)//8,(pw+7)//8
    yy,xx=np.mgrid[:bh,:bw]
    if plane==0:yy,xx=yy//2,xx//2
    return scale_map[yy,xx].reshape(-1)


def block_tables(scale_map,w,h,plane):
    scales=block_scales(scale_map,w,h,plane)
    tables=np.stack([ft.qtable(scale,plane!=0) for scale in SCALES])
    return tables[np.searchsorted(SCALES,scales)]


def quantized(rgb,scale_map):
    a=ft._check_rgb(rgb);h,w=a.shape[:2];scale_map=check_map(scale_map,w,h)
    planes=ft.rgb_to_planes(a);coefficients=[]
    for i,p in enumerate(planes):
        coeff=ft.round_quantize(ft.forward(ft._blocks(p)),block_tables(scale_map,w,h,i))
        if np.any(np.abs(coeff)>ft.MAX_COEFF):raise ValueError('coefficient wire range')
        coefficients.append(coeff.astype(np.int16))
    return coefficients


def reconstruct_planes(coefficients,scale_map,w,h):
    planes=[]
    for i,c in enumerate(coefficients):
        pw,ph=(w,h) if i==0 else (w//2,h//2)
        padded_w,padded_h=((pw+7)//8)*8,((ph+7)//8)*8
        samples=np.clip(ft.inverse(c.astype(np.int64)*block_tables(scale_map,w,h,i))+128,0,255)
        planes.append(samples.reshape(padded_h//8,padded_w//8,8,8).transpose(0,2,1,3)
                      .reshape(padded_h,padded_w)[:ph,:pw].astype(np.int16))
    return planes


def encode(rgb,scale_map):
    a=ft._check_rgb(rgb);h,w=a.shape[:2];scale_map=check_map(scale_map,w,h)
    coefficients=quantized(a,scale_map);payloads=[]
    for i,c in enumerate(coefficients):
        pw=w if i==0 else w//2
        payloads.append(token_coeff.encode_coefficients(c,(pw+7)//8))
    mw,mh=geometry(w,h);mapped=pack_map(scale_map)
    body=HEADER.pack(MAGIC,1,0,w,h,mw,mh,len(mapped),*(len(p) for p in payloads))+mapped+b''.join(payloads)
    return body+struct.pack('<I',zlib.crc32(body))


def parse(packet):
    if not isinstance(packet,bytes) or len(packet)<HEADER.size+4:
        raise ValueError('RG01 truncated bytes')
    magic,version,flags,w,h,mw,mh,nmap,ny,ncb,ncr=HEADER.unpack_from(packet)
    expected_mw,expected_mh=geometry(w,h)
    if (magic,version,flags,mw,mh)!=(MAGIC,1,0,expected_mw,expected_mh):
        raise ValueError('RG01 header profile')
    map_bound=(mw*mh+3)//4
    if nmap!=map_bound:raise ValueError('RG01 map length')
    lengths=(ny,ncb,ncr)
    dimensions=((w,h),(w//2,h//2),(w//2,h//2))
    for n,(pw,ph) in zip(lengths,dimensions):
        blocks=((pw+7)//8)*((ph+7)//8)
        if not cc.PAYLOAD_OVERHEAD<=n<=128*blocks+cc.PAYLOAD_OVERHEAD:
            raise ValueError('RG01 plane length bound')
    if len(packet)!=HEADER.size+nmap+sum(lengths)+4:raise ValueError('RG01 exact frame length')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('RG01 CRC')
    pos=HEADER.size;scale_map=unpack_map(packet[pos:pos+nmap],mw,mh);pos+=nmap
    coefficients=[]
    for n,(pw,ph) in zip(lengths,dimensions):
        bw,bh=(pw+7)//8,(ph+7)//8
        coefficients.append(cc.decode_coefficients(packet[pos:pos+n],bw*bh,bw));pos+=n
    return w,h,scale_map,coefficients


def decode(packet):
    w,h,scale_map,coefficients=parse(packet)
    return ft.planes_to_rgb(reconstruct_planes(coefficients,scale_map,w,h))


def info(packet):
    w,h,scale_map,_=parse(packet)
    mw,mh=geometry(w,h)
    return {'width':w,'height':h,'bytes':len(packet),'scale_map_bytes':(mw*mh+3)//4,
            'outer_header_crc_bytes':HEADER.size+4,'scale_counts':{str(s):int((scale_map==s).sum()) for s in SCALES},
            'raw_bound_bytes':HEADER.size+4+(mw*mh+3)//4+sum(128*((pw+7)//8)*((ph+7)//8)+cc.PAYLOAD_OVERHEAD
                                                              for pw,ph in ((w,h),(w//2,h//2),(w//2,h//2)))}


def declared_map(w,h,rectangles,roi_scale=8,background_scale=32):
    mw,mh=geometry(w,h)
    if roi_scale not in SCALES or background_scale not in SCALES:raise ValueError('scale choice')
    result=np.full((mh,mw),background_scale,np.uint8)
    for rect in rectangles:
        if len(rect)!=4 or any(type(v) is not int for v in rect):raise ValueError('rectangle integers')
        x,y,rw,rh=rect
        if x<0 or y<0 or rw<=0 or rh<=0 or x+rw>w or y+rh>h:raise ValueError('rectangle bounds')
        result[y//16:(y+rh+15)//16,x//16:(x+rw+15)//16]=roi_scale
    return result
