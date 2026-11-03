#!/usr/bin/env python3
"""Actual byte-identical GM01 source-cache preparation pairs at720x480."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time
import numpy as np
import memo_encoder as memo

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(a):return hashlib.sha256(a.tobytes()).hexdigest()
def stats(a):return {'n':len(a),'mean':float(np.mean(a)),'p50':float(np.percentile(a,50)),'p95':float(np.percentile(a,95)),'max':max(a)}


def main():
    sources=[HERE/'memo_encoder.py',HERE/'benchmark.py',HERE/'test_memo_encoder.py',Path(memo.gm.__file__),Path(corpus.__file__),
        Path(memo.gm.roi.__file__),Path(memo.gm.ft.__file__),Path(memo.gm.mt.__file__),Path(memo.gm.token_coeff.__file__),
        Path(memo.gm.word_coeff.__file__),Path(memo.gm.word_coeff.frozen_codec.__file__)]
    pins={str(p):sha(p) for p in sources}
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')));inputs=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/(clip+'.mp4'),max_frames=60,start_seconds=1)
        inputs.append((clip,frames,manifest,30))
    rng=np.random.default_rng(1201)
    for name in ('flat-repeat','alternating-two-sources','noise-repeat-cut'):
        if name=='flat-repeat':frames=[np.full((480,720,3),[40,60,80],np.uint8) for _ in range(12)]
        elif name=='alternating-two-sources':frames=[np.full((480,720,3),[40+i%2,60,80],np.uint8) for i in range(12)]
        else:
            images=[rng.integers(0,256,(480,720,3),dtype=np.uint8) for _ in range(4)]
            frames=[images[i//3].copy() for i in range(12)]
        manifest={'source':'synthetic:'+name,'synthetic':True,'frame_count':len(frames),
            'frame_sha256':[digest(a) for a in frames],'active_rects':[(0,0,720,480)]*len(frames)}
        inputs.append((name,frames,manifest,6))
    cases=[]
    for case_index,(name,frames,manifest,key_period) in enumerate(inputs):
        baseline=memo.gm.Encoder();cached=memo.Encoder();rx=memo.gm.Receiver();rows=[]
        m=memo.gm.roi.declared_map(720,480,((16,48,192,80),(160,352,400,80)),8,16)
        for i,rgb in enumerate(frames):
            outputs={};times={};calls={}
            order=(('baseline',baseline),('memo',cached)) if (i+case_index)%2==0 else (('memo',cached),('baseline',baseline))
            for label,enc in order:
                before=enc.forward_calls;t=time.perf_counter_ns()
                outputs[label]=enc.prepare(rgb,i,scale_map=m,force_key=(i%key_period==0));times[label]=(time.perf_counter_ns()-t)/1e6
                calls[label]=enc.forward_calls-before
            assert outputs['baseline']==outputs['memo']
            packet=outputs['memo'];actual,info=rx.receive(packet)
            assert digest(actual)==baseline.expected_hash(i)==cached.expected_hash(i)
            rows.append({'id':i,'input_sha256':manifest['frame_sha256'][i],'key':i%key_period==0,
                'baseline_packet_sha256':hashlib.sha256(outputs['baseline']).hexdigest(),'memo_packet_sha256':hashlib.sha256(packet).hexdigest(),
                'packet_bytes':len(packet),'cap_fit':len(packet)<=49152,'decoded_rgb_sha256':digest(actual),
                'baseline_prepare_ms':times['baseline'],'memo_prepare_ms':times['memo'],
                'baseline_forward_calls':calls['baseline'],'memo_forward_calls':calls['memo'],
                'memo':cached.last_memo_info.copy(),'reference_id':info['reference_id'],'anchor_id':info['anchor_id']})
            assert baseline.ack(i,epoch=1) and cached.ack(i,epoch=1)
            for a,b in zip(baseline._anchor,cached._anchor):np.testing.assert_array_equal(a,b)
        summary={}
        for kind in ('all','key','p','hit','miss'):
            selected=[r for r in rows if kind=='all' or (kind in ('key','p') and r['key']==(kind=='key'))
                      or (kind in ('hit','miss') and r['memo']['hit']==(kind=='hit'))]
            if not selected:continue
            summary[kind]={'frames':len(selected),'baseline_prepare_ms':stats([r['baseline_prepare_ms'] for r in selected]),
                'memo_prepare_ms':stats([r['memo_prepare_ms'] for r in selected]),
                'baseline_forward_calls':sum(r['baseline_forward_calls'] for r in selected),
                'memo_forward_calls':sum(r['memo_forward_calls'] for r in selected)}
        cases.append({'source':name,'manifest':manifest,'key_period':key_period,'rows':rows,'summary':summary,
                      'unique_source_rgb_hashes':len(set(manifest['frame_sha256']))})
        print(name,'hits',sum(r['memo']['hit'] for r in rows),'mean',summary['all']['baseline_prepare_ms']['mean'],
              summary['all']['memo_prepare_ms']['mean'],'capfails',sum(not r['cap_fit'] for r in rows),flush=True)
    assert pins=={str(p):sha(p) for p in sources}
    result={'evidence':'Actualexactlast-source P-payloadcache preservesfullGM01bytesandnormalACKkey/creditsemantics.',
        'source_sha256':pins,'versions':{'python':platform.python_version(),**{x:importlib.metadata.version(x) for x in ('numpy','Pillow','av')}},
        'cases':cases,'paired_source_ids':sum(len(c['rows']) for c in cases),'encoded_packets':2*sum(len(c['rows']) for c in cases),
        'decoded_packets':sum(len(c['rows']) for c in cases),
        'scope':'All720x480. Same completepacketbytes and reconstructedpixels; no rate savings,newwire/reference,or targetFPSclaim. Wholepacketstillsentanddecoded.',
        'timing_scope':'Completeprepincludingvalidation,currentRGB/mapequalitychecks,misssourcecopy,normalkeyreconstruction,andhitheaderCRC. Mapsconstructedoutsidebothclocks;sourcecapture/resize,oracle/decode/hashes excluded. AlternatingAB/BAorders,hostloaduncontrolled; nocacheperformanceclaimforuniquesources.',
        'memory_scope':'PCcacheboundedtooneimmutableRGBsourcecopy,onequantmap,onePpayload/header andpointertoexistingimmutableACKkey. DoesnotcopyYUVkeyorallocateFPGA/ESP32storage; existingpendingpacket/transformworkspacesremainextra.',
        'comparison_scope':'Tworelatedprecompressednative25/29.88fpssamples andsyntheticrepeat/noisecontrols. Repeatedsourcehitratio notrepresentativeof30distinctfpsgameplay. Capfailpacketstestcachearithmeticbutarecountednotadmittedstreamframes.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
