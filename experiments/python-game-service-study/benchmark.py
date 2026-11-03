#!/usr/bin/env python3
"""Charge measured Python BOX and transport CPU calls; native RGB input offline."""
import hashlib
import json
import os
from pathlib import Path
import platform
import time
from fractions import Fraction
import av
import numpy as np
import PIL
import model

HERE=Path(__file__).resolve().parent


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def native(path,n=60,start=1):
    frames=[];pts=[];times=[]
    with av.open(str(path)) as c:
        stream=next(s for s in c.streams if s.type=='video')
        for f in c.decode(stream):
            timestamp=Fraction(f.pts)*f.time_base if f.pts is not None else None
            if timestamp is not None and timestamp<Fraction(start):continue
            frames.append(f.to_ndarray(format='rgb24'));pts.append(f.pts)
            times.append(None if timestamp is None else float(timestamp))
            if len(frames)==n:break
        meta=dict(source=str(path),source_sha256=digest(path),source_fps=str(stream.average_rate),
                  source_width=stream.codec_context.width,source_height=stream.codec_context.height,
                  selected_pts=pts,selected_times_seconds=times,start_seconds=start,
                  target_width=720,target_height=480,frame_count=len(frames),resampler='Pillow BOX in modeled service')
    hashes=[hashlib.sha256(a.tobytes()).hexdigest() for a in frames]
    meta.update(frame_sha256=hashes,unique_frame_count=len(set(hashes)),
                input_scope='Native RGB extracted by offline PyAV; decode/read is excluded, not desktop acquisition')
    return frames,meta


def stress():
    rng=np.random.default_rng(1009)
    frames=[rng.integers(0,256,(480,720,3),dtype=np.uint8) for _ in range(6)]
    frames.extend(np.full((480,720,3),75+i,np.uint8) for i in range(6))
    return frames,dict(source='synthetic:seed1009-six-noise-six-flat',synthetic=True,frame_count=12,
                       frame_sha256=[hashlib.sha256(a.tobytes()).hexdigest() for a in frames],
                       source_fps=None,input_scope='Synthetic720x480; BOX call still executes, no live acquisition')


def check_drained(row):
    assert all(v is None for v in row['unresolved_sender_slots'])
    assert not row['unresolved_ingress_frames'] and not row['unresolved_credits'] and not row['pending_ids']
    assert row['waiting_at_end'] is None and all(v==0 for v in row['unresolved_cpu'].values())


def summarize_pair(a,b):
    aa={p['id']:p for p in a['packets']};bb={p['id']:p for p in b['packets']}
    common=sorted(aa.keys()&bb.keys());ap={p['id'] for p in a['presented']};bp={p['id'] for p in b['presented']}
    equal=[i for i in common if aa[i].get('packet_sha256') is not None and aa[i].get('packet_sha256')==bb[i].get('packet_sha256')]
    return dict(common_prepared_ids=common,common_presented_ids=sorted(ap&bp),
                same_packet_ids=equal,only_zero_cpu_presented=sorted(ap-bp),only_charged_presented=sorted(bp-ap),
                caveat='Preparation and receive are remeasured per run. Identical sources do not fix virtual reference histories; host timing variation is confounded with tiny added CPU costs.')


def main():
    paths=[HERE/'model.py',HERE/'benchmark.py',HERE/'test_model.py',HERE/'verify.py',
           Path(model.gc.__file__),Path(model.normal_controller.__file__),Path(model.cheap_gate.__file__),
           Path(model.cheap_gate.exact.__file__),Path(model.transport.__file__),Path(model.corpus.__file__),
           Path(model.gc.roi.__file__),Path(model.gc.mt.__file__),Path(model.gc.ft.__file__),
           Path(model.gc.token_coeff.__file__),Path(model.gc.word_coeff.__file__),Path(model.gc.word_coeff.frozen_codec.__file__),
           HERE.parent/'python-coupled-study/validation.py']
    hashes={str(p):digest(p) for p in paths};cases=[];pairs=[];started=time.perf_counter()
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    for k,clip in enumerate(('mass-effect-combat','mass-effect-2600')):
        frames,manifest=native(media/f'{clip}.mp4')
        local={}
        # Reverse paired order in the other clip; this does not isolate host load.
        for charged in ((False,True) if k==0 else (True,False)):
            cfg=model.Config(controller='gate',decoder_service='python_wall',transport_cpu=charged,resize_cpu=charged)
            row=model.run(frames,manifest,cfg);check_drained(row);local[charged]=row
            cases.append(dict(name=clip,kind='baseline',charged=charged,manifest=manifest,result=row))
            print(clip,'charged',charged,'strict/eventual',row['presented_strict'],row['presented_eventual'],
                  'diagnostic',row['metrics']['steady_fps'],'drops',row['drops_by_reason'],flush=True)
        pairs.append(dict(name=clip,**summarize_pair(local[False],local[True])))
        if k==1:
            for label,changes in (
                ('initial_key_chunk_loss',dict(data_loss_ids=(0,),duplicate_chunk_ids=(12,))),
                ('initial_key_ack_loss',dict(feedback_loss_ids=(0,),duplicate_feedback_ids=(12,)))):
                row=model.run(frames,manifest,model.Config(controller='gate',decoder_service='python_wall',**changes))
                check_drained(row);cases.append(dict(name=clip,kind=label,charged=True,manifest=manifest,result=row))
                print(clip,label,row['presented_strict'],row['presented_eventual'],row['drops_by_reason'],flush=True)
    frames,manifest=stress()
    for controller in ('normal','gate'):
        row=model.run(frames,manifest,model.Config(controller=controller,decoder_service='python_wall'))
        check_drained(row);cases.append(dict(name='seed1009-noise-recovery',kind='stress',charged=True,manifest=manifest,result=row))
        print('stress',controller,row['prepared'],row['presented_eventual'],row['drops_by_reason'],flush=True)
    assert hashes=={str(p):digest(p) for p in paths},'executed source changed'
    result=dict(evidence='Finite actual GM01/GF02/GA01 model with optional charged measured Python transport/BOX stages; no physical rate proof',
                source_sha256=hashes,case_count=len(cases),cases=cases,pairs=pairs,
                versions=dict(python=platform.python_version(),numpy=np.__version__,pillow=PIL.__version__,pyav=av.__version__),
                total_python_wall_seconds=time.perf_counter()-started,
                service_scope='Full preparation including cap rejects; actual receive; BOX RGB resize/canvas; datagram construction; each Reassembler.feed call including failures; each GA01 construction and parse including failures. Each stage has its own serialized virtual server, not a shared physical host CPU scheduler.',
                acquisition_scope='Offline native PyAV RGB extraction excluded. BOX service includes Image.fromarray, BOX resize and zero canvas/copy; this is measured preprocessing, not desktop acquisition. Config acquisition_ms remains external assumed delay0.',
                oracle_scope='Expected RGB/hash, packet hashes and display error metrics outside service timers; codec/transport source unchanged.',
                timing_scope='Forward/reverse8Mb/s, QSPI160Mb/s, propagation10ms,60Hzvblank assumed; no sockets, target/native CPU, OS, DMA/CDC, real transport framing/scanout or hardware test.',
                pairing_scope='Both pairs use identical native input hashes. Actual preparation/receive costs are remeasured, so selected histories and common IDs are compared; changes cannot all be attributed to tiny transport CPU work.',
                ownership_scope='Encode semantic commit staged until encode_done preserving concurrent P ACK removal; receiver state publication likewise waits decode_done. CPU queues/read pins prevent active-owner release. This oracle rollback/staging is Python scheduling scaffolding, not a native codec API or memory-fit proof.',
                memory_scope='Two sender transactions/two ingress payloads/two GM01credits/three metadata framebufferroles plus one active/one latest resize capture. Four feedback descriptors. Actual source RGB, resized/oracle/output arrays, packet copies/queues and transform/reference workspaces are additional host allocation.')
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
