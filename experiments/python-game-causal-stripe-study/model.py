"""Actual AR03 sparse-inverse work and bounded stripe planning model.

Arithmetic comparison is exact. Service times are declared assumptions, not FPGA
cycles, native execution, mapped memory fit, or physical scanline proof.
"""
from dataclasses import dataclass,asdict
from pathlib import Path
import math,sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-game-ar03-trace-study'))
import trace_codec as trace
import importlib.util
_spec=importlib.util.spec_from_file_location('v19_ar03_fixture_reader',HERE.parent/'python-game-ar03-trace-study/verify.py')
fixture=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=fixture;_spec.loader.exec_module(fixture)
ft=trace.codec.gm.ft

def signed_bits(max_abs):return max(1,int(max_abs).bit_length()+1)

def inverse(a):
    """Exact two-pass Q14 inverse with zero/DC and actual zero-product skipping.

Zero discovery, output writes and index work are not free in the service model.
The Python batch arrays are correctness oracles, not the proposed local storage.
"""
    a=np.asarray(a,dtype=np.int64)
    if a.ndim!=3 or a.shape[1:]!=(8,8) or a.min(initial=0)<-522240 or a.max(initial=0)>522240:raise ValueError('legal dequantized8x8 block batch')
    n=len(a);flat=a.reshape(n,64);general=np.any(flat[:,1:]!=0,axis=1);dc=(~general)&(flat[:,0]!=0);zero=(~general)&(~dc)
    out=np.zeros_like(a);first=np.zeros(n,np.int64);second=np.zeros(n,np.int64);mid_nnz=np.zeros(n,np.int64)
    first_acc=second_acc=first_product=second_product=0
    max_second_input=0
    if np.any(dc):
        v=a[dc,0,0];stage=(v*5793+8192)>>14
        out[dc]=((stage*5793+8192)>>14)[:,None,None]
        max_second_input=max(max_second_input,int(np.max(np.abs(stage))))
        first_acc=max(first_acc,int(np.max(np.abs(v*5793))));second_acc=max(second_acc,int(np.max(np.abs(stage*5793))))
        first_product=max(first_product,first_acc);second_product=max(second_product,second_acc)
    if np.any(general):
        selected=a[general];mid=np.zeros_like(selected)
        for k in range(8):
            bi,ri=np.nonzero(selected[:,:,k]);products=selected[bi,ri,k,None]*ft.Q14[k,:]
            mid[bi,ri,:]+=products
            first_acc=max(first_acc,int(np.max(np.abs(mid),initial=0)));first_product=max(first_product,int(np.max(np.abs(products),initial=0)))
        mid=(mid+8192)>>14
        max_second_input=max(max_second_input,int(np.max(np.abs(mid),initial=0)))
        result=np.zeros_like(selected)
        for k in range(8):
            bi,ci=np.nonzero(mid[:,k,:]);products=mid[bi,k,ci,None]*ft.Q14[k,:]
            result[bi,:,ci]+=products
            second_acc=max(second_acc,int(np.max(np.abs(result),initial=0)));second_product=max(second_product,int(np.max(np.abs(products),initial=0)))
        out[general]=(result+8192)>>14
        first[general]=8*np.count_nonzero(selected,axis=(1,2));second[general]=8*np.count_nonzero(mid,axis=(1,2));mid_nnz[general]=np.count_nonzero(mid,axis=(1,2))
    return out,dict(blocks=n,zero=int(zero.sum()),dc=int(dc.sum()),general=int(general.sum()),
        first_mac=first.tolist(),second_mac=second.tolist(),nonzero_coeff=np.count_nonzero(a,axis=(1,2)).tolist(),intermediate_nnz=mid_nnz.tolist(),
        dc_constant_multiplies=2*int(dc.sum()),max_first_accumulator_abs=first_acc,max_second_accumulator_abs=second_acc,
        max_first_product_abs=first_product,max_second_product_abs=second_product,
        max_dequantized_abs=int(np.abs(a).max(initial=0)),max_second_multiply_input_abs=max_second_input,
        rounding_bias_abs_upper=max(first_acc,second_acc)+8192,
        observed_accumulator_signed_bits=signed_bits(max(first_acc,second_acc)+8192))

def selected_reads(rec):
    def size(r):return 0 if r is None else r[1]-r[0]
    if rec['storage']=='raw':return size(rec['raw_range'])
    if rec['storage']=='rice':return size(rec['dc_read_range'])+size(rec['ac_read_range'])
    return size(rec['mode_read_range'])+size(rec.get('dc_value_range'))+(selected_reads(rec['compact_cp02']) if 'compact_cp02' in rec else 0)

def logical_bits(rec):
    if rec['storage']=='raw':return 8*(rec['raw_range'][1]-rec['raw_range'][0])
    if rec['storage']=='rice':return sum(rec[k][1]-rec[k][0] for k in ('dc_bits','ac_bits'))
    return 2+(16 if rec.get('dc_value_range') else 0)+(logical_bits(rec['compact_cp02']) if 'compact_cp02' in rec else 0)

@dataclass(frozen=True)
class Budget:
    clock_mhz:float=100
    wide_lanes:int=4
    sparse:bool=True
    bypass:bool=True
    stripe_buffers:int=2
    entropy_bits_cycle:float=8
    compressed_cache_bytes_cycle:float=1
    index_coeff_cycle:float=1
    dequant_cycle_per_lane:float=1
    output_samples_cycle:float=1
    color_control_cycles_pixel:float=2
    pass_overhead_cycles:int=16
    effective_sdram_MBps:float=140
    scanout_width:int=800
    scanout_height:int=480
    scanout_hz:float=60
    bytes_per_sample:int=2
    qspi_MBps:float=20
    memory_burst_bytes:int=64
    memory_burst_overhead_ns:float=80
    packet_preflight_passes:int=4
    crc_MBps:float=100
    tag_hash_MBps:float=100
    tag_expand_cycles_sample:float=1
    ui_pixels_cycle:float=1
    frame_budget_ms:float=1000/30

    def validate(self):
        ints=('wide_lanes','stripe_buffers','pass_overhead_cycles','scanout_width','scanout_height','bytes_per_sample','memory_burst_bytes','packet_preflight_passes')
        if any(type(getattr(self,k))is not int or getattr(self,k)<1 for k in ints):raise ValueError('positive integral budget')
        if self.stripe_buffers>4 or self.wide_lanes>32 or type(self.sparse)is not bool or type(self.bypass)is not bool or (self.sparse and not self.bypass):raise ValueError('bounded lanes/buffers')
        for k,v in asdict(self).items():
            if type(v) in (int,float) and (not math.isfinite(v) or v<=0):raise ValueError('positive finite budget')
        if self.effective_sdram_MBps<=self.scanout_width*self.scanout_height*self.scanout_hz*2/1e6:raise ValueError('no service after scanout reservation')

def block_cycles(s,b):
    """Two dependent passes; scan, dequant, round overhead and output all paid."""
    n=s['blocks'];z=s['zero'];d=s['dc'];g=s['general']
    writes=n*math.ceil(64/b.output_samples_cycle)
    if b.bypass:
        scan=n*math.ceil(64/b.index_coeff_cycle)+(g*math.ceil(64/b.index_coeff_cycle) if b.sparse else 0)
        dequant=(sum(math.ceil(x*b.dequant_cycle_per_lane/b.wide_lanes) for x in s['nonzero_coeff']) if b.sparse else g*math.ceil(64*b.dequant_cycle_per_lane/b.wide_lanes)+d)
        mult=(sum(math.ceil(x/b.wide_lanes)+math.ceil(y/b.wide_lanes) for x,y in zip(s['first_mac'],s['second_mac'])) if b.sparse else g*2*math.ceil(512/b.wide_lanes))+2*d
        overhead=(2*g+2*d)*b.pass_overhead_cycles
    else:
        scan=0;dequant=n*math.ceil(64*b.dequant_cycle_per_lane/b.wide_lanes)
        mult=n*2*math.ceil(512/b.wide_lanes);overhead=2*n*b.pass_overhead_cycles
    return dict(index_scan=scan,dequant=dequant,dependent_mac=mult,pass_overhead=overhead,output=writes,total=scan+dequant+mult+overhead+writes)

def schedule(frame,b=Budget(),uniform=False):
    """Two bounded coefficient stripes; one prediction/inverse/write consumer.

Complete compressed packet is staged externally, CRC/preflight paid before any
stripe. Entropy can overlap consumer, with backpressure when its stripe bank is
owned. Shared-memory consumer is deliberately serial (not optimistic future
reservation); scanout receives a declared rate reservation, not line deadlines.
"""
    b.validate();reserve=b.scanout_width*b.scanout_height*b.scanout_hz*2/1e6
    memrate=b.effective_sdram_MBps-reserve
    def transfer(n):return n/(memrate*1000)+math.ceil(n/b.memory_burst_bytes)*b.memory_burst_overhead_ns/1e6
    staged=frame['packet_bytes']/(b.qspi_MBps*1000)+transfer(frame['packet_bytes'])
    preflight_bytes=b.packet_preflight_passes*frame['packet_bytes']
    preflight=transfer(preflight_bytes)+preflight_bytes/(b.crc_MBps*1000)
    cache_read=transfer(frame['packet_bytes'])
    start=staged+preflight+cache_read;entropy_free=consumer_free=start;buffer_free=[start]*b.stripe_buffers
    entries=[];wait=0;peak_coeff=0;total_refill=sum(s['refill_bytes'] for s in frame['stripes'])
    total_bits=sum(s['logical_bits'] for s in frame['stripes'])
    plane_totals={p:{k:sum(s[k] for s in frame['stripes'] if s['plane']==p) for k in ('blocks','refill_bytes','logical_bits')} for p in range(3)}
    for i,s in enumerate(frame['stripes']):
        slot=i%b.stripe_buffers;es=max(entropy_free,buffer_free[slot]);wait+=es-entropy_free
        pt=plane_totals[s['plane']]
        refill=pt['refill_bytes']*s['blocks']/pt['blocks'] if uniform else s['refill_bytes']
        bits=pt['logical_bits']*s['blocks']/pt['blocks'] if uniform else s['logical_bits']
        entropy_cycles=math.ceil(max(refill/b.compressed_cache_bytes_cycle,bits/b.entropy_bits_cycle))+2*s['blocks']
        ee=es+entropy_cycles/(b.clock_mhz*1000);entropy_free=ee
        cs=max(consumer_free,ee);pred_bytes=0 if frame['key'] else s['samples']*b.bytes_per_sample
        pred_done=cs+transfer(pred_bytes)
        cycles=block_cycles(s['work'],b);inverse_done=pred_done+cycles['total']/(b.clock_mhz*1000)
        write_bytes=s['samples']*b.bytes_per_sample;done=inverse_done+transfer(write_bytes)
        consumer_free=done;buffer_free[slot]=done
        entries.append(dict(index=i,plane=s['plane'],y=s['y'],blocks=s['blocks'],refill_bytes=refill,logical_bits=bits,
            entropy_start_ms=es,entropy_done_ms=ee,consumer_start_ms=cs,prediction_done_ms=pred_done,inverse_done_ms=inverse_done,done_ms=done,
            coefficient_slot=slot,coefficient_bytes=s['blocks']*64*2,prediction_read_bytes=pred_bytes,reconstruction_write_bytes=write_bytes,cycles=cycles))
    # Canonical stored reference tags serialize int16 Y/Cb/Cr; color conversion
    # reads all planes and writes a complete coded RGB565 frame; UI is display-only.
    tag_bytes=4+frame['samples']*b.bytes_per_sample if frame['published'] else 0
    tag_canonical_bytes=4+frame['samples']*2 if frame['published'] else 0
    color_read=frame['samples']*b.bytes_per_sample;display_write=frame['width']*frame['height']*2
    ui_write=frame['selected_ui_pixels']*2
    post_bytes=tag_bytes+color_read+display_write+ui_write
    color_multiplies=4*frame['width']*frame['height']
    color_cycles=math.ceil(color_multiplies/b.wide_lanes)+math.ceil(frame['width']*frame['height']*b.color_control_cycles_pixel)
    tag_expand_cycles=frame['samples']*b.tag_expand_cycles_sample if frame['published'] and b.bytes_per_sample==1 else 0
    post_ms=transfer(post_bytes)+(frame['selected_ui_pixels']/b.ui_pixels_cycle+color_cycles+tag_expand_cycles)/(b.clock_mhz*1000)+tag_canonical_bytes/(b.tag_hash_MBps*1000)
    color_lines_bytes=frame['width']*(4*4+2+2) #2horizontal rows perCb/Cr int32 +Y16/RGB565 lines
    ui_palette_bytes=512 if frame['selected_ui_pixels'] else 0
    done=consumer_free+post_ms
    local_coefficient_bytes=b.stripe_buffers*max((e['coefficient_bytes'] for e in entries),default=0)
    return dict(config=asdict(b),uniform=uniform,scanout_reserved_MBps=reserve,decoder_memory_MBps=memrate,
        packet_staging_bytes=frame['packet_bytes'],preflight_read_bytes=preflight_bytes,compressed_cache_load_read_bytes=frame['packet_bytes'],
        local_compressed_cache_bytes=49152,local_inverse_scratch_bytes=960,local_basis_quantizer_rom_bytes=512,local_color_line_bytes=color_lines_bytes,local_ui_palette_bytes=ui_palette_bytes,
        local_buffer_total_bytes=49152+local_coefficient_bytes+max((e['coefficient_bytes'] for e in entries),default=0)+16+960+512+color_lines_bytes+ui_palette_bytes,
        entropy_refill_bytes=total_refill,prediction_read_bytes=sum(e['prediction_read_bytes'] for e in entries),
        reconstruction_write_bytes=sum(e['reconstruction_write_bytes'] for e in entries),tag_read_bytes=tag_bytes,tag_canonical_hashed_bytes=tag_canonical_bytes,tag_expand_cycles=tag_expand_cycles,color_constant_multiplies=color_multiplies,color_control_and_mac_cycles=color_cycles,
        color_read_bytes=color_read,display_write_bytes=display_write,ui_display_only_write_bytes=ui_write,
        staged_ms=staged,preflight_ms=preflight,compressed_cache_load_ms=cache_read,postprocess_ms=post_ms,frame_done_ms=done,
        frame_budget_ms=b.frame_budget_ms,missed_frame_budget=done>b.frame_budget_ms,
        entropy_backpressure_ms=wait,local_coefficient_stripe_bytes=local_coefficient_bytes,
        local_reconstruction_stripe_bytes=max((e['coefficient_bytes'] for e in entries),default=0),
        two_entropy_reservoir_bits_max_each=64,conditional_18x18_multiplier_primitives=2*b.wide_lanes,
        stripes=entries)

def legal_width_bounds():
    """Conservative absolute bounds include each frozen +8192 rounding bias."""
    qmax=int(np.abs(ft.Q14).max());dequant=ft.MAX_COEFF*255
    first_acc=8*dequant*qmax;mid=(first_acc+8192)//16384
    second_acc=8*mid*qmax
    return dict(max_quantized_abs=ft.MAX_COEFF,max_quantizer=255,max_q14_abs=qmax,
        dequant_abs_bound=dequant,first_biased_accumulator_abs_bound=first_acc+8192,
        intermediate_abs_bound=mid,second_biased_accumulator_abs_bound=second_acc+8192,
        dequant_signed_bits=signed_bits(dequant),intermediate_signed_bits=signed_bits(mid),
        accumulator_signed_bits=signed_bits(max(first_acc,second_acc)+8192),
        product_slots_assumed=dict(left_signed_bits=32,right_signed_bits=16,accumulator_signed_bits=40))
