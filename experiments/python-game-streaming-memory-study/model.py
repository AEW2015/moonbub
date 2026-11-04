"""Bounded request-level SDRAM/scanline model, not a command-level controller."""
from collections import Counter, deque
from dataclasses import asdict, dataclass
from math import ceil
import heapq

@dataclass(frozen=True)
class Config:
    name: str = 'nominal'
    mode: str = 'baseline'
    clock_hz: int = 100_000_000
    fps: int = 30
    frames: int = 30
    panel_width: int = 800
    panel_height: int = 480
    scan_hz: int = 60
    prefetch_lines: int = 4
    quantum_bursts: int = 8
    burst_bytes: int = 16
    row_bytes: int = 1024
    read_cycles: int = 15
    write_cycles: int = 13
    row_change_cycles: int = 8
    turnaround_cycles: int = 2
    refresh_period: int = 780
    refresh_cycles: int = 12
    refresh_phase: int = 0
    stall_period: int = 100_000
    stall_cycles: int = 0
    stall_phase: int = 0
    mac_lanes: int = 8
    entropy_bits_per_cycle: int = 4
    sample_positions_per_cycle: int = 2
    sha_cycles_per_block: int = 80
    inverse_pipeline_cycles: int = 16
    max_decode_age_ms: int = 150
    drain_ms: int = 250
    address_window_bytes: int = 8*1024*1024
    policy: str = 'deadline_rr'

    def validate(self):
        if self.mode not in ('baseline','streaming') or self.policy not in ('strict_display','deadline_rr'):
            raise ValueError('mode/policy')
        zero={'row_change_cycles','turnaround_cycles','refresh_phase','stall_cycles','stall_phase'}
        for key,value in asdict(self).items():
            if key in ('name','mode','policy'):continue
            if type(value) is not int or value < (0 if key in zero else 1):raise ValueError(key)
        if self.refresh_cycles>=self.refresh_period or self.stall_cycles>=self.stall_period:
            raise ValueError('bounded refresh/stall duty')
        if self.refresh_phase>=self.refresh_period or self.stall_phase>=self.stall_period:
            raise ValueError('phase')
        if self.panel_width<720 or self.panel_height!=480 or self.burst_bytes!=16:
            raise ValueError('retained geometry/BL8')

def allocation(cfg):
    """One chip/bank address space; larger window is an unqualified extension."""
    cursor=0;regions={}
    def add(name,n):
        nonlocal cursor
        cursor=ceil(cursor/1024)*1024
        regions[name]=dict(address=cursor,bytes=n,padded_bytes=ceil(n/1024)*1024)
        cursor+=ceil(n/1024)*1024
    for i in range(3):add('panel'+str(i),cfg.panel_width*cfg.panel_height*2)
    for i in range(3):add('yuv'+str(i),720*480*3//2)
    for i in range(2):add('input'+str(i),49152)
    if cfg.mode=='baseline':add('coefficients',720*480*3)
    local=dict(scanline_fifo=cfg.prefetch_lines*cfg.panel_width*2,
               reconstructed_tag_stripe=8*720*2 if cfg.mode=='streaming' else 0,
               reconstructed_packed_strip=8*720 if cfg.mode=='baseline' else 0,
               coefficient_block_strip=8*720*2,prediction_strip=8*720,
               color_y_pair=2*720,color_chroma_rows=4*360,color_rgb_pair=2*720*2,
               parser_input_fifo=1024,sha_canonical_block=64,
               decoded_ui_words=21120*2,metadata=4096)
    return dict(regions=regions,external_address_end=cursor,local_bytes=local,
                local_total=sum(local.values()),window_bytes=cfg.address_window_bytes,
                window_sufficient=cursor<=cfg.address_window_bytes,
                physical_fit_proven=False)

class Request:
    def __init__(self,address,count,write,done,kind='background',deadline=None):
        self.address=address-address%16;self.count=count;self.write=write;self.done=done
        self.kind=kind;self.deadline=deadline;self.offset=0
        self.bursts=ceil((address%16+count)/16);self.remaining=self.bursts

def stages(trace,cfg,refbase,privatebase,outbase,inbase,coeffbase):
    """Causal strip schedule. Offline trace supplies counts, not runtime storage."""
    packet=trace['packet_bytes'];payload=trace['plane_payload_bytes']
    work=[]
    def mem(address,count,write):
        if count:work.append(('memory',address,count,write))
    def cpu(cycles):
        if cycles:work.append(('compute',int(cycles)))
    mem(inbase,packet,True)
    # A bounded1KiB first pass validates CRC/UI before reconstruction. CRC/UI
    # work is proportionally distributed across actual packet-byte chunks.
    total_preflight=trace['crc_validation_bytes']+trace['ui_pixels'];paid=0
    for off in range(0,packet,1024):
        nb=min(1024,packet-off);mem(inbase+off,nb,False)
        through=total_preflight*(off+nb)//packet;cpu(through-paid);paid=through
    offsets=[0,720*480,720*480+360*240]
    canonical_seen=4;payload_seen=0;block_seen=0
    blocks=sum(s['blocks'] for s in trace['stripes'])
    def parse_strip(strip):
        nonlocal payload_seen,block_seen
        block_seen+=strip['blocks'];end=payload*block_seen//blocks;nb=end-payload_seen
        # Entropy byte position is an offline block-proportional demand model,
        # not an implemented CP02 token parser. Split reads bound inputFIFO.
        previous=0
        for offset in range(0,nb,1024):
            part=min(1024,nb-offset);mem(inbase+payload_seen+offset,part,False)
            through=ceil((offset+part)*8/cfg.entropy_bits_per_cycle)
            cpu(through-previous);previous=through
        payload_seen=end
    if cfg.mode=='baseline':
        for strip in trace['stripes']:
            parse_strip(strip);off=offsets[strip['plane']]+strip['y']*strip['width']
            mem(coeffbase+2*off,2*strip['width']*strip['rows'],True)
    for strip in trace['stripes']:
        n=strip['width']*strip['rows'];off=offsets[strip['plane']]+strip['y']*strip['width']
        if cfg.mode=='baseline':mem(coeffbase+2*off,2*n,False)
        else:parse_strip(strip)
        if not trace['key']:mem(refbase+off,n,False)
        full=strip['general'];dc=strip['dc']
        cycles=ceil((1088*full+3*dc)/cfg.mac_lanes)+full*cfg.inverse_pipeline_cycles+ceil(n/cfg.sample_positions_per_cycle)
        if cfg.mode=='streaming' and trace['publication']:
            old=canonical_seen;canonical_seen+=2*n
            cycles+=(canonical_seen//64-old//64)*cfg.sha_cycles_per_block
        cpu(cycles);mem(privatebase+off,n,True)
    if trace['publication']:
        tagbytes=4+2*(720*480*3//2)
        if cfg.mode=='baseline':
            seen=4
            # Reuse the5760B predictionstrip as bounded packed tag-input FIFO.
            for off in range(0,720*480*3//2,8*720):
                n=min(8*720,720*480*3//2-off);mem(privatebase+off,n,False)
                previous=seen;seen+=2*n;cpu((seen//64-previous//64)*cfg.sha_cycles_per_block)
            cpu((ceil((tagbytes+9)/64)-seen//64)*cfg.sha_cycles_per_block)
        else:cpu((ceil((tagbytes+9)/64)-canonical_seen//64)*cfg.sha_cycles_per_block)
    # Paired output rows consume each reconstructed Y/Cb/Cr sample once with
    # a two-row Y buffer and two cached rows in each chroma plane.
    last_chroma=-1;xpad=(cfg.panel_width-720)//2
    for y in range(0,480,2):
        mem(privatebase+y*720,2*720,False)
        needed=min(239,y//2+1)
        if needed>last_chroma:
            rows=needed-last_chroma
            for plane in (1,2):mem(privatebase+offsets[plane]+(last_chroma+1)*360,rows*360,False)
            last_chroma=needed
        pixels=2*720
        cpu(ceil(pixels/cfg.sample_positions_per_cycle)+ceil(4*pixels/cfg.mac_lanes)+ceil(pixels/cfg.sample_positions_per_cycle))
        for yy in (y,y+1):mem(outbase+yy*cfg.panel_width*2+xpad*2,720*2,True)
    return work

def simulate(traces,cfg=Config()):
    cfg.validate();layout=allocation(cfg)
    if not layout['window_sufficient']:
        return dict(config=asdict(cfg),allocation=layout,status='address_window_rejected',physical_proof=False)
    if not traces or any((t['width'],t['height'])!=(720,480) for t in traces):raise ValueError('trace geometry')
    region=layout['regions'];addr=lambda name:region[name]['address']
    events=[];sequence=0;now=0;end=cfg.frames*cfg.clock_hz//cfg.fps
    horizon=end+cfg.drain_ms*cfg.clock_hz//1000
    def event(at,kind,data=None):
        nonlocal sequence
        sequence+=1;heapq.heappush(events,(int(at),0 if kind=='bus_done' else 1,sequence,kind,data))
    for fid in range(cfg.frames):event(fid*cfg.clock_hz//cfg.fps,'capture',fid)
    line_period=cfg.clock_hz/(cfg.scan_hz*cfg.panel_height)
    total_lines=ceil(horizon/line_period)
    for line in range(total_lines):event(round(line*line_period),'line',line)
    for at in range(cfg.refresh_phase,horizon,cfg.refresh_period):event(at,'refresh')
    if cfg.stall_cycles:
        for at in range(cfg.stall_phase,horizon,cfg.stall_period):event(at,'stall')
    display=deque();background=None;bus=None;open_row=None;last_write=None
    debt_refresh=debt_stall=0;last_client='display'
    inputs=[None,None];waiting=None;active=None;pending=None;front=0
    fb=[dict(frame=None,epochs=set(),readers=0,writer=False) for _ in range(3)]
    epoch_buffers={0:0};epoch_frames={0:None};fb[0]['epochs'].add(0)
    reference=[addr('yuv0'),addr('yuv1')];private=addr('yuv2');ref_readers=[0,0]
    lines={};next_line=0;last_due=-1;underflows=[];outcomes={};presented=[];completed=[];drops=[]
    missed_epochs=Counter();clean_presented=[];clean_seen=set()
    stats=Counter();peaks=Counter();traffic=Counter();wait_start=None;max_bg_wait=0
    def drop(fid,reason):
        if fid not in outcomes:outcomes[fid]=reason;drops.append(dict(id=fid,reason=reason,at_cycle=now))
    def free_fb(index):return index!=front and not fb[index]['epochs'] and not fb[index]['readers'] and not fb[index]['writer'] and index!=pending
    def choose_epoch(epoch):
        nonlocal front,pending
        if epoch not in epoch_buffers:
            if pending is not None:
                front=pending;pending=None
            epoch_buffers[epoch]=front;epoch_frames[epoch]=fb[front]['frame'];fb[front]['epochs'].add(epoch)
        return epoch_buffers[epoch]
    def refill():
        nonlocal next_line
        while len(lines)<cfg.prefetch_lines and next_line<total_lines:
            if next_line<=last_due:next_line+=1;continue
            line=next_line;next_line+=1;epoch=line//cfg.panel_height;row=line%cfg.panel_height
            index=choose_epoch(epoch);state=dict(done=False,buffer=index)
            lines[line]=state;fb[index]['readers']+=1
            def done(line=line,index=index,state=state):
                fb[index]['readers']-=1;state['done']=True
                if line<=last_due:lines.pop(line,None)
            display.append(Request(addr('panel'+str(index))+row*cfg.panel_width*2,cfg.panel_width*2,False,done,'display',round(line*line_period)))
    # Warm start: one front buffer's initial FIFO contents exist before observation.
    for line in range(cfg.prefetch_lines):
        lines[line]=dict(done=True,buffer=0);next_line=line+1
    def next_stage():
        nonlocal background,active,pending,private
        if active is None:return
        if active['position']==len(active['stages']):
            a=active;fid=a['id'];index=a['output'];fb[index]['writer']=False
            inputs[a['input']]=None
            if a['source'] is not None:ref_readers[a['source']]-=1
            if now-fid*cfg.clock_hz//cfg.fps>cfg.max_decode_age_ms*cfg.clock_hz//1000:
                drop(fid,'deadline_after_drain')
            else:
                if a['trace']['publication']:
                    dest=0 if a['trace']['key'] else 1
                    assert ref_readers[dest]==0
                    reference[dest],private=private,reference[dest]
                if pending is not None:drop(fb[pending]['frame'],'superseded_before_scanout')
                pending=index;fb[index]['frame']=fid
                completed.append(dict(id=fid,at_cycle=now,age_ms=(now-fid*cfg.clock_hz/cfg.fps)*1000/cfg.clock_hz,
                                      publication=a['trace']['publication']))
            active=None;return
        s=active['stages'][active['position']];active['position']+=1
        if s[0]=='compute':
            active['compute']=True;stats['compute_cycles']+=s[1];event(now+s[1],'compute_done',active['id'])
        else:
            assert background is None
            _,address,count,write=s
            assert 0<=address and address+ceil(count/16)*16<=cfg.address_window_bytes
            background=Request(address,count,write,next_stage)
            traffic['write' if write else 'read']+=count
    def admission():
        nonlocal waiting,active
        if active is not None or waiting is None:return
        fid,inp=waiting
        if now-fid*cfg.clock_hz//cfg.fps>cfg.max_decode_age_ms*cfg.clock_hz//1000:
            inputs[inp]=None;waiting=None;drop(fid,'stale_waiting');return
        output=next((i for i in range(3) if free_fb(i)),None)
        if output is None:return
        waiting=None;t=traces[fid%len(traces)]
        source=None if t['key'] else (0 if t['publication'] else 1)
        if source is not None:ref_readers[source]+=1
        fb[output]['writer']=True
        active=dict(id=fid,input=inp,output=output,trace=t,source=source,position=0,compute=False,
                    stages=stages(t,cfg,0 if source is None else reference[source],private,addr('panel'+str(output)),addr('input'+str(inp)),addr('coefficients') if cfg.mode=='baseline' else 0))
        stats['admitted']+=1;next_stage()
    def start_bus():
        nonlocal bus,open_row,last_write,debt_refresh,debt_stall,last_client,max_bg_wait,wait_start
        if bus is not None:return
        if debt_refresh or debt_stall:
            delay=debt_refresh+debt_stall;stats['refresh_cycles']+=debt_refresh;stats['stall_cycles']+=debt_stall
            debt_refresh=debt_stall=0;open_row=None;last_write=None
            bus=('pause',None);event(now+delay,'bus_done',bus);return
        while display and display[0].remaining==0:display.popleft()
        if not display and background is None:return
        urgent=False
        if display:
            request=display[0]
            bound=request.remaining*(cfg.read_cycles+cfg.row_change_cycles)+cfg.quantum_bursts*(max(cfg.read_cycles,cfg.write_cycles)+cfg.row_change_cycles)+cfg.refresh_cycles
            urgent=request.deadline-now<=bound
        use_display=bool(display) and (background is None or cfg.policy=='strict_display' or urgent or last_client=='background')
        request=display[0] if use_display else background
        kind='display' if use_display else 'background';last_client=kind
        if background is not None:
            if kind=='display' and wait_start is None:wait_start=now
            if kind=='background' and wait_start is not None:max_bg_wait=max(max_bg_wait,now-wait_start);wait_start=None
        count=min(cfg.quantum_bursts,request.remaining);cycles=0
        if last_write is not None and request.write!=last_write:cycles+=cfg.turnaround_cycles;stats['turnarounds']+=1
        for i in range(count):
            row=(request.address+request.offset+16*i)//cfg.row_bytes
            if row!=open_row:cycles+=cfg.row_change_cycles;stats['row_changes']+=1;open_row=row
            cycles+=cfg.write_cycles if request.write else cfg.read_cycles
        last_write=request.write;stats[kind+'_grants']+=1;stats[kind+'_bursts']+=count
        bus=(kind,request,count);event(now+cycles,'bus_done',bus)
    refill();admission();start_bus()
    while events:
        at,_,_,kind,data=heapq.heappop(events)
        if at>horizon:break
        now=at
        if kind=='capture':
            fid=data
            if waiting is not None:
                old,inp=waiting;drop(old,'latest_replaced');inputs[inp]=None;waiting=None
            inp=next((i for i,v in enumerate(inputs) if v is None),None)
            if inp is None:drop(fid,'input_pool_full')
            else:inputs[inp]=fid;waiting=(fid,inp)
        elif kind=='line':
            line=data;last_due=line
            state=lines.get(line)
            if state is not None:
                assert state['buffer']==epoch_buffers[line//cfg.panel_height]
                assert fb[state['buffer']]['frame']==epoch_frames[line//cfg.panel_height]
            if state is None or not state['done']:
                underflows.append(dict(line=line,cycle=now));missed_epochs[line//cfg.panel_height]+=1
            else:
                lines.pop(line);stats['served_line_epoch_checks']+=1
            epoch=line//cfg.panel_height
            if line%cfg.panel_height==0:
                index=epoch_buffers.get(epoch)
                if index is not None:
                    fid=fb[index]['frame']
                    if fid is not None and fid not in outcomes:
                        outcomes[fid]='presented';presented.append(dict(id=fid,at_cycle=now,age_ms=(now-fid*cfg.clock_hz/cfg.fps)*1000/cfg.clock_hz))
            if line%cfg.panel_height==cfg.panel_height-1:
                index=epoch_buffers.pop(epoch,None)
                if index is not None:
                    fid=fb[index]['frame']
                    if not missed_epochs[epoch] and fid is not None and fid not in clean_seen:
                        clean_seen.add(fid);clean_presented.append(dict(id=fid,epoch=epoch,epoch_start_cycle=round(epoch*cfg.panel_height*line_period),validated_at_cycle=now,buffer_index=index,epoch_frame_id=epoch_frames[epoch]))
                    fb[index]['epochs'].discard(epoch)
                epoch_frames.pop(epoch,None)
        elif kind=='compute_done':
            assert active is not None and active['id']==data;active['compute']=False;next_stage()
        elif kind=='refresh':debt_refresh+=cfg.refresh_cycles
        elif kind=='stall':debt_stall+=cfg.stall_cycles
        elif kind=='bus_done':
            assert bus is data;bus=None
            if data[0]!='pause':
                _,request,count=data;request.remaining-=count;request.offset+=16*count
                if not request.remaining:
                    if data[0]=='display':assert display.popleft() is request
                    else:assert background is request;background=None
                    request.done()
        else:raise AssertionError(kind)
        refill();admission();start_bus()
        peaks['input_slots']=max(peaks['input_slots'],sum(v is not None for v in inputs))
        peaks['display_fifo_slots']=max(peaks['display_fifo_slots'],len(lines))
        peaks['display_requests']=max(peaks['display_requests'],len(display))
        peaks['decoder_jobs']=max(peaks['decoder_jobs'],int(active is not None))
        peaks['background_requests']=max(peaks['background_requests'],int(background is not None))
        peaks['reference_readers']=max(peaks['reference_readers'],sum(ref_readers))
        assert len(lines)<=cfg.prefetch_lines and sum(v is not None for v in inputs)<=2
        assert sum(ref_readers)<=1 and all(v>=0 for v in ref_readers)
        assert all(not x['writer'] or (i!=front and not x['epochs'] and not x['readers']) for i,x in enumerate(fb))
    strict=[p for p in presented if p['at_cycle']<end]
    steady=[p for p in presented if cfg.clock_hz//4<=p['at_cycle']<end-cfg.clock_hz//4]
    steady_seconds=max(0,(end-cfg.clock_hz//2)/cfg.clock_hz)
    unresolved=sorted(set(range(cfg.frames))-set(outcomes))
    clean_steady=[p for p in clean_presented if cfg.clock_hz//4<=p['epoch_start_cycle']<end-cfg.clock_hz//4]
    return dict(config=asdict(cfg),allocation=layout,status='simulated',capture_count=cfg.frames,capture_end_cycle=end,horizon_cycle=horizon,
                display_line_deadline_count=total_lines,display_line_misses=len(underflows),line_miss_first=underflows[:12],
                strict_presentations=len(strict),eventual_presentations=len(presented),presented=presented,
                steady_source_ids=[p['id'] for p in steady],steady_seconds=steady_seconds,
                steady_ids_per_second=None if not steady_seconds else len(steady)/steady_seconds,
                clean_full_panel_epoch_presentations=clean_presented,clean_eventual_unique_ids=len(clean_presented),
                clean_steady_source_ids=[p['id'] for p in clean_steady],
                clean_steady_ids_per_second=None if not steady_seconds else len(clean_steady)/steady_seconds,
                completed=completed,drops=drops,drops_by_reason=dict(Counter(d['reason'] for d in drops)),
                unresolved_ids=unresolved,decoder_drained=active is None and waiting is None and background is None and all(v is None for v in inputs),
                live_scanout_reader_requests=sum(x['readers'] for x in fb),live_scanout_fifo_slots=len(lines),
                max_background_arbitration_wait_cycles=max_bg_wait,peak_bounds=dict(peaks),bus_counters=dict(stats),traffic_bytes=dict(traffic),
                physical_proof=False,packet_decode_or_reference_identity_proof=False,
                scope='Actual coefficient-count demand templates repeated with fresh model IDs; conditional integer issue rates and request-level memory service. Not AR02 replay/nativeDSP/SDRAMpart/scanlinephysicalproof.')
