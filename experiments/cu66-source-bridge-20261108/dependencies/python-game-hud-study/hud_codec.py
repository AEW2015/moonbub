"""HP01/GH01: bounded lossless RGB565 display patches over GM01.

Patch output never becomes the YUV prediction anchor. This is an experimental
wrapper requiring a matching decoder, not an installed Sunshine/GF01 mode.
"""
from pathlib import Path
import hashlib
import math
import struct
import sys
import time
import zlib
import numpy as np

HERE=Path(__file__).resolve().parent
for directory in ('python-game-codec-study','python-codec-study'):
    sys.path.insert(0,str(HERE.parent/directory))
import game_codec as gm
import corpus

PATCH=struct.Struct('<4sBBHHHHHII')
FRAME=struct.Struct('<4sBBIHHI')
LENGTH=struct.Struct('<I')
MAX_PATCHES=4
MAX_COLORS=256
MODES=(1,2,4,8)


def _crc(body):return body+struct.pack('<I',zlib.crc32(body))


def _check_crc(packet):
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:
        raise ValueError('HUD CRC mismatch')


def _rect(rect,w,h):
    if (not isinstance(rect,(tuple,list)) or len(rect)!=4 or any(type(v) is not int for v in rect)):
        raise ValueError('HUD rectangle integers')
    x,y,rw,rh=rect
    if x<0 or y<0 or rw<=0 or rh<=0 or x+rw>w or y+rh>h:
        raise ValueError('HUD rectangle bounds')
    return x,y,rw,rh


def _mode(colors):
    if colors<=2:return 1
    if colors<=4:return 2
    if colors<=16:return 4
    if colors<=256:return 8
    return 0


def _pack_indices(indices,bits):
    per=8//bits;a=np.asarray(indices,np.uint8).reshape(-1)
    a=np.pad(a,(0,(-len(a))%per)).reshape(-1,per)
    shifts=np.arange(8-bits,-1,-bits,dtype=np.uint8)
    return np.bitwise_or.reduce(a<<shifts,axis=1).tobytes()


def _unpack_indices(data,pixels,bits):
    if len(data)!=(pixels*bits+7)//8:raise ValueError('HUD index length')
    shifts=np.arange(8-bits,-1,-bits,dtype=np.uint8)
    indices=((np.frombuffer(data,np.uint8)[:,None]>>shifts)&((1<<bits)-1)).reshape(-1)
    if np.any(indices[pixels:]):raise ValueError('HUD nonzero index padding')
    return indices[:pixels]


def encode_patch(rgb,rect):
    a=gm.ft._check_rgb(rgb);h,w=a.shape[:2];x,y,rw,rh=_rect(rect,w,h)
    words=corpus.rgb565(a[y:y+rh,x:x+rw]).reshape(-1)
    colors,indices=np.unique(words,return_inverse=True)
    mode=_mode(len(colors))
    if mode:
        palette=colors.astype('<u2').tobytes();count=len(colors)
        payload=_pack_indices(indices,mode)
    else:
        palette=b'';count=0;payload=words.astype('<u2').tobytes()
    body=PATCH.pack(b'HP01',1,mode,x,y,rw,rh,count,rw*rh,len(payload))+palette+payload
    return _crc(body)


def decode_patch(packet,w,h):
    gm.roi.geometry(w,h)
    if type(packet) is not bytes or len(packet)<PATCH.size+4:
        raise ValueError('HUD truncated patch/type')
    magic,version,mode,x,y,rw,rh,colors,pixels,length=PATCH.unpack_from(packet)
    _rect((x,y,rw,rh),w,h)
    if magic!=b'HP01' or version!=1 or mode not in (0,*MODES) or pixels!=rw*rh:
        raise ValueError('HUD patch profile/count')
    if len(packet)!=PATCH.size+colors*2+length+4:
        raise ValueError('HUD exact patch length')
    if len(packet)>PATCH.size+MAX_COLORS*2+2*pixels+4:
        raise ValueError('HUD patch bound')
    _check_crc(packet)
    start=PATCH.size;palette=packet[start:start+colors*2];payload=packet[start+colors*2:-4]
    if mode==0:
        if colors or length!=pixels*2:raise ValueError('HUD RAW length/palette')
        words=np.frombuffer(payload,'<u2').copy()
    else:
        if not 1<=colors<=min(MAX_COLORS,pixels) or _mode(colors)!=mode:
            raise ValueError('HUD palette count/mode')
        values=np.frombuffer(palette,'<u2')
        if len(values)>1 and np.any(values[1:]<=values[:-1]):
            raise ValueError('HUD noncanonical palette')
        indices=_unpack_indices(payload,pixels,mode)
        if np.any(indices>=colors):raise ValueError('HUD palette index range')
        if not np.array_equal(np.unique(indices),np.arange(colors)):
            raise ValueError('HUD unused palette entry')
        words=values[indices].copy()
    words=words.reshape(rh,rw);words.setflags(write=False)
    return {'rect':(x,y,rw,rh),'mode':mode,'colors':colors,'words':words,
            'bytes':len(packet),'header_crc_bytes':PATCH.size+4,
            'palette_bytes':colors*2,'payload_bytes':length}


def _disjoint(rectangles):
    for i,(x,y,w,h) in enumerate(rectangles):
        for xx,yy,ww,hh in rectangles[:i]:
            if x<xx+ww and xx<x+w and y<yy+hh and yy<y+h:
                raise ValueError('HUD overlapping patches')


def _base_bound(w,h):
    mw,mh=gm.roi.geometry(w,h)
    return gm.HEADER.size+4+(mw*mh+3)//4+sum(gm.word_coeff.PAYLOAD_OVERHEAD+128*((pw+7)//8)*((ph+7)//8)
                   for pw,ph in ((w,h),(w//2,h//2),(w//2,h//2)))


def encode_frame(base,rgb,rectangles,*,return_info=False):
    started=time.perf_counter_ns()
    a=gm.ft._check_rgb(rgb);h,w=a.shape[:2]
    if type(base) is not bytes or len(base)<gm.HEADER.size+4:raise ValueError('HUD GM01 base bytes')
    fields=gm.HEADER.unpack_from(base);gm.parse(base,fields[3])
    base_validate_ms=(time.perf_counter_ns()-started)/1e6
    if fields[6:8]!=(w,h):raise ValueError('HUD base/source geometry')
    if not isinstance(rectangles,(tuple,list)) or not 0<=len(rectangles)<=MAX_PATCHES:
        raise ValueError('HUD patch count')
    rects=[_rect(rect,w,h) for rect in rectangles];_disjoint(rects)
    begun=time.perf_counter_ns();patches=[encode_patch(a,rect) for rect in rects]
    patch_encode_ms=(time.perf_counter_ns()-begun)/1e6
    begun=time.perf_counter_ns()
    payload=b''.join(LENGTH.pack(len(p))+p for p in patches)
    body=FRAME.pack(b'GH01',1,len(patches),len(base),w,h,len(payload))+base+payload
    packet=_crc(body)
    info={'base_validation_ms':base_validate_ms,'patch_encode_ms':patch_encode_ms,
          'assembly_crc_ms':(time.perf_counter_ns()-begun)/1e6,
          'total_ms':(time.perf_counter_ns()-started)/1e6}
    return (packet,info) if return_info else packet


def parse_frame(packet,epoch):
    if type(packet) is not bytes or len(packet)<FRAME.size+4:
        raise ValueError('HUD wrapper type/truncated')
    magic,version,count,nbase,w,h,npatch=FRAME.unpack_from(packet)
    gm.roi.geometry(w,h)
    if magic!=b'GH01' or version!=1 or not 0<=count<=MAX_PATCHES:
        raise ValueError('HUD wrapper profile')
    if not gm.HEADER.size+4<=nbase<=_base_bound(w,h):raise ValueError('HUD base bound')
    if len(packet)!=FRAME.size+nbase+npatch+4:
        raise ValueError('HUD exact wrapper length')
    # Disjoint patches have total area <= canvas; palette/header overhead is bounded.
    max_patch_bytes=2*w*h+MAX_PATCHES*(4+PATCH.size+4+MAX_COLORS*2)
    if npatch>max_patch_bytes:raise ValueError('HUD aggregate patch bound')
    _check_crc(packet)
    start=FRAME.size;base=packet[start:start+nbase];parsed=gm.parse(base,epoch)
    if (parsed['width'],parsed['height'])!=(w,h):raise ValueError('HUD base/wrapper geometry')
    position=start+nbase;patches=[]
    for _ in range(count):
        if position+4>len(packet)-4:raise ValueError('HUD missing patch length')
        length=LENGTH.unpack_from(packet,position)[0];position+=4
        if length<PATCH.size+4 or position+length>len(packet)-4:raise ValueError('HUD patch frame length')
        patches.append(decode_patch(packet[position:position+length],w,h));position+=length
    if position!=len(packet)-4:raise ValueError('HUD trailing patch bytes')
    _disjoint([p['rect'] for p in patches])
    return base,patches,{'epoch':parsed['epoch'],'frame_id':parsed['frame_id'],'width':w,'height':h,
                         'bytes':len(packet),'base_bytes':nbase,'patch_section_bytes':npatch,
                         'wrapper_header_crc_bytes':FRAME.size+4}


class Receiver:
    def __init__(self,epoch=1):
        self.epoch=epoch;self.base=gm.Receiver(epoch)

    def receive(self,packet):
        begun=time.perf_counter_ns();base,patches,meta=parse_frame(packet,self.epoch)
        validate_ms=(time.perf_counter_ns()-begun)/1e6
        # Every patch has been parsed, range/CRC checked, and overlap rejected
        # before the stateful GM01 base is permitted to commit its anchor.
        begun=time.perf_counter_ns();rgb,info=self.base.receive(base)
        base_ms=(time.perf_counter_ns()-begun)/1e6
        begun=time.perf_counter_ns();base_hash=hashlib.sha256(rgb.tobytes()).hexdigest()
        hash_ms=(time.perf_counter_ns()-begun)/1e6
        begun=time.perf_counter_ns();words=corpus.rgb565(rgb)
        for patch in patches:
            x,y,w,h=patch['rect'];words[y:y+h,x:x+w]=patch['words']
        display=corpus.expand565(words)
        overlay_ms=(time.perf_counter_ns()-begun)/1e6
        return display,{**info,**meta,'base_rgb_sha256':base_hash,'patches':[
            {k:v for k,v in p.items() if k!='words'} for p in patches],
            'stages_ms':{'validate_wrapper_and_base':validate_ms,'base_receive':base_ms,'verification_base_hash':hash_ms,'overlay_rgb565':overlay_ms},
            'scope':'LosslessRGB565displaypatch; GM01YUVanchor unchanged. Experimental GH01, no firmware/hardware/FPS proof.'}
