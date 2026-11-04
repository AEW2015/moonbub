#!/usr/bin/env python3
"""Controlled serial versus bank-specific overlap in the same finite model."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import time

import av
import numpy as np
import PIL
import model

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('overlap_native_inputs',HERE.parent/'python-game-service-study/benchmark.py')
source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dependencies():
    rc=model.rc
    return sorted(set([HERE/name for name in ('model.py','overlap_codec.py','benchmark.py','test_overlap.py','verify.py')]+
        [Path(source.__file__),Path(rc.__file__),Path(rc.gm.__file__),Path(model.transport.__file__),
         Path(model.corpus.__file__),Path(rc.gm.roi.__file__),Path(rc.gm.mt.__file__),Path(rc.gm.ft.__file__),
         Path(rc.gm.token_coeff.__file__),Path(rc.gm.word_coeff.__file__),Path(rc.gm.word_coeff.frozen_codec.__file__),
         HERE.parent/'python-game-reference-ownership-study/model.py']))


def brief(case):
    r=case['result'];packets=r['packets'];commits=r['commits']
    return dict(source=case['source'],profile=case['profile'],policy=case['policy'],captures=r['capture_count'],
        prepared=r['prepared'],decoded=len(commits),strict=r['presented_strict'],eventual=r['presented_eventual'],
        diagnostic_ids_per_second=r['diagnostic_ids_per_second'],
        accepted_promotions=sum(p['admitted'] and p['promoted'] for p in packets),
        bank1_references=sum(p['admitted'] and p['reference_bank']==1 for p in packets),
        bank0_fallbacks=sum(p['admitted'] and p['bank0_fallback'] for p in packets),
        key0_during_pending_writer=sum(p['admitted'] and p['bank0_fallback'] and
            p['info'].get('pending_writers_before',0)>0 for p in packets),
        promotions_with_pending_key0=sum(p['admitted'] and p['promoted'] and
            p['info'].get('pending_bank0_consumers',0)>0 for p in packets),
        promotion_reconstruction_ms=sum(p['info']['reconstruction_ms'] for p in packets if p['promoted']),
        reference_tag_ms=sum(p['info']['reference_tag_ms'] for p in packets),
        encode_service_ms=sum(p['encode_service_ms'] for p in packets),
        decode_service_ms=sum(w['service_ms'] for w in r['work'] if w['stage'].startswith('decode_')),
        forward_ipv4_udp_bytes=r['forward_ipv4_udp_bytes'],
        mean_packet_bytes=float(np.mean([p['bytes'] for p in packets if p['admitted']])),
        active_rgb565_mse_mean=None if not commits else float(np.mean([c['active_rgb565_mse'] for c in commits])),
        max_age_ms=max((p['age_ms'] for p in r['presented']),default=None),
        admission_wait_ms=r['admission_wait_ms'],drops=r['drops_by_reason'])


def case(frames,manifest,label,profile,*,policy,promotion,refresh,**faults):
    cfg=model.Config(reference_policy=policy,promotion_period=promotion,refresh_period=refresh,**faults)
    r=model.run(frames,manifest,cfg)
    assert not r['unresolved_ids'] and all(v is None for v in r['unresolved_sender_slots'])
    assert not r['unresolved_encoder_pending'] and not r['unresolved_ingress']
    assert not r['unresolved_receiver_readers'] and not r['unresolved_decode']
    return dict(source=label,profile=profile,policy=policy,manifest=manifest,result=r)


def compare(a,b):
    aa={p['id']:p for p in a['result']['packets'] if p['admitted']}
    bb={p['id']:p for p in b['result']['packets'] if p['admitted']}
    common=sorted(aa.keys()&bb.keys())
    fields=('key','promoted','reference_bank','reference_id','reference_tag')
    same_choices=[i for i in common if all(aa[i][f]==bb[i][f] for f in fields)]
    for i in same_choices:assert aa[i]['packet_sha256']==bb[i]['packet_sha256']
    ac={c['id']:c for c in a['result']['commits']};bc={c['id']:c for c in b['result']['commits']}
    common_decodes=sorted(ac.keys()&bc.keys())
    return dict(source=a['source'],control=a['profile'],candidate=b['profile'],common_admitted_ids=common,
        same_reference_and_promotion_ids=same_choices,same_choice_packet_hashes_exact=True,
        common_decoded_ids=common_decodes,
        common_decoded_active_mse_delta_mean=None if not common_decodes else float(np.mean([
            bc[i]['active_rgb565_mse']-ac[i]['active_rgb565_mse'] for i in common_decodes])),
        strict_delta=b['result']['presented_strict']-a['result']['presented_strict'],
        eventual_delta=b['result']['presented_eventual']-a['result']['presented_eventual'],
        caveat='Policies cause different admission/ACK/reference histories and source subsets. Host work is remeasured per run; equal quantizers do not imply equal output quality.')


def main():
    pins={str(p):sha(p) for p in dependencies()};cases=[];pairs=[];started=time.perf_counter()
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    for index,clip in enumerate(('mass-effect-combat','mass-effect-2600')):
        frames,manifest=source.native(media/(clip+'.mp4'),n=60,start=1)
        selected={}
        for policy in (('serial','overlap') if index==0 else ('overlap','serial')):
            c=case(frames,manifest,clip,policy+'_recent8_key30',policy=policy,promotion=8,refresh=30)
            selected[policy]=c;cases.append(c);print(json.dumps(brief(c)),flush=True)
        pairs.append(compare(selected['serial'],selected['overlap']))
    frames,manifest=source.native(media/'mass-effect-2600.mp4',n=180,start=4)
    selected={}
    for profile,policy,promotion in [('immutable_initial','serial',0),
                                     ('serial_recent16_initial','serial',16),
                                     ('overlap_recent16_initial','overlap',16)]:
        c=case(frames,manifest,'mass-effect-2600-heldout180',profile,policy=policy,promotion=promotion,refresh=0)
        selected[profile]=c;cases.append(c);print(json.dumps(brief(c)),flush=True)
    pairs.append(compare(selected['serial_recent16_initial'],selected['overlap_recent16_initial']))
    pairs.append(compare(selected['immutable_initial'],selected['overlap_recent16_initial']))
    yy,xx=np.indices((480,720))
    frames=[np.stack(((xx//8+i)%180+20,(yy//8+i)%140+20,np.full_like(xx,70+i)),axis=-1).astype(np.uint8) for i in range(24)]
    manifest=dict(source='synthetic:overlap-fault-gradient24',synthetic=True,frame_count=24,
        frame_sha256=[model.digest(f) for f in frames],input_scope='Declared synthetic full720x480; no live acquisition')
    selected={}
    for policy in ('serial','overlap'):
        c=case(frames,manifest,'synthetic-lost-promotion-ack24',policy+'_lost_promotion_ack',
               policy=policy,promotion=8,refresh=0,drop_first_promotion_ack=True)
        cases.append(c);selected[policy]=c;print(json.dumps(brief(c)),flush=True)
    pairs.append(compare(selected['serial'],selected['overlap']))
    assert pins=={str(p):sha(p) for p in dependencies()},'executed source changed'
    out=dict(evidence='AR01 same-wire bank-specific overlap policy with bounded references/readers and actual paid host stages',
        source_sha256=pins,cases=cases,case_count=len(cases),summary=[brief(c) for c in cases],pairs=pairs,
        total_python_wall_seconds=time.perf_counter()-started,
        versions=dict(python=platform.python_version(),numpy=np.__version__,pillow=PIL.__version__,pyav=av.__version__),
        policy_scope='Serialcontrolandbank-specificoverlap share one newmodel. Overlapadmitskey0fallbackwhileoldbank1consumersdrainorpromotionACKpending, permitspromotionwithpendingbank0only. Keydrainsall. ExactlysameAR01/AF01coding,CRC/tagrules and receiver.',
        timing_scope='ActualBOX/map/preparation/rejectedwork/fullpromotionreconstruction+tag/packetize/feedbatch/decodebegin/complete/abort/AFparse+apply wall costs paid on independentserializedvirtualservers. Link8Mb/s/reverse8Mb/s/QSPI160Mb/s/feedback10ms/vblank60Hz assumptions; not target concurrent timing.',
        transport_scope='Frame-batchedGF02wire/feed asparentownershipmodel, same stagedsemanticpublication/expiryguards and twoingress slots/threehosttransactions/fourfeedbackdescriptors/threeframebufferroles. Not v13UI pipeline.',
        quality_scope='Allbaseonly720x480,nativeactive720x405; noHG01orSR01. Recomputed actual references/capture subsets can changebytes/distortion; compare commonIDs too. Quality/hashoraclesoutsidecostsnotusedpolicy.',
        source_scope='Nativeprecompressed25/29.88fps files offlineRGB extraction excluded, measuredBOXincluded; scheduled30captureIDs/s notlive30distinctcapture. Duplicateimages andrepeatedpolicycohortsnotuniqueacquisitions.',
        memory_scope='Two retainedYUVbanks with bank-specificlogicalleases andreservedpromotiondestination; referencepayloadone-pass8bit/int16countersnotmeasuredDRAMtraffic. Additionalpendingpromotion/scratch/RGB/source/coefficients/GF02copies/queues/metadata notpeakRAMfit.',
        comparison_scope='Reversepolicyorderbetweenclips but uncontrolledhostload; policies remeasure service and alter causal capture/ACK/reference histories. No hardware30fps, RF, QSPI, native decoder or physical-memory qualification.')
    (HERE/'results.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
