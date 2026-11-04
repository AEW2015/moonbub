#!/usr/bin/env python3
"""Encode deterministic real AR02 packets then count work; never time hardware."""
import hashlib
import json
from pathlib import Path
import sys
import av
from PIL import Image
from fractions import Fraction
from dataclasses import replace
import numpy as np
import budget
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'python-game-unified-codec-study'))
import unified_codec as codec
from ui_plugin import PatchSelector


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def source(width,height,index):
    y,x=np.indices((height,width))
    image=np.stack((30+(x//8+index)%150,40+(y//8+index)%130,60+(x//32+y//32)%100),axis=-1).astype(np.uint8)
    if width==720:
        for rx,ry,rw,rh in PatchSelector().rectangles:image[ry:ry+rh,rx:rx+rw]=[40+index,90,150]
    return image


def trace_packet(packet,label):
    m=codec.identity(packet,decode=True);p=m['parsed'];planes=[]
    for i,c in enumerate(p['coefficients']):
        a=c.reshape(-1,64);mixed=np.any(a[:,1:]!=0,axis=1);dc=~mixed&(a[:,0]!=0);zero=~mixed&~dc
        planes.append(dict(plane=i,blocks=len(a),general_inverse=int(mixed.sum()),dc_only=int(dc.sum()),zero=int(zero.sum())))
    f=codec.gm.HEADER.unpack_from(m['inner'])
    pos=codec.gm.HEADER.size+f[12]
    crc_bytes=len(packet)-4+len(m['inner'])-4+sum(len(p)-4 for p in m['patch_packets'])
    for length in f[13:16]:
        blob=m['inner'][pos:pos+length];pos+=length
        if m['inner_codec']=='GM01':crc_bytes+=len(blob)-4
        else:
            _,mode,n,nmap,ndc,nfull=codec.sr.PLANE.unpack_from(blob)
            if nfull:crc_bytes+=nfull-4
    return dict(label=label,width=m['width'],height=m['height'],key=m['key'],publication=m['destination_bank']!=codec.NO_BANK,
                selected_codec=m['inner_codec'],packet_bytes=len(packet),packet_sha256=hashlib.sha256(packet).hexdigest(),packet_hex=packet.hex(),
                inner_bytes=len(m['inner']),plane_payload_bytes=sum(f[13:16]),crc_validation_bytes=crc_bytes,
                ui_pixels=sum(x['rect'][2]*x['rect'][3] for x in m['patches']),planes=planes,
                trace_scope='Actual admitted AR02 packet parsed into decoded coefficients; deterministic synthetic pixels, not native gameplay.')


def pins():
    modules=[codec,codec.old,codec.overlap_codec,codec.sr,codec.fast_codec,codec.gm,codec.gm.roi,codec.gm.mt,codec.gm.ft,
             codec.gm.token_coeff,codec.gm.word_coeff,codec.gm.word_coeff.frozen_codec,codec.corpus]
    import ui_plugin
    modules += [ui_plugin,ui_plugin.frozen_cache,ui_plugin.hybrid,ui_plugin.row,ui_plugin.hp]
    paths={Path(m.__file__).resolve() for m in modules}|{HERE/'budget.py',HERE/'benchmark.py',HERE/'verify.py',HERE/'test_budget.py',ROOT/'docs/external-memory-audit-plan.md'}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}


def build():
    before=pins();traces=[]
    for width,height in [(64,48),(720,480)]:
        for mode in ['gm','exact']:
            enc=codec.Encoder(mode=mode,patch_builder=PatchSelector() if width==720 else None);rx=codec.Receiver()
            for i in range(3):
                rgb=source(width,height,i);d=enc.prepare(rgb,i,promote=i==1)
                assert d.accepted
                trace=trace_packet(d.packet,f'{width}x{height}_{mode}_{i}')
                assert sum(p['blocks'] for p in trace['planes'])==sum(((w+7)//8)*((h+7)//8) for w,h in [(width,height),(width//2,height//2),(width//2,height//2)])
                task=rx.begin(d.packet);assert task.info['selected_pixels']==trace['ui_pixels']
                _,info,ack=rx.complete(task);assert enc.ack(ack)
                if not trace['key']:assert info['reference_read_bytes']==width*height*3//2
                traces.append(trace)
    media=ROOT.parents[1]/'media/mass-effect-2600.mp4'
    media_before=sha(media);native=[];pts=[];native_hashes=[]
    with av.open(str(media)) as container:
        stream=container.streams.video[0]
        for frame in container.decode(stream):
            if frame.pts is None or Fraction(frame.pts)*frame.time_base<Fraction(4):continue
            raw=frame.to_ndarray(format='rgb24');native_hashes.append(hashlib.sha256(raw.tobytes()).hexdigest())
            fitted=np.asarray(Image.fromarray(raw).resize((720,405),Image.Resampling.BOX))
            canvas=np.zeros((480,720,3),np.uint8);canvas[37:442]=fitted
            native.append(canvas);pts.append(frame.pts)
            if len(native)==3:break
        media_meta=dict(source=str(media),source_sha256=media_before,source_fps=str(stream.average_rate),
                        selected_pts=pts,native_rgb_sha256=native_hashes,active_canvas='720x405atrow37inside720x480',
                        resampler='PillowBOX',capture_scope='Offline precompressed clip at4seconds, not live30fps acquisition')
    for mode in ['gm','exact']:
        enc=codec.Encoder(mode=mode,patch_builder=PatchSelector());rx=codec.Receiver()
        for i,rgb in enumerate(native):
            d=enc.prepare(rgb,i,promote=i==1);assert d.accepted
            t=trace_packet(d.packet,f'720x480_native_{mode}_{i}');t['trace_scope']='Actual admitted native-derived AR02; uniformscale16; offline clip/PillowBOX, not matched v15 finite stream timing.'
            traces.append(t)
            task=rx.begin(d.packet);_,_,ack=rx.complete(task);assert enc.ack(ack)
    assert len(native)==3 and media_before==sha(media)
    # Analytical all-general P decode, not a claim that dense noise fits the cap.
    dense=dict(traces[-1]);dense.update(label='720x480_analytical_all_general_P',selected_codec='analytical',
        packet_bytes=49152,plane_payload_bytes=49000,crc_validation_bytes=3*49152,packet_sha256=None,packet_hex=None,key=False,publication=True,
        trace_scope='Analytical dense-block and maximum-admitted-byte conjunction; not a serialized/admitted packet and not all legal worst cases.')
    dense['planes']=[dict(plane=i,blocks=p['blocks'],general_inverse=p['blocks'],dc_only=0,zero=0) for i,p in enumerate(dense['planes'])]
    traces.append(dense)
    results=[dict(trace=t['label'],estimate=budget.estimate(t,a)) for t in traces for a in budget.scenarios()]
    sweep=[]
    for t in traces:
        if t['width']!=720:continue
        for lanes in [4,8,16,32]:
            # Scan integer MHz, no interpolation or hidden measured-target inference.
            first=None
            for mhz in range(50,201):
                e=budget.estimate(t,replace(budget.Architecture(),clock_hz=mhz*1_000_000,dsp_lanes=lanes))
                if e['passes_average_30fps_budget']:
                    first=mhz;break
            sweep.append(dict(trace=t['label'],dsp_lanes=lanes,first_passing_clock_mhz=first,
                              clock_search_mhz=[50,200],step_mhz=1,burst_profile='read15/write13BL8',
                              caveat='Only average serialized planning budget; no clock closure or deadline proof.'))
    assert before==pins()
    caps=budget.capacity()
    return dict(source_sha256=before,input_media=media_meta,trace_count=len(traces),actual_packet_traces=len(traces)-1,traces=traces,estimates=results,
                clock_sweep=sweep,capacity_bytes=caps,capacity_total=sum(caps.values()),modeled_memory_capacity_bytes=2*1024*1024,
                advertised_sdram_bytes=64*1024*1024,advertised_sram_bytes=512*1024,
                sources='Local v15 arithmetic and external-memory-audit-plan.md; chip1/SRAM are not assumed implemented.',
                scope='Offline Python operation/service assumptions; neither synthesis nor physical timing/native30fps/line-deadline proof.',
                architecture_scope='8-bit reference/reconstruction memory, external fullYUV scratch, local decoded UI + two-chroma-row cache, direct RGB565 mux; stages serialized; display budget reserved before background fair-average service.',
                entropy_scope='All plane payload bits counted at assumed bits/cycle; variable Rice-token control and worst-case timing unimplemented. No actual pipeline scheduling evidence.',
                memory_scope='Capacity plan includes fullcoeffscratch and metadata but excludes vendor IP/CDC/control implementation buffers. Not a peak physical allocation or BRAM fit proof.',
                nominal_timing_scope='BL8 serialized read15/write13 and rowmiss23/21 intervals are local short RTL handshake observations, not board service; optimistic8/8 is hypothetical. No refresh collision/row sequence/deadline guarantee.')

def main():
    result=build();(HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    for row in result['estimates']:
        if row['trace'].startswith('720'):
            e=row['estimate'];print(row['trace'],e['architecture']['name'],round(e['serialized_planning_frame_ms'],3) if e['serialized_planning_frame_ms'] else None,e['passes_average_30fps_budget'])
    print('capacity_bytes',result['capacity_total'])

if __name__=='__main__':main()
