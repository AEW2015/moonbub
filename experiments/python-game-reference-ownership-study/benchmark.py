#!/usr/bin/env python3
"""Actual measured-stage reference-bank feedback and ownership at720x480."""
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
spec=importlib.util.spec_from_file_location('reference_native_inputs',HERE.parent/'python-game-service-study/benchmark.py')
source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dependencies():
    rc=model.rc
    paths=[HERE/x for x in ('model.py','benchmark.py','test_model.py','verify.py')]
    paths += [Path(source.__file__),Path(rc.__file__),Path(rc.gm.__file__),Path(model.transport.__file__),
              Path(model.corpus.__file__),Path(rc.gm.roi.__file__),Path(rc.gm.mt.__file__),
              Path(rc.gm.ft.__file__),Path(rc.gm.token_coeff.__file__),Path(rc.gm.word_coeff.__file__),
              Path(rc.gm.word_coeff.frozen_codec.__file__)]
    return sorted(set(paths))


def brief(case):
    r=case['result'];packets=r['packets'];commits=r['commits']
    return dict(source=case['source'],profile=case['profile'],captures=r['capture_count'],
                strict=r['presented_strict'],eventual=r['presented_eventual'],
                diagnostic_ids_per_second=r['diagnostic_ids_per_second'],
                prepared=r['prepared'],decoded=len(commits),
                accepted_promotions=sum(p['admitted'] and p['promoted'] for p in packets),
                bank1_references=sum(p['admitted'] and p['reference_bank']==1 for p in packets),
                promotion_reconstruction_ms=sum(p['info']['reconstruction_ms'] for p in packets if p['promoted']),
                reference_tag_ms=sum(p['info']['reference_tag_ms'] for p in packets),
                encode_service_ms=sum(p['encode_service_ms'] for p in packets),
                decode_service_ms=sum(w['service_ms'] for w in r['work'] if w['stage'].startswith('decode_')),
                logical_reference_read_bytes=sum(p['info']['reference_read_bytes'] for p in packets),
                encoder_reference_array_peak_bytes=r['sender_peak_reference_array_bytes'],
                receiver_reference_array_peak_bytes=r['receiver_peak_reference_array_bytes'],
                forward_ipv4_udp_bytes=r['forward_ipv4_udp_bytes'],
                active_rgb565_mse_mean=None if not commits else float(np.mean([c['active_rgb565_mse'] for c in commits])),
                admission_wait_ms=r['admission_wait_ms'],drops=r['drops_by_reason'])


def case(frames,manifest,label,profile,*,promotion,refresh,**faults):
    cfg=model.Config(promotion_period=promotion,refresh_period=refresh,**faults)
    result=model.run(frames,manifest,cfg)
    assert not result['unresolved_ids'] and all(x is None for x in result['unresolved_sender_slots'])
    assert not result['unresolved_encoder_pending'] and not result['unresolved_ingress']
    assert not result['unresolved_receiver_readers'] and not result['unresolved_decode']
    return dict(source=label,profile=profile,manifest=manifest,result=result)


def main():
    paths=dependencies();pins={str(p):sha(p) for p in paths};cases=[];started=time.perf_counter()
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    primary=[('immutable30',0,30),('recent8_key30',8,30),('recent16_key30',16,30)]
    for index,clip in enumerate(('mass-effect-combat','mass-effect-2600')):
        frames,manifest=source.native(media/(clip+'.mp4'),n=60,start=1)
        for name,promote,refresh in (primary if index==0 else list(reversed(primary))):
            c=case(frames,manifest,clip,name,promotion=promote,refresh=refresh)
            cases.append(c);print(json.dumps(brief(c)),flush=True)
    frames,manifest=source.native(media/'mass-effect-2600.mp4',n=180,start=4)
    assert len(frames)==180
    for name,promote,refresh in [('immutable30',0,30),('recent8_key30',8,30),
                                 ('immutable_initial',0,0),('recent16_initial',16,0)]:
        c=case(frames,manifest,'mass-effect-2600-heldout180',name,promotion=promote,refresh=refresh)
        cases.append(c);print(json.dumps(brief(c)),flush=True)
    yy,xx=np.indices((480,720));images=[]
    for i in range(24):
        images.append(np.stack(((xx//8+i)%180+20,(yy//8+i)%140+20,np.full_like(xx,70+i)),axis=-1).astype(np.uint8))
    manifest=dict(source='synthetic:reference-fault-gradient24',synthetic=True,frame_count=len(images),
                  frame_sha256=[model.digest(f) for f in images],input_scope='Synthetic full720x480 fault workload,not native acquisition')
    for name,faults in [('key_chunk_loss',dict(drop_first_key_chunk=True)),
                        ('promotion_ack_loss',dict(drop_first_promotion_ack=True)),
                        ('conflicting_promotion_feedback',dict(conflict_first_promotion_feedback=True))]:
        c=case(images,manifest,'synthetic-fault24',name,promotion=8,refresh=0,**faults)
        cases.append(c);print(json.dumps(brief(c)),flush=True)
    assert pins=={str(p):sha(p) for p in paths},'executed source changed'
    result=dict(evidence='AR01 two-reference actual-packet ownership with paid host stages,not physical target timing',
                source_sha256=pins,cases=cases,case_count=len(cases),summary=[brief(c) for c in cases],
                total_python_wall_seconds=time.perf_counter()-started,
                versions=dict(python=platform.python_version(),numpy=np.__version__,pillow=PIL.__version__,pyav=av.__version__),
                protocol_scope='AR01baseGM01/GF02/AF01only.NoHG01orSR01integration; different framing and decoder execution from v13UI, so no directFPScomparison.',
                timing_scope='Each actual BOX/map/encode/reject/packetize/feedbatch/decodebegin/complete/abort/AFparse+apply pays observedwall on independentserializedvirtualservers.No fixedservice tape. Forward8Mb/s/reverse8Mb/s/QSPI160Mb/s/propagation10ms/vblank60Hz assumed.',
                transport_scope='AllactualGF02chunksconsume wiretime; frame-batchedfeed afterwholeframewirecompletion differsfrompreviousperchunkmodel. Reassemblytwo actualslots,3hosttransactions,4feedbackdescriptors,3framebufferroles.',
                publication_scope='Offline mutating ACKapply/Receiver.complete calls are staged with semantic snapshots until paidcompletion; expiry/deadline wins. Readleases/ingresspins and reservations persist through completion. Workcountersare not refunded. This is singlethreadeddriver scaffolding,not a native concurrentAPI.',
                source_scope='Native25/29.88fpsprecompressedfiles decodedoffline andscheduled30IDs/s; capturedesktopread/decodeexcluded, actualBOXincluded. Allperformancecanvases720x480,nativeactive720x405. RepeatedpolicyIDsnotuniqueimages.',
                memory_scope='Two retainedYUVbanksperpeer pluspendingpromotionreconstruction,RGBoutput/scratch,coeffarrays,PCsourceimages,GF02copiesqueuesanddisplaymetadataextra. Logical8bit/referencepasses and int16arraycountsnotpeakmemory/SDRAMtiming.',
                selection_scope='Promotion/key cadencecurrentcaptureIDsandACKedhistoryonly; conservativefullpendingdrainbeforepromotion. Quality metrics/expectedhash oracleoutsidepaidserviceandneverusedbylivepolicy.')
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
