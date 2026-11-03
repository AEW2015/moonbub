"""GM01 temporal residuals with an explicit macroblock quantizer map.

Python protocol reference only: immutable ACKed key anchor, bounded P credits,
one source/prediction/forward transform per analyze, pure candidate previews,
and admission via commit. No wire ACK or physical read-drain implementation.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct
import sys
import time
import weakref
import zlib

import numpy as np

HERE=Path(__file__).resolve().parent
for directory in ('python-game-roi-study','python-motion-study','python-token-entropy-study','python-word-decode-study'):
    sys.path.insert(0,str(HERE.parent/directory))
import roi_codec as roi
import motion_codec as mt
import token_coeff
import word_coeff
ft=mt.ft
NO_REF=mt.NO_REF
HEADER=struct.Struct('<4sBBIIIHHhhHHIIII')
MAGIC=b'GM01'


def _readonly(a):
    result=a.copy();result.setflags(write=False);return result


@dataclass(frozen=True,eq=False)
class Prepared:
    owner: object
    generation: int
    epoch: int
    frame_id: int
    key: bool
    reference_id: int
    width: int
    height: int
    dx: int
    dy: int
    prediction: tuple
    raw_coefficients: tuple
    forward_calls: int
    analyze_ms: float


@dataclass(frozen=True,eq=False)
class Candidate:
    prepared: Prepared
    scale_map: np.ndarray
    coefficients: tuple
    packet: bytes
    candidate_ms: float


def reconstruct(coefficients,prediction,scale_map,w,h):
    result=[]
    for i,(c,pred) in enumerate(zip(coefficients,prediction)):
        pw,ph=(w,h) if i==0 else (w//2,h//2)
        ph8,pw8=((ph+7)//8)*8,((pw+7)//8)*8
        residual=ft.inverse(c.astype(np.int64)*roi.block_tables(scale_map,w,h,i))
        residual=residual.reshape(ph8//8,pw8//8,8,8).transpose(0,2,1,3).reshape(ph8,pw8)[:ph,:pw]
        plane=np.clip(pred+residual,0,255).astype(np.int16)
        plane.setflags(write=False);result.append(plane)
    return tuple(result)


class Encoder:
    def __init__(self,epoch=1,window=2):
        if type(epoch) is not int or not 0<=epoch<NO_REF or type(window) is not int or not 1<=window<=8:
            raise ValueError('GM01 session/window')
        self.epoch,self.window=epoch,window
        self.anchor_id,self._anchor=None,None
        self.pending={};self.last_issued=-1;self.peak_pending=0
        self._owner=object();self._generation=0
        self._prepared=weakref.WeakSet();self._candidates=weakref.WeakSet()
        self.analysis_count=0;self.forward_calls=0

    def can_prepare(self,force_key=False):
        if any(row['key'] for row in self.pending.values()):return False
        if force_key or self._anchor is None:return not self.pending
        return len(self.pending)<self.window

    def analyze(self,rgb,frame_id,*,force_key=False,mode='zero'):
        started=time.perf_counter_ns();a=ft._check_rgb(rgb);h,w=a.shape[:2]
        key=force_key or self._anchor is None or self._anchor[0].shape!=(h,w)
        if not self.can_prepare(key) or type(frame_id) is not int or not self.last_issued<frame_id<NO_REF:
            raise ValueError('GM01 credit, drain or identity')
        if mode not in ('zero','global'):raise ValueError('GM01 motion mode')
        source=ft.rgb_to_planes(a)
        if key:
            ref,dx,dy=NO_REF,0,0
            prediction=tuple(np.full_like(p,128) for p in source)
        else:
            ref=self.anchor_id
            dx,dy=mt.estimate_motion(source[0],self._anchor[0]) if mode=='global' else (0,0)
            prediction=tuple(mt.predict(self._anchor,dx,dy))
        transformed=[]
        for src,pred in zip(source,prediction):
            residual=src.astype(np.int64)-pred;ph,pw=residual.shape
            padded=np.pad(residual,((0,(-ph)%8),(0,(-pw)%8)),mode='edge')
            hh,ww=padded.shape
            blocks=padded.reshape(hh//8,8,ww//8,8).transpose(0,2,1,3).reshape(-1,8,8)
            raw=ft.forward(blocks);raw.setflags(write=False);transformed.append(raw)
        for plane in prediction:plane.setflags(write=False)
        result=Prepared(self._owner,self._generation,self.epoch,frame_id,key,ref,w,h,dx,dy,
                        prediction,tuple(transformed),3,(time.perf_counter_ns()-started)/1e6)
        self._prepared.add(result);self.analysis_count+=1;self.forward_calls+=3
        return result

    def _check_prepared(self,p):
        if (not isinstance(p,Prepared) or p not in self._prepared or p.owner is not self._owner
                or p.generation!=self._generation or p.epoch!=self.epoch
                or p.frame_id<=self.last_issued or not self.can_prepare(p.key)
                or (not p.key and p.reference_id!=self.anchor_id)):
            raise ValueError('GM01 stale/foreign prepared analysis')

    def encode_candidate(self,prepared,scale_map):
        started=time.perf_counter_ns();self._check_prepared(prepared)
        p=prepared;m=_readonly(roi.check_map(scale_map,p.width,p.height));coefficients=[];payloads=[]
        for i,raw in enumerate(p.raw_coefficients):
            c=ft.round_quantize(raw,roi.block_tables(m,p.width,p.height,i))
            if np.any(np.abs(c)>ft.MAX_COEFF):raise ValueError('GM01 coefficient domain')
            c=c.astype(np.int16);c.setflags(write=False);coefficients.append(c)
            pw=p.width if i==0 else p.width//2
            payloads.append(token_coeff.encode_coefficients(c,(pw+7)//8))
        mw,mh=roi.geometry(p.width,p.height);mapped=roi.pack_map(m)
        body=HEADER.pack(MAGIC,1,int(p.key),p.epoch,p.frame_id,p.reference_id,p.width,p.height,
                         p.dx,p.dy,mw,mh,len(mapped),*(len(v) for v in payloads))+mapped+b''.join(payloads)
        packet=body+struct.pack('<I',zlib.crc32(body))
        candidate=Candidate(p,m,tuple(coefficients),packet,(time.perf_counter_ns()-started)/1e6)
        self._candidates.add(candidate);return candidate

    def commit(self,candidate):
        if not isinstance(candidate,Candidate) or candidate not in self._candidates:
            raise ValueError('GM01 foreign/forged candidate')
        p=candidate.prepared;self._check_prepared(p)
        planes=reconstruct(candidate.coefficients,p.prediction,candidate.scale_map,p.width,p.height) if p.key else None
        self.pending[p.frame_id]={'key':p.key,'planes':planes,'expected_rgb_sha256':None,
                                  'packet':candidate.packet,'reference_id':None if p.key else p.reference_id}
        if p.key:self.anchor_id,self._anchor=None,None
        self.last_issued=p.frame_id;self._generation+=1
        self.peak_pending=max(self.peak_pending,len(self.pending))
        return candidate.packet

    def prepare(self,rgb,frame_id,*,scale_map=None,quant_scale=16,force_key=False,mode='zero'):
        p=self.analyze(rgb,frame_id,force_key=force_key,mode=mode)
        if scale_map is None:
            if type(quant_scale) is not int or quant_scale not in roi.SCALES:raise ValueError('GM01 uniform scale')
            mw,mh=roi.geometry(p.width,p.height)
            scale_map=np.full((mh,mw),quant_scale,np.uint8)
        return self.commit(self.encode_candidate(p,scale_map))

    def expected_hash(self,frame_id):
        row=self.pending[frame_id]
        if row['expected_rgb_sha256'] is None:
            if row['key']:rgb=ft.planes_to_rgb(row['planes'])
            else:
                rx=Receiver(self.epoch);rx.anchor_id,rx._anchor=self.anchor_id,self._anchor
                rgb,_=rx.receive(row['packet'])
            row['expected_rgb_sha256']=hashlib.sha256(rgb.tobytes()).hexdigest()
        return row['expected_rgb_sha256']

    def ack(self,frame_id,*,epoch):
        if type(epoch) is not int or epoch!=self.epoch or type(frame_id) is not int:
            raise ValueError('GM01 ACK epoch/identity')
        row=self.pending.pop(frame_id,None)
        if row is None:return False
        if row['key']:
            self.anchor_id,self._anchor=frame_id,row['planes'];self._generation+=1
        return True

    def expire(self,frame_id):
        row=self.pending.pop(frame_id,None)
        if row is None:return False
        if row['key']:
            self.anchor_id,self._anchor=None,None;self._generation+=1
        return True

    def retained_reference_bytes(self):
        planes=self._anchor
        if planes is None:planes=next((r['planes'] for r in self.pending.values() if r['key']),None)
        return sum(p.nbytes for p in planes) if planes is not None else 0


def parse(packet,epoch):
    if not isinstance(packet,bytes) or len(packet)<HEADER.size+4:raise ValueError('GM01 truncated/type')
    magic,version,key,session,frame,ref,w,h,dx,dy,mw,mh,nmap,ny,ncb,ncr=HEADER.unpack_from(packet)
    expected=roi.geometry(w,h)
    if (magic!=MAGIC or version!=1 or key not in (0,1) or session!=epoch or session==NO_REF
        or frame==NO_REF or (mw,mh)!=expected or dx%2 or dy%2 or abs(dx)>mt.MV_LIMIT or abs(dy)>mt.MV_LIMIT
        or bool(key)!=(ref==NO_REF) or (key and (dx or dy)) or (not key and ref>=frame)):
        raise ValueError('GM01 profile/identity/vector')
    if nmap!=(mw*mh+3)//4:raise ValueError('GM01 map length')
    dimensions=((w,h),(w//2,h//2),(w//2,h//2));lengths=(ny,ncb,ncr)
    for n,(pw,ph) in zip(lengths,dimensions):
        blocks=((pw+7)//8)*((ph+7)//8)
        if not word_coeff.PAYLOAD_OVERHEAD<=n<=128*blocks+word_coeff.PAYLOAD_OVERHEAD:
            raise ValueError('GM01 plane length bound')
    if len(packet)!=HEADER.size+nmap+sum(lengths)+4:raise ValueError('GM01 exact frame length')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('GM01 CRC')
    pos=HEADER.size;m=roi.unpack_map(packet[pos:pos+nmap],mw,mh);pos+=nmap;coefficients=[]
    for n,(pw,ph) in zip(lengths,dimensions):
        bw,bh=(pw+7)//8,(ph+7)//8
        coefficients.append(word_coeff.decode_coefficients(packet[pos:pos+n],bw*bh,bw));pos+=n
    return dict(epoch=session,frame_id=frame,key=bool(key),reference_id=ref,width=w,height=h,dx=dx,dy=dy,
                scale_map=m,coefficients=tuple(coefficients),map_bytes=nmap)


class Receiver:
    def __init__(self,epoch=1):
        if type(epoch) is not int or not 0<=epoch<NO_REF:raise ValueError('GM01 receiver epoch')
        self.epoch=epoch;self.anchor_id,self._anchor=None,None;self.last_frame_id=-1

    def receive(self,packet):
        p=parse(packet,self.epoch);w,h=p['width'],p['height'];frame=p['frame_id']
        if frame<=self.last_frame_id:raise ValueError('GM01 replay/regression')
        if p['key']:prediction=tuple(np.full(shape,128,np.int16) for shape in ((h,w),(h//2,w//2),(h//2,w//2)))
        else:
            if p['reference_id']!=self.anchor_id or self._anchor is None or self._anchor[0].shape!=(h,w):
                raise ValueError('GM01 missing exact anchor')
            prediction=tuple(mt.predict(self._anchor,p['dx'],p['dy']))
        planes=reconstruct(p['coefficients'],prediction,p['scale_map'],w,h)
        rgb=ft.planes_to_rgb(planes)
        if p['key']:self.anchor_id,self._anchor=frame,planes
        self.last_frame_id=frame
        return rgb,dict(epoch=self.epoch,frame_id=frame,key=p['key'],reference_id=None if p['key'] else p['reference_id'],
                        anchor_id=self.anchor_id,width=w,height=h,dx=p['dx'],dy=p['dy'],map_bytes=p['map_bytes'],bytes=len(packet),
                        retained_reference_array_bytes=sum(x.nbytes for x in self._anchor),
                        scope='Python GM01 software reference; no wireACK/physical-memory/target-FPS proof')
