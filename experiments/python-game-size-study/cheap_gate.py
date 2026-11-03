"""Conservative CP02 minimum-byte gate; exact emission only when not ruled out."""
from dataclasses import dataclass
import struct
import time
import weakref
import zlib
import numpy as np
import preflight as exact

gc,rate,cc=exact.gc,exact.rate,exact.cc


def _lower_checked(a):
    n=len(a);flat=a.reshape(n,64)
    nnz=int(np.count_nonzero(flat[:,1:]));last=int(np.count_nonzero(flat[:,int(gc.ft.ZIGZAG[-1])]))
    dc_bytes=1+(n+7)//8
    ac_bytes=3+(6*nnz+2*(n-last)+7)//8
    return cc.PAYLOAD_OVERHEAD+min(128*n,dc_bytes+ac_bytes)


def coefficient_lower_bound(coefficients,blocks_w):
    return _lower_checked(cc._check(coefficients,blocks_w))


@dataclass(frozen=True,eq=False)
class Plan:
    prepared: gc.Prepared
    scale_map: np.ndarray
    coefficients: tuple
    lower_plane_sizes: tuple
    lower_packet_size: int
    gate_ms: float


class Encoder(gc.Encoder):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self._plans=weakref.WeakSet()

    def gate(self,p,scale_map):
        started=time.perf_counter_ns();self._check_prepared(p)
        mapped=gc._readonly(gc.roi.check_map(scale_map,p.width,p.height));coefficients=[];sizes=[]
        for i,raw in enumerate(p.raw_coefficients):
            c=gc.ft.round_quantize(raw,gc.roi.block_tables(mapped,p.width,p.height,i))
            if np.any(np.abs(c)>gc.ft.MAX_COEFF):raise ValueError('GM01 coefficient domain')
            c=c.astype(np.int16);c.setflags(write=False);coefficients.append(c)
            sizes.append(_lower_checked(c))
        mw,mh=gc.roi.geometry(p.width,p.height)
        result=Plan(p,mapped,tuple(coefficients),tuple(sizes),gc.HEADER.size+4+(mw*mh+3)//4+sum(sizes),
                    (time.perf_counter_ns()-started)/1e6)
        self._plans.add(result);return result

    def emit_gate(self,plan):
        if not isinstance(plan,Plan) or plan not in self._plans:raise ValueError('foreign gate plan')
        p=plan.prepared;self._check_prepared(p);started=time.perf_counter_ns();payloads=[]
        for i,c in enumerate(plan.coefficients):
            pw=p.width if i==0 else p.width//2
            data=gc.token_coeff.encode_coefficients(c,(pw+7)//8)
            assert len(data)>=plan.lower_plane_sizes[i];payloads.append(data)
        mw,mh=gc.roi.geometry(p.width,p.height);mapped=gc.roi.pack_map(plan.scale_map)
        body=gc.HEADER.pack(gc.MAGIC,1,int(p.key),p.epoch,p.frame_id,p.reference_id,p.width,p.height,
                            p.dx,p.dy,mw,mh,len(mapped),*(len(x) for x in payloads))+mapped+b''.join(payloads)
        packet=body+struct.pack('<I',zlib.crc32(body));assert len(packet)>=plan.lower_packet_size
        result=gc.Candidate(p,plan.scale_map,plan.coefficients,packet,(time.perf_counter_ns()-started)/1e6)
        self._candidates.add(result);return result


class Controller(rate.Controller):
    def __init__(self,encoder=None,config=None):super().__init__(encoder or Encoder(),config)

    def prepare(self,rgb,frame_id,*,force_key=False,reuse=True):
        if not reuse:raise ValueError('gate always reuses analysis')
        started=time.perf_counter_ns();maps=self.maps(rgb);map_ms=(time.perf_counter_ns()-started)/1e6
        p=self.encoder.analyze(rgb,frame_id,force_key=force_key,mode=self.config.motion_mode)
        attempts=[];selected=None;counts=None;packet=None;commit_ms=0.0
        for label,mapped in maps:
            plan=self.encoder.gate(p,mapped)
            counts={str(v):int((mapped==v).sum()) for v in (8,16,32)}
            row=dict(label=label,lower_bytes=plan.lower_packet_size,gate_ms=plan.gate_ms,serialized=False,scale_counts=counts)
            if plan.lower_packet_size>self.config.frame_cap:
                row.update(bytes=None,fits=False,provably_rejected=True);attempts.append(row);continue
            begin=time.perf_counter_ns();candidate=self.encoder.emit_gate(plan)
            row.update(bytes=len(candidate.packet),fits=len(candidate.packet)<=self.config.frame_cap,
                       serialized=True,provably_rejected=False,serialization_ms=(time.perf_counter_ns()-begin)/1e6)
            attempts.append(row)
            if row['fits']:
                begin=time.perf_counter_ns();packet=self.encoder.commit(candidate)
                commit_ms=(time.perf_counter_ns()-begin)/1e6;selected=label;break
        return rate.Decision(packet,selected,tuple(attempts),1,3,(time.perf_counter_ns()-started)/1e6,
                             commit_ms,map_ms,counts if packet is not None else None)
