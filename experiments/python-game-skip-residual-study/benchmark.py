#!/usr/bin/env python3
"""Actual SR01 syntax and bounded-P-pruning candidates at720x480."""
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
import skip_codec as s

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus

RECTS=((16,48,192,80),(160,352,400,80))
PROFILES=('gm','sr_dense','sr_exact','sr_prune2','sr_prune4')


def digest(a):return hashlib.sha256(a.tobytes()).hexdigest()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def anchor_digest(p):return None if p is None else digest(np.concatenate([x.reshape(-1) for x in p]))


def metrics(rgb,decoded,active,priority):
    source=corpus.expand565(corpus.rgb565(rgb)).astype(np.float64)
    actual=corpus.expand565(corpus.rgb565(decoded)).astype(np.float64)
    x,y,w,h=active;valid=np.zeros(rgb.shape[:2],bool);valid[y:y+h,x:x+w]=True
    out={}
    for name,mask in (('active',valid),('priority',valid&priority),('background',valid&~priority)):
        delta=source[mask]-actual[mask];mse=float(np.mean(delta*delta))
        out[name]=dict(mse=mse,psnr=None if mse==0 else 10*math.log10(255**2/mse),pixels=int(mask.sum()))
    return out


def synthetic():
    rng=np.random.default_rng(1404);y,x=np.mgrid[:480,:720]
    images=[]
    for i in range(8):
        a=np.stack(((x+i*2)%180+30,(y//2+i)%150+40,((x+y)//5+i)%140+60),axis=-1).astype(np.uint8)
        images.append(a)
    return [('synthetic-flat',[np.full((480,720,3),128,np.uint8) for _ in range(4)]),
            ('synthetic-moving-gradient',images),
            ('synthetic-noise-cut',[np.full((480,720,3),128,np.uint8),
                *[rng.integers(0,256,(480,720,3),dtype=np.uint8) for _ in range(3)],
                np.full((480,720,3),220,np.uint8),np.full((480,720,3),128,np.uint8)])]


def summary(rows):
    admitted=[r for r in rows if r['accepted']]
    return dict(source_ids=len(rows),admitted=len(admitted),rejected=len(rows)-len(admitted),
                mean_packet_bytes=float(np.mean([r['packet_bytes'] for r in admitted])) if admitted else None,
                mean_prepare_ms_all=float(np.mean([r['prepare_ms'] for r in rows])),
                rejected_prepare_ms=sum(r['prepare_ms'] for r in rows if not r['accepted']),
                mean_receive_ms=float(np.mean([r['receive_ms'] for r in admitted])) if admitted else None,
                mean_full_service_ms=float(np.mean([r['prepare_ms']+r['receive_ms'] for r in admitted])) if admitted else None,
                mean_active_mse=float(np.mean([r['metrics']['active']['mse'] for r in admitted])) if admitted else None,
                mean_priority_mse=float(np.mean([r['metrics']['priority']['mse'] for r in admitted])) if admitted else None,
                split_planes=sum(p['mode']=='split' for r in rows for p in r.get('plane_choices',[])),
                dense_planes=sum(p['mode']=='dense' for r in rows for p in r.get('plane_choices',[])),
                zeroed_blocks=sum(p['zeroed'] for r in rows for p in r.get('pruning',[])),
                dc_pruned_blocks=sum(p['dc_only'] for r in rows for p in r.get('pruning',[])),
                max_yuv_delta=max((r.get('baseline_yuv_max_delta',0) for r in admitted),default=0),
                max_protected_rgb565_mismatches=max((r.get('protected_rgb565_mismatches',0) for r in admitted),default=0))


def run_case(name,cohort,frames,manifest,keys):
    encoders={'gm':s.gm.Encoder(),'sr_dense':s.Encoder(profile='dense'),'sr_exact':s.Encoder(),
              'sr_prune2':s.Encoder(profile='prune',limit=2),'sr_prune4':s.Encoder(profile='prune',limit=4)}
    receivers={'gm':s.fast_codec.Receiver(),**{p:s.Receiver() for p in PROFILES if p!='gm'}}
    rows={p:[] for p in PROFILES};m=s.gm.roi.declared_map(720,480,RECTS,8,16)
    priority=np.repeat(np.repeat(m==8,16,0),16,1)[:480,:720]
    for i,rgb in enumerate(frames):
        assert rgb.shape==(480,720,3)
        before={p:(enc.anchor_id,anchor_digest(enc._anchor)) for p,enc in encoders.items()}
        assert len(set(before.values()))==1
        decisions={};outputs={};decoded_planes={};base_packet=None
        order=PROFILES[i%len(PROFILES):]+PROFILES[:i%len(PROFILES)]
        for profile in order:
            enc=encoders[profile];started=time.perf_counter_ns()
            if profile=='gm':
                prepared=enc.analyze(rgb,i,force_key=i in keys,mode='zero')
                candidate=enc.encode_candidate(prepared,m);base_packet=candidate.packet
                packet=enc.commit(candidate) if len(candidate.packet)<=49152 else None
                d=dict(accepted=packet is not None,packet=packet,candidate_bytes=len(candidate.packet),
                       key=prepared.key,level=0,plane_choices=[],pruning=[])
            else:
                result=enc.prepare(rgb,i,scale_map=m,force_key=i in keys)
                d=dict(accepted=result.accepted,packet=result.packet,candidate_bytes=result.candidate_bytes,
                       key=result.key,level=result.level,plane_choices=result.planes,pruning=result.pruning,
                       internal_service_ms=result.service_ms,analyze_ms=result.analyze_ms,
                       candidate_ms=result.candidate_ms,commit_ms=result.commit_ms)
            d['prepare_ms']=(time.perf_counter_ns()-started)/1e6;decisions[profile]=d
        # Independent reconstruction of the GM candidate remains outside every
        # service timer, including when that candidate exceeded admission cap.
        parsed=s.gm.parse(base_packet,1)
        if parsed['key']:prediction=tuple(np.full(shape,128,np.int16) for shape in ((480,720),(240,360),(240,360)))
        else:prediction=encoders['gm']._anchor
        baseline_planes=s.fast_codec.reconstruct(parsed['coefficients'],prediction,m,720,480)
        baseline_rgb=s.gm.ft.planes_to_rgb(baseline_planes)
        for profile in order:
            enc=encoders[profile];d=decisions[profile];packet=d.pop('packet')
            row=dict(id=i,source_rgb_sha256=manifest['frame_sha256'][i],width=720,height=480,
                     reference_before=before[profile][0],reference_yuv_sha256=before[profile][1],
                     **d,pending_after_prepare=len(enc.pending),frame_cap=49152)
            if d['accepted']:
                start=time.perf_counter_ns();actual,info=receivers[profile].receive(packet)
                row['receive_ms']=(time.perf_counter_ns()-start)/1e6
                assert digest(actual)==enc.expected_hash(i)
                if profile=='gm':
                    actual_planes=baseline_planes;assert np.array_equal(actual,baseline_rgb)
                    assert enc.ack(i,epoch=1)
                else:
                    p=s.parse(packet,1)
                    actual_planes=s.fast_codec.reconstruct(p['coefficients'],prediction,p['scale_map'],720,480)
                    assert enc.ack(i,epoch=1,content_crc=info['content_crc'])
                maximum=max(int(np.max(np.abs(a-b))) for a,b in zip(actual_planes,baseline_planes))
                words=corpus.rgb565(actual);base_words=corpus.rgb565(baseline_rgb)
                protected_mismatches=int(np.count_nonzero(words[priority]!=base_words[priority]))
                assert maximum<=d['level'] and protected_mismatches==0,(name,i,profile,maximum,d['level'],protected_mismatches)
                if d['level']==0:np.testing.assert_array_equal(actual,baseline_rgb)
                row.update(packet_bytes=len(packet),packet_sha256=hashlib.sha256(packet).hexdigest(),
                           decoded_rgb_sha256=digest(actual),baseline_rgb_sha256=digest(baseline_rgb),
                           baseline_yuv_max_delta=maximum,protected_rgb565_mismatches=protected_mismatches,
                           metrics=metrics(rgb,actual,tuple(manifest['active_rects'][i]),priority),
                           forward_ipv4_udp_bytes=len(packet)+59*math.ceil(len(packet)/1024),
                           reference_after=enc.anchor_id,reference_yuv_after_sha256=anchor_digest(enc._anchor))
            else:
                assert not enc.pending and (enc.anchor_id,anchor_digest(enc._anchor))==before[profile]
                row.update(packet_bytes=None,receive_ms=None)
            row['pending_after_feedback']=len(enc.pending);rows[profile].append(row)
    return dict(name=name,cohort=cohort,manifest=manifest,keys=sorted(keys),profiles=rows,
                summary={p:summary(r) for p,r in rows.items()})


def main():
    modules=[s,s.gm,s.fast_codec,s.gm.roi,s.gm.ft,s.gm.mt,s.gm.token_coeff,
             s.gm.word_coeff,s.gm.word_coeff.frozen_codec,corpus]
    files=[HERE/'benchmark.py',HERE/'test_skip_codec.py',HERE/'verify.py']+[Path(m.__file__) for m in modules]
    pins={str(p):sha(p) for p in files};media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    cases=[];started=time.perf_counter()
    for cohort,start,count in (('native_temporal',1,60),('heldout_key',4,8)):
        for clip in ('mass-effect-combat','mass-effect-2600'):
            frames,manifest=corpus.load_video(media/(clip+'.mp4'),max_frames=count,start_seconds=start)
            keys=set(range(len(frames))) if cohort=='heldout_key' else {0,30}
            case=run_case(clip+'-'+cohort,cohort,frames,manifest,keys);cases.append(case)
            print(case['name'],json.dumps(case['summary']),flush=True)
    for name,frames in synthetic():
        manifest=dict(source='synthetic:'+name,synthetic=True,frame_count=len(frames),
                      frame_sha256=[digest(a) for a in frames],active_rects=[(0,0,720,480)]*len(frames),
                      target_width=720,target_height=480)
        case=run_case(name,'synthetic',frames,manifest,{0});cases.append(case)
        print(name,json.dumps(case['summary']),flush=True)
    assert pins=={str(p):sha(p) for p in files}
    out=dict(evidence='Actual bounded SR01 residual syntax and explicitly lossy P-only pruning; no physical timing claim',
             source_sha256=pins,cases=cases,source_ids=sum(len(c['manifest']['frame_sha256']) for c in cases),
             decisions=sum(sum(len(r) for r in c['profiles'].values()) for c in cases),
             wall_seconds=time.perf_counter()-started,
             versions=dict(python=platform.python_version(),**{p:importlib.metadata.version(p) for p in ('numpy','Pillow','av')}),
             format_scope='SR01 is a new profile, not GM01-compatible or a standards stream. Dense CP02 and zero/DC/full split are actually serialized and compared; headers/map/CRC included.',
             quality_scope='Exact SR pixels match quantized GM. Pruned P-only reconstructed YUV differs at most2or4per sample from quantized GM, scale8 priority blocks unchanged. Source RGB is already lossy under GM; no lossless original UI claim.',
             timing_scope='Whole prepare includes transforms, quantization, actual pruning inverse/error/recheck, both plane coding alternatives, cap check and key reconstruction. Fair receivers both use exact zero/DC bypass. Verification reconstruction/hashes/metrics, source decode/resize and map construction excluded.',
             ownership_scope='Immediate content-bound ACK; one immutable ACKed reconstructed key, no P promotion. No finite-link integration, physical readers, target memory or hardware30fps proof.',
             source_scope='Two related precompressed25/29.88fps samples plus synthetic controls; all720x480coded with720x405active native. Not live30distinctcapture.')
    (HERE/'results.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
