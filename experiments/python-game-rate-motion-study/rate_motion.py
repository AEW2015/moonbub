"""RM01 actual-rate GM01/BM01 choice with one canonical ACKed YUV key.

Pure previews never install references or consume credits. Key transforms,
entropy and one reconstruction may be shared because all key predictors are128.
All actual candidate work, including losing P searches/transforms, is paid.
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
sys.path.insert(0,str(HERE.parent/'python-game-block-study'))
import block_codec as bm
gm=bm.gc
MAX_FRAME=49152
HEADER=struct.Struct('<4sBBIIIHHI')
MODES=('gm_zero','gm_global','bm_block')


def _identity(value):return type(value) is int and 0<=value<gm.NO_REF

def _seal(body):return body+struct.pack('<I',zlib.crc32(body))

def _readonly(a):
    a=a.copy();a.setflags(write=False);return a


def _envelope(inner,kind,epoch,frame,reference,w,h):
    return _seal(HEADER.pack(b'RM01',1,kind,epoch,frame,reference,w,h,len(inner))+inner)


def identity(packet,epoch=None,frame_cap=MAX_FRAME):
    """Envelope and inner-header identity/CRC preflight, not entropy validity."""
    if type(frame_cap) is not int or not 1<=frame_cap<=MAX_FRAME:raise ValueError('RM01 cap')
    if type(packet) is not bytes or not HEADER.size+4<=len(packet)<=frame_cap:raise ValueError('RM01 packet bound/type')
    magic,version,kind,session,frame,reference,w,h,length=HEADER.unpack_from(packet)
    gm.roi.geometry(w,h)
    if (magic!=b'RM01' or version!=1 or kind not in (0,1) or not _identity(session) or not _identity(frame)
        or (epoch is not None and (not _identity(epoch) or epoch!=session))
        or (reference!=gm.NO_REF and not reference<frame)
        or len(packet)!=HEADER.size+length+4):raise ValueError('RM01 envelope profile/identity/length')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('RM01 outer CRC')
    inner=packet[HEADER.size:-4];header=gm.HEADER if kind==0 else bm.HEADER
    if len(inner)<header.size+4:raise ValueError('RM01 missing inner header')
    fields=header.unpack_from(inner)
    if (fields[0]!=(b'GM01' if kind==0 else b'BM01') or fields[1]!=1
        or fields[3:8]!=(session,frame,reference,w,h)):
        raise ValueError('RM01 outer/inner identity')
    if zlib.crc32(inner[:-4])!=struct.unpack('<I',inner[-4:])[0]:raise ValueError('RM01 inner CRC')
    return {'epoch':session,'frame_id':frame,'reference_id':reference,'key':reference==gm.NO_REF,
            'width':w,'height':h,'codec':'GM01' if kind==0 else 'BM01','inner_bytes':length,
            'bytes':len(packet),'body_tag':zlib.crc32(packet[:-4])}


def parse(packet,epoch,frame_cap=MAX_FRAME):
    ident=identity(packet,epoch,frame_cap);inner=packet[HEADER.size:-4]
    parsed=(gm.parse if ident['codec']=='GM01' else bm.parse)(inner,epoch)
    if (parsed['frame_id']!=ident['frame_id'] or parsed['reference_id']!=ident['reference_id']
        or parsed['key']!=ident['key']):raise ValueError('RM01 parsed identity disagreement')
    return parsed,ident


@dataclass(frozen=True,eq=False)
class Candidate:
    owner:object
    generation:int
    mode:str
    packet:bytes
    prediction:tuple
    coefficients:tuple
    key_planes:tuple|None
    zero_residual:bool
    stages:dict


@dataclass(frozen=True,eq=False)
class Preview:
    owner:object
    generation:int
    epoch:int
    frame_id:int
    reference_id:int
    key:bool
    width:int
    height:int
    scale_map:np.ndarray
    candidates:tuple
    common_stages:dict
    service_ms:float


@dataclass(frozen=True)
class Decision:
    packet:bytes|None
    selected_mode:str|None
    frame_id:int
    key:bool
    reference_id:int
    attempts:tuple
    common_stages:dict
    preview_ms:float
    commit_ms:float
    service_ms:float

    @property
    def accepted(self):return self.packet is not None


def select(preview,frame_cap=MAX_FRAME):
    """Actual complete RM01 bytes only; deterministic declared-order tie break."""
    if not isinstance(preview,Preview) or type(frame_cap) is not int or not 1<=frame_cap<=MAX_FRAME:
        raise ValueError('RM01 selection profile')
    best=min(preview.candidates,key=lambda c:len(c.packet))
    return best if len(best.packet)<=frame_cap else None


class Encoder:
    def __init__(self,epoch=1,window=2,modes=('gm_zero','bm_block'),search_range=4):
        if (not _identity(epoch) or type(window) is not int or not 1<=window<=2
            or type(modes) is not tuple or not modes or len(set(modes))!=len(modes)
            or any(mode not in MODES for mode in modes) or type(search_range) is not int or search_range not in (4,8)):
            raise ValueError('RM01 encoder profile')
        self.epoch,self.window,self.modes,self.search_range=epoch,window,modes,search_range
        self.anchor_id,self._anchor=None,None;self.pending={};self.last_issued=-1
        self._owner=object();self._generation=0
        self._previews=weakref.WeakSet();self._candidates=weakref.WeakSet()
        self.last_info=None

    def can_prepare(self,force_key=False):
        if any(p['key'] for p in self.pending.values()):return False
        if force_key or self._anchor is None:return not self.pending
        return len(self.pending)<self.window

    @property
    def read_pins(self):return sum(not row['key'] for row in self.pending.values())

    def preview(self,rgb,frame_id,*,scale_map,force_key=False):
        start=time.perf_counter_ns();a=gm.ft._check_rgb(rgb);h,w=a.shape[:2]
        key=force_key or self._anchor is None or self._anchor[0].shape!=(h,w)
        if not _identity(frame_id) or frame_id<=self.last_issued or not self.can_prepare(key):
            raise ValueError('RM01 credit/key-drain/frame identity')
        t=time.perf_counter_ns();source=gm.ft.rgb_to_planes(a)
        for p in source:p.setflags(write=False)
        convert_ms=(time.perf_counter_ns()-t)/1e6
        t=time.perf_counter_ns();m=_readonly(gm.roi.check_map(scale_map,w,h));mapped=gm.roi.pack_map(m)
        mw,mh=gm.roi.geometry(w,h);map_ms=(time.perf_counter_ns()-t)/1e6
        reference=gm.NO_REF if key else self.anchor_id
        common={'source_conversion_ms':convert_ms,'map_ms':map_ms,'shared_key_transform_ms':0.,
                'shared_key_entropy_ms':0.,'shared_key_reconstruction_ms':0.,'shared_key_reconstruction_count':0}
        key_coefficients=key_prediction=key_payloads=key_planes=None
        if key:
            t=time.perf_counter_ns();key_prediction=tuple(np.full_like(p,128) for p in source)
            for plane in key_prediction:plane.setflags(write=False)
            key_coefficients=bm.transform(source,key_prediction,m,w,h)
            common['shared_key_transform_ms']=(time.perf_counter_ns()-t)/1e6
            t=time.perf_counter_ns();key_payloads=tuple(gm.token_coeff.encode_coefficients(c,((w if i==0 else w//2)+7)//8)
                                                        for i,c in enumerate(key_coefficients))
            common['shared_key_entropy_ms']=(time.perf_counter_ns()-t)/1e6
            t=time.perf_counter_ns();key_planes=gm.reconstruct(key_coefficients,key_prediction,m,w,h)
            common['shared_key_reconstruction_ms']=(time.perf_counter_ns()-t)/1e6
            common['shared_key_reconstruction_count']=1
        candidates=[]
        for mode in self.modes:
            began=time.perf_counter_ns();search_ms=transform_ms=entropy_ms=0.;search={};dx=dy=0
            vectors=np.zeros((mh,mw,2),np.int8) if mode=='bm_block' else None
            if key:
                prediction,coefficients,payloads=key_prediction,key_coefficients,key_payloads
            else:
                t=time.perf_counter_ns()
                if mode=='bm_block':
                    vectors,search=bm.estimate_vectors(source[0],self._anchor[0],self.search_range)
                    prediction=bm.predict(self._anchor,vectors)
                else:
                    if mode=='gm_global':dx,dy=gm.mt.estimate_motion(source[0],self._anchor[0])
                    prediction=tuple(gm.mt.predict(self._anchor,dx,dy))
                search_ms=(time.perf_counter_ns()-t)/1e6
                t=time.perf_counter_ns();coefficients=bm.transform(source,prediction,m,w,h)
                transform_ms=(time.perf_counter_ns()-t)/1e6
                t=time.perf_counter_ns()
                zero=mode=='bm_block' and all(not np.any(c) for c in coefficients)
                payloads=() if zero else tuple(gm.token_coeff.encode_coefficients(c,((w if i==0 else w//2)+7)//8)
                                               for i,c in enumerate(coefficients))
                entropy_ms=(time.perf_counter_ns()-t)/1e6
            zero=(not key and mode=='bm_block' and not payloads)
            t=time.perf_counter_ns();vector_bytes=b''
            if mode=='bm_block':
                vmode,vector_bytes=bm.pack_vectors(vectors,key)
                lengths=(0,0,0) if zero else tuple(map(len,payloads))
                body=bm.HEADER.pack(b'BM01',1,(bm.KEY if key else 0)|(bm.ZERO_RESIDUAL if zero else 0),
                    self.epoch,frame_id,reference,w,h,self.search_range,vmode,mw,mh,len(mapped),len(vector_bytes),*lengths)
                body+=mapped+vector_bytes+b''.join(payloads);kind=1
            else:
                body=gm.HEADER.pack(b'GM01',1,int(key),self.epoch,frame_id,reference,w,h,dx,dy,mw,mh,len(mapped),*map(len,payloads))
                body+=mapped+b''.join(payloads);kind=0
            inner=_seal(body);packet=_envelope(inner,kind,self.epoch,frame_id,reference,w,h)
            packet_ms=(time.perf_counter_ns()-t)/1e6
            stages={'search_prediction_ms':search_ms,'transform_quantize_ms':transform_ms,'entropy_ms':entropy_ms,
                    'packet_vectors_envelope_ms':packet_ms,'candidate_total_ms':(time.perf_counter_ns()-began)/1e6,
                    'search':search,'vector_bytes':len(vector_bytes),'inner_bytes':len(inner),'zero_residual':zero,
                    'dx':dx,'dy':dy,'shared_key_work':key}
            candidate=Candidate(self._owner,self._generation,mode,packet,prediction,coefficients,key_planes,zero,stages)
            self._candidates.add(candidate);candidates.append(candidate)
        result=Preview(self._owner,self._generation,self.epoch,frame_id,reference,key,w,h,m,tuple(candidates),common,
                       (time.perf_counter_ns()-start)/1e6)
        self._previews.add(result);return result

    def _check_preview(self,preview):
        if (not isinstance(preview,Preview) or preview not in self._previews or preview.owner is not self._owner
            or preview.generation!=self._generation or preview.epoch!=self.epoch
            or preview.frame_id<=self.last_issued or not self.can_prepare(preview.key)
            or (not preview.key and preview.reference_id!=self.anchor_id)):
            raise ValueError('RM01 stale/foreign/blocked preview')

    def commit(self,preview,candidate,*,frame_cap=MAX_FRAME):
        self._check_preview(preview)
        if type(frame_cap) is not int or not 1<=frame_cap<=MAX_FRAME:raise ValueError('RM01 commit cap')
        if (candidate not in preview.candidates or candidate not in self._candidates or candidate.owner is not self._owner
            or candidate.generation!=self._generation or len(candidate.packet)>frame_cap
            or type(frame_cap) is not int or not 1<=frame_cap<=MAX_FRAME):
            raise ValueError('RM01 foreign/oversized candidate')
        tag=zlib.crc32(candidate.packet[:-4])
        self.pending[preview.frame_id]={'key':preview.key,'planes':candidate.key_planes,'prediction':candidate.prediction,
            'coefficients':candidate.coefficients,'zero_residual':candidate.zero_residual,
            'scale_map':preview.scale_map,
            'width':preview.width,'height':preview.height,'packet':candidate.packet,'frame_crc':tag,'expected':None,'mode':candidate.mode}
        self.last_issued=preview.frame_id
        return candidate.packet

    def prepare(self,rgb,frame_id,*,scale_map,force_key=False,frame_cap=MAX_FRAME):
        if type(frame_cap) is not int or not 1<=frame_cap<=MAX_FRAME:raise ValueError('RM01 prepare cap')
        start=time.perf_counter_ns();preview=self.preview(rgb,frame_id,scale_map=scale_map,force_key=force_key)
        candidate=select(preview,frame_cap);packet=None;commit_ms=0.
        if candidate is not None:
            t=time.perf_counter_ns();packet=self.commit(preview,candidate,frame_cap=frame_cap);commit_ms=(time.perf_counter_ns()-t)/1e6
        attempts=tuple({'mode':c.mode,'bytes':len(c.packet),'fits':len(c.packet)<=frame_cap,
                        'selected':c is candidate,'packet_sha256':hashlib.sha256(c.packet).hexdigest(),'stages':c.stages} for c in preview.candidates)
        decision=Decision(packet,None if candidate is None else candidate.mode,frame_id,preview.key,preview.reference_id,
                          attempts,preview.common_stages,preview.service_ms,commit_ms,(time.perf_counter_ns()-start)/1e6)
        self.last_info=decision;return decision

    def expected_hash(self,frame_id):
        p=self.pending[frame_id]
        if p['expected'] is None:
            if p['key']:planes=p['planes']
            elif p['zero_residual']:planes=p['prediction']
            else:planes=gm.reconstruct(p['coefficients'],p['prediction'],p['scale_map'],p['width'],p['height'])
            p['expected']=hashlib.sha256(gm.ft.planes_to_rgb(planes).tobytes()).hexdigest()
        return p['expected']

    def ack(self,frame_id,*,epoch,frame_crc):
        if not _identity(frame_id) or not _identity(epoch) or epoch!=self.epoch:raise ValueError('RM01 ACK identity/session')
        row=self.pending.get(frame_id)
        if row is None:return False
        if type(frame_crc) is not int or frame_crc!=row['frame_crc']:raise ValueError('RM01 ACK outer body tag')
        del self.pending[frame_id]
        if row['key']:
            self.anchor_id,self._anchor=frame_id,row['planes'];self._generation+=1
        return True

    def expire(self,frame_id):
        if not _identity(frame_id):raise ValueError('RM01 expire identity')
        row=self.pending.pop(frame_id,None)
        if row is None:return False
        if row['key']:self.anchor_id,self._anchor=None,None;self._generation+=1
        return True


class Decoder:
    def __init__(self,epoch=1,frame_cap=MAX_FRAME):
        if not _identity(epoch) or type(frame_cap) is not int or not 1<=frame_cap<=MAX_FRAME:raise ValueError('RM01 decoder profile')
        self.epoch,self.frame_cap=epoch,frame_cap
        self.anchor_id,self._anchor=None,None;self.last_frame_id=-1

    def receive(self,packet):
        p,ident=parse(packet,self.epoch,self.frame_cap);frame=p['frame_id'];w,h=p['width'],p['height']
        if frame<=self.last_frame_id:raise ValueError('RM01 replay/regression')
        if p['key']:
            prediction=tuple(np.full(shape,128,np.int16) for shape in ((h,w),(h//2,w//2),(h//2,w//2)))
        else:
            if p['reference_id']!=self.anchor_id or self._anchor is None or self._anchor[0].shape!=(h,w):
                raise ValueError('RM01 missing exact anchor')
            prediction=bm.predict(self._anchor,p['vectors']) if ident['codec']=='BM01' else tuple(gm.mt.predict(self._anchor,p['dx'],p['dy']))
        zero=bool(p.get('zero_residual',False))
        planes=tuple(_readonly(plane) for plane in prediction) if zero else gm.reconstruct(p['coefficients'],prediction,p['scale_map'],w,h)
        rgb=gm.ft.planes_to_rgb(planes)
        if p['key']:self.anchor_id,self._anchor=frame,planes
        self.last_frame_id=frame
        return rgb,{**ident,'anchor_id':self.anchor_id,'zero_residual':zero,
                    'vector_bytes':p.get('vector_bytes',0),'map_bytes':p['map_bytes']}
