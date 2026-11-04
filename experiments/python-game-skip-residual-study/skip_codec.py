"""SR01 bounded zero/DC/full coefficient coding and P-only residual pruning.

Same Q14 predictor/quantizer as GM01. New plane syntax chooses actual complete
dense CP02 bytes or a 2-bit zero/DC/full map, DC int16 values and compact CP02
full blocks. Optional P-only pruning bounds reconstructed YUV error per block
against the quantized GM baseline; scale8 priority blocks are never pruned.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import struct
import sys
import time
import zlib
import numpy as np

HERE=Path(__file__).resolve().parent
for folder in ('python-game-codec-study','python-game-sparse-study'):
    sys.path.insert(0,str(HERE.parent/folder))
import game_codec as gm
import fast_codec

MAGIC=b'SR01'
HEADER=gm.HEADER
PLANE=struct.Struct('<4sBIIII')
PLANE_MAGIC=b'SP01'
LEVELS=(0,2,4)
CAP=49152


def ms(start):return (time.perf_counter_ns()-start)/1e6
def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def tag(packet):return zlib.crc32(packet[:-4])


def classifications(coeff):
    flat=coeff.reshape(len(coeff),64)
    full=np.any(flat[:,1:]!=0,axis=1)
    dc=~full & (flat[:,0]!=0)
    modes=np.where(full,2,np.where(dc,1,0)).astype(np.uint8)
    return modes,dc,full


def pack_modes(modes):
    padded=np.pad(modes,(0,(-len(modes))%4))
    return ((padded[::4]<<6)|(padded[1::4]<<4)|(padded[2::4]<<2)|padded[3::4]).tobytes()


def encode_plane(coeff,blocks_w,*,structured=True):
    dense=gm.token_coeff.encode_coefficients(coeff,blocks_w)
    n=len(coeff)
    d=PLANE.pack(PLANE_MAGIC,0,n,0,0,len(dense))+dense
    if not structured:return d,dict(mode='dense',dense_bytes=len(d),split_bytes=None,selected_bytes=len(d))
    modes,dc,full=classifications(coeff)
    mapped=pack_modes(modes)
    dcdata=coeff[dc,0,0].astype('<i2').tobytes()
    full_data=gm.token_coeff.encode_coefficients(coeff[full],1) if np.any(full) else b''
    s=PLANE.pack(PLANE_MAGIC,1,n,len(mapped),int(dc.sum()),len(full_data))+mapped+dcdata+full_data
    packet=s if len(s)<len(d) else d
    return packet,dict(mode='split' if packet is s else 'dense',dense_bytes=len(d),split_bytes=len(s),
                       selected_bytes=len(packet),zero_blocks=int((modes==0).sum()),
                       dc_blocks=int(dc.sum()),full_blocks=int(full.sum()),actual_candidates=2)


def decode_plane(packet,n,blocks_w):
    if type(packet) is not bytes or len(packet)<PLANE.size:raise ValueError('SR01 plane truncated/type')
    magic,mode,count,nmap,ndc,nfull=PLANE.unpack_from(packet)
    if magic!=PLANE_MAGIC or count!=n or mode not in (0,1):raise ValueError('SR01 plane identity')
    if mode==0:
        if nmap or ndc or len(packet)!=PLANE.size+nfull:raise ValueError('SR01 dense plane lengths')
        return gm.word_coeff.decode_coefficients(packet[PLANE.size:],n,blocks_w)
    if nmap!=(n+3)//4 or ndc>n or len(packet)!=PLANE.size+nmap+2*ndc+nfull:
        raise ValueError('SR01 split plane lengths')
    raw=np.frombuffer(packet[PLANE.size:PLANE.size+nmap],np.uint8)
    modes=np.stack(((raw>>6)&3,(raw>>4)&3,(raw>>2)&3,raw&3),axis=1).reshape(-1)
    if np.any(modes[:n]>2) or np.any(modes[n:]):raise ValueError('SR01 modes/padding')
    modes=modes[:n];dc=modes==1;full=modes==2
    if int(dc.sum())!=ndc or bool(nfull)!=bool(np.any(full)):raise ValueError('SR01 split counts')
    coeff=np.zeros((n,8,8),np.int16);start=PLANE.size+nmap
    values=np.frombuffer(packet[start:start+ndc*2],dtype='<i2')
    if np.any(values==0) or np.any(np.abs(values.astype(np.int32))>gm.ft.MAX_COEFF):
        raise ValueError('SR01 DC values')
    coeff[dc,0,0]=values
    if np.any(full):
        decoded=gm.word_coeff.decode_coefficients(packet[start+ndc*2:],int(full.sum()),1)
        if np.any(~np.any(decoded.reshape(len(decoded),64)[:,1:]!=0,axis=1)):
            raise ValueError('SR01 full block must contain AC')
        coeff[full]=decoded
    return coeff


def prune(coeff,scale_map,w,h,plane,limit):
    """Actual Q14 inverse error check; all work belongs to measured encode."""
    result=coeff.copy();scales=gm.roi.block_scales(scale_map,w,h,plane)
    protected=scales==8
    if plane:
        # Frozen color conversion bilinearly interpolates chroma right/down.
        # Protect that one-sample halo as whole chroma blocks so last odd
        # priority pixels cannot read a pruned neighbor across the ROI edge.
        priority=scale_map==8
        halo=priority.copy()
        halo[:,1:]|=priority[:,:-1]
        halo[1:,:]|=priority[:-1,:]
        halo[1:,1:]|=priority[:-1,:-1]
        protected=halo.reshape(-1)
    eligible=~protected
    stats=dict(eligible=int(eligible.sum()),protected=int((~eligible).sum()),zeroed=0,dc_only=0,
               max_reconstructed_yuv_delta=0,checked_blocks=0)
    if not limit or not np.any(eligible):return result,stats
    indices=np.flatnonzero(eligible)
    tables=gm.roi.block_tables(scale_map,w,h,plane)[indices]
    original=gm.ft.inverse(coeff[indices].astype(np.int64)*tables)
    dc=fast_codec.dc_inverse(coeff[indices,0,0].astype(np.int64)*tables[:,0,0])[:,None,None]
    zero_ok=np.max(np.abs(original),axis=(1,2))<=limit
    dc_ok=~zero_ok & (np.max(np.abs(original-dc),axis=(1,2))<=limit)
    selected=result[indices].copy()
    selected[zero_ok]=0
    selected[dc_ok,0,1:]=0
    selected[dc_ok,1:,:]=0
    result[indices]=selected
    changed=np.any(result[indices]!=coeff[indices],axis=(1,2))
    if np.any(changed):
        actual=gm.ft.inverse(result[indices[changed]].astype(np.int64)*tables[changed])
        maximum=int(np.max(np.abs(actual-original[changed])))
        assert maximum<=limit
    else:maximum=0
    stats.update(zeroed=int(np.sum(zero_ok&changed)),dc_only=int(np.sum(dc_ok&changed)),
                 max_reconstructed_yuv_delta=maximum,checked_blocks=len(indices))
    assert np.array_equal(result[~eligible],coeff[~eligible])
    return result,stats


@dataclass(frozen=True)
class Decision:
    packet:bytes|None
    candidate_bytes:int
    service_ms:float
    analyze_ms:float
    candidate_ms:float
    commit_ms:float
    key:bool
    level:int
    planes:tuple
    pruning:tuple
    @property
    def accepted(self):return self.packet is not None


class Encoder(gm.Encoder):
    def __init__(self,epoch=1,window=2,*,profile='exact',limit=0,frame_cap=CAP):
        super().__init__(epoch,window)
        if profile not in ('dense','exact','prune') or type(limit) is not int or limit not in LEVELS:
            raise ValueError('SR01 profile/limit')
        if profile!='prune' and limit:raise ValueError('SR01 exact profile threshold')
        if type(frame_cap) is not int or not 1<=frame_cap<=CAP:raise ValueError('SR01 cap')
        self.profile,self.limit,self.frame_cap=profile,limit,frame_cap

    def encode_sr_candidate(self,p,scale_map):
        start=time.perf_counter_ns();self._check_prepared(p)
        if p.dx or p.dy:raise ValueError('SR01 zero-motion profile required')
        mapped=gm._readonly(gm.roi.check_map(scale_map,p.width,p.height))
        coefficients=[];payloads=[];details=[];pruning=[]
        level=self.limit if self.profile=='prune' and not p.key else 0
        for i,raw in enumerate(p.raw_coefficients):
            c=gm.ft.round_quantize(raw,gm.roi.block_tables(mapped,p.width,p.height,i))
            if np.any(np.abs(c)>gm.ft.MAX_COEFF):raise ValueError('SR01 coefficients')
            c=c.astype(np.int16)
            c,stats=prune(c,mapped,p.width,p.height,i,level)
            c.setflags(write=False);coefficients.append(c);pruning.append(stats)
            pw=p.width if i==0 else p.width//2
            payload,info=encode_plane(c,(pw+7)//8,structured=self.profile!='dense')
            payloads.append(payload);details.append(info)
        mw,mh=gm.roi.geometry(p.width,p.height);mapbytes=gm.roi.pack_map(mapped)
        flags=int(p.key)|(LEVELS.index(level)<<1)
        body=HEADER.pack(MAGIC,1,flags,p.epoch,p.frame_id,p.reference_id,p.width,p.height,
                         0,0,mw,mh,len(mapbytes),*(len(a) for a in payloads))+mapbytes+b''.join(payloads)
        candidate=gm.Candidate(p,mapped,tuple(coefficients),seal(body),ms(start))
        self._candidates.add(candidate)
        return candidate,tuple(details),tuple(pruning),level

    def prepare(self,rgb,frame_id,*,scale_map,force_key=False):
        start=time.perf_counter_ns();p=self.analyze(rgb,frame_id,force_key=force_key,mode='zero')
        candidate,planes,pruning,level=self.encode_sr_candidate(p,scale_map)
        commit_ms=0.0;packet=None
        if len(candidate.packet)<=self.frame_cap:
            began=time.perf_counter_ns();packet=self.commit(candidate);commit_ms=ms(began)
        return Decision(packet,len(candidate.packet),ms(start),p.analyze_ms,candidate.candidate_ms,
                        commit_ms,p.key,level,planes,pruning)

    def expected_hash(self,frame_id):
        row=self.pending[frame_id]
        if row['expected_rgb_sha256'] is None:
            if row['key']:rgb=gm.ft.planes_to_rgb(row['planes'])
            else:
                rx=Receiver(self.epoch,self.frame_cap);rx.anchor_id,rx._anchor=self.anchor_id,self._anchor
                rgb,_=rx.receive(row['packet'])
            row['expected_rgb_sha256']=hashlib.sha256(rgb.tobytes()).hexdigest()
        return row['expected_rgb_sha256']

    def ack(self,frame_id,*,epoch,content_crc):
        if epoch!=self.epoch or frame_id not in self.pending:return False
        if content_crc!=tag(self.pending[frame_id]['packet']):return False
        return super().ack(frame_id,epoch=epoch)


def parse(packet,epoch,frame_cap=CAP):
    if type(packet) is not bytes or not HEADER.size+4<=len(packet)<=frame_cap:
        raise ValueError('SR01 size/type/cap')
    fields=HEADER.unpack_from(packet)
    magic,version,flags,session,frame,ref,w,h,dx,dy,mw,mh,nmap,*lengths=fields
    if (magic!=MAGIC or version!=1 or flags not in (0,1,2,4) or session!=epoch or session==gm.NO_REF
            or frame==gm.NO_REF or dx or dy or (mw,mh)!=gm.roi.geometry(w,h)
            or bool(flags&1)!=(ref==gm.NO_REF) or (not flags&1 and ref>=frame)):
        raise ValueError('SR01 identity/profile')
    if nmap!=(mw*mh+3)//4 or len(packet)!=HEADER.size+nmap+sum(lengths)+4:
        raise ValueError('SR01 exact lengths')
    if tag(packet)!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('SR01 CRC')
    pos=HEADER.size;scale_map=gm.roi.unpack_map(packet[pos:pos+nmap],mw,mh);pos+=nmap
    coefficients=[]
    for i,length in enumerate(lengths):
        pw,ph=(w,h) if i==0 else (w//2,h//2);bw,bh=(pw+7)//8,(ph+7)//8;n=bw*bh
        if not PLANE.size<=length<=PLANE.size+(n+3)//4+2*n+128*n+gm.word_coeff.PAYLOAD_OVERHEAD:
            raise ValueError('SR01 plane length bound')
        coefficients.append(decode_plane(packet[pos:pos+length],n,bw));pos+=length
    return dict(epoch=session,frame_id=frame,key=bool(flags&1),reference_id=ref,width=w,height=h,
                coefficients=tuple(coefficients),scale_map=scale_map,level=LEVELS[flags>>1])


class Receiver:
    def __init__(self,epoch=1,frame_cap=CAP):
        if type(epoch) is not int or not 0<=epoch<gm.NO_REF:raise ValueError('SR01 epoch')
        if type(frame_cap) is not int or not 1<=frame_cap<=CAP:raise ValueError('SR01 receive cap')
        self.epoch,self.frame_cap=epoch,frame_cap
        self.anchor_id,self._anchor=None,None;self.last_frame_id=-1

    def receive(self,packet):
        p=parse(packet,self.epoch,self.frame_cap);w,h=p['width'],p['height'];frame=p['frame_id']
        if frame<=self.last_frame_id:raise ValueError('SR01 replay')
        if p['key']:
            prediction=tuple(np.full(s,128,np.int16) for s in ((h,w),(h//2,w//2),(h//2,w//2)))
        else:
            if self._anchor is None or p['reference_id']!=self.anchor_id or self._anchor[0].shape!=(h,w):
                raise ValueError('SR01 missing ACKed key')
            prediction=self._anchor
        planes=fast_codec.reconstruct(p['coefficients'],prediction,p['scale_map'],w,h)
        rgb=gm.ft.planes_to_rgb(planes)
        if p['key']:self.anchor_id,self._anchor=frame,planes
        self.last_frame_id=frame
        return rgb,dict(epoch=self.epoch,frame_id=frame,key=p['key'],reference_id=None if p['key'] else p['reference_id'],
                        anchor_id=self.anchor_id,level=p['level'],content_crc=tag(packet),bytes=len(packet))
