#!/usr/bin/env python3
"""Actual mixed HG01/GM01 packets, GF02 ingress and GA01 feedback finite replay."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import time
import numpy as np
import av
import PIL
import adapter
import model

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('native_v10_inputs',HERE.parent/'python-game-service-study/benchmark.py')
source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def projected(rectangles,w,h):
    if (w,h)==(720,480):return tuple(rectangles)
    # Declared priorities are projected from the720x405 active window at y37,
    # rather than shrinking the existing black bars a second time.
    result=[]
    for x,y,rw,rh in rectangles:
        xx=max(0,min(w-1,int(x*w/720)));yy=max(0,min(h-1,int((y-37)*h/405)))
        ww=max(1,min(w-xx,int(rw*w/720)));hh=max(1,min(h-yy,int(rh*h/405)))
        result.append((xx,yy,ww,hh))
    return tuple(result)


def run_case(frames,manifest,clip,w,h,fps,mode,kind='baseline',**changes):
    base_rects=projected(adapter.hybrid.BROAD,w,h);patch_rects=projected(adapter.hybrid.COMPACT,w,h)
    factory=adapter.make_controller(patch_policy='adaptive_row',rectangles=patch_rects,
                                    max_attempts=0 if mode=='gm_only' else 4,use_gate=True)
    cfg=model.Config(width=w,height=h,fps=fps,rectangles=base_rects,controller='gate',decoder_service='python_wall',**changes)
    row=model.run(frames,manifest,cfg,controller_factory=factory,
                  receiver_factory=lambda:adapter.DecoderState(frame_cap=cfg.frame_cap))
    source.check_drained(row)
    assert all(c['selected_rgb565_mismatches']==0 for c in row['commits'])
    return {'source':clip,'kind':kind,'coded_width':w,'coded_height':h,'target_ids_per_second':fps,
            'mode':mode,'base_rectangles':base_rects,'patch_rectangles':patch_rects,'manifest':manifest,'result':row}


def functional_faults():
    rgb=np.full((32,64,3),[20,30,40],np.uint8);rgb[4:12,4:20]=[220,240,180]
    enc=adapter.hybrid.gm.Encoder();base=enc.prepare(rgb,0,quant_scale=16)
    decision=adapter.hybrid.select_frame(base,rgb,adapter.hybrid.Config(rectangles=((4,4,16,8),)))
    packet=decision.packet;rx=adapter.DecoderState();ingress=adapter.transport.Reassembler()
    chunks=adapter.transport.datagrams(packet,1,0);completed=None
    for i,c in enumerate(reversed(chunks)):
        out=ingress.feed(c,i)
        if out is not None:completed=out
    actual,info,feedback,error=adapter.receive_complete(ingress,completed,rx)
    assert error is None
    fb=adapter.transport.parse_feedback(feedback)
    outer=adapter.transport.content_crc(packet);inner=adapter.transport.content_crc(base)
    assert outer!=inner and adapter.transport.matches_feedback(fb,1,0,outer)
    assert not adapter.transport.matches_feedback(fb,1,0,inner)
    assert not ingress.pending
    return {'actual_format':info['format'],'outer_body_tag':outer,'inner_body_tag':inner,
        'feedback_binds_outer':True,'inner_only_tag_cannot_ack':True,'inner_epoch':1,'inner_frame_id':0,
        'outer_epoch':1,'outer_frame_id':0,'decoded_rgb565_sha256':hashlib.sha256(adapter.hybrid.hp.corpus.rgb565(actual).tobytes()).hexdigest(),
        'ingress_drained':True,'scope':'Immediate actual serialized functional proof; negative atomicity/readpins covered by20tests'}


def main():
    dependencies=[HERE/'model.py',HERE/'adapter.py',HERE/'benchmark.py',HERE/'test_hybrid_link.py',HERE/'test_legacy_model.py',
        Path(adapter.hybrid.__file__),Path(adapter.hybrid.row.__file__),Path(adapter.hybrid.hp.__file__),
        Path(model.gc.__file__),Path(model.normal_controller.__file__),Path(model.cheap_gate.__file__),Path(model.cheap_gate.exact.__file__),
        Path(model.transport.__file__),Path(model.corpus.__file__),Path(model.gc.roi.__file__),Path(model.gc.mt.__file__),Path(model.gc.ft.__file__),
        Path(model.gc.token_coeff.__file__),Path(model.gc.word_coeff.__file__),Path(model.gc.word_coeff.frozen_codec.__file__),
        HERE.parent/'python-coupled-study/validation.py',Path(source.__file__)]
    pins={str(p):sha(p) for p in dependencies};cases=[]
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=source.native(media/(clip+'.mp4'))
        for w,h,fps in ((720,480,30),(512,288,30),(512,288,20)):
            modes=('gm_only','adaptive_ui') if fps==30 else ('adaptive_ui',)
            if clip.endswith('2600'):modes=tuple(reversed(modes))
            for mode in modes:
                case=run_case(frames,manifest,clip,w,h,fps,mode);cases.append(case)
                r=case['result'];print(clip,w,h,fps,mode,'strict/eventual',r['presented_strict'],r['presented_eventual'],
                                      'diagnostic',r['metrics']['steady_fps'],flush=True)
        if clip.endswith('2600'):
            for kind,changes in (('initial_key_chunk_loss',{'data_loss_ids':(0,),'duplicate_chunk_ids':(12,)}),
                                 ('initial_key_ack_loss',{'feedback_loss_ids':(0,),'duplicate_feedback_ids':(12,)})):
                c=run_case(frames,manifest,clip,512,288,30,'adaptive_ui',kind,**changes);cases.append(c)
                r=c['result'];print(kind,r['presented_strict'],r['presented_eventual'],r['drops_by_reason'],flush=True)
    fault=functional_faults()
    assert pins=={str(p):sha(p) for p in dependencies},'executed source changed'
    data={'evidence':'Actual mixed HG01/GM01 over GF02 and outer-body-bound GA01, finite charged service replay. No targetnetworkorhardware30fps proof.',
        'source_sha256':pins,'versions':{'python':platform.python_version(),'numpy':np.__version__,'pillow':PIL.__version__,'pyav':av.__version__},
        'cases':cases,'case_count':len(cases),'functional_outer_feedback':fault,
        'codec_scope':'FrozenGM01base andboundedadaptiveHP01/HR01HG01selection now actuallytransportedanddecoded together. BM01notintegrated.',
        'timing_scope':'Actualcompletebase+selector calls and HG/GMreceive, resize/transportCPU charged with independentvirtualservers, ideal8Mb/slinks/QSPI160Mb/s/propagation10ms/vblank60. NotsharedtargetCPU, livecapture,actualradio/memory/display.',
        'oracle_scope':'IndependentclonedfullHG/GMreceiver reconstruction/hash afterpreparetimer. Readpin/referencepublication waitsvirtualcompletion. Oracles/ROIerror andRGB565checks excluded, consumeextrahostmemory.',
        'resolution_scope':'DirectnativeRGB BOX atselectedcanvas. Priorityrectsprojectedfrom720x405activewindow, noverifiedHUD. Per-canvasquality notcross-resolutionmatchedquality. Sourceframesare25/29.88fpsprecompressed, scheduledhypothetical20or30IDs/s; same60IDs over3sor2s, notlivedecimation. Refreshintervalfixed30captureIDs, referencehistoriescanchange.',
        'format_scope':'New mixedprofile, notinstalledpeernegotiation. GF02 carriesactualouterpacket;GA01tag excludesouterCRCfooter andbindsUI+innerGMbody. InnerGMidentitymustmatchouterepoch/frame.',
        'memory_scope':'Two49KiBsender/ingresspayloadpools,2GMcredits,3framebufferroles+boundedCPUdescriptors arelogical. Codec/patch arrays/source/oracle/copies additionalhoststorage; noDMA/CDCfitproof.'}
    (HERE/'results.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
