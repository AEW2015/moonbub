"""Actual MT02 packet/reconstruction coupled to an assumed-time event model."""
from __future__ import annotations
import dataclasses
import hashlib
import heapq
import math
from pathlib import Path
import sys
import time
import collections

import numpy as np

HERE=Path(__file__).resolve().parent
for p in (HERE.parent/'python-motion-study',HERE.parent/'python-codec-study'):
    sys.path.insert(0,str(p))
import motion_codec as mc
import corpus
import pacing
from validation import summarize_presentation,validate_conservation


@dataclasses.dataclass
class Config:
    fps: float=30
    encode_ms: float=2
    decode_ms: float=8
    link_mbps: float=8
    qspi_mbps: float=160
    feedback_ms: float=0
    refresh_hz: float=60
    frame_cap: int=49152
    max_age_ms: float=100
    ack_timeout_ms: float=200
    drain_ms: float=1000
    quant_scale: int=8
    key_period: int=30
    mode: str='global'
    loss_ids: tuple[int,...]=()
    ack_loss_ids: tuple[int,...]=()
    corrupt_ids: tuple[int,...]=()
    duplicate_ack_ms: float|None=None
    cap_backoff_scales: tuple[int,...]=()


def run(frames, manifest, cfg=None):
    cfg=cfg or Config()
    frames=list(frames)
    if not frames: raise ValueError('nonempty frame corpus required')
    if any(not math.isfinite(x) or x<=0 for x in (cfg.fps,cfg.link_mbps,cfg.qspi_mbps,cfg.refresh_hz,cfg.ack_timeout_ms)):
        raise ValueError('positive finite rates/timeout required')
    if any(not math.isfinite(x) or x<0 for x in (cfg.encode_ms,cfg.decode_ms,cfg.feedback_ms,cfg.drain_ms,cfg.max_age_ms)):
        raise ValueError('nonnegative service durations required')
    if type(cfg.frame_cap) is not int or cfg.frame_cap<1 or type(cfg.key_period) is not int or cfg.key_period<1:
        raise ValueError('positive finite storage/key period required')
    if cfg.duplicate_ack_ms is not None and (not math.isfinite(cfg.duplicate_ack_ms) or cfg.duplicate_ack_ms<0):
        raise ValueError('duplicate ACK delay')
    for ids in (cfg.loss_ids,cfg.ack_loss_ids,cfg.corrupt_ids):
        if any(type(i) is not int or not 0<=i<len(frames) for i in ids): raise ValueError('fault IDs')
    mc.ft.qtable(cfg.quant_scale)
    if cfg.cap_backoff_scales:
        values=cfg.cap_backoff_scales
        if (any(type(x) is not int or not 1<=x<=32 for x in values)
                or tuple(sorted(set(values)))!=tuple(values) or values[0]!=cfg.quant_scale):
            raise ValueError('adaptive scales must increase from initial quantizer to at most32')
    if cfg.mode not in ('global','zero'): raise ValueError('mode')
    captures=[i*1000/cfg.fps for i in range(len(frames))]
    end=len(frames)*1000/cfg.fps
    horizon=end+cfg.drain_ms
    enc,receiver=mc.Encoder(),mc.Receiver()
    events=[];serial=0
    def schedule(at,kind,item=None):
        nonlocal serial
        serial+=1
        priority=1 if kind=='vblank' else (2 if kind=='capture' else 0)
        heapq.heappush(events,(at,priority,serial,kind,item))
    for i,at in enumerate(captures):schedule(at,'capture',i)
    for i in range(math.ceil(horizon*cfg.refresh_hz/1000)+1):schedule(i*1000/cfg.refresh_hz,'vblank')
    now=0.;waiting=None;active=None;generation=0;pipeline_free=0.;pending=None;front=None;last_key_id=-cfg.key_period
    current_scale=cfg.quant_scale
    records=[];drops=[];commits=[];presentations=[];acks=[];physical={}
    max_waiting=max_physical=0
    def drop(i,reason):drops.append({'id':i,'reason':reason,'at_ms':now})
    def pump():
        nonlocal waiting,active,generation,pipeline_free,max_physical,last_key_id,current_scale
        if active is not None or waiting is None:return
        if now<pipeline_free-1e-9:
            schedule(pipeline_free,'kick');return
        i=waiting;waiting=None
        if now-captures[i]>cfg.max_age_ms:
            drop(i,'stale_before_encode');return
        generation+=1
        wall=time.perf_counter_ns()
        packet=enc.prepare(frames[i],i,quant_scale=current_scale,mode=cfg.mode,force_key=i-last_key_id>=cfg.key_period)
        encode_wall=(time.perf_counter_ns()-wall)/1e6
        expected=enc.prepared_rgb()
        fields=mc.HEADER.unpack_from(packet)
        row={'id':i,'generation':generation,'capture_ms':captures[i],'encode_start_ms':now,
             'encode_wall_ms_python':encode_wall,'bytes':len(packet),'wire_bytes':pacing.wire_bytes(len(packet)),
             'key':fields[4]==mc.NO_REF,'reference_id':None if fields[4]==mc.NO_REF else fields[4],
             'dx':fields[8],'dy':fields[9],'status':'prepared'}
        row['quant_scale']=current_scale
        if row['key']:last_key_id=i
        records.append(row)
        ready=now+cfg.encode_ms
        if len(packet)>cfg.frame_cap:
            enc.abort();row['status']='cap_drop';drop(i,'cap')
            if cfg.cap_backoff_scales:
                position=cfg.cap_backoff_scales.index(current_scale)
                current_scale=cfg.cap_backoff_scales[min(position+1,len(cfg.cap_backoff_scales)-1)]
            pipeline_free=ready;schedule(ready,'kick');return
        # Admission age is evaluated after actual packet preparation's assumed delay.
        if ready-captures[i]>cfg.max_age_ms:
            enc.abort();row['status']='age_drop';drop(i,'stale_after_encode')
            pipeline_free=ready;schedule(ready,'kick');return
        network_end=ready+row['wire_bytes']*8/(cfg.link_mbps*1000)
        decode_end=network_end+len(packet)*8/(cfg.qspi_mbps*1000)+cfg.decode_ms
        pipeline_free=network_end if i in cfg.loss_ids else decode_end
        transaction={'id':i,'generation':generation,'packet':packet,'expected':expected,'row':row,
                     'decode_end':decode_end,'timed_out':False}
        active=transaction
        physical[generation]=transaction
        max_physical=max(max_physical,1)
        row.update(network_end_ms=network_end,decode_scheduled_ms=decode_end)
        if i in cfg.loss_ids:schedule(network_end,'loss',transaction)
        else:schedule(decode_end,'decode',transaction)
        schedule(ready+cfg.ack_timeout_ms,'timeout',transaction)

    while events:
        at,_,_,kind,item=heapq.heappop(events)
        if at>horizon+1e-9:break
        now=at
        if kind=='capture':
            if waiting is not None:drop(waiting,'latest_replaced')
            waiting=item
            max_waiting=max(max_waiting,1)
        elif kind=='loss':
            physical.pop(item['generation'],None)
            item['row']['status']='network_loss';drop(item['id'],'network_loss')
        elif kind=='decode':
            physical.pop(item['generation'],None)
            i=item['id'];packet=item['packet'];before=receiver.reference_id
            if i in cfg.corrupt_ids:packet=packet[:-1]+bytes([packet[-1]^1])
            started=time.perf_counter_ns()
            try:
                rgb,info=receiver.receive(packet)
            except ValueError:
                assert receiver.reference_id==before
                drop(i,'decode_reject');item['row']['status']='decode_reject'
            else:
                if not np.array_equal(rgb,item['expected']):raise AssertionError('host/receiver reconstruction mismatch')
                output=corpus.expand565(corpus.rgb565(rgb))
                quality=corpus.metrics(frames[i],output,tuple(manifest['active_rects'][i]))
                item['row'].update(status='committed',decode_at_ms=now,
                    decode_wall_ms_python=(time.perf_counter_ns()-started)/1e6,
                    reconstructed_hash=hashlib.sha256(corpus.rgb565(rgb).astype('<u2').tobytes()).hexdigest(),quality=quality)
                commits.append({'id':i,'at_ms':now,'capture_ms':captures[i]})
                if pending is not None:drop(pending['id'],'pending_superseded')
                pending={'id':i,'at_ms':now,'capture_ms':captures[i]}
                if i not in cfg.ack_loss_ids:
                    schedule(now+cfg.feedback_ms,'ack',item)
                    if cfg.duplicate_ack_ms is not None:schedule(now+cfg.feedback_ms+cfg.duplicate_ack_ms,'ack',item)
                else:drop(i,'ACK_loss')
        elif kind=='ack':
            if active is not None and active['generation']==item['generation']:
                enc.ack(item['id'],epoch=receiver.epoch)
                acks.append({'id':item['id'],'at_ms':now,'accepted':True})
                active=None
            else:acks.append({'id':item['id'],'at_ms':now,'accepted':False})
        elif kind=='timeout':
            if active is not None and active['generation']==item['generation']:
                enc.abort();item['timed_out']=True;active=None
                drop(item['id'],'timeout')
        elif kind=='vblank' and pending is not None:
            front=pending;pending=None
            presentations.append({**front,'at_ms':now,'age_ms':now-front['capture_ms']})
        pump()
        assert active is None or enc._pending is not None
    steady_start,steady_end=500.,end-500.
    metrics=summarize_presentation([{'id':i,'capture_ms':at} for i,at in enumerate(captures)],
                                  presentations,end,(steady_start,steady_end) if end>=2000 else None)
    age=[r['age_ms'] for r in presentations]
    ids=[r['id'] for r in presentations]
    assert ids==sorted(set(ids))
    shown=set(ids)
    pending_ids=set(x['id'] for x in physical.values())
    if active is not None:pending_ids.add(active['id'])
    if waiting is not None:pending_ids.add(waiting)
    if pending is not None:pending_ids.add(pending['id'])
    pending_ids-=shown
    dropped_ids=set(range(len(frames)))-shown-pending_ids
    reasons={}
    for row in drops:reasons[row['id']]=row['reason']
    assert all(i in reasons for i in dropped_ids),'unexplained unpresented capture'
    validate_conservation(range(len(frames)),shown,dropped_ids,pending_ids)
    outcomes=[{'id':i,'state':'presented' if i in shown else ('pending' if i in pending_ids else 'dropped'),
               'reason':reasons.get(i) if i in dropped_ids else None} for i in range(len(frames))]
    shown_records=[r for r in records if r['id'] in shown]
    sse=sum(r['quality']['active']['mse']*manifest['active_rects'][r['id']][2]*manifest['active_rects'][r['id']][3]*3 for r in shown_records)
    samples=sum(manifest['active_rects'][r['id']][2]*manifest['active_rects'][r['id']][3]*3 for r in shown_records)
    mse=sse/samples if samples else None
    return {'config':dataclasses.asdict(cfg),'input_frames':len(frames),'attempted':len(records),
            'committed':len(commits),'presented_strict':metrics['presented_count'],'presented_after_drain':len(presentations),
            'capture_window_ms':[0,end],'steady_window_ms':[steady_start,steady_end] if end>=2000 else None,
            'steady_fps':metrics['steady_fps'],'strict_presentation_metrics':metrics,
            'age_ms':{'p95':float(np.percentile(age,95)) if age else None,'max':max(age,default=None)},
            'wire_bytes':sum(r['wire_bytes'] for r in records if r['status']!='cap_drop' and r['status']!='age_drop'),
            'drop_counts':dict(collections.Counter(r['reason'] for r in drops)),
            'stale_ack_count':sum(not x['accepted'] for x in acks),'max_waiting':max_waiting,
            'physical_pipeline_limit':1,'observed_max_pipeline_transactions':max_physical,
            'pending_at_horizon':None if active is None else active['id'],
            'physical_transactions_at_horizon':[{'id':x['id'],'generation':x['generation'],'decode_end_ms':x['decode_end'],
                                                 'timed_out':x['timed_out']} for x in physical.values()],
            'physical_busy_until_ms':pipeline_free,'host_waiting_at_horizon':waiting,
            'pending_back_at_horizon':None if pending is None else pending['id'],
            'front_at_horizon':None if front is None else front['id'],
            'terminal_outcomes':outcomes,'terminal_counts':dict(collections.Counter(x['state'] for x in outcomes)),
            'disposition_conserved':True,
            'attempt_scale_histogram':dict(collections.Counter(r['quant_scale'] for r in records)),
            'presented_scale_histogram':dict(collections.Counter(r['quant_scale'] for r in shown_records)),
            'pooled_presented_active_mse':mse,
            'pooled_presented_active_psnr_db':None if mse is None or mse==0 else float(10*np.log10(65025/mse)),
            'quality_scope':'Only presented IDs; adaptive/fixed outputs and selected corpus subsets differ',
            'records':records,'drops':drops,'commits':commits,'presentations':presentations,'acks':acks,
            'scope':'Actual packet re-encoding/decode with assumed virtual stage times; Python wall costs separate, no physical FPS'}
