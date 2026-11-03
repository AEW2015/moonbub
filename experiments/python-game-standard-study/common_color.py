#!/usr/bin/env python3
"""Supplement: all codecs share frozen GM RGB/YUV420 arithmetic.

Standard syntax remains HEVC/AV1; this probe compares decoded sample planes,
then uses the same custom display color conversion as GM01. It removes the
separate swscale color-roundtrip floor, not network/reference/memory differences.
"""
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import time
import numpy as np
import av
import benchmark as b
import standard_codec as sc

HERE=Path(__file__).resolve().parent


def frame_from_planes(planes,pts):
    h,w=planes[0].shape
    frame=av.VideoFrame(w,h,'yuv420p');frame.pts=pts;frame.time_base=Fraction(1,30)
    frame.color_range=2
    for destination,source in zip(frame.planes,planes):
        buffer=np.zeros((destination.height,destination.line_size),np.uint8)
        buffer[:source.shape[0],:source.shape[1]]=source
        destination.update(buffer.tobytes())
    return frame


def planes_from_frame(frame):
    if frame.format.name not in ('yuv420p','yuvj420p'):raise ValueError('unexpected native decoded pixel format')
    return tuple(np.frombuffer(p,np.uint8).reshape(p.height,p.line_size)[:,:p.width].copy()
                 for p in frame.planes)


def run(frames,encoder_name,parameter):
    h,w=frames[0].shape[:2]
    enc=av.CodecContext.create(encoder_name,'w');enc.width=w;enc.height=h;enc.pix_fmt='yuv420p'
    enc.time_base=Fraction(1,30);enc.framerate=Fraction(30,1);enc.thread_count=1
    enc.gop_size=30;enc.max_b_frames=0;enc.color_range=2;enc.options=sc.options(encoder_name,parameter)
    enc.open()
    if enc.options:raise AssertionError(('unconsumed',enc.options))
    packets=[];calls=[]
    for i,rgb in enumerate(frames):
        planes=b.gm.ft.rgb_to_planes(rgb);frame=frame_from_planes(planes,i)
        batch=enc.encode(frame);packets.extend(batch)
        calls.append({'id':i,'emitted_pts':[p.pts for p in batch]})
    tail=enc.encode(None);packets.extend(tail)
    dec=av.CodecContext.create('hevc' if encoder_name=='libx265' else 'libdav1d','r');dec.thread_count=1
    if enc.extradata:dec.extradata=enc.extradata
    outputs={};records=[]
    for packet in packets:
        data=bytes(packet);p=av.Packet(data);p.pts=packet.pts;p.dts=packet.dts;p.time_base=Fraction(1,30)
        for frame in dec.decode(p):
            if frame.pts in outputs:raise AssertionError('duplicate native output')
            outputs[frame.pts]=b.gm.ft.planes_to_rgb(planes_from_frame(frame))
        records.append({'pts':packet.pts,'dts':packet.dts,'bytes':len(data),'is_key':packet.is_keyframe,
                        'sha256':hashlib.sha256(data).hexdigest()})
    for frame in dec.decode(None):
        if frame.pts in outputs:raise AssertionError('duplicate flushed output')
        outputs[frame.pts]=b.gm.ft.planes_to_rgb(planes_from_frame(frame))
    assert sorted(outputs)==list(range(len(frames)))
    return outputs,{'packets':records,'extradata_bytes':len(enc.extradata or b''),
                    'input_calls':calls,'packets_only_at_flush':len(tail),
                    'requested_options':sc.options(encoder_name,parameter),
                    'color_range_flag_requested':2,'output_pixel_contract':'GM01 frozen YUV420sampleplanes→RGB→RGB565'}


def main():
    sources=[HERE/'common_color.py',HERE/'benchmark.py',HERE/'standard_codec.py',Path(b.gm.ft.__file__),Path(b.corpus.__file__)]
    pins={str(p):b.sha(p) for p in sources};prior=HERE/'results.json';prior_hash=b.sha(prior)
    old=json.loads(prior.read_text());cases=[]
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=b.corpus.load_video(media/(clip+'.mp4'),max_frames=60,start_seconds=1)
        for oldcase in old['cases']:
            if oldcase['source']==clip and oldcase['profile'].startswith('gm_'):
                assert oldcase['manifest']['frame_sha256']==manifest['frame_sha256']
                cases.append({**oldcase,'evidence_origin':'Unchanged GM01 records reused from pinned original reference study'})
        for encoder,parameters in (('libx265',(28,36,44)),('libsvtav1',(28,38,48))):
            for parameter in parameters:
                outputs,info=run(frames,encoder,parameter);rows=[]
                for i,rgb in enumerate(frames):
                    group=[p for p in info['packets'] if p['pts']==i]
                    rows.append({'id':i,'bytes':sum(p['bytes'] for p in group)+(info['extradata_bytes'] if i==0 else 0),
                        'is_key':any(p['is_key'] for p in group),'quality':b.quality(rgb,outputs[i],manifest['active_rects'][i]),
                        'decoded_rgb565_sha256':b.digest(b.corpus.rgb565(outputs[i]).astype('<u2'))})
                case={'source':clip,'profile':encoder+'_q'+str(parameter),'manifest':manifest,'records':rows,
                      'summary':b.summarize(rows),'reference':info,'requested_quality_parameter':parameter}
                cases.append(case);print(clip,case['profile'],case['summary'],flush=True)
    assert pins=={str(p):b.sha(p) for p in sources} and b.sha(prior)==prior_hash
    result={'evidence':'Separate common-GMYUV420 HEVC/AV1/GM01 RDprobe; actualnativeplaneencodes/decodes, notphysicaltargetproof.',
        'source_sha256':pins,'prior_results_sha256':prior_hash,'cases':cases,
        'scope':'IdenticalfrozenGMRGB→YUV420 andYUV420→RGB arithmetic for all profiles. Nativecodecspredict their own reconstructedreferences; GMhasACKedimmutablekey. No commonnetwork/loss/deadline/memorypolicy. Firstclip32distinctRGB/60,second60/60. No overallpercentgap/BD-rateclaim.',
        'timing_scope':'No cost measurements; functionalRDsupplement only. KeyIDs andfuturebuffering recorded. NotnativeCPUthroughput orhardware30fps.'}
    (HERE/'common-color-results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
