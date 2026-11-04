#!/usr/bin/env python3
"""Actual AR02 GM/SR candidates with common reconstruction and optional UI."""
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import time
import numpy as np
import unified_codec as u
import ui_plugin

HERE=Path(__file__).resolve().parent
BASE_PROFILES=('gm','exact','prune4')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(a):return hashlib.sha256(a.tobytes()).hexdigest()
def stats(a):return dict(n=len(a),mean=float(np.mean(a)),p95=float(np.percentile(a,95)),max=max(a)) if a else None


def dependencies():
    g=u.gm
    return sorted(set([HERE/n for n in ('unified_codec.py','benchmark.py','verify.py','test_unified_codec.py')]+[
        Path(ui_plugin.__file__),Path(ui_plugin.frozen_cache.__file__),Path(ui_plugin.hybrid.__file__),
        Path(ui_plugin.row.__file__),Path(ui_plugin.hp.__file__),Path(u.old.__file__),Path(u.overlap_codec.__file__),
        Path(u.sr.__file__),Path(u.fast_codec.__file__),Path(u.corpus.__file__),Path(g.__file__),
        Path(g.roi.__file__),Path(g.mt.__file__),Path(g.ft.__file__),Path(g.token_coeff.__file__),
        Path(g.word_coeff.__file__),Path(g.word_coeff.frozen_codec.__file__)]))


def metrics(source,actual,active):
    x,y,w,h=active
    a=u.corpus.expand565(u.corpus.rgb565(source)).astype(np.float64)
    b=u.corpus.expand565(u.corpus.rgb565(actual)).astype(np.float64)
    mse=float(np.mean((a[y:y+h,x:x+w]-b[y:y+h,x:x+w])**2))
    return dict(active_rgb565_mse=mse,active_rgb565_psnr=None if mse==0 else 10*math.log10(65025/mse))


def oracle(source,frame,mapped,key,ref):
    local=u.gm.Encoder(window=3)
    if ref is not None:local.anchor_id,local._anchor=ref.frame_id,ref.planes
    prepared=local.analyze(source,frame,force_key=key)
    candidate=local.encode_candidate(prepared,mapped)
    return u.fast_codec.reconstruct(candidate.coefficients,prepared.prediction,mapped,source.shape[1],source.shape[0])


def scene(name,frames,manifest,cohort,profiles,*,all_keys=False):
    controls={}
    for profile in profiles:
        mode=profile.removesuffix('_ui')
        builder=ui_plugin.PatchSelector() if profile.endswith('_ui') else None
        controls[profile]=(u.Encoder(mode=mode,patch_builder=builder),u.Receiver())
    w,h=720,480
    mapped=u.gm.roi.declared_map(w,h,((16,48,192,80),(160,352,400,80)),8,16)
    protected=np.repeat(np.repeat(mapped==8,16,axis=0),16,axis=1)[:h,:w]
    rows={p:[] for p in profiles}
    for i,rgb in enumerate(frames):
        offset=i%len(profiles);order=profiles[offset:]+profiles[:offset]
        for profile in order:
            enc,rx=controls[profile];key=all_keys or i%30==0;promote=not key and i%8==0
            references=enc.banks.copy();before_calls=enc.forward_calls;before_analysis=enc.analysis_count
            started=time.perf_counter_ns();decision=enc.prepare(rgb,i,scale_map=mapped,force_key=key,promote=promote)
            prep=(time.perf_counter_ns()-started)/1e6
            record=dict(id=i,input_sha256=manifest['frame_sha256'][i],accepted=decision.accepted,
                attempted_key=decision.key,promoted=decision.promoted,reference_bank=decision.reference_bank,
                reference_id=decision.reference_id,reference_tag=decision.reference_tag.hex(),
                prepare_ms=prep,internal_service_ms=decision.service_ms,info=decision.info,
                actual_forward_calls=enc.forward_calls-before_calls,actual_analyze_calls=enc.analysis_count-before_analysis)
            if not decision.accepted:
                assert not enc.pending
                record['pending_after_feedback']=0;rows[profile].append(record);continue
            expected=enc.expected_hash(i);expected_base=enc.expected_base_hash(i)
            started=time.perf_counter_ns();task=rx.begin(decision.packet);actual_planes=task.planes
            actual,info,ack=rx.complete(task);receive=(time.perf_counter_ns()-started)/1e6
            assert digest(actual)==expected and info['base_rgb_sha256']==expected_base
            reference=None if decision.key else references[decision.reference_bank]
            baseline=oracle(rgb,i,mapped,decision.key,reference)
            maximum=max(int(np.max(np.abs(a-b))) for a,b in zip(baseline,actual_planes))
            assert maximum<=decision.info['level']
            gm_base=u.gm.ft.planes_to_rgb(baseline);actual_base=u.gm.ft.planes_to_rgb(actual_planes)
            priority_errors=int(np.count_nonzero(u.corpus.rgb565(gm_base)[protected]!=u.corpus.rgb565(actual_base)[protected]))
            assert priority_errors==0
            selected_errors=0
            source_words=u.corpus.rgb565(rgb);out_words=u.corpus.rgb565(actual)
            for patch in info['patches']:
                x,y,rw,rh=patch['rect'];selected_errors+=int(np.count_nonzero(source_words[y:y+rh,x:x+rw]!=out_words[y:y+rh,x:x+rw]))
            assert selected_errors==0
            started=time.perf_counter_ns();accepted=enc.ack(ack);feedback_ms=(time.perf_counter_ns()-started)/1e6
            assert accepted
            for slot in (0,1):
                left,right=enc.banks[slot],rx.banks[slot]
                assert (left is None)==(right is None)
                if left is not None:
                    assert (left.frame_id,left.tag)==(right.frame_id,right.tag)
                    for a,b in zip(left.planes,right.planes):np.testing.assert_array_equal(a,b)
            record.update(packet_bytes=len(decision.packet),packet_sha256=sha_bytes(decision.packet),
                inner_codec=info['inner_codec'],level=info['level'],receive_ms=receive,feedback_ms=feedback_ms,
                complete_service_ms=prep+receive+feedback_ms,decoded_rgb_sha256=digest(actual),base_rgb_sha256=info['base_rgb_sha256'],
                expected_rgb_sha256=expected,expected_base_rgb_sha256=expected_base,
                max_yuv_delta_same_reference_gm=maximum,protected_gm_rgb565_mismatches=priority_errors,
                selected_source_rgb565_mismatches=selected_errors,selected_pixels=info['selected_pixels'],
                patches=info['patches'],same_reconstructed_banks=True,pending_after_feedback=len(enc.pending),
                metrics=metrics(rgb,actual,manifest['active_rects'][i]))
            rows[profile].append(record)
    summary={}
    for profile,records in rows.items():
        admitted=[r for r in records if r['accepted']]
        summary[profile]=dict(source_ids=len(records),admitted=len(admitted),rejected=len(records)-len(admitted),
            mean_prepare_ms_all=stats([r['prepare_ms'] for r in records]),mean_receive_ms=stats([r['receive_ms'] for r in admitted]),
            mean_packet_bytes=None if not admitted else float(np.mean([r['packet_bytes'] for r in admitted])),
            codecs={name:sum(r['inner_codec']==name for r in admitted) for name in ('GM01','SR01')},
            mean_exact_source_pixels=None if not admitted else float(np.mean([r['selected_pixels'] for r in admitted])),
            active_rgb565_mse=None if not admitted else float(np.mean([r['metrics']['active_rgb565_mse'] for r in admitted])),
            rejected_work_ms=sum(r['prepare_ms'] for r in records if not r['accepted']))
    return dict(name=name,cohort=cohort,manifest=manifest,all_keys=all_keys,profiles=rows,summary=summary)


def sha_bytes(data):return hashlib.sha256(data).hexdigest()


def main():
    paths=dependencies();pins={str(p):sha(p) for p in paths};scenes=[];started=time.perf_counter()
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=u.corpus.load_video(media/(clip+'.mp4'),max_frames=60,start_seconds=1)
        result=scene(clip,frames,manifest,'native_temporal',BASE_PROFILES)
        scenes.append(result);print(clip,json.dumps(result['summary']),flush=True)
    frames,manifest=u.corpus.load_video(media/'mass-effect-2600.mp4',max_frames=180,start_seconds=4)
    assert len(frames)==180
    result=scene('mass-effect-2600-heldout180',frames,manifest,'native_heldout_temporal',BASE_PROFILES)
    scenes.append(result);print(result['name'],json.dumps(result['summary']),flush=True)
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=u.corpus.load_video(media/(clip+'.mp4'),max_frames=8,start_seconds=4)
        result=scene(clip+'-ui-heldout-keys',frames,manifest,'native_ui_keys',tuple(p+'_ui' for p in BASE_PROFILES),all_keys=True)
        scenes.append(result);print(result['name'],json.dumps(result['summary']),flush=True)
    rng=np.random.default_rng(1505);images=[]
    for i in range(12):
        if 4<=i<7:rgb=rng.integers(0,256,(480,720,3),dtype=np.uint8)
        else:
            yy,xx=np.indices((480,720));rgb=np.stack(((xx//8+i)%180+20,(yy//8+i)%140+30,np.full_like(xx,70+i)),axis=-1).astype(np.uint8)
        images.append(rgb)
    manifest=dict(source='synthetic:seed1505-cuts-noise',synthetic=True,frame_count=12,
                  frame_sha256=[digest(a) for a in images],active_rects=[(0,0,720,480)]*12)
    profiles=BASE_PROFILES+tuple(p+'_ui' for p in BASE_PROFILES)
    result=scene('synthetic-cuts-noise',images,manifest,'synthetic',profiles)
    scenes.append(result);print(result['name'],json.dumps(result['summary']),flush=True)
    assert pins=={str(p):sha(p) for p in paths},'timed source changed'
    decisions=sum(len(rows) for s in scenes for rows in s['profiles'].values())
    output=dict(evidence='Actual unifiedAR02 GM/SR references plus exact displaypatches,not target timing',
        source_sha256=pins,scenes=scenes,source_ids=sum(s['manifest']['frame_count'] for s in scenes),decisions=decisions,
        versions=dict(python=platform.python_version(),**{n:importlib.metadata.version(n) for n in ('numpy','Pillow','av')}),
        total_python_wall_seconds=time.perf_counter()-started,
        syntax_scope='AR02/AF02 includesactual GM/SR fullinner minimumandoptionalHP01/HR01patches. GMfallbackkeepssmallercompleteinner; UIcoveragecanvarywithremainingcap. Not installedpeercompatible.',
        quality_scope='Prune2/4bounds comparequantizedGM atTHE SAME currentreference,notoriginalsourceoradiifferenthistory. PriorityGMwordsprotectedwithchroma halo. UIselectedwords areexactoriginalsourceRGB565 andexcludedfromYUVreference/tag. Metricsquantizebothsource/output565.',
        timing_scope='Completeprepare including oneanalyze/3forwards,actualGM andSRsplit/prunecandidates/losers,sharedalreadyserializedCP02densepayloads,UIselection/validation,promotionreconstruct/hash. Decoderfullparse/reconstruct/UI plusAFbuildandencoderAFparse/storemeasured. Maps/sourceBOX/offlineacquisition/verificationoracles/hash/metrics excluded. Rotatingprofileorder,uncontrolledhostload.',
        reference_scope='Immediatefeedback,keys30/promotions8,overlapbankrulesbutnorealqueuedowners/transporttiming. TwoACKedbankswithcontenttags; allsender/receiverbankarraysverified independently afterfeedback.',
        memory_scope='Two retainedbanks pluspendingreconstruction,coeff/raw/prediction/output/patch/sourcearraysandcandidatebytesextra; nopeakphysicalmemoryorFPGAfitproof.',
        source_scope='300nativebaseIDs+16nativeUIkeyIDs+12syntheticIDs repeatedacrossprofiles; relatedprecompressed25/29.88fpssourcesat720x480nativeactive720x405,notlive30Hz acquisition.',
        deployment_scope='No nativeSunshine/ESP32/FPGA implementation,noRF/QSPI/SDRAMorphysical30fpsproof.')
    (HERE/'results.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
