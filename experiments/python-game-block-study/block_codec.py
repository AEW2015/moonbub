"""BM01 integer macroblock motion around frozen Q14/ROI/CP02 arithmetic.

Python protocol prototype only. One immutable ACKed reconstructed key, up to two
P credits. No installed firmware/transport/RTL support or physical read-drain.
"""
from pathlib import Path
import hashlib
import struct
import sys
import time
import zlib
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-game-codec-study'))
import game_codec as gc
ft,roi=gc.ft,gc.roi
NO_REF=gc.NO_REF
MAGIC=b'BM01'
# magic/version/flags/epoch/frame/ref/w/h/range/vector_mode/mw/mh/map/vector/Y/Cb/Cr lengths
HEADER=struct.Struct('<4sBBIIIHHBBHHIIIII')
KEY=1
ZERO_RESIDUAL=2


def _identity(value):return type(value) is int and 0<=value<NO_REF


def _frozen(planes):
    out=[]
    for plane in planes:
        a=plane.copy();a.setflags(write=False);out.append(a)
    return tuple(out)


def estimate_vectors(current,reference,search_range=4):
    """All actual luma samples; candidate ordering gives deterministic tie bias."""
    if type(search_range) is not int or search_range not in (4,8):raise ValueError('BM01 search range')
    if current.shape!=reference.shape:raise ValueError('BM01 search geometry')
    h,w=current.shape;mw,mh=roi.geometry(w,h)
    best=np.full((mh,mw),2**31-1,np.int64);vectors=np.zeros((mh,mw,2),np.int8)
    candidates=sorted(((dx,dy) for dy in range(-search_range,search_range+1,2)
                       for dx in range(-search_range,search_range+1,2)),
                      key=lambda xy:(abs(xy[0])+abs(xy[1]),xy[1],xy[0]))
    yy=np.arange(h);xx=np.arange(w)
    for dx,dy in candidates:
        prediction=reference[np.clip(yy+dy,0,h-1)[:,None],np.clip(xx+dx,0,w-1)]
        error=np.abs(current.astype(np.int16)-prediction.astype(np.int16))
        if h%16 or w%16:error=np.pad(error,((0,(-h)%16),(0,(-w)%16)),constant_values=0)
        sad=error.reshape(mh,16,mw,16).sum(axis=(1,3),dtype=np.int64)
        update=sad<best
        best[update]=sad[update];vectors[update]=(dx,dy)
    return vectors,dict(candidate_count=len(candidates),luma_sad_samples=len(candidates)*w*h,
                        zero_blocks=int(np.sum(np.all(vectors==0,axis=2))),blocks=mw*mh)


def predict(planes,vectors):
    """Normative output[y,x] = key[clamp(y+dy),clamp(x+dx)], chroma /2."""
    out=[]
    for i,p in enumerate(planes):
        h,w=p.shape;block=16 if i==0 else 8
        yy,xx=np.mgrid[:h,:w];v=vectors[yy//block,xx//block]
        dx,dy=v[...,0].astype(np.int32),v[...,1].astype(np.int32)
        if i:dx=dx//2;dy=dy//2
        a=p[np.clip(yy+dy,0,h-1),np.clip(xx+dx,0,w-1)].astype(np.int16)
        a.setflags(write=False);out.append(a)
    return tuple(out)


def pack_vectors(vectors,key=False):
    if key:return 0,b''
    flat=vectors.reshape(-1,2);dense=flat.tobytes()
    nonzero=np.any(flat!=0,axis=1)
    mask=np.packbits(nonzero,bitorder='big').tobytes()
    sparse=mask+flat[nonzero].tobytes()
    return (1,sparse) if len(sparse)<len(dense) else (0,dense)


def unpack_vectors(data,mw,mh,mode,key,limit):
    n=mw*mh;flat=np.zeros((n,2),np.int8)
    if key:
        if mode!=0 or data:raise ValueError('BM01 key vectors')
    elif mode==0:
        if len(data)!=2*n:raise ValueError('BM01 dense vector length')
        flat=np.frombuffer(data,np.int8).reshape(n,2).copy()
        # Dense is only canonical if sparse would be no smaller.
        if (n+7)//8+2*np.count_nonzero(np.any(flat!=0,axis=1))<2*n:
            raise ValueError('BM01 nonminimum dense vector mode')
    elif mode==1:
        maskbytes=(n+7)//8
        if len(data)<maskbytes:raise ValueError('BM01 sparse map length')
        bits=np.unpackbits(np.frombuffer(data[:maskbytes],np.uint8),bitorder='big')
        if np.any(bits[n:]):raise ValueError('BM01 sparse padding')
        indices=np.flatnonzero(bits[:n]);count=len(indices)
        if len(data)!=maskbytes+2*count or len(data)>=2*n:raise ValueError('BM01 sparse exact/nonminimum size')
        pairs=np.frombuffer(data[maskbytes:],np.int8).reshape(count,2)
        if np.any(np.all(pairs==0,axis=1)):raise ValueError('BM01 sparse zero pair')
        flat[indices]=pairs
    else:raise ValueError('BM01 vector mode')
    if np.any(flat.astype(np.int16)%2) or np.any(np.abs(flat.astype(np.int16))>limit):
        raise ValueError('BM01 vector domain')
    a=flat.reshape(mh,mw,2);a.setflags(write=False);return a


def transform(source,prediction,scale_map,w,h):
    coefficients=[]
    for i,(src,pred) in enumerate(zip(source,prediction)):
        residual=src.astype(np.int64)-pred
        ph,pw=residual.shape
        padded=np.pad(residual,((0,(-ph)%8),(0,(-pw)%8)),mode='edge')
        hh,ww=padded.shape
        blocks=padded.reshape(hh//8,8,ww//8,8).transpose(0,2,1,3).reshape(-1,8,8)
        raw=ft.forward(blocks)
        c=ft.round_quantize(raw,roi.block_tables(scale_map,w,h,i))
        if np.any(np.abs(c)>ft.MAX_COEFF):raise ValueError('BM01 coefficient domain')
        c=c.astype(np.int16);c.setflags(write=False);coefficients.append(c)
    return tuple(coefficients)


def parse(packet,epoch):
    if type(packet) is not bytes or len(packet)<HEADER.size+4:raise ValueError('BM01 truncated/type')
    magic,version,flags,session,frame,ref,w,h,limit,vmode,mw,mh,nmap,nvec,ny,ncb,ncr=HEADER.unpack_from(packet)
    expected=roi.geometry(w,h)
    key=bool(flags&KEY);zero=bool(flags&ZERO_RESIDUAL)
    if (magic!=MAGIC or version!=1 or flags&~(KEY|ZERO_RESIDUAL) or (key and zero)
        or not _identity(epoch) or session!=epoch or not _identity(frame)
        or limit not in (4,8) or (mw,mh)!=expected or key!=(ref==NO_REF)
        or (not key and ref>=frame) or nmap!=(mw*mh+3)//4):
        raise ValueError('BM01 profile/identity/geometry')
    if (key and nvec) or nvec>2*mw*mh:raise ValueError('BM01 vector byte bound')
    lengths=(ny,ncb,ncr);dimensions=((w,h),(w//2,h//2),(w//2,h//2))
    for n,(pw,ph) in zip(lengths,dimensions):
        blocks=((pw+7)//8)*((ph+7)//8)
        if zero:
            if n:raise ValueError('BM01 zero residual payload')
        elif not gc.word_coeff.PAYLOAD_OVERHEAD<=n<=128*blocks+gc.word_coeff.PAYLOAD_OVERHEAD:
            raise ValueError('BM01 plane bound')
    if len(packet)!=HEADER.size+nmap+nvec+sum(lengths)+4:raise ValueError('BM01 exact length')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('BM01 CRC')
    pos=HEADER.size;scale_map=roi.unpack_map(packet[pos:pos+nmap],mw,mh);pos+=nmap
    vectors=unpack_vectors(packet[pos:pos+nvec],mw,mh,vmode,key,limit);pos+=nvec
    coefficients=[]
    for n,(pw,ph) in zip(lengths,dimensions):
        if zero:coefficients.append(None)
        else:
            bw,bh=(pw+7)//8,(ph+7)//8
            coefficients.append(gc.word_coeff.decode_coefficients(packet[pos:pos+n],bw*bh,bw));pos+=n
    return dict(epoch=session,frame_id=frame,reference_id=ref,key=key,zero_residual=zero,
                width=w,height=h,search_range=limit,vector_mode=vmode,vectors=vectors,
                map_bytes=nmap,vector_bytes=nvec,scale_map=scale_map,coefficients=tuple(coefficients))


class Encoder:
    def __init__(self,epoch=1,window=2,search_range=4):
        if not _identity(epoch) or type(window) is not int or not 1<=window<=2 or type(search_range) is not int or search_range not in (4,8):
            raise ValueError('BM01 session/window/range')
        self.epoch,self.window,self.search_range=epoch,window,search_range
        self.anchor_id,self._anchor=None,None;self.pending={};self.last_issued=-1;self.last_info=None

    def can_prepare(self,force_key=False):
        if any(p['key'] for p in self.pending.values()):return False
        if force_key or self._anchor is None:return not self.pending
        return len(self.pending)<self.window

    def prepare(self,rgb,frame_id,*,scale_map,force_key=False):
        start=time.perf_counter_ns();source=ft.rgb_to_planes(ft._check_rgb(rgb));h,w=source[0].shape
        m=roi.check_map(scale_map,w,h);mw,mh=roi.geometry(w,h)
        key=force_key or self._anchor is None or self._anchor[0].shape!=(h,w)
        if not _identity(frame_id) or frame_id<=self.last_issued or not self.can_prepare(key):
            raise ValueError('BM01 credit/identity/drain')
        t=time.perf_counter_ns()
        if key:
            vectors=np.zeros((mh,mw,2),np.int8);prediction=tuple(np.full_like(p,128) for p in source)
            search=dict(candidate_count=0,luma_sad_samples=0,zero_blocks=mw*mh,blocks=mw*mh)
        else:
            vectors,search=estimate_vectors(source[0],self._anchor[0],self.search_range)
            prediction=predict(self._anchor,vectors)
        search_ms=(time.perf_counter_ns()-t)/1e6
        t=time.perf_counter_ns();coefficients=transform(source,prediction,m,w,h)
        transform_ms=(time.perf_counter_ns()-t)/1e6
        zero=not key and all(not np.any(c) for c in coefficients)
        t=time.perf_counter_ns();vmode,vector_bytes=pack_vectors(vectors,key);mapped=roi.pack_map(m)
        payloads=[] if zero else [gc.token_coeff.encode_coefficients(c,((w if i==0 else w//2)+7)//8) for i,c in enumerate(coefficients)]
        lengths=(0,0,0) if zero else tuple(map(len,payloads))
        ref=NO_REF if key else self.anchor_id
        body=HEADER.pack(MAGIC,1,(KEY if key else 0)|(ZERO_RESIDUAL if zero else 0),self.epoch,frame_id,ref,
                         w,h,self.search_range,vmode,mw,mh,len(mapped),len(vector_bytes),*lengths)+mapped+vector_bytes+b''.join(payloads)
        packet=body+struct.pack('<I',zlib.crc32(body));packet_ms=(time.perf_counter_ns()-t)/1e6
        t=time.perf_counter_ns()
        planes=gc.reconstruct(coefficients,prediction,m,w,h) if key else None
        reconstruction_ms=(time.perf_counter_ns()-t)/1e6
        self.pending[frame_id]=dict(key=key,planes=planes,coefficients=coefficients,prediction=prediction,scale_map=m.copy(),
                                   width=w,height=h,expected=None,frame_crc=zlib.crc32(body))
        if key:self.anchor_id,self._anchor=None,None
        self.last_issued=frame_id
        self.last_info=dict(search=search,search_prediction_ms=search_ms,transform_quantize_ms=transform_ms,
                            packet_vectors_entropy_ms=packet_ms,key_reconstruction_ms=reconstruction_ms,
                            service_ms=(time.perf_counter_ns()-start)/1e6,vector_bytes=len(vector_bytes),
                            map_bytes=len(mapped),header_crc_bytes=HEADER.size+4,zero_residual=zero)
        return packet

    def expected_hash(self,frame_id):
        p=self.pending[frame_id]
        if p['expected'] is None:
            planes=p['planes'] if p['key'] else gc.reconstruct(p['coefficients'],p['prediction'],p['scale_map'],p['width'],p['height'])
            p['expected']=hashlib.sha256(ft.planes_to_rgb(planes).tobytes()).hexdigest()
        return p['expected']

    def ack(self,frame_id,*,epoch,frame_crc):
        if not _identity(frame_id) or not _identity(epoch) or epoch!=self.epoch:raise ValueError('BM01 ACK epoch/identity')
        row=self.pending.get(frame_id)
        if row is None:return False
        if type(frame_crc) is not int or frame_crc!=row['frame_crc']:raise ValueError('BM01 ACK body CRC')
        del self.pending[frame_id]
        if row['key']:self.anchor_id,self._anchor=frame_id,row['planes']
        return True

    def expire(self,frame_id):
        if not _identity(frame_id):raise ValueError('BM01 expire identity')
        row=self.pending.pop(frame_id,None)
        if row is None:return False
        if row['key']:self.anchor_id,self._anchor=None,None
        return True


class Receiver:
    def __init__(self,epoch=1):
        if not _identity(epoch):raise ValueError('BM01 receiver epoch')
        self.epoch=epoch;self.anchor_id,self._anchor=None,None;self.last_frame_id=-1

    def receive(self,packet):
        p=parse(packet,self.epoch);frame=p['frame_id'];h,w=p['height'],p['width']
        if frame<=self.last_frame_id:raise ValueError('BM01 replay/regression')
        if p['key']:
            prediction=tuple(np.full(shape,128,np.int16) for shape in ((h,w),(h//2,w//2),(h//2,w//2)))
        else:
            if p['reference_id']!=self.anchor_id or self._anchor is None or self._anchor[0].shape!=(h,w):
                raise ValueError('BM01 missing exact ACKable key')
            prediction=predict(self._anchor,p['vectors'])
        planes=[]
        # Receiver rebuilds directly from parsed data, never encoder pending objects.
        for i,pred in enumerate(prediction):
            ph,pw=pred.shape
            if p['zero_residual']:plane=pred.copy()
            else:
                hh,ww=((ph+7)//8)*8,((pw+7)//8)*8
                residual=ft.inverse(p['coefficients'][i].astype(np.int64)*roi.block_tables(p['scale_map'],w,h,i))
                residual=residual.reshape(hh//8,ww//8,8,8).transpose(0,2,1,3).reshape(hh,ww)[:ph,:pw]
                plane=np.clip(pred+residual,0,255).astype(np.int16)
            plane.setflags(write=False);planes.append(plane)
        planes=tuple(planes);rgb=ft.planes_to_rgb(planes)
        if p['key']:self.anchor_id,self._anchor=frame,planes
        self.last_frame_id=frame
        return rgb,dict(frame_id=frame,key=p['key'],reference_id=p['reference_id'],anchor_id=self.anchor_id,
                        zero_residual=p['zero_residual'],vector_bytes=p['vector_bytes'],map_bytes=p['map_bytes'])
