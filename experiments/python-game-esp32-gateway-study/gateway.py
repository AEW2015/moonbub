"""Packet-level ESP32 gateway sensitivity model; not ISA or radio emulation."""
from collections import Counter,deque
from dataclasses import asdict,dataclass
import heapq
import math

@dataclass(frozen=True)
class Config:
    name:str='nominal'
    cpu_hz:int=240_000_000
    cpu_fraction:float=.6
    crc_cycles_per_bit_step:int=5
    copies_per_payload:int=2
    copy_cycles_per_byte:int=2
    packet_fixed_cycles:int=2000
    driver_call_us:float=20
    poll_jitter_us:float=20
    wifi_payload_mbps:float=8
    qspi_write_hz:int=40_000_000
    qspi_read_hz:int=16_000_000
    mailbox_packets:int=6
    chunk:int=1024
    header:int=40
    burst_packets:int=1
    burst_spacing_us:float=1
    fifo_bytes:int=8192
    fpga_drain_bytes_per_second:float=2_000_000
    fifo_policy:str='remaining_frame_credit'
    maximum_fifo_wait_ms:float=2
    lock_period_ms:float=16.6666667
    lock_busy_ms:float=0
    lock_phase_ms:float=0
    frame_rate:float=30
    abort_recovery_ms:float=1

    def validate(self):
        if self.fifo_policy not in ('remaining_frame_credit','bounded_fifo_wait'):raise ValueError('FIFO policy')
        for k in ('cpu_hz','crc_cycles_per_bit_step','copies_per_payload','copy_cycles_per_byte','packet_fixed_cycles','qspi_write_hz','qspi_read_hz','mailbox_packets','chunk','header','burst_packets','fifo_bytes'):
            if type(getattr(self,k)) is not int or getattr(self,k)<=0:raise ValueError(k)
        if not 0<self.cpu_fraction<=1:raise ValueError('CPU availability')
        for k in ('driver_call_us','poll_jitter_us','burst_spacing_us','maximum_fifo_wait_ms','lock_busy_ms','lock_phase_ms','abort_recovery_ms'):
            if not math.isfinite(getattr(self,k)) or getattr(self,k)<0:raise ValueError(k)
        for k in ('wifi_payload_mbps','fpga_drain_bytes_per_second','lock_period_ms','frame_rate'):
            if not math.isfinite(getattr(self,k)) or getattr(self,k)<=0:raise ValueError(k)
        if self.lock_busy_ms>self.lock_period_ms:raise ValueError('lock interval')


def packet_service_us(payload,index,cfg):
    """One serialized task: CRC/copies/control, credit reads then blocking write."""
    cfg.validate()
    cycles=payload*(8*cfg.crc_cycles_per_bit_step+cfg.copies_per_payload*cfg.copy_cycles_per_byte)+cfg.packet_fixed_cycles
    cpu=1e6*cycles/(cfg.cpu_hz*cfg.cpu_fraction)
    # read_u32: 1single-line commandbyte+4quadaddress+8quaddummy+4quaddata.
    read_us=1e6*(8+8+16+8)/cfg.qspi_read_hz
    write_us=1e6*(8+8+2*payload)/cfg.qspi_write_hz
    polls=3*read_us+3*cfg.driver_call_us
    # Frame-start 4 reads+5u32 writes; frame-commit 2reads+1u32 write.
    return dict(cpu_us=cpu,poll_us=polls+index%4*cfg.poll_jitter_us/3,
                dma_blocking_us=write_us+cfg.driver_call_us,read_u32_us=read_us,
                cpu_cycles=cycles)


def arrivals(frames,cfg):
    """Deterministic link pacing with grouped delivery bursts, no RF model."""
    result=[];wire_free=0.;sequence=0
    for frame in frames:
        fid=frame['id'];size=frame['bytes'];offset=0;packets=[]
        while offset<size:
            n=min(cfg.chunk,size-offset)
            packets.append(dict(frame=fid,offset=offset,payload=n,length=size,index=sequence))
            sequence+=1;offset+=n
        for begin in range(0,len(packets),cfg.burst_packets):
            group=packets[begin:begin+cfg.burst_packets]
            start=max(wire_free,1e6*fid/cfg.frame_rate)
            wire_us=sum((p['payload']+cfg.header+28)*8/cfg.wifi_payload_mbps for p in group)
            # Wi-Fi stacks may deliver a completed burst nearly simultaneously.
            delivered=start+wire_us
            for index,p in enumerate(group):result.append(dict(p,at_us=delivered+index*cfg.burst_spacing_us))
            wire_free=start+wire_us
    return result


def simulate(frames,cfg=Config()):
    cfg.validate();packets=arrivals(frames,cfg);events=[];seq=0;queue=deque();busy=False
    counters=Counter();records=[];peak=0;now=0.;active=None;expected_offset=0;failed=set();completed=[]
    fifo=0.;fifo_at=0.;max_fifo=0.;service_total=0.;cpu_cycles=0;waits=[];abort_service_us=0.
    def add(t,kind,p):
        nonlocal seq
        seq+=1;heapq.heappush(events,(t,0 if kind=='done' else 1,seq,kind,p))
    for p in packets:add(p['at_us'],'arrival',p)
    def drain(t):
        nonlocal fifo,fifo_at
        fifo=max(0.,fifo-(t-fifo_at)*cfg.fpga_drain_bytes_per_second/1e6);fifo_at=t
    def dispatch():
        nonlocal busy,active,expected_offset,fifo,max_fifo,service_total,cpu_cycles,abort_service_us
        if busy or not queue:return
        p=queue.popleft();busy=True;fid=p['frame'];start=now
        service=packet_service_us(p['payload'],p['index'],cfg);cpu_cycles+=service['cpu_cycles']
        done=start+service['cpu_us']+service['poll_us']
        reason=None
        if p['offset']==0:
            if active is not None:
                penalty=cfg.abort_recovery_ms*1000+2*(service['read_u32_us']+cfg.driver_call_us)+24/cfg.qspi_write_hz*1e6+cfg.driver_call_us
                done+=penalty;abort_service_us+=penalty;counters['abort_calls']+=1
            active=None
            begin_busy=((done/1000-cfg.lock_phase_ms)%cfg.lock_period_ms)<cfg.lock_busy_ms
            if begin_busy:reason='begin_device_lock_busy'
            else:active=fid;expected_offset=0
            # Control transaction overhead is a scenario approximation, not exact driver timing.
            if not reason:done+=4*(service['read_u32_us']+cfg.driver_call_us)+5*(24/cfg.qspi_write_hz*1e6+cfg.driver_call_us)
        if not reason and (active!=fid or p['offset']!=expected_offset or fid in failed):reason='sequence_after_loss'
        if not reason and ((done/1000-cfg.lock_phase_ms)%cfg.lock_period_ms)<cfg.lock_busy_ms:reason='device_lock_busy'
        if not reason:
            drain(done)
            shortage=max(0.,fifo+p['payload']-cfg.fifo_bytes)
            if shortage:
                wait=shortage/cfg.fpga_drain_bytes_per_second*1e6
                if cfg.fifo_policy=='bounded_fifo_wait' and wait<=cfg.maximum_fifo_wait_ms*1000:
                    done+=wait;drain(done);waits.append(wait)
                else:reason='fifo_overflow' if cfg.fifo_policy=='remaining_frame_credit' else 'fifo_wait_timeout'
            if not reason:
                done+=service['dma_blocking_us'];drain(done);fifo+=p['payload'];max_fifo=max(max_fifo,fifo)
                expected_offset+=p['payload']
                if expected_offset==p['length']:
                    done+=2*(service['read_u32_us']+cfg.driver_call_us)+24/cfg.qspi_write_hz*1e6+cfg.driver_call_us
                    active=None
        if reason:
            if active is not None:
                penalty=cfg.abort_recovery_ms*1000+2*(service['read_u32_us']+cfg.driver_call_us)+24/cfg.qspi_write_hz*1e6+cfg.driver_call_us
                done+=penalty;abort_service_us+=penalty;counters['abort_calls']+=1
            failed.add(fid);active=None;counters[reason]+=1
        service_total+=done-start
        add(done,'done',dict(p,start_us=start,done_us=done,reason=reason,service=service))
    while events:
        now,_,_,kind,p=heapq.heappop(events)
        if kind=='arrival':
            counters['arrived']+=1
            if len(queue)>=cfg.mailbox_packets:
                counters['mailbox_full']+=1
            else:queue.append(p);peak=max(peak,len(queue));dispatch()
        else:
            records.append(p);counters['serviced']+=1
            if p['reason'] is None:
                counters['forwarded']+=1
                if p['offset']+p['payload']==p['length'] and p['frame'] not in failed:
                    completed.append(dict(id=p['frame'],at_ms=now/1000,age_ms=now/1000-p['frame']*1000/cfg.frame_rate))
            busy=False;dispatch()
    end_ms=1000*(max(p['id'] for p in frames)+1)/cfg.frame_rate if frames else 0
    sizes=sum(p['bytes'] for p in frames);wire_bytes=sum(p['payload']+cfg.header+28 for p in packets)
    # Mean service bound ignores lock failures, burst loss and FIFO waits; label it as such.
    direct=sum(sum(v for k,v in packet_service_us(p['payload'],p['index'],cfg).items() if k in ('cpu_us','poll_us','dma_blocking_us')) for p in packets)
    return dict(config=asdict(cfg),frames=len(frames),packets=len(packets),input_payload_bytes=sizes,ipv4_udp_wire_bytes=wire_bytes,
                capture_id_denominator=max(p['id'] for p in frames)+1 if frames else 0,completed_frames=len(completed),strict_completed_frames=sum(c['at_ms']<end_ms for c in completed),completed=completed,failed_frames=sorted(set(p['id'] for p in frames)-{c['id'] for c in completed}),
                counters=dict(counters),peak_mailbox=peak,peak_dma_working_packets=1 if records else 0,
                peak_fifo_bytes=max_fifo,fifo_waits_us=waits,service_total_us=service_total,abort_service_us=abort_service_us,charged_cpu_cycles=cpu_cycles,
                capture_window_ms=end_ms,drain_end_ms=now/1000,
                mean_input_payload_mbps=sizes*8/(end_ms*1000) if end_ms else 0,
                required_ipv4_udp_mbps=wire_bytes*8/(end_ms*1000) if end_ms else 0,
                no_contention_mean_packet_service_ceiling_payload_mbps=sizes*8/direct if direct else None,
                maximum_completed_age_ms=max((c['age_ms'] for c in completed),default=None),
                queue_drained=not queue and not busy,transport_queue_drained=not queue and not busy,active_incomplete_frame_at_end=active,
                idle_500ms_timeout_simulated=False,protocol_supported_by_current_firmware=False,
                physical_30fps_proven=False)


def ram_budget(facts,available_internal_bytes=320*1024,ui_heap_reserve=96*1024,other_runtime_reserve=64*1024,
               wifi_buffer_bytes=1600,mailbox_pbuf_reserve=True,largest_dma_block_bytes=4096):
    # Conservative independent reserves may double-count aliased networking buffers.
    parts=dict(stream_stack=facts['stream_stack_bytes'],main_stack=facts['main_stack_bytes'],
               working_dma=facts['dma_buffer_bytes'],wifi_static=facts['wifi_static_rx']*wifi_buffer_bytes,
               wifi_dynamic_max=facts['wifi_dynamic_rx']*wifi_buffer_bytes,
               udp_mailbox_payloads=facts['udp_mailbox_packets']*(facts['payload_bytes']+facts['header_bytes']) if mailbox_pbuf_reserve else 0,
               udp_descriptors=facts['udp_mailbox_packets']*32,ui_heap_reserve=ui_heap_reserve,other_runtime_reserve=other_runtime_reserve)
    total=sum(parts.values())
    return dict(assumed_available_internal_bytes=available_internal_bytes,reserve_bytes=parts,total_reserve=total,
                reserve_margin=available_internal_bytes-total,assumed_largest_dma_block_bytes=largest_dma_block_bytes,
                working_dma_contiguous_requirement=facts['dma_buffer_bytes'],
                contiguous_requirement_met_by_assumption=largest_dma_block_bytes>=facts['dma_buffer_bytes'],
                fit_proven=False,psram_assumed=False,network_aliasing_unknown=True)
