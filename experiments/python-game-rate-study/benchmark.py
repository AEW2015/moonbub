#!/usr/bin/env python3
"""Actual two-candidate GM01 admission and paired transform reuse measurement."""
import dataclasses
import hashlib
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
from controller import Config,Controller,codec,RECTANGLES

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def psnr(mse):return None if mse==0 else float(10*np.log10(65025/mse))
def wire_bytes(size):return size+68*math.ceil(size/1024)


def stats(values):
    if not values:return {'n':0,'mean':None,'p50':None,'p95':None,'max':None}
    return dict(n=len(values),**{k:float(v) for k,v in zip(('mean','p50','p95','max'),
                (np.mean(values),*np.percentile(values,[50,95]),max(values)))})


def metrics(source,rgb,active):
    output=corpus.expand565(corpus.rgb565(rgb))
    squared=np.mean((source.astype(np.float64)-output.astype(np.float64))**2,axis=2)
    h,w=source.shape[:2];mask=np.zeros((h,w),bool);roi=mask.copy()
    x,y,rw,rh=active;mask[y:y+rh,x:x+rw]=True
    for x,y,rw,rh in RECTANGLES:roi[y:y+rh,x:x+rw]=True
    result={}
    for label,m in (('active',mask),('roi',mask&roi),('background',mask&~roi)):
        mse=float(np.mean(squared[m]));result[label]={'mse':mse,'pixels':int(m.sum()),'psnr_db':psnr(mse)}
    return result


def pooled(rows):
    result={}
    for label in ('active','roi','background'):
        values=[r['metrics'][label] for r in rows if r['accepted']]
        pixels=sum(v['pixels'] for v in values)
        mse=None if not pixels else sum(v['mse']*v['pixels'] for v in values)/pixels
        result[label]={'pixels':pixels,'mse':mse,'psnr_db':None if mse is None else psnr(mse)}
    return result


def run_sequence(frames,manifest,policy):
    encoder=codec.Encoder();receiver=codec.Receiver();controller=Controller(encoder,Config(policy=policy))
    rows=[]
    for frame,rgb in enumerate(frames):
        before=(encoder.analysis_count,encoder.forward_calls)
        call_started=time.perf_counter_ns()
        decision=controller.prepare(rgb,frame)
        call_ms=(time.perf_counter_ns()-call_started)/1e6
        assert encoder.analysis_count-before[0]==decision.analyze_calls
        assert encoder.forward_calls-before[1]==decision.forward_calls
        assert decision.analyze_calls==1 and decision.forward_calls==3 and len(decision.attempts)<=2
        row={'id':frame,'input_sha256':manifest['frame_sha256'][frame],
             'accepted':decision.accepted,'selected':decision.selected,'attempts':list(decision.attempts),
             'analyze_calls':decision.analyze_calls,'forward_calls':decision.forward_calls,
             'service_ms':call_ms,'internal_service_ms':decision.service_ms,'commit_ms':decision.commit_ms,'map_build_ms':decision.map_build_ms,
             'selected_scale_counts':decision.selected_scale_counts,'cap_bytes':49152}
        if decision.accepted:
            actual,info=receiver.receive(decision.packet)
            parsed=codec.parse(decision.packet,1)
            selected_map=parsed['scale_map']
            priority_mask=codec.roi.declared_map(rgb.shape[1],rgb.shape[0],RECTANGLES,8,16)==8
            roi_scales=selected_map[priority_mask]
            if policy=='priority':assert np.all(roi_scales==8),'priorityfloorviolated'
            actual_hash=hashlib.sha256(actual.tobytes()).hexdigest()
            assert actual_hash==encoder.expected_hash(frame),'receiver drift'
            row.update(bytes=len(decision.packet),wire_bytes=wire_bytes(len(decision.packet)),
                       packet_sha256=hashlib.sha256(decision.packet).hexdigest(),rgb_sha256=actual_hash,
                       key=info['key'],reference_id=info['reference_id'],map_bytes=info['map_bytes'],
                       verified_roi_scale_min=int(roi_scales.min()),verified_roi_scale_max=int(roi_scales.max()),
                       verified_selected_scale_counts={str(v):int((selected_map==v).sum()) for v in (8,16,32)},
                       metrics=metrics(rgb,actual,manifest['active_rects'][frame]))
            encoder.ack(frame,epoch=1)
        else:
            assert not encoder.pending,'rejected admission consumed credit'
            row['reason']='both_candidates_exceed_cap'
        assert not encoder.pending
        rows.append(row)
    accepted=[r for r in rows if r['accepted']]
    return {'policy':policy,'rows':rows,'capture_count':len(rows),'admitted':len(accepted),
            'dropped':len(rows)-len(accepted),'normal_count':sum(r['selected']=='normal' for r in rows),
            'fallback_count':sum(r['selected']=='fallback' for r in rows),
            'two_attempt_calls':sum(len(r['attempts'])==2 for r in rows),
            'analysis_calls':sum(r['analyze_calls'] for r in rows),'forward_calls':sum(r['forward_calls'] for r in rows),
            'service_ms':stats([r['service_ms'] for r in rows]),
            'service_ms_accepted':stats([r['service_ms'] for r in accepted]),
            'service_ms_rejected':stats([r['service_ms'] for r in rows if not r['accepted']]),
            'accepted_calls_over_33_333_ms':sum(r['service_ms']>1000/30 for r in accepted),
            'packet_bytes':sum(r['bytes'] for r in accepted),
            'wire_bytes':sum(r['wire_bytes'] for r in accepted),
            'wire_mbps_if30capture_ids_per_second':sum(r['wire_bytes'] for r in accepted)/len(rows)*8*30/1e6,
            'pooled_metrics':pooled(rows),'final_anchor_id':encoder.anchor_id,
            'retained_anchor_array_bytes':encoder.retained_reference_bytes(),
            'scope':'Immediate in-process ACK after full receiver+hash check; rejected sources pay all selected preparation. No capture/feedback/transport/decoder-stage schedule.'}


def common_comparison(a,b):
    left={r['id']:r for r in a['rows'] if r['accepted']};right={r['id']:r for r in b['rows'] if r['accepted']}
    ids=sorted(set(left)&set(right));la=[left[i] for i in ids];rb=[right[i] for i in ids]
    assert all(left[i]['input_sha256']==right[i]['input_sha256'] for i in ids)
    lm,rm=pooled(la),pooled(rb)
    return {'common_admitted_ids':ids,'only_uniform':sorted(set(left)-set(right)),
            'only_priority':sorted(set(right)-set(left)),
            'uniform_common_metrics':lm,'priority_common_metrics':rm,
            'priority_minus_uniform_psnr_db':{k:None if not ids else rm[k]['psnr_db']-lm[k]['psnr_db'] for k in lm},
            'same_cap_not_equal_bytes':True,'priority_roi_scale':8,'uniform_scales':[16,32]}


def stress_frames():
    rng=np.random.default_rng(0x808)
    frames=[]
    for i in range(12):
        if i<6:rgb=rng.integers(0,256,(480,720,3),dtype=np.uint8)
        else:
            rgb=np.full((480,720,3),(12,18,24),np.uint8)
            rgb[52:60,20+i:92+i]=(245,245,235)
        frames.append(rgb)
    return frames,{'source':'synthetic-noise-to-quiet','seed':'0x808','frame_count':12,
                   'frame_sha256':[hashlib.sha256(a.tobytes()).hexdigest() for a in frames],
                   'active_rects':[(0,0,720,480)]*12,'synthetic':True,
                   'scope':'Six seeded high-entropy inputs then six simple recovery images; no native FPS or real game claim'}


def paired_keys(frames,manifest):
    records=[]
    # A fixed declared pressure cap, not a per-input oracle derived from future
    # sizes. This exercises key fallbacks; it is not the nominal48KiB profile.
    for repeat in range(2):
        for i,rgb in enumerate(frames):
            controllers={label:Controller(config=Config(frame_cap=28672)) for label in ('naive','shared')}
            order=('naive','shared') if (repeat+i)%2==0 else ('shared','naive')
            decisions={};call_times={}
            for label in order:
                call_started=time.perf_counter_ns()
                decisions[label]=controllers[label].prepare(rgb,0,reuse=label=='shared')
                call_times[label]=(time.perf_counter_ns()-call_started)/1e6
            a,b=decisions['naive'],decisions['shared']
            assert a.packet==b.packet and a.selected==b.selected
            assert [(r['bytes'],r['fits']) for r in a.attempts]==[(r['bytes'],r['fits']) for r in b.attempts]
            assert b.analyze_calls==1 and a.analyze_calls==len(a.attempts)
            if b.accepted:
                actual,_=codec.Receiver().receive(b.packet)
                expected=hashlib.sha256(actual.tobytes()).hexdigest()
                assert all(c.encoder.expected_hash(0)==expected for c in controllers.values())
            records.append({'repeat':repeat,'source_index':i,'input_sha256':manifest['frame_sha256'][i],
                            'cap_bytes':28672,'accepted':b.accepted,'selected':b.selected,'attempts':len(b.attempts),
                            'naive_service_ms':call_times['naive'],'shared_service_ms':call_times['shared'],
                            'naive_internal_ms':a.service_ms,'shared_internal_ms':b.service_ms,
                            'naive_forward_calls':a.forward_calls,'shared_forward_calls':b.forward_calls,
                            'bytes':None if b.packet is None else len(b.packet),
                            'packet_sha256':None if b.packet is None else hashlib.sha256(b.packet).hexdigest()})
    return {'records':records,'checks':len(records),
            'naive_ms':stats([r['naive_service_ms'] for r in records]),
            'shared_ms':stats([r['shared_service_ms'] for r in records]),
            'two_attempt_pairs':sum(r['attempts']==2 for r in records),
            'admitted_pairs':sum(r['accepted'] for r in records),
            'source_scope':'Twelve native input captures repeated twice as independent keys; no temporal/admission-history timing equivalence to main sequence.'}


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    sources=[HERE/'benchmark.py',HERE/'controller.py',HERE/'test_controller.py',Path(codec.__file__),
             Path(codec.roi.__file__),Path(codec.ft.__file__),Path(codec.mt.__file__),Path(codec.token_coeff.__file__),
             Path(codec.word_coeff.__file__),Path(codec.word_coeff.frozen_codec.__file__),Path(corpus.__file__)]
    hashes={str(p):digest(p) for p in sources};scenes=[];pairs=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        for start in (1,4):
            frames,manifest=corpus.load_video(media/f'{clip}.mp4',max_frames=12,start_seconds=start)
            cases={policy:run_sequence(frames,manifest,policy) for policy in ('uniform','priority')}
            scenes.append({'name':f'{clip}-start{start}','manifest':manifest,'cases':cases,
                           'comparison':common_comparison(cases['uniform'],cases['priority'])})
            print(scenes[-1]['name'],{k:{f:v[f] for f in ('admitted','fallback_count','two_attempt_calls','service_ms','packet_bytes')} for k,v in cases.items()},flush=True)
            if start==4:
                pair=paired_keys(frames,manifest);pairs.append({'name':clip,'manifest':manifest,**pair})
                print(clip,'paired',pair['naive_ms'],pair['shared_ms'],'two_attempt',pair['two_attempt_pairs'],flush=True)
    frames,manifest=stress_frames();cases={policy:run_sequence(frames,manifest,policy) for policy in ('uniform','priority')}
    scenes.append({'name':'synthetic-noise-to-quiet','manifest':manifest,'cases':cases,
                   'comparison':common_comparison(cases['uniform'],cases['priority'])})
    print('stress',{k:(v['admitted'],v['dropped'],v['fallback_count']) for k,v in cases.items()},flush=True)
    assert hashes=={str(p):digest(p) for p in sources},'executed source changed'
    result={'evidence':'Actual GM01 two-candidate admission with shared forward transform; paired actual Python service, not a live/network/hardwareFPS proof',
            'source_sha256':hashes,'versions':{'python':platform.python_version(),'numpy':np.__version__,'pillow':PIL.__version__,'pyav':av.__version__},
            'nominal_cap_bytes':49152,'paired_pressure_cap_bytes':28672,'scenes':scenes,'paired_keys':pairs,
            'policy':dataclasses.asdict(Config()),'priority_floor':'Scale8 in declared rectangles for both candidates; no automatic HUD detection or perceptual-quality guarantee',
            'causality':{'future_frames_used':0,'oracle_used_for_selection':False,'selection_inputs':['current candidate byte lengths','fixed current geometry/maps','configured cap'],'quality_metrics_used_for_selection':False},
            'timing_scope':'Map construction+RGB/prediction+forwardDCT+everycandidatequant/entropy/assembly+selection+selectedkeyreconstructioncommit; excludes sourcecapture/scale,lazyoracle,receiver,network,QSPI,vblank. Rejected attempts are paid.',
            'load_scope':'Uncontrolled concurrent host load; paired order alternated, no affinity/isolatedwarmup. Twelveprecompressednativecaptures/repeat, not distinct30fps or broad heldout evidence.',
            'memory_scope':'Prepared retains prediction+rawDCT arrays during bounded call; one current candidate plus selectedpacket/pendingoracle storage. Original source/candidate/reconstruction temporaries are host allocations, not receiverRAM proof.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
