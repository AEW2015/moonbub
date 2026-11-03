"""DT01: exact-source dirty tiles plus independent FT02 tiles, one ACK credit.

Research-only syntax. No temporal prediction inside a changed tile. SKIP copies
an ACKed reconstructed tile only when the source tile exactly matches the host's
ACKed original. An unacknowledged source can never become a skip reference.
"""
from pathlib import Path
import struct
import sys
import zlib

import numpy as np

HERE=Path(__file__).resolve().parent
for directory in ('python-token-entropy-study','python-coefficient-study'):
    sys.path.insert(0,str(HERE.parent/directory))
import token_coeff as entropy
cc=entropy.frozen
ft=cc.frozen
HEADER=struct.Struct('<4sBIIIHHBBII')
LENGTH=struct.Struct('<I')
NO_REF=0xffffffff
TILE=32


def rectangles(w,h):
    return [(x,y,min(TILE,w-x),min(TILE,h-y)) for y in range(0,h,TILE) for x in range(0,w,TILE)]


def tile_bound(w,h):
    dimensions=((w,h),(w//2,h//2),(w//2,h//2))
    return cc.FRAME.size+4+3*cc.PLANE.size+sum(128*((ww+7)//8)*((hh+7)//8)+cc.PAYLOAD_OVERHEAD for ww,hh in dimensions)


def bound(w,h):
    rects=rectangles(w,h)
    return HEADER.size+4+(len(rects)+7)//8+sum(4+tile_bound(ww,hh) for _,_,ww,hh in rects)


def _identity(epoch,frame):
    if type(epoch) is not int or type(frame) is not int or not 0<=epoch<NO_REF or not 0<=frame<NO_REF:
        raise ValueError('DT01 epoch/frame')


class Encoder:
    def __init__(self,epoch=1):
        _identity(epoch,0)
        self.epoch=epoch;self.reference_id=None;self.source=None;self.rgb=None;self.pending=None;self.last=-1;self.quant_scale=None

    def prepare(self,rgb,frame,*,quant_scale=8,force_key=False):
        _identity(self.epoch,frame)
        a=ft._check_rgb(rgb);ft.qtable(quant_scale)
        if self.pending is not None or frame<=self.last:
            raise ValueError('DT01 pending credit or regressing frame')
        h,w=a.shape[:2]
        key=force_key or self.source is None or self.source.shape!=a.shape or self.quant_scale!=quant_scale
        rects=rectangles(w,h);bitmap=bytearray((len(rects)+7)//8)
        rebuilt=np.empty_like(a) if key else self.rgb.copy()
        pieces=[];changed=0
        for i,(x,y,ww,hh) in enumerate(rects):
            tile=a[y:y+hh,x:x+ww]
            if not key and np.array_equal(tile,self.source[y:y+hh,x:x+ww]):
                continue
            bitmap[i//8]|=1<<(7-i%8);changed+=1
            packet=entropy.encode(tile,quant_scale)
            pieces.append(LENGTH.pack(len(packet))+packet)
            rebuilt[y:y+hh,x:x+ww]=cc.decode(packet)
        payload=b''.join(pieces)
        header=HEADER.pack(b'DT01',1,self.epoch,frame,NO_REF if key else self.reference_id,
                           w,h,TILE,quant_scale,len(bitmap),len(payload))
        body=header+bitmap+payload
        packet=body+struct.pack('<I',zlib.crc32(body))
        assert len(packet)<=bound(w,h)
        source=a.copy();source.setflags(write=False);rebuilt.setflags(write=False)
        self.pending=(frame,source,rebuilt,quant_scale);self.last=frame
        return packet,{'key':key,'tiles':len(rects),'changed_tiles':changed,'skipped_tiles':len(rects)-changed,
                       'map_bytes':len(bitmap),'bytes':len(packet),'source_sha256_scope':'exact RGB source tile equality only'}

    def expected_rgb(self):
        if self.pending is None:raise ValueError('DT01 no pending RGB')
        return self.pending[2]

    def ack(self,frame,*,epoch):
        if type(epoch) is not int or epoch!=self.epoch or self.pending is None or type(frame) is not int or frame!=self.pending[0]:
            raise ValueError('DT01 stale/mismatched ACK')
        self.reference_id,self.source,self.rgb,self.quant_scale=self.pending;self.pending=None

    def abort(self):
        self.reference_id=None;self.source=None;self.rgb=None;self.pending=None;self.quant_scale=None


class Receiver:
    def __init__(self,epoch=1):
        _identity(epoch,0)
        self.epoch=epoch;self.reference_id=None;self.rgb=None;self.quant_scale=None

    def receive(self,packet):
        if not isinstance(packet,bytes) or len(packet)<HEADER.size+5:
            raise ValueError('DT01 truncated/type')
        magic,version,epoch,frame,ref,w,h,tile,scale,maplen,length=HEADER.unpack_from(packet)
        _identity(epoch,frame)
        if (magic!=b'DT01' or version!=1 or epoch!=self.epoch or tile!=TILE or not 1<=scale<=128
            or not 2<=w<=ft.MAX_DIM or not 2<=h<=ft.MAX_DIM or w%2 or h%2 or w*h>ft.MAX_PIXELS
            or (self.reference_id is not None and frame<=self.reference_id)):
            raise ValueError('DT01 profile/geometry/replay')
        rects=rectangles(w,h)
        if maplen!=(len(rects)+7)//8 or len(packet)!=HEADER.size+maplen+length+4 or len(packet)>bound(w,h):
            raise ValueError('DT01 lengths/bounds')
        if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:
            raise ValueError('DT01 CRC')
        bitmap=packet[HEADER.size:HEADER.size+maplen]
        if len(rects)%8 and bitmap[-1]&((1<<(8-len(rects)%8))-1):
            raise ValueError('DT01 nonzero bitmap padding')
        key=ref==NO_REF
        if not key and (ref>=frame or ref!=self.reference_id or self.rgb is None or self.rgb.shape!=(h,w,3) or self.quant_scale!=scale):
            raise ValueError('DT01 missing exact reference')
        result=np.empty((h,w,3),np.uint8) if key else self.rgb.copy()
        position=HEADER.size+maplen;changed=0;skipped_pixels=0
        for i,(x,y,ww,hh) in enumerate(rects):
            if not bitmap[i//8]&(1<<(7-i%8)):
                if key:raise ValueError('DT01 skipped independent tile')
                skipped_pixels+=ww*hh;continue
            changed+=1
            if position+4>len(packet)-4:raise ValueError('DT01 missing tile length')
            count=LENGTH.unpack_from(packet,position)[0];position+=4
            if not cc.FRAME.size+4<=count<=tile_bound(ww,hh) or position+count>len(packet)-4:
                raise ValueError('DT01 tile payload bounds')
            data=packet[position:position+count];position+=count
            fields=cc.FRAME.unpack_from(data)
            if fields[2:5]!=(scale,ww,hh):raise ValueError('DT01 tile profile geometry')
            result[y:y+hh,x:x+ww]=cc.decode(data)
        if position!=len(packet)-4:raise ValueError('DT01 trailing tiles')
        stored=result.copy();stored.setflags(write=False)
        self.rgb=stored;self.reference_id=frame;self.quant_scale=scale
        return result,{'key':key,'tiles':len(rects),'changed_tiles':changed,'skipped_tiles':len(rects)-changed,
                       'map_bytes':maplen,'bytes':len(packet),'logical_skip_rgb565_read_bytes':skipped_pixels*2,
                       'logical_rgb565_write_bytes':w*h*2,'scope':'logical copy/write payload only; physical transactions unmodeled'}
