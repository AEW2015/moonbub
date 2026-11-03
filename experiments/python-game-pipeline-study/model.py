"""Finite actual GM01/GF02/GA01 pipeline with measured per-selected-call work.

Calls execute offline to learn their service cost. Virtual completion controls
publication, transport release and feedback. Physical ownership here is a
single-threaded software read-pin oracle, not DMA/CDC/hardware qualification.
"""
from __future__ import annotations
import collections
from dataclasses import dataclass,asdict
import hashlib
import heapq
import math
from pathlib import Path
import sys
import time

import numpy as np

HERE=Path(__file__).resolve().parent
for directory in ('python-game-codec-study','python-game-rate-study','python-game-size-study',
                  'python-game-feedback-study','python-codec-study','python-coupled-study'):
    sys.path.insert(0,str(HERE.parent/directory))
import game_codec as gc
import controller as normal_controller
import cheap_gate
import transport
import corpus
from validation import summarize_presentation,validate_conservation


@dataclass(frozen=True)
class Config:
    fps:float=30
    controller:str='normal'
    policy:str='priority'
    rectangles:tuple=((16,48,192,80),(160,352,400,80))
    decoder_service:str='assumed'
    decode_ms:float=8
    acquisition_ms:float=0
    link_mbps:float=8
    feedback_mbps:float=8
    qspi_mbps:float=160
    feedback_latency_ms:float=10
    refresh_hz:float=60
    refresh_period:int=30
    frame_cap:int=49152
    ingress_timeout_ms:float=150
    ack_timeout_ms:float=250
    preencode_age_ms:float=100
    frame_deadline_ms:float=150
    drain_ms:float=1000
    data_loss_ids:tuple=()
    corruption_ids:tuple=()
    duplicate_chunk_ids:tuple=()
    feedback_loss_ids:tuple=()
    duplicate_feedback_ids:tuple=()
    wrong_epoch_feedback_ids:tuple=()
    reverse_chunks:bool=False


def _stats(values):
    if not values:return dict(n=0,mean=None,p50=None,p95=None,max=None)
    return dict(n=len(values),mean=float(np.mean(values)),p50=float(np.percentile(values,50)),
                p95=float(np.percentile(values,95)),max=max(values))


def run(frames,manifest,cfg=None,*,controller_factory=None,receiver_factory=None,
        clock_ns=time.perf_counter_ns):
    cfg=cfg or Config()
    positive=(cfg.fps,cfg.link_mbps,cfg.feedback_mbps,cfg.qspi_mbps,cfg.refresh_hz,
              cfg.ingress_timeout_ms,cfg.ack_timeout_ms)
    nonnegative=(cfg.decode_ms,cfg.acquisition_ms,cfg.feedback_latency_ms,cfg.preencode_age_ms,
                 cfg.frame_deadline_ms,cfg.drain_ms)
    if (not frames or any(not math.isfinite(v) or v<=0 for v in positive)
        or any(not math.isfinite(v) or v<0 for v in nonnegative)
        or cfg.controller not in ('normal','gate') or cfg.decoder_service not in ('assumed','python_wall')
        or type(cfg.frame_cap) is not int or not 1<=cfg.frame_cap<=49152
        or type(cfg.refresh_period) is not int or cfg.refresh_period<0):
        raise ValueError('invalid finite-pipeline configuration')
    fault_ids=(*cfg.data_loss_ids,*cfg.corruption_ids,*cfg.duplicate_chunk_ids,*cfg.feedback_loss_ids,
               *cfg.duplicate_feedback_ids,*cfg.wrong_epoch_feedback_ids)
    if any(type(v) is not int or not 0<=v<len(frames) for v in fault_ids):raise ValueError('fault capture ID')
    profile=normal_controller.Config(frame_cap=cfg.frame_cap,policy=cfg.policy,rectangles=cfg.rectangles)
    factory=controller_factory or (normal_controller.Controller if cfg.controller=='normal' else cheap_gate.Controller)
    control=factory(config=profile);enc=control.encoder;dec=(receiver_factory or gc.Receiver)()
    ingress=transport.Reassembler(1,slots=2,max_frame=cfg.frame_cap,timeout_ms=cfg.ingress_timeout_ms)
    captures=[i*1000/cfg.fps for i in range(len(frames))]
    end=len(frames)*1000/cfg.fps;horizon=end+cfg.drain_ms
    events=[];sequence=0;now=0.0
    def event(at,kind,value=None):
        nonlocal sequence
        sequence+=1;heapq.heappush(events,(at,1 if kind=='vblank' else 0,sequence,kind,value))
    for i,t in enumerate(captures):event(t,'capture',i)
    for i in range(math.floor(horizon*cfg.refresh_hz/1000)+1):event(i*1000/cfg.refresh_hz,'vblank')
    sender=[None,None];encoding=None;waiting=None;network=None;qspi=None;decoder=None;feedback=None
    q_network=collections.deque();q_qspi=collections.deque();q_decode=collections.deque();q_feedback=collections.deque()
    framebuffers=[{'frame':-1,'roles':{'front'}},{'frame':None,'roles':set()},{'frame':None,'roles':set()}]
    front=0;pending=None;last_key_capture=None
    tx={};drops=[];presented=[];commits=[];feedback_rows=[];wire_rows=[];allocations=[];timeout_rows=[]
    outcomes={};peak_sender=peak_ingress=peak_credits=peak_roles=peak_sender_bytes=peak_ingress_bytes=peak_wire_bytes=0
    forward_bytes=reverse_bytes=0;wall_start=time.perf_counter()

    def elapsed(start):
        duration=(clock_ns()-start)/1e6
        if not math.isfinite(duration) or duration<0:raise ValueError('invalid observed service')
        return duration

    def drop(frame,reason):
        if frame in outcomes:return
        outcomes[frame]='dropped';drops.append(dict(id=frame,at_ms=now,reason=reason))

    def physical_drained(frame):
        r=tx[frame]
        return (r['encode_done'] and r.get('wire_pending',0)==0 and frame not in ingress.pending
                and not r.get('qspi_owned',False) and not r.get('decode_owned',False)
                and not r.get('queued_decode',False) and not r.get('queued_qspi',False))

    def release(frame,reason):
        r=tx[frame]
        assert physical_drained(frame),('unsafe release',frame,reason)
        slot=r['slot'];assert sender[slot]==frame
        sender[slot]=None;r['released_ms']=now;r['release_reason']=reason
        r.pop('packet',None);r.pop('expected',None)
        allocations.append(dict(kind='release',id=frame,slot=slot,at_ms=now,reason=reason))

    def request_expire(frame,reason):
        r=tx[frame];r['expire_requested']=reason
        if r.get('released_ms') is not None:return
        if physical_drained(frame):
            enc.expire(frame)
            if not r.get('decode_ok'):drop(frame,reason)
            release(frame,reason)

    def finish_expiries():
        for frame,r in tx.items():
            if r.get('ack_waiting') and r.get('released_ms') is None and physical_drained(frame):
                enc.ack(frame,epoch=1);r['ack_waiting']=False
                feedback_rows.append(dict(kind='deferred_ack_accepted',id=frame,at_ms=now))
                release(frame,'decoded_ack_after_drain')
            if r.get('expire_requested') and r.get('released_ms') is None and physical_drained(frame):
                request_expire(frame,r['expire_requested'])

    def enqueue_feedback(frame,status,reason=0):
        r=tx[frame]
        epoch=2 if frame in cfg.wrong_epoch_feedback_ids else 1
        data=transport.feedback_datagram(epoch,frame,status=status,frame_crc=r['frame_crc'],reason=reason)
        copies=2 if frame in cfg.duplicate_feedback_ids else 1
        for _ in range(copies):q_feedback.append((frame,data))
        feedback_rows.append(dict(kind='enqueue',id=frame,status=status,epoch=epoch,bytes=len(data),at_ms=now))

    def ingress_tick():
        expired=ingress.expire(now)
        for frame in expired:
            if frame not in tx or tx[frame].get('released_ms') is not None:continue
            tx[frame]['ingress_expired_ms']=now
            enqueue_feedback(frame,transport.NACK,reason=2)
            request_expire(frame,'partial_ingress_timeout')

    def due_key(frame):
        return cfg.refresh_period>0 and last_key_capture is not None and frame-last_key_capture>=cfg.refresh_period

    def pump():
        nonlocal encoding,waiting,network,qspi,decoder,feedback,last_key_capture
        changed=True
        while changed:
            changed=False
            if decoder is None and q_decode:
                frame=q_decode[0];r=tx[frame]
                free=next((i for i,b in enumerate(framebuffers) if not b['roles']),None)
                if free is not None:
                    q_decode.popleft();r['queued_decode']=False
                    if r.get('expire_requested') or now-captures[frame]>cfg.frame_deadline_ms:
                        ingress.reject(r.pop('complete'));drop(frame,'deadline_before_decode')
                        enqueue_feedback(frame,transport.NACK,reason=3);request_expire(frame,'deadline_before_decode')
                        changed=True;continue
                    complete=r['complete'];fields=gc.HEADER.unpack_from(complete.data)
                    assert fields[3:5]==(complete.epoch,complete.frame)==(1,frame)
                    assert complete.frame_crc==r['frame_crc']
                    framebuffers[free]={'frame':frame,'roles':{'decoding'}}
                    decoder=(frame,free);r['decode_owned']=True;r['decode_started_ms']=now
                    started=clock_ns()
                    try:rgb,info=dec.receive(complete.data)
                    except ValueError:r['decode_error']=True
                    else:r['decoded_rgb'],r['decoded_info']=rgb,info
                    r['decode_wall_ms']=elapsed(started)
                    r['decode_service_ms']=r['decode_wall_ms'] if cfg.decoder_service=='python_wall' else cfg.decode_ms
                    event(now+r['decode_service_ms'],'decode_done',decoder);changed=True
            if qspi is None and q_qspi:
                frame=q_qspi.popleft();r=tx[frame];r['queued_qspi']=False;r['qspi_owned']=True;qspi=frame
                event(now+r['bytes']*8/(cfg.qspi_mbps*1000),'qspi_done',frame);changed=True
            if network is None and q_network:
                frame,index,data=q_network.popleft();r=tx[frame];network=(frame,index,data)
                if 'send_started_ms' not in r:
                    r['send_started_ms']=now;event(now+cfg.ack_timeout_ms,'ack_timeout',frame)
                event(now+(len(data)+28)*8/(cfg.link_mbps*1000),'network_done',network);changed=True
            if feedback is None and q_feedback:
                frame,data=q_feedback.popleft();feedback=(frame,data)
                event(now+(len(data)+28)*8/(cfg.feedback_mbps*1000),'feedback_wire_done',feedback);changed=True
            if encoding is None and waiting is not None:
                frame=waiting;key=due_key(frame)
                if now-captures[frame]>cfg.preencode_age_ms:
                    waiting=None;drop(frame,'stale_before_encode');changed=True;continue
                free=next((i for i,v in enumerate(sender) if v is None),None)
                if free is not None and enc.can_prepare(key):
                    waiting=None;sender[free]=frame;encoding=frame
                    before=clock_ns();decision=control.prepare(frames[frame],frame,force_key=key)
                    duration=elapsed(before)
                    r={'slot':free,'encode_started_ms':now,'encode_wall_ms':duration,'encode_service_ms':duration,
                       'encode_done':False,'controller_internal_ms':decision.service_ms,'oracle_excluded':decision.oracle_excluded,'admitted':decision.accepted,'attempts':list(decision.attempts),
                       'analyze_calls':decision.analyze_calls,'forward_calls':decision.forward_calls,
                       'selected':decision.selected,'map_build_ms':decision.map_build_ms,'commit_ms':decision.commit_ms,
                       'bytes':0 if decision.packet is None else len(decision.packet),'wire_pending':0}
                    tx[frame]=r
                    if decision.accepted:
                        r['packet']=decision.packet;r['frame_crc']=transport.content_crc(decision.packet)
                        r['key']=bool(gc.HEADER.unpack_from(decision.packet)[2]);r['expected']=enc.expected_hash(frame)
                        if r['key']:last_key_capture=frame
                    else:r['key']=None
                    allocations.append(dict(kind='acquire',id=frame,slot=free,at_ms=now))
                    event(now+duration,'encode_done',frame);changed=True
        finish_expiries()

    while events:
        at,_,_,kind,value=heapq.heappop(events)
        if at>horizon+1e-9:break
        now=at
        if kind=='capture':event(now+cfg.acquisition_ms,'acquired',value)
        elif kind=='acquired':
            if waiting is not None:drop(waiting,'latest_replaced')
            waiting=value
        elif kind=='encode_done':
            assert encoding==value;encoding=None;r=tx[value];r['encode_done']=True
            if not r['admitted']:
                drop(value,'cap_rejected');release(value,'cap_rejected')
            elif now-captures[value]>cfg.frame_deadline_ms:
                drop(value,'deadline_after_encode');request_expire(value,'deadline_after_encode')
            else:
                parts=transport.datagrams(r['packet'],1,value)
                order=list(enumerate(parts))
                if cfg.reverse_chunks:order.reverse()
                if value in cfg.duplicate_chunk_ids:order.insert(1,order[0])
                r['wire_pending']=len(order);r['datagram_count']=len(order)
                for index,data in order:q_network.append((value,index,data))
        elif kind=='network_done':
            assert network==value;network=None;frame,index,data=value;r=tx[frame]
            forward_bytes+=len(data)+28;r['wire_pending']-=1
            wire_rows.append(dict(id=frame,index=index,at_ms=now,bytes=len(data)+28))
            lost=frame in cfg.data_loss_ids and index==0
            if not lost:
                if frame in cfg.corruption_ids and index==0:data=data[:-1]+bytes([data[-1]^1])
                try:
                    new=frame not in ingress.pending
                    complete=ingress.feed(data,now)
                    if new:event(now+cfg.ingress_timeout_ms,'ingress_tick')
                except ValueError as error:
                    r['ingress_error']=str(error)
                    if frame not in ingress.pending:
                        enqueue_feedback(frame,transport.NACK,reason=1)
                        request_expire(frame,'ingress_rejected')
                else:
                    if complete is not None:
                        r['complete']=complete;r['ingress_complete_ms']=now;r['queued_qspi']=True;q_qspi.append(frame)
        elif kind=='ingress_tick':ingress_tick()
        elif kind=='qspi_done':
            assert qspi==value;qspi=None;r=tx[value];r['qspi_owned']=False
            r['queued_decode']=True;q_decode.append(value)
        elif kind=='decode_done':
            assert decoder==value;decoder=None;frame,back=value;r=tx[frame];r['decode_owned']=False
            complete=r.pop('complete');r['decode_done_ms']=now
            if r.get('decode_error'):
                ingress.reject(complete);framebuffers[back]['roles'].clear();drop(frame,'decoder_rejected')
                enqueue_feedback(frame,transport.NACK,reason=4);request_expire(frame,'decoder_rejected')
            else:
                rgb=r.pop('decoded_rgb');info=r.pop('decoded_info')
                assert hashlib.sha256(rgb.tobytes()).hexdigest()==r['expected']
                ingress.commit(complete);r['decode_ok']=True
                framebuffers[back]['roles'].remove('decoding')
                display=corpus.expand565(corpus.rgb565(rgb))
                rect=tuple(manifest.get('active_rects',[(0,0,rgb.shape[1],rgb.shape[0])]*len(frames))[frame])
                mse=corpus.metrics(frames[frame],display,rect)['active']['mse']
                commits.append(dict(id=frame,at_ms=now,key=r['key'],anchor=info['anchor_id'],active_rgb565_mse=mse))
                if now-captures[frame]>cfg.frame_deadline_ms:
                    drop(frame,'deadline_after_decode')
                else:
                    if pending is not None:
                        old=framebuffers[pending]['frame'];framebuffers[pending]['roles'].remove('pending');drop(old,'pending_superseded')
                    pending=back;framebuffers[back]['roles'].add('pending')
                enqueue_feedback(frame,transport.ACK)
        elif kind=='feedback_wire_done':
            assert feedback==value;feedback=None;frame,data=value
            reverse_bytes+=len(data)+28
            feedback_rows.append(dict(kind='wire',id=frame,at_ms=now,bytes=len(data)+28))
            if frame in cfg.feedback_loss_ids:feedback_rows.append(dict(kind='lost',id=frame,at_ms=now))
            else:event(now+cfg.feedback_latency_ms,'feedback_received',(frame,data))
        elif kind=='feedback_received':
            frame,data=value
            try:fb=transport.parse_feedback(data)
            except ValueError:feedback_rows.append(dict(kind='parse_rejected',id=frame,at_ms=now))
            else:
                r=tx.get(frame);accepted=False
                if (r is not None and r.get('released_ms') is None
                    and transport.matches_feedback(fb,1,frame,r['frame_crc'])):
                    if fb.status==transport.ACK:
                        if physical_drained(frame) and r.get('decode_ok'):
                            accepted=enc.ack(frame,epoch=fb.epoch);release(frame,'decoded_ack')
                        elif r.get('decode_ok'):
                            r['ack_waiting']=True;accepted=True
                    else:
                        request_expire(frame,'receiver_nack');accepted=True
                feedback_rows.append(dict(kind='received',id=frame,at_ms=now,status=fb.status,
                                          accepted=accepted,epoch=fb.epoch,frame_crc=fb.frame_crc))
        elif kind=='ack_timeout':
            r=tx[value]
            if r.get('released_ms') is None and not r.get('ack_waiting'):
                timeout_rows.append(dict(id=value,at_ms=now,physical_drained=physical_drained(value)))
                request_expire(value,'ack_timeout')
        elif kind=='vblank' and pending is not None:
            framebuffers[front]['roles'].remove('front');front=pending;pending=None
            framebuffers[front]['roles'].remove('pending');framebuffers[front]['roles'].add('front')
            frame=framebuffers[front]['frame']
            if frame not in outcomes:
                outcomes[frame]='presented';presented.append(dict(id=frame,at_ms=now,capture_ms=captures[frame],age_ms=now-captures[frame]))
        pump()
        assert sum(v is not None for v in sender)<=2 and len(enc.pending)<=2
        assert len(ingress.pending)<=2 and sum('front' in b['roles'] for b in framebuffers)==1
        assert sum('decoding' in b['roles'] for b in framebuffers)<=1
        peak_sender=max(peak_sender,sum(v is not None for v in sender));peak_ingress=max(peak_ingress,len(ingress.pending))
        peak_credits=max(peak_credits,len(enc.pending));peak_roles=max(peak_roles,sum(bool(b['roles']) for b in framebuffers))
        peak_sender_bytes=max(peak_sender_bytes,sum(len(r.get('packet',b'')) for r in tx.values()))
        peak_ingress_bytes=max(peak_ingress_bytes,ingress.payload_bytes())
        live_wire=sum(len(x[2]) for x in q_network)+(len(network[2]) if network else 0)
        peak_wire_bytes=max(peak_wire_bytes,live_wire)
    pending_ids=set(range(len(frames)))-set(outcomes)
    validate_conservation(range(len(frames)),(r['id'] for r in presented),(r['id'] for r in drops),pending_ids)
    steady=(500,end-500) if end>=2000 else None
    metrics=summarize_presentation([dict(id=i,capture_ms=t) for i,t in enumerate(captures)],presented,end,steady)
    services={}
    for key in ('key','p'):
        for stage in ('encode','decode'):
            vals=[r[stage+'_wall_ms'] for r in tx.values() if r['key']==(key=='key') and stage+'_wall_ms' in r]
            services[key+'_'+stage+'_ms']=_stats(vals)
    services['rejected_encode_ms']=_stats([r['encode_wall_ms'] for r in tx.values() if not r['admitted']])
    public=[dict(id=i,**{k:v for k,v in r.items() if k not in ('packet','expected','decoded_rgb','decoded_info','complete')}) for i,r in tx.items()]
    return dict(config=asdict(cfg),metrics=metrics,capture_count=len(frames),capture_window_ms=[0,end],
                steady_window_ms=steady,presented=presented,presented_strict=metrics['presented_count'],
                presented_eventual=len(presented),drops=drops,drops_by_reason=dict(collections.Counter(r['reason'] for r in drops)),
                pending_ids=sorted(pending_ids),prepared=len(tx),commits=commits,packets=public,
                feedback=feedback_rows,forward_wire=wire_rows,forward_ipv4_udp_bytes=forward_bytes,
                feedback_ipv4_udp_bytes=reverse_bytes,feedback_protocol_bytes=transport.FEEDBACK_SIZE,
                forward_header_bytes=transport.HEADER.size,service_summary=services,timeout_events=timeout_rows,
                allocations=allocations,unresolved_sender_slots=sender,unresolved_ingress_frames=sorted(ingress.pending),
                unresolved_credits=sorted(enc.pending),waiting_at_end=waiting,
                peak_sender_slots=peak_sender,peak_ingress_slots=peak_ingress,peak_credits=peak_credits,
                peak_framebuffer_roles=peak_roles,peak_sender_packet_bytes=peak_sender_bytes,
                peak_ingress_payload_bytes=peak_ingress_bytes,peak_forward_datagram_bytes=peak_wire_bytes,
                python_wall_seconds=time.perf_counter()-wall_start,
                scope='Actual selected GM01/GF02/GA01 bytes and observed preparation/optional receive costs in offline finite-stage replay; not concurrent endpoint/native/hardware throughput',
                omitted='Source files are predecoded; acquisition_ms is declared external delay. RF/feedback retries, actual QSPI framing, physical memory/CDC/scanout and real display are unmeasured. Framebuffers are role metadata; source/oracle/output/codec workspaces extra.')
