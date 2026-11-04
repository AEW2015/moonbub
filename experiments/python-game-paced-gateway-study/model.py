"""Bounded prospective packet-credit gateway model; not firmware/RF emulation."""
from collections import Counter, deque
from dataclasses import asdict, dataclass, replace
import importlib.util
import heapq
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('paced_frozen_gateway',HERE.parent/'python-game-esp32-gateway-study/gateway.py')
frozen=importlib.util.module_from_spec(spec);sys.modules[spec.name]=frozen;spec.loader.exec_module(frozen)

@dataclass(frozen=True)
class Policy:
    window:int=6
    session:int=17
    pacing_us:float=1100
    aggregate_ms:float=8
    feedback_latency_ms:float=2
    feedback_mbps:float=8
    feedback_timeout_ms:float=30
    max_queries:int=3
    deadline_ms:float=120
    estimate_service_factor:float=1
    drop_first_feedback:bool=False
    lose_all_feedback:bool=False
    inject_stale_feedback:bool=False
    inject_foreign_feedback:bool=False
    extra_feedback_delay_ms:float=0
    drain_ms:float=300
    control_query_us:float=50

    def validate(self):
        if type(self.session) is not int or not 0<self.session<2**32:raise ValueError('session identity')
        if type(self.window) is not int or not 1<=self.window<=6:raise ValueError('bounded credit window')
        if type(self.max_queries) is not int or not 0<=self.max_queries<=5:raise ValueError('bounded query count')
        for k in ('pacing_us','aggregate_ms','feedback_latency_ms','extra_feedback_delay_ms','drain_ms'):
            x=getattr(self,k)
            if not math.isfinite(x) or x<0:raise ValueError(k)
        for k in ('feedback_mbps','feedback_timeout_ms','deadline_ms','estimate_service_factor','control_query_us'):
            x=getattr(self,k)
            if not math.isfinite(x) or x<=0:raise ValueError(k)
        if any(type(getattr(self,k)) is not bool for k in ('drop_first_feedback','lose_all_feedback','inject_stale_feedback','inject_foreign_feedback')):raise ValueError('fault boolean')


def packets(frame,cfg):
    out=[];offset=0
    while offset<frame['bytes']:
        n=min(cfg.chunk,frame['bytes']-offset)
        out.append(dict(frame=frame['id'],offset=offset,payload=n,length=frame['bytes'],index=len(out)))
        offset+=n
    return out


def estimate_frame_us(frame,cfg,policy):
    """Causal admission estimate from declared size and configured allowances only."""
    parts=packets(frame,cfg)
    wire=sum((p['payload']+cfg.header+28)*8/cfg.wifi_payload_mbps for p in parts)
    service=sum(sum(s[k] for k in ('cpu_us','poll_us','dma_blocking_us')) for p in parts for s in [frozen.packet_service_us(p['payload'],p['index'],cfg)])
    # Conservative sum instead of pretending compute/network perfectly overlap.
    pacing=max(0,len(parts)-1)*policy.pacing_us
    credit_rounds=math.ceil(len(parts)/policy.window)*(policy.feedback_latency_ms+policy.extra_feedback_delay_ms)*1000
    fifo_drain=frame['bytes']/cfg.fpga_drain_bytes_per_second*1e6 if cfg.fifo_policy=='bounded_fifo_wait' else 0
    return max(wire,pacing,fifo_drain)+service*policy.estimate_service_factor+credit_rounds+policy.aggregate_ms*1000


def run(frames,cfg=None,policy=Policy()):
    cfg=cfg or frozen.Config(fifo_policy='bounded_fifo_wait',chunk=1008,header=56)
    cfg.validate();policy.validate()
    if cfg.header+cfg.chunk>1064 or cfg.header<56:raise ValueError('prospective header/DMA geometry')
    if any(type(f.get('id')) is not int or f['id']<0 or type(f.get('bytes')) is not int or not 0<f['bytes']<=49152 for f in frames):raise ValueError('frame identity/cap')
    if [f['id'] for f in frames]!=sorted({f['id'] for f in frames}):raise ValueError('ordered unique capture IDs')
    events=[];serial=0;now=0.;counter=Counter();drops=[];admissions=[];done_frames=[];packet_rows=[];feedback=[]
    source={f['id']:dict(f,capture_us=f['id']*1e6/cfg.frame_rate) for f in frames}
    capture_end=(max(source)+1)*1e6/cfg.frame_rate if source else 0
    horizon=capture_end+policy.drain_ms*1000
    latest=None;active=None;wire_free=feedback_free=pacing_free=0.;queue=deque();busy=False
    slots=[None]*policy.window;slot_seq=[0]*policy.window;ledger=[None]*policy.window
    peak_source=peak_host=peak_mailbox=peak_inflight=peak_ledger=0
    fifo=0.;fifo_at=0.;max_fifo=0.;rx_active=None;expected_offset=0;failed=set();committed=set()
    first_feedback_dropped=False;stale_injected=False;foreign_injected=False
    query_pending=deque();query_inflight=None;peak_control_pending=0
    def event(at,kind,value=None):
        nonlocal serial
        serial+=1;heapq.heappush(events,(at,serial,kind,value))
    for f in source.values():event(f['capture_us'],'capture',f['id'])
    def record_drop(fid,reason):
        if not any(d['id']==fid for d in drops):drops.append(dict(id=fid,at_us=now,reason=reason))
    def drain(t):
        nonlocal fifo,fifo_at
        fifo=max(0.,fifo-(t-fifo_at)*cfg.fpga_drain_bytes_per_second/1e6);fifo_at=t
    def send_feedback(p,status,query=False):
        nonlocal feedback_free,first_feedback_dropped,stale_injected,foreign_injected
        data=dict(session=policy.session,slot=p['slot'],seq=p['seq'],frame=p['frame'],status=status,query=query)
        if policy.lose_all_feedback or (policy.drop_first_feedback and not first_feedback_dropped):
            first_feedback_dropped=True;counter['feedback_lost']+=1;return
        start=max(now,feedback_free);feedback_free=start+92*8/policy.feedback_mbps
        at=feedback_free+(policy.feedback_latency_ms+policy.extra_feedback_delay_ms)*1000
        feedback.append(dict(kind='credit_wire',start_us=start,done_us=feedback_free,bytes=92,**data))
        event(at,'credit',data)
        if policy.inject_foreign_feedback and not foreign_injected:
            foreign_injected=True;old=dict(data,session=policy.session+1)
            duplicate_start=max(now,feedback_free);feedback_free=duplicate_start+92*8/policy.feedback_mbps
            feedback.append(dict(kind='foreign_credit_wire',start_us=duplicate_start,done_us=feedback_free,bytes=92,**old))
            event(at+100,'credit',old);counter['foreign_feedback_injected']+=1
        if policy.inject_stale_feedback and not stale_injected:
            stale_injected=True
            duplicate_start=max(now,feedback_free);feedback_free=duplicate_start+92*8/policy.feedback_mbps
            feedback.append(dict(kind='duplicate_credit_wire',start_us=duplicate_start,done_us=feedback_free,bytes=92,**data))
            event(at+40000+92*8/policy.feedback_mbps,'credit',data);counter['stale_feedback_injected']+=1
    def dispatch():
        nonlocal busy,rx_active,expected_offset,fifo,max_fifo
        if busy or not queue:return
        p=queue.popleft();busy=True
        if p.get('control'):
            event(now+policy.control_query_us/cfg.cpu_fraction,'queried',p)
            counter['control_queries_serviced']+=1
            return
        s=frozen.packet_service_us(p['payload'],p['index'],cfg)
        end=now+s['cpu_us']+s['poll_us'];reason=None
        if p['offset']==0:
            if rx_active is not None:
                end+=cfg.abort_recovery_ms*1000+2*(s['read_u32_us']+cfg.driver_call_us)+24/cfg.qspi_write_hz*1e6+cfg.driver_call_us
                counter['replacement_abort']+=1
            rx_active=None
            if ((end/1000-cfg.lock_phase_ms)%cfg.lock_period_ms)<cfg.lock_busy_ms:reason='begin_device_lock_busy'
            else:
                rx_active=p['frame'];expected_offset=0
                end+=4*(s['read_u32_us']+cfg.driver_call_us)+5*(24/cfg.qspi_write_hz*1e6+cfg.driver_call_us)
        if not reason and (rx_active!=p['frame'] or expected_offset!=p['offset'] or p['frame'] in failed):reason='sequence_after_loss'
        if not reason and ((end/1000-cfg.lock_phase_ms)%cfg.lock_period_ms)<cfg.lock_busy_ms:reason='device_lock_busy'
        if not reason:
            drain(end);short=max(0.,fifo+p['payload']-cfg.fifo_bytes)
            if short:
                wait=short/cfg.fpga_drain_bytes_per_second*1e6
                if cfg.fifo_policy=='bounded_fifo_wait' and wait<=cfg.maximum_fifo_wait_ms*1000:
                    end+=wait;drain(end);counter['fifo_waits']+=1
                else:reason='fifo_overflow' if cfg.fifo_policy=='remaining_frame_credit' else 'fifo_wait_timeout'
            if not reason:
                end+=s['dma_blocking_us'];drain(end);fifo+=p['payload'];max_fifo=max(max_fifo,fifo)
                expected_offset+=p['payload']
                if expected_offset==p['length']:
                    end+=2*(s['read_u32_us']+cfg.driver_call_us)+24/cfg.qspi_write_hz*1e6+cfg.driver_call_us
                    rx_active=None
        if reason:
            if rx_active is not None:
                end+=cfg.abort_recovery_ms*1000+2*(s['read_u32_us']+cfg.driver_call_us)+24/cfg.qspi_write_hz*1e6+cfg.driver_call_us
                counter['error_abort']+=1
            failed.add(p['frame']);rx_active=None;counter[reason]+=1
        event(end,'serviced',dict(p,reason=reason,service_start_us=now,service_done_us=end))
    def pump():
        nonlocal latest,active,wire_free,pacing_free,peak_source,peak_host,peak_inflight,query_inflight,peak_control_pending
        if active is None and latest is not None:
            f=source[latest];latest=None
            predicted=max(now,wire_free)+estimate_frame_us(f,cfg,policy)
            if predicted>f['capture_us']+policy.deadline_ms*1000:
                record_drop(f['id'],'pre_admission_deadline');counter['pre_admission_deadline']+=1
            else:
                active=dict(frame=f['id'],packets=packets(f,cfg),next=0,acked=0,negative=False)
                admissions.append(dict(id=f['id'],at_us=now,predicted_complete_us=predicted,deadline_us=f['capture_us']+policy.deadline_ms*1000,bytes=f['bytes']))
        if query_inflight is None:
            while query_pending:
                slot,seq=query_pending.popleft();pending=slots[slot]
                if pending is None or pending['seq']!=seq:continue
                if pending['queries']>=policy.max_queries:
                    counter['credit_query_exhausted']+=1;continue
                pending['queries']+=1;query_inflight=(slot,seq)
                start=max(now,wire_free);wire_free=start+60*8/cfg.wifi_payload_mbps
                delivery=wire_free+policy.feedback_latency_ms*1000
                if policy.aggregate_ms:delivery=math.ceil(delivery/(policy.aggregate_ms*1000))*policy.aggregate_ms*1000
                event(delivery,'query_arrival',dict(session=policy.session,slot=slot,seq=seq,frame=pending['frame'],control=True))
                counter['credit_queries']+=1;break
        peak_control_pending=max(peak_control_pending,len(query_pending))
        if active is not None:
            for slot in range(policy.window):
                if slots[slot] is not None or active['next']>=len(active['packets']):continue
                p=dict(active['packets'][active['next']]);active['next']+=1
                slot_seq[slot]+=1;p.update(session=policy.session,slot=slot,seq=slot_seq[slot],queries=0)
                slots[slot]=p
                start=max(now,wire_free,pacing_free)
                end=start+(p['payload']+cfg.header+28)*8/cfg.wifi_payload_mbps
                wire_free=end;pacing_free=start+policy.pacing_us
                delivery=end
                if policy.aggregate_ms:delivery=math.ceil(delivery/(policy.aggregate_ms*1000))*policy.aggregate_ms*1000
                packet_rows.append(dict(p,wire_start_us=start,wire_done_us=end,arrival_us=delivery))
                event(delivery,'arrival',p)
                event(end+policy.feedback_timeout_ms*1000,'timeout',(slot,p['seq']))
        peak_source=max(peak_source,int(latest is not None));peak_host=max(peak_host,int(active is not None))
        peak_inflight=max(peak_inflight,sum(x is not None for x in slots))
    while events:
        now,_,kind,value=heapq.heappop(events)
        if now>horizon:
            now=horizon
            break
        if kind=='capture':
            if latest is not None:record_drop(latest,'latest_replaced')
            latest=value
        elif kind=='arrival':
            p=value;counter['arrived']+=1
            if len(queue)>=cfg.mailbox_packets:
                counter['mailbox_full']+=1;failed.add(p['frame'])
                # Receiver learns a lost chunk only after a sequence gap. There
                # is no fabricated credit for the packet never admitted.
            else:
                queue.append(p);peak_mailbox=max(peak_mailbox,len(queue));dispatch()
        elif kind=='query_arrival':
            if len(queue)>=cfg.mailbox_packets:
                counter['control_mailbox_full']+=1
            else:
                queue.append(value);peak_mailbox=max(peak_mailbox,len(queue));dispatch()
        elif kind=='queried':
            p=value;busy=False;entry=ledger[p['slot']]
            if entry is not None and entry['seq']==p['seq']:
                send_feedback(p,entry['status'],query=True)
            else:
                counter['query_not_yet_known']+=1;send_feedback(p,'WAIT',query=True)
            dispatch()
        elif kind=='serviced':
            p=value;counter['serviced']+=1;busy=False
            ledger[p['slot']]=dict(slot=p['slot'],seq=p['seq'],frame=p['frame'],status='NACK' if p['reason'] else 'ACK')
            if p['reason'] is None and p['offset']+p['payload']==p['length'] and p['frame'] not in failed:
                committed.add(p['frame']);done_frames.append(dict(id=p['frame'],at_us=now,age_us=now-source[p['frame']]['capture_us']))
            send_feedback(p,'NACK' if p['reason'] else 'ACK');dispatch()
        elif kind=='credit':
            p=value;current=slots[p['slot']]
            if p['session']!=policy.session:
                counter['foreign_credit_ignored']+=1;p=dict(p,status='FOREIGN')
            if p.get('query') and p['session']==policy.session and query_inflight==(p['slot'],p['seq']):query_inflight=None
            if p['status']=='FOREIGN':pass
            elif p['status']=='WAIT':
                counter['query_wait_replies']+=1
                if current is not None and current['seq']==p['seq']:event(now+policy.feedback_timeout_ms*1000,'timeout',(p['slot'],p['seq']))
            elif p['session']!=policy.session or current is None or (current['seq'],current['frame'])!=(p['seq'],p['frame']):counter['stale_credit_ignored']+=1
            else:
                slots[p['slot']]=None;counter['credits_applied']+=1
                assert active is not None and active['frame']==p['frame']
                active['acked']+=1;active['negative']|=p['status']=='NACK'
                if active['acked']==len(active['packets']):
                    if active['frame'] not in committed:record_drop(active['frame'],'gateway_frame_failed')
                    active=None
        elif kind=='timeout':
            slot,seq=value;p=slots[slot]
            if p is not None and p['seq']==seq:
                token=(slot,seq)
                if p['queries']<policy.max_queries and token not in query_pending and query_inflight!=token:
                    query_pending.append(token)
                elif p['queries']>=policy.max_queries:counter['credit_query_exhausted']+=1
        else:raise AssertionError(kind)
        peak_ledger=max(peak_ledger,sum(x is not None for x in ledger));pump()
        assert sum(x is not None for x in slots)<=policy.window
        assert len(queue)<=cfg.mailbox_packets and len(ledger)==policy.window
    if latest is not None:record_drop(latest,'end_latest_unadmitted')
    if active is not None and active['frame'] not in committed:record_drop(active['frame'],'unresolved_credit_or_gateway')
    admitted={r['id'] for r in admissions};complete={r['id'] for r in done_frames}
    for fid in source:
        if fid not in complete and not any(d['id']==fid for d in drops):record_drop(fid,'not_completed')
    return dict(config=asdict(cfg),policy=asdict(policy),input_frames=len(source),capture_id_denominator=max(source)+1 if source else 0,
        capture_window_us=capture_end,horizon_us=horizon,admissions=admissions,drops=drops,completed=done_frames,
        strict_complete=sum(r['at_us']<capture_end for r in done_frames),eventual_complete=len(done_frames),
        packets=packet_rows,feedback=feedback,counters=dict(counter),
        ipv4_udp_data_bytes=sum(p['payload']+cfg.header+28 for p in packet_rows),
        feedback_wire_bytes=sum(f['bytes'] for f in feedback),query_wire_bytes=counter['credit_queries']*60,
        peak_host_active_frames=peak_host,peak_host_latest_frames=peak_source,peak_packet_credits=peak_inflight,
        peak_receiver_mailbox=peak_mailbox,peak_receiver_credit_ledger=peak_ledger,peak_fifo_bytes=max_fifo,
        peak_control_queries_pending=peak_control_pending,control_query_inflight=None if query_inflight is None else list(query_inflight),
        outstanding_credit_slots=[None if p is None else dict(frame=p['frame'],seq=p['seq'],queries=p['queries']) for p in slots],
        host_active_frame=None if active is None else active['frame'],receiver_active_incomplete_frame=rx_active,
        transport_queue_drained=not queue and not busy,all_admitted_packets_issued=all(sum(p['frame']==f for p in packet_rows)==len(packets(source[f],cfg)) for f in admitted),
        no_intentional_partial_frame_admission=True,
        maximum_gateway_age_ms=max((r['age_us']/1000 for r in done_frames),default=None),
        physical_30fps_proven=False,current_firmware_supports_credit_protocol=False)
