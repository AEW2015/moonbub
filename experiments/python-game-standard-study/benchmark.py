#!/usr/bin/env python3
"""Same-source GM01, native HEVC and native AV1 rate/distortion references."""
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import numpy as np
import standard_codec as sc

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-game-codec-study'))
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import game_codec as gm
import corpus
RECTS=((16,48,192,80),(160,352,400,80))


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(a):return hashlib.sha256(a.tobytes()).hexdigest()
def ms(t):return (time.perf_counter_ns()-t)/1e6


def quality(source,actual,active):
    display=corpus.expand565(corpus.rgb565(actual))
    error=np.mean((source.astype(np.float64)-display.astype(np.float64))**2,axis=2)
    h,w=error.shape;m=np.zeros((h,w),bool);x,y,ww,hh=active;m[y:y+hh,x:x+ww]=True
    roi=np.zeros((h,w),bool)
    for x,y,ww,hh in RECTS:roi[y:y+hh,x:x+ww]=True
    out={}
    for name,mask in (('active',m),('roi',m&roi),('background',m&~roi)):
        out[name]={'squared_error_sum':float(error[mask].sum()),'pixels':int(mask.sum())}
    return out


def summarize(records):
    total=sum(r['bytes'] for r in records)
    pooled={}
    for key in ('active','roi','background'):
        values=[r['quality'][key] for r in records];mse=sum(r['squared_error_sum'] for r in values)/sum(r['pixels'] for r in values)
        pooled[key]={'mse':mse,'psnr':10*math.log10(65025/mse) if mse else None}
    return {'frames':len(records),'coded_bytes':total,'mean_bytes':total/len(records),
            'coded_mbps_at_hypothetical30':total/len(records)*8*30/1e6,
            'frames_over_49152':sum(r['bytes']>49152 for r in records),'pooled':pooled}


def main():
    paths=[HERE/'benchmark.py',HERE/'standard_codec.py',HERE/'test_standard_codec.py',Path(gm.__file__),Path(corpus.__file__),
           Path(gm.roi.__file__),Path(gm.ft.__file__),Path(gm.mt.__file__),Path(gm.token_coeff.__file__),
           Path(gm.word_coeff.__file__),Path(gm.word_coeff.frozen_codec.__file__)]
    pins={str(p):sha(p) for p in paths};cases=[]
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/(clip+'.mp4'),max_frames=60,start_seconds=1)
        n=len(frames);assert n==60
        for label,bg in (('gm_uniform16',16),('gm_roi8bg16',16),('gm_roi8bg32',32)):
            enc=gm.Encoder();rx=gm.Receiver();records=[]
            h,w=frames[0].shape[:2];mw,mh=gm.roi.geometry(w,h)
            scale=np.full((mh,mw),16,np.uint8) if label=='gm_uniform16' else gm.roi.declared_map(w,h,RECTS,8,bg)
            for i,rgb in enumerate(frames):
                started=time.perf_counter_ns();packet=enc.prepare(rgb,i,scale_map=scale,force_key=(i%30==0));encode_ms=ms(started)
                started=time.perf_counter_ns();actual,meta=rx.receive(packet);decode_ms=ms(started)
                assert digest(actual)==enc.expected_hash(i)
                enc.ack(i,epoch=1)
                records.append({'id':i,'bytes':len(packet),'packet_sha256':hashlib.sha256(packet).hexdigest(),
                    'decoded_rgb565_sha256':digest(corpus.rgb565(actual).astype('<u2')),'is_key':meta['key'],
                    'encode_ms':encode_ms,'decode_ms':decode_ms,'quality':quality(rgb,actual,manifest['active_rects'][i])})
            cases.append({'source':clip,'profile':label,'manifest':manifest,'records':records,'summary':summarize(records),
                          'scope':'ActualGM01temporalpacket, immediateACKno losses, keyevery30, noadmission/transport; stateYUVintegercustomcolor.'})
            print(clip,label,cases[-1]['summary'],flush=True)
        for encoder,values in (('libx265',(28,36,44)),('libsvtav1',(28,38,48))):
            for parameter in values:
                outputs,info=sc.run(frames,encoder,parameter)
                packets={}
                for packet in info['packets']:
                    if packet['pts'] is None:raise AssertionError('unassociatedpacket')
                    packets.setdefault(packet['pts'],[]).append(packet)
                records=[]
                for i,rgb in enumerate(frames):
                    group=packets.get(i,[])
                    records.append({'id':i,'bytes':sum(p['bytes'] for p in group)+(info['extradata_bytes'] if i==0 else 0),
                        'packet_sha256s':[p['sha256'] for p in group],
                        'decoded_rgb565_sha256':digest(corpus.rgb565(outputs[i]).astype('<u2')),
                        'is_key':any(p['is_keyframe'] for p in group),'quality':quality(rgb,outputs[i],manifest['active_rects'][i])})
                assert sum(r['bytes'] for r in records)==info['coded_bytes']
                case={'source':clip,'profile':encoder+'_q'+str(parameter),'manifest':manifest,'requested_quality_parameter':parameter,
                    'records':records,'reference':info,'summary':summarize(records),
                    'scope':'NativeCPUreferenceonly. CRFvaluesacrossencodersarenotmatchedquality; comparemeasuredRDpoints. RequestedlowdelayoptionsandreturnedPTS/flushcountsrecorded; not equivalentfinitefeedback/deadlinepolicy.'}
                cases.append(case);print(clip,case['profile'],case['summary'],flush=True)
    assert pins=={str(p):sha(p) for p in paths},'sourcechanged'
    result={'evidence':'Same-sourceGM01/HEVC/AV1softwareRDreferences, nottargetdecoder/30fpsproof',
        'source_sha256':pins,'versions':{'python':platform.python_version(),**{p:importlib.metadata.version(p) for p in ('numpy','Pillow','av')}},
        'cases':cases,'case_count':len(cases),'unique_source_frames':120,
        'quality_scope':'PooledareaweightedMSE againstsourceRGB888afteralloutputsquantizedRGB565, sameBOX720x480canvas/720x405active+declaredROI. CodecRGB/YUVmatrices differ. NoVMAF/perceptualequivalenceclaim.',
        'rate_scope':'Elementarycodedbytes+encoderextradata, excludesUDP/mux/QSPI/FEC/feedback. GMhasownheaders/CRCs. StandardAUbytecountsnot49KiBpacketproof. Mbps useshypothetical30IDs/s, source25/29.88fpsandprecompressedrepeatedcontent.',
        'timing_scope':'NativeCPUreferenceencode/decode andPythoncustomcostsarenottargetperformancecomparisons. Offlinepreloadedinputs, uncontrolledhost, noactualcapture/network/gameinput/display. Encoderflush/bufferingretained.',
        'sources':{'HEVC':'https://www.itu.int/rec/t-rec-h.265','AV1':'https://aomedia.org/docs/AV1_ToolDescription_v11-clean.pdf',
            'x265_options':'https://x265.readthedocs.io/en/stable/presets.html',
            'SVT_options':'https://gitlab.com/AOMediaCodec/SVT-AV1/-/raw/master/Docs/Parameters.md'}}
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
