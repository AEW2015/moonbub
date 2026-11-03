"""Actual selected-frame Python service replay in a finite MA01 stage model.

Preparation and optionally receiver service are measured per selected packet,
then charged to virtual serialized stages. Calls execute offline; this is not
concurrent wall-clock throughput or target timing. Integrity oracles/metrics
are deliberately outside charged preparation/receive timing.
"""
from __future__ import annotations
import collections
import dataclasses
import hashlib
import heapq
import math
import time
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-anchor-study'))
from anchor_codec import AnchorEncoder, AnchorReceiver, mt
sys.path.insert(0,str(HERE.parent/'python-coupled-study'))
from validation import summarize_presentation,validate_conservation
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'python-codec-study'))
import corpus


@dataclasses.dataclass(frozen=True)
class Config:
    fps: float = 30
    quant_scale: int = 8
    encoder_profile: str = "baseline"
    motion_mode: str = "zero"
    decoder_service: str = "assumed"
    decode_ms: float = 8
    link_mbps: float = 8
    qspi_mbps: float = 160
    refresh_hz: float = 60
    feedback_ms: float = 10
    frame_cap: int = 49152
    window: int = 2
    refresh_period: int = 30
    ack_timeout_ms: float = 200
    max_age_before_encode_ms: float = 100
    drain_ms: float = 1000
    data_loss_ids: tuple[int, ...] = ()
    ack_loss_ids: tuple[int, ...] = ()
    corruption_ids: tuple[int, ...] = ()
    cap_backoff_max: int | None = None


def wire_bytes(size):
    return size+68*math.ceil(size/1024)


def _summary(values):
    if not values: return dict(p50=None, p95=None, max=None)
    a=sorted(values)
    return dict(p50=a[(len(a)-1)//2],p95=a[math.ceil(.95*len(a))-1],max=a[-1])


def encoder_class(profile):
    if profile=='baseline':return AnchorEncoder
    if profile=='fast_p':
        sys.path.insert(0,str(HERE.parent/'python-fast-entropy-study'))
        from fast_anchor import Encoder
        return Encoder
    if profile=='fast_key':
        sys.path.insert(0,str(HERE.parent/'python-key-prepare-study'))
        from key_encoder import Encoder
        return Encoder
    raise ValueError('unknown encoder profile')


def run(frames, manifest, cfg=None, *, encoder_factory=None, receiver_factory=None,
        clock_ns=time.perf_counter_ns):
    cfg = cfg or Config()
    positive=(cfg.fps,cfg.link_mbps,cfg.qspi_mbps,cfg.refresh_hz,cfg.ack_timeout_ms)
    nonnegative=(cfg.decode_ms,cfg.feedback_ms,cfg.drain_ms,cfg.max_age_before_encode_ms)
    if (not frames or any(not math.isfinite(x) or x<=0 for x in positive)
            or any(not math.isfinite(x) or x<0 for x in nonnegative)
            or type(cfg.frame_cap) is not int or cfg.frame_cap<=0 or type(cfg.refresh_period) is not int or cfg.refresh_period<0):
        raise ValueError('invalid timing/storage/corpus configuration')
    if any(type(i) is not int or not 0<=i<len(frames) for i in (*cfg.data_loss_ids,*cfg.ack_loss_ids,*cfg.corruption_ids)):
        raise ValueError('fault ID outside capture list')
    if cfg.cap_backoff_max is not None and (type(cfg.cap_backoff_max) is not int or not cfg.quant_scale<=cfg.cap_backoff_max<=128):
        raise ValueError('cap backoff bound')
    if cfg.encoder_profile not in ('baseline','fast_p','fast_key') or cfg.decoder_service not in ('assumed','python_wall') or cfg.motion_mode not in ('zero','global'):
        raise ValueError('unknown service/profile')
    factory=encoder_factory or encoder_class(cfg.encoder_profile)
    enc,dec=factory(window=cfg.window),(receiver_factory or AnchorReceiver)()
    def elapsed(begin):
        value=(clock_ns()-begin)/1e6
        if not math.isfinite(value) or value<0:raise ValueError('invalid measured service')
        return value
    captures=[i*1000/cfg.fps for i in range(len(frames))]
    end=len(frames)*1000/cfg.fps; horizon=end+cfg.drain_ms
    events=[]; sequence=0
    def event(at,kind,data=None):
        nonlocal sequence
        sequence+=1
        heapq.heappush(events,(at,1 if kind=='vblank' else 0,sequence,kind,data))
    for i,t in enumerate(captures): event(t,'capture',i)
    for i in range(math.floor(horizon*cfg.refresh_hz/1000)+1):event(i*1000/cfg.refresh_hz,'vblank')
    waiting=None; encoding=network=qspi=decoder=None
    q_network=collections.deque();q_qspi=collections.deque();q_decode=collections.deque()
    slots=[None]*cfg.window
    framebuffers=[dict(frame=-1,roles={'front'}),dict(frame=None,roles=set()),dict(frame=None,roles=set())]
    front=0; pending=None
    tx={}; committed=[]; presented=[]; dropped=[]; ack_events=[]; allocations=[]
    last_key_capture=None; now=0.; peak_slots=peak_pending=peak_buffers=peak_packet_bytes=0
    active_scale=cfg.quant_scale;force_refresh=False

    def drop(i,reason):dropped.append(dict(id=i,at_ms=now,reason=reason))
    def release(slot):
        frame=slots[slot]
        allocations.append(dict(kind='release',slot=slot,id=frame,at_ms=now));slots[slot]=None
        tx[frame].pop('packet',None);tx[frame].pop('expected',None)
    def refresh_due(i):
        return force_refresh or (cfg.refresh_period>0 and last_key_capture is not None and i-last_key_capture>=cfg.refresh_period)
    def pump():
        nonlocal waiting,encoding,network,qspi,decoder,last_key_capture,force_refresh
        changed=True
        while changed:
            changed=False
            if decoder is None and q_decode:
                free=next((i for i,b in enumerate(framebuffers) if not b['roles']),None)
                if free is not None:
                    slot=q_decode.popleft();frame=slots[slot]
                    framebuffers[free]=dict(frame=frame,roles={'decoding'})
                    decoder=(slot,free)
                    record=tx[frame]
                    packet=record['packet']
                    if frame in cfg.corruption_ids:packet=packet[:-1]+bytes([packet[-1]^1])
                    began=clock_ns()
                    try:
                        rgb,info=dec.receive(packet)
                    except ValueError:
                        record['receive_error']=True
                    else:
                        record['decoded_rgb'],record['decoded_info']=rgb,info
                    record['decode_wall_ms']=elapsed(began)
                    record['decode_started_ms']=now
                    record['decode_service_ms']=record['decode_wall_ms'] if cfg.decoder_service=='python_wall' else cfg.decode_ms
                    event(now+record['decode_service_ms'],'decode_done',decoder);changed=True
            if qspi is None and q_qspi:
                slot=q_qspi.popleft();qspi=slot
                event(now+len(tx[slots[slot]]['packet'])*8/(cfg.qspi_mbps*1000),'qspi_done',slot);changed=True
            if network is None and q_network:
                slot=q_network.popleft();network=slot
                frame=slots[slot];tx[frame]['send_ms']=now
                event(now+wire_bytes(len(tx[frame]['packet']))*8/(cfg.link_mbps*1000),'network_done',slot)
                event(now+cfg.ack_timeout_ms,'timeout',frame);changed=True
            if encoding is None and waiting is not None:
                frame=waiting;key=refresh_due(frame)
                if now-captures[frame]>cfg.max_age_before_encode_ms:
                    waiting=None;drop(frame,'stale_before_encode');changed=True;continue
                free=next((i for i,owner in enumerate(slots) if owner is None),None)
                if free is not None and enc.can_prepare(key):
                    waiting=None; started=clock_ns()
                    packet=enc.prepare(frames[frame],frame,quant_scale=active_scale,force_key=key,mode=cfg.motion_mode)
                    wall=elapsed(started)
                    fields=mt.HEADER.unpack_from(packet);is_key=fields[4]==mt.NO_REF
                    if is_key:last_key_capture=frame;force_refresh=False
                    tx[frame]=dict(packet=packet,expected=enc.expected_hash(frame),bytes=len(packet),
                                   key=is_key,reference_id=None if is_key else fields[4],
                                   quant_scale=active_scale,encode_started_ms=now,encode_wall_ms=wall,encode_service_ms=wall)
                    if len(packet)>cfg.frame_cap:
                        tx[frame]['cap_rejected']=True
                        tx[frame].pop('packet');tx[frame].pop('expected')
                    slots[free]=frame
                    allocations.append(dict(kind='acquire',slot=free,id=frame,at_ms=now))
                    encoding=free;event(now+wall,'encode_done',free);changed=True

    wall_started=time.perf_counter()
    while events:
        at,_,_,kind,value=heapq.heappop(events)
        if at>horizon+1e-9:break
        now=at
        if kind=='capture':
            if waiting is not None:drop(waiting,'latest_replaced')
            waiting=value
        elif kind=='encode_done':
            assert encoding==value
            encoding=None
            frame=slots[value]
            if tx[frame].get('cap_rejected'):
                enc.expire(frame);drop(frame,'cap');release(value)
                if cfg.cap_backoff_max is not None:
                    active_scale=min(cfg.cap_backoff_max,active_scale*2);force_refresh=True
            else:q_network.append(value)
        elif kind=='network_done':
            assert network==value
            network=None;frame=slots[value]
            if frame in cfg.data_loss_ids:drop(frame,'data_loss');release(value)
            else:q_qspi.append(value)
        elif kind=='qspi_done':
            assert qspi==value
            qspi=None;q_decode.append(value)
        elif kind=='decode_done':
            assert decoder==value
            slot,back=value;frame=slots[slot];record=tx[frame]
            if record.get('receive_error'):
                framebuffers[back]['roles'].clear();drop(frame,'receiver_rejected')
                event(now+cfg.feedback_ms,'nack',frame)
            else:
                rgb=record.pop('decoded_rgb');info=record.pop('decoded_info')
                assert hashlib.sha256(rgb.tobytes()).hexdigest()==record['expected']
                display=corpus.expand565(corpus.rgb565(rgb))
                rect=tuple(manifest.get('active_rects',[(0,0,rgb.shape[1],rgb.shape[0])]*len(frames))[frame])
                mse=corpus.metrics(frames[frame],display,rect)['active']['mse']
                framebuffers[back]['roles'].remove('decoding')
                if pending is not None:
                    old=framebuffers[pending]['frame'];framebuffers[pending]['roles'].remove('pending');drop(old,'pending_superseded')
                pending=back;framebuffers[back]['roles'].add('pending')
                row=dict(id=frame,at_ms=now,anchor=dec.anchor_id,key=record['key'],bytes=record['bytes'],active_rgb565_mse=mse)
                committed.append(row)
                if frame not in cfg.ack_loss_ids:event(now+cfg.feedback_ms,'ack',frame)
                else:ack_events.append(dict(id=frame,at_ms=now,kind='ACK_lost'))
            release(slot);decoder=None
        elif kind=='ack':
            accepted=enc.ack(value,epoch=1)
            ack_events.append(dict(id=value,at_ms=now,kind='ack',accepted=accepted))
        elif kind=='nack':enc.expire(value)
        elif kind=='timeout':
            if enc.expire(value):ack_events.append(dict(id=value,at_ms=now,kind='timeout'))
        elif kind=='vblank' and pending is not None:
            framebuffers[front]['roles'].remove('front');front=pending;pending=None
            framebuffers[front]['roles'].remove('pending');framebuffers[front]['roles'].add('front')
            frame=framebuffers[front]['frame']
            presented.append(dict(id=frame,at_ms=now,capture_ms=captures[frame],age_ms=now-captures[frame]))
        pump()
        assert len(enc.pending)<=cfg.window
        assert sum('front' in b['roles'] for b in framebuffers)==1
        assert sum('decoding' in b['roles'] for b in framebuffers)<=1
        peak_slots=max(peak_slots,sum(x is not None for x in slots))
        peak_pending=max(peak_pending,len(enc.pending));peak_buffers=max(peak_buffers,sum(bool(b['roles']) for b in framebuffers))
        packet_bytes=sum(len(r.get('packet',b'')) for r in tx.values())
        assert packet_bytes<=cfg.window*cfg.frame_cap
        peak_packet_bytes=max(peak_packet_bytes,packet_bytes)
    assert len({r['id'] for r in presented})==len(presented)
    assert [r['id'] for r in presented]==sorted(r['id'] for r in presented)
    steady_start,steady_end=500,end-500
    steady=[r for r in presented if steady_start<=r['at_ms']<steady_end] if end>=2000 else []
    used=[r for r in tx.values() if 'send_ms' in r]
    capture_rows=[dict(id=i,capture_ms=t) for i,t in enumerate(captures)]
    metrics=summarize_presentation(capture_rows,presented,end,(steady_start,steady_end) if end>=2000 else None)
    pending_ids=set(range(len(frames)))-{r['id'] for r in presented}-{r['id'] for r in dropped}
    validate_conservation(range(len(frames)),(r['id'] for r in presented),(r['id'] for r in dropped),pending_ids)
    service_summary={}
    for kind in ('key','p'):
        rows=[r for r in tx.values() if bool(r['key'])==(kind=='key')]
        for stage in ('encode','decode'):
            values=[r[stage+'_wall_ms'] for r in rows if stage+'_wall_ms' in r]
            service_summary[kind+'_'+stage+'_ms']=dict(n=len(values),mean=float(np.mean(values)) if values else None,**_summary(values))
    return dict(config=dataclasses.asdict(cfg),metrics=metrics,service_summary=service_summary,pending_ids=sorted(pending_ids),scope='Actual selected MA01 packets with per-call Python prepare service replay; receiver is assumed8ms or measured per-call Python receive; not concurrent realtime/native/FPGA FPS',
                capture_count=len(frames),capture_window_ms=[0,end],window_kind='[start,end)',
                prepared=len(tx),transmitted=len(used),committed=len(committed),presented_eventual=len(presented),
                presented_strict=sum(r['at_ms']<end-1e-9 for r in presented),
                steady_window_ms=[steady_start,steady_end] if end>=2000 else None,
                steady_count=len(steady) if end>=2000 else None,
                steady_fps=len(steady)*1000/(steady_end-steady_start) if end>=2000 else None,
                age_ms=_summary([r['age_ms'] for r in presented]),
                steady_age_ms=_summary([r['age_ms'] for r in steady]),
                transmitted_wire_bytes=sum(wire_bytes(r['bytes']) for r in used),
                transmitted_mbps_over_capture_window=sum(wire_bytes(r['bytes']) for r in used)*8/(end*1000),
                keyframes=sum(r['key'] for r in used),
                drops_by_reason=dict(collections.Counter(r['reason'] for r in dropped)),
                drops=dropped,commits=committed,presented=presented,ack_events=ack_events,
                packets=[dict(id=i,**{k:v for k,v in r.items() if k not in ('packet','expected','decoded_rgb','decoded_info')}) for i,r in tx.items()],
                final_quant_scale=active_scale,
                peak_compressed_slots=peak_slots,peak_pending_credits=peak_pending,peak_framebuffers=peak_buffers,
                peak_retained_packet_bytes=peak_packet_bytes,
                encoder_reference_array_bytes=enc.retained_reference_bytes(),
                receiver_reference_array_bytes=0 if dec._anchor is None else sum(x.nbytes for x in dec._anchor),
                unresolved_slots=slots,unresolved_pending=list(enc.pending),waiting_at_end=waiting,
                allocation_events=allocations,python_run_wall_seconds=time.perf_counter()-wall_started)
