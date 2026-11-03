#!/usr/bin/env python3
"""Actual BM01 packets versus frozen GM01 zero/global on matching source IDs."""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import av
import numpy as np
import PIL
import block_codec as bc
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus
spec=importlib.util.spec_from_file_location('v11_block_metrics',HERE.parent/'python-game-roi-study/benchmark.py')
quality=importlib.util.module_from_spec(spec);sys.modules[spec.name]=quality;spec.loader.exec_module(quality)
RECTS=((16,48,192,80),(160,352,400,80))
PROFILES=('gm_zero','gm_global','bm_block4')

def scaled_rectangles(rectangles,width,height):
    out=[]
    for x,y,w,h in rectangles:
        x0=max(0,min(width-1,round(x*width/720)));y0=max(0,min(height-1,round(y*height/480)))
        x1=max(x0+1,min(width,round((x+w)*width/720)));y1=max(y0+1,min(height,round((y+h)*height/480)))
        out.append((x0,y0,x1-x0,y1-y0))
    return tuple(out)


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def synthetic():
    rng=np.random.default_rng(1111);h,w=96,128
    # Textured blocks translate in opposite directions, unlike a single global vector.
    image=rng.integers(30,226,(h,w,3),dtype=np.uint8)
    image=(image//16*16).astype(np.uint8)
    def translated(i):
        yy,xx=np.mgrid[:h,:w];shift=2*(i%3)
        dx=np.where(xx<w//2,shift,-shift)
        return image[yy,np.clip(xx+dx,0,w-1)]
    return [('synthetic-static128',[np.full((h,w,3),128,np.uint8) for _ in range(8)]),
            ('synthetic-block-translation',[translated(i) for i in range(8)]),
            ('synthetic-noise-cut',[rng.integers(0,256,(h,w,3),dtype=np.uint8) if i<4 else
                                     np.full((h,w,3),220,np.uint8) for i in range(8)])]


def run_scene(name,frames,manifest,rectangles,key_period):
    records=[]
    for profile in PROFILES:
        block=profile=='bm_block4';enc=bc.Encoder() if block else bc.gc.Encoder()
        rx=bc.Receiver() if block else bc.gc.Receiver()
        for i,rgb in enumerate(frames):
            h,w=rgb.shape[:2]
            started=time.perf_counter_ns()
            m=bc.roi.declared_map(w,h,rectangles,8,16)
            if block:packet=enc.prepare(rgb,i,scale_map=m,force_key=i%key_period==0)
            else:packet=enc.prepare(rgb,i,scale_map=m,force_key=i%key_period==0,mode='zero' if profile=='gm_zero' else 'global')
            prepare_ms=(time.perf_counter_ns()-started)/1e6
            started=time.perf_counter_ns();actual,info=rx.receive(packet);receive_ms=(time.perf_counter_ns()-started)/1e6
            expected=enc.expected_hash(i);actual_hash=hashlib.sha256(actual.tobytes()).hexdigest()
            assert actual_hash==expected
            parsed=bc.parse(packet,1) if block else bc.gc.parse(packet,1)
            if block:assert enc.ack(i,epoch=1,frame_crc=zlib_crc(packet))
            else:assert enc.ack(i,epoch=1)
            metrics=quality.metric(rgb,actual,rectangles,tuple(manifest['active_rects'][i]),False)
            n=len(packet);wire=n+59*math.ceil(n/1024)
            row=dict(id=i,profile=profile,input_sha256=manifest['frame_sha256'][i],
                     packet_sha256=hashlib.sha256(packet).hexdigest(),rgb_sha256=actual_hash,
                     bytes=n,forward_ipv4_udp_size_calculation=wire,feedback_size_assumption=52,
                     cap_fit=n<=49152,key=info['key'],reference_id=parsed['reference_id'],anchor_id=info['anchor_id'],
                     prepare_ms=prepare_ms,receive_ms=receive_ms,map_bytes=parsed['map_bytes'],
                     vector_bytes=parsed['vector_bytes'] if block else 0,global_vector_bytes_inside_header=0 if block else 4,
                     header_crc_bytes=(bc.HEADER.size if block else bc.gc.HEADER.size)+4,
                     zero_residual=parsed['zero_residual'] if block else False,metrics=metrics)
            if block:
                row['block_services']=dict(enc.last_info)
                row['vector_mode']=parsed['vector_mode']
                row['nonzero_vector_blocks']=int(np.count_nonzero(np.any(parsed['vectors']!=0,axis=2)))
            records.append(row)
        assert not enc.pending
    return dict(name=name,manifest=manifest,rectangles=rectangles,key_period=key_period,records=records)


def zlib_crc(packet):
    import zlib
    return zlib.crc32(packet[:-4])


def summarize(scene):
    out={}
    for profile in PROFILES:
        rows=[r for r in scene['records'] if r['profile']==profile]
        groups={}
        for region in ('active','roi','background'):
            n=sum(r['metrics'][region]['pixels'] for r in rows)
            mse=sum(r['metrics'][region]['mse']*r['metrics'][region]['pixels'] for r in rows)/n if n else None
            groups[region]=dict(pixels=n,mse=mse,psnr=None if mse in (None,0) else 10*math.log10(65025/mse))
        out[profile]=dict(frames=len(rows),mean_bytes=float(np.mean([r['bytes'] for r in rows])),
                          mean_vector_bytes=float(np.mean([r['vector_bytes'] for r in rows])),
                          forward_mbps_if30=sum(r['forward_ipv4_udp_size_calculation'] for r in rows)/len(rows)*8*30/1e6,
                          forward_mbps_if20=sum(r['forward_ipv4_udp_size_calculation'] for r in rows)/len(rows)*8*20/1e6,
                          cap_fail=sum(not r['cap_fit'] for r in rows),zero_residual=sum(r['zero_residual'] for r in rows),
                          prepare_mean_ms=float(np.mean([r['prepare_ms'] for r in rows])),
                          prepare_p95_ms=float(np.percentile([r['prepare_ms'] for r in rows],95)),
                          receive_mean_ms=float(np.mean([r['receive_ms'] for r in rows])),regions=groups)
    return out


def main():
    paths=[HERE/'block_codec.py',HERE/'benchmark.py',HERE/'test_block_codec.py',HERE/'verify.py',
           Path(bc.gc.__file__),Path(bc.ft.__file__),Path(bc.roi.__file__),Path(bc.gc.mt.__file__),
           Path(bc.gc.token_coeff.__file__),Path(bc.gc.word_coeff.__file__),Path(bc.gc.word_coeff.frozen_codec.__file__),
           Path(corpus.__file__),HERE.parent/'python-game-roi-study/benchmark.py']
    hashes={str(p):digest(p) for p in paths};scenes=[];start=time.perf_counter()
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    for name in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/f'{name}.mp4',max_frames=60,start_seconds=1)
        scene=run_scene(name,frames,manifest,RECTS,30);scene['summary']=summarize(scene);scenes.append(scene)
        print(name,json.dumps(scene['summary']),flush=True)
    for name in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/f'{name}.mp4',max_frames=30,start_seconds=1,width=512,height=288)
        manifest['resolution_scope']='Direct native RGB BOX to512x288, not a resized720canvas. Canvas-proportional declared ROI changes position/area; distortion across resolutions is not a matched quality point.'
        scene=run_scene(name+'-512x288',frames,manifest,scaled_rectangles(RECTS,512,288),30)
        scene['summary']=summarize(scene);scenes.append(scene)
        print(name+'-512x288',json.dumps(scene['summary']),flush=True)
    for name,frames in synthetic():
        h,w=frames[0].shape[:2];manifest=dict(synthetic=True,source=name,frame_count=len(frames),
            frame_sha256=[hashlib.sha256(a.tobytes()).hexdigest() for a in frames],active_rects=[(0,0,w,h)]*len(frames))
        scene=run_scene(name,frames,manifest,((0,0,w//2,h//2),),8)
        scene['summary']=summarize(scene);scenes.append(scene)
        print(name,json.dumps(scene['summary']),flush=True)
    assert hashes=={str(p):digest(p) for p in paths},'executed source changed'
    doc=dict(evidence='Actual BM01 packets with bounded block motion and independent decode, paired fixed-source GM01 controls; no installed/native/hardware proof',
             source_sha256=hashes,versions=dict(python=platform.python_version(),numpy=np.__version__,pillow=PIL.__version__,pyav=av.__version__),
             scenes=scenes,packet_count=sum(len(s['records']) for s in scenes),wall_seconds=time.perf_counter()-start,
             policy=dict(profiles=PROFILES,block_search_range=4,even_step=2,key_refresh_real=[0,30],
                         feedback='Immediate in-process ACK after successful decode/hash check; no paced transport or feedback loss in benchmark',
                         reference='Only reconstructed ACKed immutable key; no original-source/future reference or frame chaining',
                         oracle_used_for_selection=False,future_frames_used=0),
             timing_scope='Actual prepare includes declared-map construction, RGB/YUV conversion, bounded SAD/prediction, all three forward transforms, quantization, vector/map/entropy bytes and key reference reconstruction. Verification-only P expected reconstruction, hashes, metrics, source acquisition/scale and transport/display excluded. Receive parses/reconstructs independently. No native or shared-CPU schedule.',
             resolution_scope='Two60frames720x480 and two30frames512x288 direct-nativeBOX source windows; newROIgeometry declared percanvas. Never compare cross-resolution PSNR as matched quality; bitrate20/30fps fields are arithmetic, not pacing.',
             comparison_scope='Identical sources/maps/key IDs; GM01 global uses frozen sparse global ±16 search, BM01 full-block search±4. Distortion must be compared, not assumed equal from maps. All packets including cap failures are decoded as algorithm evidence.',
             skip_scope='Whole-P zero-residual flag only when all three actual quantized coefficient arrays are zero; normative output is reconstructed-key block prediction. No per-block skip map, source RGB copy, unchanged-source shortcut, patch integration or motion refinement.',
             memory_scope='Full source/prediction/coefficients/optional expectation arrays and key planes are Python host allocations; vector/search bounds do not establish target BRAM/DSP/SDRAM fit or reference-read drain.',
             transport_scope='Forward59bytes/chunk and reverse52bytes are arithmetic assumptions only; GF02 installed GM01 adapter does not parse BM01, no real packets or wire feedback sent.')
    (HERE/'results.json').write_text(json.dumps(doc,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
