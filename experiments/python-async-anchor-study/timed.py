"""Actual AA01 packets in finite virtual stages; no hardware timing proof."""
import collections
import dataclasses
import hashlib
import heapq
import math
from pathlib import Path
import sys
import time

import numpy as np
from async_codec import Encoder,Receiver,KEY,DISPLAY,RETIRE,parse,mt

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus
sys.path.insert(0,str(HERE.parent/'python-coupled-study'))
from validation import summarize_presentation,validate_conservation


@dataclasses.dataclass
class Config:
    fps:float=30
    quant_scale:int=8
    encode_ms:float=2
    decode_ms:float=8
    control_ms:float=.05
    link_mbps:float=8
    qspi_mbps:float=160
    feedback_ms:float=10
    refresh_hz:float=60
    refresh_period:int=30
    frame_cap:int=49152
    ack_timeout_ms:float=200
    drain_ms:float=1000
    max_age_ms:float=100
    max_key_retries:int=2
    lost_key_ack_once:bool=False
    drop_first_display:bool=False
    duplicate_ack_ms:float|None=None


def wire_bytes(n):return n+68*math.ceil(n/1024)


def run(frames,manifest,cfg=None):
    cfg=cfg or Config();frames=list(frames)
    if not frames or any(not math.isfinite(x) or x<=0 for x in (cfg.fps,cfg.link_mbps,cfg.qspi_mbps,cfg.refresh_hz,cfg.ack_timeout_ms)):
        raise ValueError('nonempty corpus/positive finite service')
    if any(not math.isfinite(x) or x<0 for x in (cfg.encode_ms,cfg.decode_ms,cfg.control_ms,cfg.feedback_ms,cfg.drain_ms,cfg.max_age_ms)):
        raise ValueError('nonnegative finite duration')
    if type(cfg.frame_cap) is not int or cfg.frame_cap<=0 or type(cfg.refresh_period) is not int or cfg.refresh_period<1:
        raise ValueError('cap/refresh geometry')
    if type(cfg.max_key_retries) is not int or not 0<=cfg.max_key_retries<=4:
        raise ValueError('bounded retries')
    if cfg.duplicate_ack_ms is not None and (not math.isfinite(cfg.duplicate_ack_ms) or cfg.duplicate_ack_ms<0):raise ValueError('duplicate ACK delay')
    mt.ft.qtable(cfg.quant_scale)
    enc,recv=Encoder(),Receiver()
    captures=[i*1000/cfg.fps for i in range(len(frames))]
    end=len(frames)*1000/cfg.fps;horizon=end+cfg.drain_ms
    queue=[];sequence=0
    def event(at,kind,value=None):
        nonlocal sequence
        sequence+=1
        priority=1 if kind=='vblank' else (2 if kind=='capture' else 0)
        heapq.heappush(queue,(at,priority,sequence,kind,value))
    for i,t in enumerate(captures):event(t,'capture',i)
    for i in range(math.floor(horizon*cfg.refresh_hz/1000)+1):event(i*1000/cfg.refresh_hz,'vblank')
    slots=[None,None];encoding=network=qspi=decoder=None
    qnet=collections.deque();qqspi=collections.deque();qdecode=collections.deque()
    buffers=[{'id':-1,'roles':{'front'}},{'id':None,'roles':set()},{'id':None,'roles':set()}]
    front=0;back_pending=None;waiting=None;last_key_source=-cfg.refresh_period;last_failed_key=-1
    retry_ready=False;retry_attempts=0;lost_key_ack=False;lost_display=False
    tx={};attempts=[];acks=[];drops=[];commits=[];presented=[];allocations=[];controls=[]
    now=0.;peaks=dict(slots=0,pcredits=0,buffers=0,packet_bytes=0,sender_anchors=0,receiver_anchors=0,
                     sender_reference_array_bytes=0,receiver_reference_array_bytes=0,host_key_retry_cache_bytes=0)

    def drop(i,reason):drops.append(dict(id=i,at_ms=now,reason=reason))
    def release(slot):
        aid=slots[slot];row=tx[aid];row.pop('packet',None)
        allocations.append(dict(kind='release',slot=slot,attempt=aid,at_ms=now));slots[slot]=None

    def start_packet(packet,slot,kind,source,wall=0,retry=False):
        nonlocal encoding
        row=parse(packet);aid=len(attempts)+1
        expected=enc.expected_hash(row['tx']) if kind!=RETIRE else None
        record=dict(attempt=aid,tx=row['tx'],kind=kind,source=source,anchor=row['anchor'],capture=row['capture'],
                    bytes=len(packet),wire_bytes=wire_bytes(len(packet)),prepared_ms=now,encode_wall_ms=wall,
                    retry=retry,expected=expected,packet=packet,status='prepared')
        if len(packet)>cfg.frame_cap:
            record['cap_rejected']=True;record.pop('packet')
            if kind==KEY:enc.discard_unsent_key(row['tx'])
            elif kind==DISPLAY:enc.expire(row['tx']);enc.mark_drained(row['tx'])
        tx[aid]=record;attempts.append(record);slots[slot]=aid;encoding=slot
        allocations.append(dict(kind='acquire',slot=slot,attempt=aid,at_ms=now))
        event(now+(cfg.control_ms if kind==RETIRE or retry else cfg.encode_ms),'encoded',slot)

    def pump():
        nonlocal encoding,network,qspi,decoder,waiting,last_key_source,last_failed_key,retry_ready,retry_attempts
        changed=True
        while changed:
            changed=False
            if decoder is None and qdecode:
                slot=qdecode[0];record=tx[slots[slot]]
                free=next((i for i,b in enumerate(buffers) if not b['roles']),None) if record['kind']==DISPLAY else -1
                if free is not None:
                    qdecode.popleft();decoder=(slot,free)
                    if free>=0:buffers[free]=dict(id=record['source'],roles={'decoding'})
                    event(now+(cfg.control_ms if record['kind']==RETIRE else cfg.decode_ms),'decoded',decoder);changed=True
            if qspi is None and qqspi:
                slot=qqspi.popleft();qspi=slot
                event(now+tx[slots[slot]]['bytes']*8/(cfg.qspi_mbps*1000),'qspi',slot);changed=True
            if network is None and qnet:
                slot=qnet.popleft();network=slot;row=tx[slots[slot]]
                row['send_ms']=now;row['send_generation']=slots[slot]
                event(now+row['wire_bytes']*8/(cfg.link_mbps*1000),'network',slot)
                event(now+cfg.ack_timeout_ms,'timeout',(row['tx'],slots[slot]));changed=True
            if encoding is not None:continue
            free=next((i for i,s in enumerate(slots) if s is None),None)
            if free is None:continue
            if retry_ready and enc.candidate is not None:
                # One physical copy of that control must have drained before retry.
                candidate=enc.candidate
                busy=any(r.get('packet') is not None and r['tx']==candidate for r in attempts)
                if not busy:
                    start_packet(enc.retry_key(),free,KEY,last_key_source,retry=True)
                    retry_ready=False;retry_attempts+=1;changed=True;continue
            if enc.can_retire():
                start_packet(enc.prepare_retire(),free,RETIRE,None);changed=True;continue
            if waiting is not None:
                if now-captures[waiting]>cfg.max_age_ms:
                    drop(waiting,'stale_before_encode');waiting=None;changed=True;continue
                due=waiting-last_key_source>=cfg.refresh_period
                if (enc.active is None or due) and waiting>last_failed_key and enc.can_key():
                    source=waiting;started=time.perf_counter_ns()
                    packet=enc.prepare_key(frames[source],source,cfg.quant_scale)
                    wall=(time.perf_counter_ns()-started)/1e6
                    last_key_source=source;retry_attempts=0
                    start_packet(packet,free,KEY,source,wall)
                    if tx[slots[free]].get('cap_rejected'):last_failed_key=source
                    changed=True;continue
                if enc.can_display():
                    source=waiting;waiting=None;started=time.perf_counter_ns()
                    packet=enc.prepare_display(frames[source],source,cfg.quant_scale)
                    start_packet(packet,free,DISPLAY,source,(time.perf_counter_ns()-started)/1e6)
                    changed=True

    start_wall=time.perf_counter()
    while queue:
        at,_,_,kind,value=heapq.heappop(queue)
        if at>horizon+1e-9:break
        now=at
        if kind=='capture':
            if waiting is not None:drop(waiting,'latest_replaced')
            waiting=value
        elif kind=='encoded':
            assert encoding==value;encoding=None;row=tx[slots[value]]
            if row.get('cap_rejected'):
                row['status']='cap_rejected'
                if row['kind']==DISPLAY:drop(row['source'],'cap')
                else:controls.append(dict(tx=row['tx'],at_ms=now,kind='key_cap_rejected'))
                release(value)
            else:qnet.append(value)
        elif kind=='network':
            assert network==value;network=None;row=tx[slots[value]]
            if row['kind']==DISPLAY and cfg.drop_first_display and not lost_display:
                lost_display=True;drop(row['source'],'data_loss');row['status']='network_loss'
                enc.mark_drained(row['tx']);release(value)
            else:qqspi.append(value)
        elif kind=='qspi':
            assert qspi==value;qspi=None;qdecode.append(value)
        elif kind=='decoded':
            assert decoder==value;slot,buffer=value;row=tx[slots[slot]]
            started=time.perf_counter_ns()
            try:rgb,info=recv.receive(row['packet'])
            except ValueError:
                row['status']='receiver_rejected'
                if row['kind']==DISPLAY:
                    buffers[buffer]['roles'].clear();drop(row['source'],'receiver_rejected')
                enc.mark_drained(row['tx']);event(now+cfg.feedback_ms,'nack',row['tx'])
            else:
                row['decode_wall_ms']=(time.perf_counter_ns()-started)/1e6;row['status']='committed'
                if rgb is not None and row['kind']!=RETIRE:
                    assert hashlib.sha256(rgb.tobytes()).hexdigest()==row['expected']
                enc.mark_drained(row['tx'])
                if row['kind']==DISPLAY:
                    assert info['display'];buffers[buffer]['roles'].remove('decoding')
                    if back_pending is not None:
                        drop(buffers[back_pending]['id'],'pending_superseded');buffers[back_pending]['roles'].remove('pending')
                    back_pending=buffer;buffers[buffer]['roles'].add('pending')
                    display=corpus.expand565(corpus.rgb565(rgb));rect=tuple(manifest['active_rects'][row['source']])
                    mse=corpus.metrics(frames[row['source']],display,rect)['active']['mse']
                    commits.append(dict(id=row['source'],at_ms=now,tx=row['tx'],anchor=row['anchor'],active_mse=mse))
                else:controls.append(dict(tx=row['tx'],at_ms=now,kind='key_installed' if row['kind']==KEY else 'retire_applied',duplicate=info['duplicate']))
                if row['kind']==KEY and cfg.lost_key_ack_once and not lost_key_ack:
                    lost_key_ack=True;acks.append(dict(tx=row['tx'],at_ms=now,kind='key_ACK_lost'))
                else:
                    event(now+cfg.feedback_ms,'ack',row['tx'])
                    if cfg.duplicate_ack_ms is not None:event(now+cfg.feedback_ms+cfg.duplicate_ack_ms,'ack',row['tx'])
            release(slot);decoder=None
        elif kind=='ack':acks.append(dict(tx=value,at_ms=now,kind='ack',accepted=enc.ack(value,1)))
        elif kind=='nack':enc.expire(value)
        elif kind=='timeout':
            xid,attempt=value
            # Ignore an earlier attempt's timer once that exact key was retried.
            if any(r['tx']==xid and 'send_ms' in r and r['attempt']>attempt for r in attempts):continue
            result=enc.expire(xid)
            if result:
                acks.append(dict(tx=xid,at_ms=now,kind='timeout',action=result))
                if result=='retry_key' and retry_attempts<cfg.max_key_retries:retry_ready=True
        elif kind=='vblank' and back_pending is not None:
            buffers[front]['roles'].remove('front');front=back_pending;back_pending=None
            buffers[front]['roles'].remove('pending');buffers[front]['roles'].add('front')
            i=buffers[front]['id'];presented.append(dict(id=i,at_ms=now,capture_ms=captures[i]))
        pump()
        assert len(enc.anchors)<=2 and len(recv.anchors)<=2
        assert sum(r['kind']==DISPLAY for r in enc.pending.values())<=2
        assert sum('front' in b['roles'] for b in buffers)==1
        retained=sum(len(r.get('packet',b'')) for r in attempts)
        assert retained<=2*cfg.frame_cap
        peaks['slots']=max(peaks['slots'],sum(s is not None for s in slots));peaks['packet_bytes']=max(peaks['packet_bytes'],retained)
        peaks['pcredits']=max(peaks['pcredits'],sum(r['kind']==DISPLAY for r in enc.pending.values()))
        peaks['buffers']=max(peaks['buffers'],sum(bool(b['roles']) for b in buffers))
        peaks['sender_anchors']=max(peaks['sender_anchors'],len(enc.anchors));peaks['receiver_anchors']=max(peaks['receiver_anchors'],len(recv.anchors))
        peaks['sender_reference_array_bytes']=max(peaks['sender_reference_array_bytes'],enc.retained_reference_bytes())
        peaks['receiver_reference_array_bytes']=max(peaks['receiver_reference_array_bytes'],recv.retained_reference_bytes())
        peaks['host_key_retry_cache_bytes']=max(peaks['host_key_retry_cache_bytes'],enc.retry_cache_bytes())
    if waiting is not None and enc.active is None and waiting==last_failed_key:
        drop(waiting,'no_anchor_after_cap');waiting=None
    capture_rows=[dict(id=i,capture_ms=t) for i,t in enumerate(captures)]
    metrics=summarize_presentation(capture_rows,presented,end,(500,end-500) if end>=2000 else None)
    shown={r['id'] for r in presented};pending_ids=set()
    if waiting is not None:pending_ids.add(waiting)
    for row in attempts:
        if row.get('packet') is not None and row['kind']==DISPLAY:pending_ids.add(row['source'])
    if back_pending is not None:pending_ids.add(buffers[back_pending]['id'])
    pending_ids-=shown;dropped_ids=set(range(len(frames)))-shown-pending_ids
    reasons={r['id']:r['reason'] for r in drops}
    assert all(i in reasons for i in dropped_ids)
    validate_conservation(range(len(frames)),shown,dropped_ids,pending_ids)
    byid={r['id']:r for r in commits};mse=[byid[i]['active_mse'] for i in shown]
    data=[r for r in attempts if 'send_ms' in r]
    return dict(config=dataclasses.asdict(cfg),metrics=metrics,presented=presented,commits=commits,
                drops=drops,drop_counts=dict(collections.Counter(r['reason'] for r in drops)),acks=acks,controls=controls,
                packets=[{k:v for k,v in r.items() if k!='packet'} for r in attempts],peaks=peaks,
                transmitted_wire_bytes=sum(r['wire_bytes'] for r in data),
                control_wire_bytes=sum(r['wire_bytes'] for r in data if r['kind']!=DISPLAY),
                display_wire_bytes=sum(r['wire_bytes'] for r in data if r['kind']==DISPLAY),
                displayed_psnr_db=None if not mse or np.mean(mse)==0 else float(10*np.log10(65025/np.mean(mse))),
                unresolved_slots=slots,pending_controls=[x for x,r in enc.pending.items() if r['kind']!=DISPLAY],
                pending_display_credits=[x for x,r in enc.pending.items() if r['kind']==DISPLAY],
                waiting_at_end=waiting,disposition=dict(presented=sorted(shown),dropped=sorted(dropped_ids),pending=sorted(pending_ids)),
                allocations=allocations,python_wall_seconds=time.perf_counter()-start_wall,
                scope='Actual bytes/reconstruction with assumed stages; reference-only keys never count as presented captures')
