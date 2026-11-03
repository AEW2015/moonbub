"""Exact CP02 length without Rice strings; GM01 admission before serialization."""
from dataclasses import dataclass
from pathlib import Path
import struct
import sys
import time
import weakref
import zlib
import numpy as np

HERE=Path(__file__).resolve().parent
for directory in ('python-game-codec-study','python-game-rate-study'):
    sys.path.insert(0,str(HERE.parent/directory))
import game_codec as gc
import controller as rate
cc=gc.token_coeff.frozen


def _rice_bits(values,k,escape):
    return int(np.where((values>>k)<15,(values>>k)+1+k,15+escape).sum())


def coefficient_size(coefficients,blocks_w):
    a=cc._check(coefficients,blocks_w)
    zig=a.reshape(-1,64)[:,cc.frozen.ZIGZAG].astype(np.int32)
    delta=zig[:,0].copy();delta[1:]-=zig[:-1,0];delta[::blocks_w]=zig[::blocks_w,0]
    mapped_dc=cc._mapped(delta);kd=cc._best_k(mapped_dc,13,14)
    dc_bytes=1+(_rice_bits(mapped_dc,kd,14)+7)//8
    blocks,indices=np.nonzero(zig[:,1:]);positions=indices+1
    values=zig[blocks,positions];mapped=cc._mapped(values)-1
    bands=np.where(positions<=5,0,np.where(positions<=20,1,2))
    ks=[cc._best_k(mapped[bands==band],11,12) for band in range(3)]
    previous=np.r_[0,positions[:-1]].astype(np.int32)
    if len(blocks):previous[np.r_[True,blocks[1:]!=blocks[:-1]]]=0
    runs=positions-previous-1
    ac_bits=5*len(values)+2*int((runs//16).sum())+2*(len(a)-int((positions==63).sum()))
    ac_bits+=sum(_rice_bits(mapped[bands==band],ks[band],12) for band in range(3))
    ac_bytes=3+(ac_bits+7)//8
    raw=len(a)*128
    return cc.PAYLOAD_OVERHEAD+min(raw,dc_bytes+ac_bytes)


@dataclass(frozen=True,eq=False)
class SizedCandidate:
    prepared: gc.Prepared
    scale_map: np.ndarray
    coefficients: tuple
    plane_sizes: tuple
    packet_size: int
    preflight_ms: float


class Encoder(gc.Encoder):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self._sized=weakref.WeakSet()

    def estimate_candidate(self,p,scale_map):
        started=time.perf_counter_ns();self._check_prepared(p)
        mapped=gc._readonly(gc.roi.check_map(scale_map,p.width,p.height));coefficients=[];sizes=[]
        for i,raw in enumerate(p.raw_coefficients):
            c=gc.ft.round_quantize(raw,gc.roi.block_tables(mapped,p.width,p.height,i))
            if np.any(np.abs(c)>gc.ft.MAX_COEFF):raise ValueError('GM01 coefficient domain')
            c=c.astype(np.int16);c.setflags(write=False);coefficients.append(c)
            pw=p.width if i==0 else p.width//2
            sizes.append(coefficient_size(c,(pw+7)//8))
        mw,mh=gc.roi.geometry(p.width,p.height)
        total=gc.HEADER.size+4+(mw*mh+3)//4+sum(sizes)
        result=SizedCandidate(p,mapped,tuple(coefficients),tuple(sizes),total,(time.perf_counter_ns()-started)/1e6)
        self._sized.add(result);return result

    def emit_sized(self,sized):
        if not isinstance(sized,SizedCandidate) or sized not in self._sized:raise ValueError('foreign sized candidate')
        p=sized.prepared;self._check_prepared(p);started=time.perf_counter_ns();payloads=[]
        for i,c in enumerate(sized.coefficients):
            pw=p.width if i==0 else p.width//2
            data=gc.token_coeff.encode_coefficients(c,(pw+7)//8)
            assert len(data)==sized.plane_sizes[i],'exact preflight mismatch'
            payloads.append(data)
        mw,mh=gc.roi.geometry(p.width,p.height);mapped=gc.roi.pack_map(sized.scale_map)
        body=gc.HEADER.pack(gc.MAGIC,1,int(p.key),p.epoch,p.frame_id,p.reference_id,p.width,p.height,
                            p.dx,p.dy,mw,mh,len(mapped),*(len(x) for x in payloads))+mapped+b''.join(payloads)
        packet=body+struct.pack('<I',zlib.crc32(body));assert len(packet)==sized.packet_size
        result=gc.Candidate(p,sized.scale_map,sized.coefficients,packet,(time.perf_counter_ns()-started)/1e6)
        self._candidates.add(result);return result


class Controller(rate.Controller):
    def __init__(self,encoder=None,config=None):super().__init__(encoder or Encoder(),config)

    def prepare(self,rgb,frame_id,*,force_key=False,reuse=True):
        if not reuse:raise ValueError('size controller always reuses its one analysis')
        started=time.perf_counter_ns();maps=self.maps(rgb);map_ms=(time.perf_counter_ns()-started)/1e6
        p=self.encoder.analyze(rgb,frame_id,force_key=force_key,mode=self.config.motion_mode)
        attempts=[];selected=None;counts=None;packet=None;commit_ms=0.0
        for label,mapped in maps:
            sized=self.encoder.estimate_candidate(p,mapped);fits=sized.packet_size<=self.config.frame_cap
            counts={str(v):int((mapped==v).sum()) for v in (8,16,32)}
            attempts.append(dict(label=label,bytes=sized.packet_size,fits=fits,preflight_ms=sized.preflight_ms,
                                 serialized=False,scale_counts=counts))
            if fits:
                begin=time.perf_counter_ns();candidate=self.encoder.emit_sized(sized)
                attempts[-1]['serialization_ms']=(time.perf_counter_ns()-begin)/1e6;attempts[-1]['serialized']=True
                begin=time.perf_counter_ns();packet=self.encoder.commit(candidate)
                commit_ms=(time.perf_counter_ns()-begin)/1e6;selected=label;break
        return rate.Decision(packet,selected,tuple(attempts),1,3,(time.perf_counter_ns()-started)/1e6,
                             commit_ms,map_ms,counts if packet is not None else None)
