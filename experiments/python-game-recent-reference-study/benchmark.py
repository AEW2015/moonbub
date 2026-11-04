#!/usr/bin/env python3
"""Actual two-bank codec bytes with independently reconstructed references."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import time

import av
import numpy as np
import PIL
import recent_codec as c

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus
spec=importlib.util.spec_from_file_location('recent_reference_quality',HERE.parent/'python-game-roi-study/benchmark.py')
quality=importlib.util.module_from_spec(spec);sys.modules[spec.name]=quality;spec.loader.exec_module(quality)
RECTS=((16,48,192,80),(160,352,400,80))
PROFILES=('gm_immutable','ar_immutable','ar_recent8')


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def array_digest(array):return hashlib.sha256(array.tobytes()).hexdigest()
def elapsed(start):return (time.perf_counter_ns()-start)/1e6
def stats(a):
    return dict(n=len(a),mean=float(np.mean(a)),p50=float(np.percentile(a,50)),
                p95=float(np.percentile(a,95)),max=max(a)) if a else None


def dependencies():
    return sorted(set([HERE/name for name in ('recent_codec.py','benchmark.py','verify.py','test_recent_codec.py')]+
        [Path(c.gm.__file__),Path(corpus.__file__),Path(quality.__file__),Path(c.gm.roi.__file__),
         Path(c.gm.mt.__file__),Path(c.gm.ft.__file__),Path(c.gm.token_coeff.__file__),
         Path(c.gm.word_coeff.__file__),Path(c.gm.word_coeff.frozen_codec.__file__)]))


def run_scene(name,frames,manifest,cohort,*,ar_only=False):
    profiles=PROFILES[1:] if ar_only else PROFILES
    pairs={p:(c.gm.Encoder(window=3),c.gm.Receiver()) if p=='gm_immutable'
              else (c.Encoder(window=3),c.Receiver()) for p in profiles}
    rows={p:[] for p in profiles};comparisons=[]
    m=c.gm.roi.declared_map(720,480,RECTS,8,16)
    for i,source in enumerate(frames):
        # Rotate actual call order at each source ID. Host load is uncontrolled.
        offset=i%len(profiles);order=profiles[offset:]+profiles[:offset]
        this={}
        for profile in order:
            enc,rx=pairs[profile];key=i%30==0;promote=profile=='ar_recent8' and i%8==0
            started=time.perf_counter_ns()
            if profile=='gm_immutable':
                prepared=enc.analyze(source,i,force_key=key)
                candidate=enc.encode_candidate(prepared,m)
                accepted=len(candidate.packet)<=49152
                packet=enc.commit(candidate) if accepted else None
                attempt_bytes=len(candidate.packet);encoder_info={}
            else:
                decision=enc.prepare(source,i,scale_map=m,force_key=key,promote=promote)
                packet=decision.packet;accepted=decision.accepted
                attempt_bytes=decision.info['bytes'];encoder_info=dict(decision.info)
            prepare_ms=elapsed(started)
            record=dict(id=i,input_sha256=manifest['frame_sha256'][i],accepted=accepted,
                        attempted_bytes=attempt_bytes,cap=49152,prepare_ms=prepare_ms,
                        attempted_key=key,promotion_requested=promote,encoder_info=encoder_info)
            if not accepted:
                record.update(pending_after_prepare=len(enc.pending),last_issued=enc.last_issued)
                if profile!='gm_immutable':
                    record['acknowledged_banks']={str(slot):None if bank is None else
                        dict(frame_id=bank.frame_id,tag=bank.tag.hex()) for slot,bank in enc.banks.items()}
                rows[profile].append(record);this[profile]=record;continue
            expected=enc.expected_hash(i)  # pure verification, not prep/receive service
            started=time.perf_counter_ns()
            if profile=='gm_immutable':
                actual,info=rx.receive(packet);ack=None
            else:actual,info,ack=rx.receive(packet)
            receive_ms=elapsed(started)
            actual_hash=array_digest(actual);assert expected==actual_hash
            parsed=(c.gm.parse(packet,1) if profile=='gm_immutable'
                    else c.identity(packet,1,decode=False))
            started=time.perf_counter_ns()
            ok=enc.ack(i,epoch=1) if profile=='gm_immutable' else enc.ack(ack)
            feedback_ms=elapsed(started);assert ok
            record.update(packet_bytes=len(packet),packet_sha256=hashlib.sha256(packet).hexdigest(),
                          inner_packet_sha256=hashlib.sha256(packet if profile=='gm_immutable' else parsed['inner']).hexdigest(),
                          decoded_rgb_sha256=actual_hash,expected_rgb_sha256=expected,
                          key=bool(parsed['key']),reference_id=info['reference_id'],
                          reference_bank=None if profile=='gm_immutable' else info['reference_bank'],
                          reference_tag=None if profile=='gm_immutable' else parsed['reference_tag'].hex(),
                          destination_bank=None if profile=='gm_immutable' else parsed['destination_bank'],
                          stored_tag=None if profile=='gm_immutable' else parsed['stored_tag'].hex(),
                          promoted=False if profile=='gm_immutable' else info['promoted'],
                          receive_ms=receive_ms,feedback_ms=feedback_ms,
                          complete_service_ms=prepare_ms+receive_ms+feedback_ms,
                          metrics=quality.metric(source,actual,RECTS,tuple(manifest['active_rects'][i]),False),
                          receiver_info=info,pending_after_feedback=len(enc.pending),
                          feedback_sha256=None if ack is None else hashlib.sha256(ack).hexdigest())
            if profile!='gm_immutable':
                for slot in (0,1):
                    a,b=enc.banks[slot],rx.banks[slot]
                    assert (a is None)==(b is None)
                    if a is not None:
                        assert a.frame_id==b.frame_id and a.tag==b.tag
                        for ea,ra in zip(a.planes,b.planes):np.testing.assert_array_equal(ea,ra)
                record['acknowledged_banks']={str(slot):None if bank is None else
                    dict(frame_id=bank.frame_id,tag=bank.tag.hex()) for slot,bank in enc.banks.items()}
                record['same_reconstructed_banks']=True
            rows[profile].append(record);this[profile]=record
        if not ar_only:
            a,b=this['gm_immutable'],this['ar_immutable']
            if a['accepted'] and b['accepted']:
                assert a['packet_sha256']==b['inner_packet_sha256']
                assert a['decoded_rgb_sha256']==b['decoded_rgb_sha256']
                comparisons.append(dict(id=i,gm_inner_equal=True,immutable_pixels_equal=True,
                                        envelope_bytes=b['packet_bytes']-a['packet_bytes']))
    summary={}
    for profile,records in rows.items():
        admitted=[r for r in records if r['accepted']]
        regions={}
        for region in ('active','roi','background'):
            count=sum(r['metrics'][region]['pixels'] for r in admitted)
            mse=sum(r['metrics'][region]['pixels']*r['metrics'][region]['mse'] for r in admitted)/count if count else None
            regions[region]=dict(pixels=count,mse=mse,psnr=None if not mse else float(10*np.log10(65025/mse)))
        enc,rx=pairs[profile]
        summary[profile]=dict(attempts=len(records),admitted=len(admitted),rejected=len(records)-len(admitted),
            packet_bytes=stats([r['packet_bytes'] for r in admitted]),prepare_ms_all=stats([r['prepare_ms'] for r in records]),
            receive_ms=stats([r['receive_ms'] for r in admitted]),feedback_ms=stats([r['feedback_ms'] for r in admitted]),
            complete_service_ms=stats([r['complete_service_ms'] for r in admitted]),
            rejected_prepare_ms=sum(r['prepare_ms'] for r in records if not r['accepted']),
            promotions=sum(r.get('promoted',False) for r in records),regions=regions)
        if profile!='gm_immutable':
            summary[profile]['memory']=dict(encoder_reference_read_yuv8_bytes=enc.reference_read_bytes,
                encoder_reconstruction_write_yuv8_bytes=enc.reconstruction_write_bytes,
                encoder_reference_read_array_bytes=enc.reference_read_array_bytes,
                encoder_reconstruction_write_array_bytes=enc.reconstruction_write_array_bytes,
                encoder_tag_read_bytes=enc.tag_read_bytes,
                receiver_reference_read_yuv8_bytes=rx.reference_read_bytes,
                receiver_reconstruction_write_yuv8_bytes=rx.reconstruction_write_bytes,
                receiver_reference_read_array_bytes=rx.reference_read_array_bytes,
                receiver_reconstruction_write_array_bytes=rx.reconstruction_write_array_bytes,
                receiver_tag_read_bytes=rx.tag_read_bytes,
                encoder_peak_retained_banks=enc.peak_retained_banks,receiver_peak_retained_banks=rx.peak_retained_banks,
                encoder_peak_retained_array_bytes=enc.peak_retained_array_bytes,
                receiver_peak_retained_array_bytes=rx.peak_retained_array_bytes)
    print(name,json.dumps({p:dict(bytes=s['packet_bytes']['mean'],prep=s['prepare_ms_all']['mean'],
        receive=s['receive_ms']['mean'],promotions=s['promotions'],rejected=s['rejected']) for p,s in summary.items()}),flush=True)
    return dict(source=name,cohort=cohort,manifest=manifest,key_period=30,promotion_period=8,
                profiles=rows,comparisons=comparisons,summary=summary)


def main():
    pins={str(p):digest(p) for p in dependencies()};scenes=[];started=time.perf_counter()
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    for clip,n,start,cohort in (('mass-effect-combat',60,1,'native_temporal'),
                              ('mass-effect-2600',60,1,'native_temporal'),
                              ('mass-effect-2600',180,4,'heldout_long')):
        frames,manifest=corpus.load_video(media/(clip+'.mp4'),max_frames=n,start_seconds=start)
        assert len(frames)==n
        scenes.append(run_scene(f'{clip}-{cohort}',frames,manifest,cohort))
    rng=np.random.default_rng(1401)
    frames=[rng.integers(0,256,(480,720,3),dtype=np.uint8) if 4<=i<8 else
            np.full((480,720,3),60+i,np.uint8) for i in range(12)]
    manifest=dict(source='synthetic:seed1401-noise4to7',synthetic=True,frame_count=12,
                  frame_sha256=[array_digest(f) for f in frames],active_rects=[(0,0,720,480)]*12)
    scenes.append(run_scene('synthetic-noise-recovery',frames,manifest,'synthetic',ar_only=True))
    assert pins=={str(p):digest(p) for p in dependencies()}
    result=dict(evidence='AR01 two-bank explicit acknowledged P promotion; actual bytes/reconstructions and feedback, not native timing',
        source_sha256=pins,scenes=scenes,versions=dict(python=platform.python_version(),numpy=np.__version__,pillow=PIL.__version__,pyav=av.__version__),
        attempted_packets=sum(len(rows) for s in scenes for rows in s['profiles'].values()),
        decoded_packets=sum(r['accepted'] for s in scenes for rows in s['profiles'].values() for r in rows),
        native_source_ids=300,total_python_wall_seconds=time.perf_counter()-started,
        timing_scope='Fullprepareincludingtag,reconstructionofkeys/promotions,andcaprejects;fullreceive/feedbackconstruction;senderAF01parse/publication separatelytimed. Mapbuild,capture/resize,oraclehash,qualityandtestbankcomparisonsoutside. RotateprofileorderperID;hostloaduncontrolled.',
        reference_scope='Bank0immutableACKedkey;bank1promotionsdrainallpendingandleasesandblocknewprepuntilmatchingAF01orphysicallydrainedexpiry. Lostpromotionfeedbackdisablesbank1;onlyconfirmedreferencesselectable. No UI/RGBpredictor.',
        memory_scope='CountersareexplicitlogicalYUV8payloadandone-passint16arrayamounts,notmeasuredtraffic. Canonicaltagreadincludes4dimensionbytes+int16planes. Two retainedbanks;pendingpromotionoutput/source/prediction/coefficients/RGB/scratch/hashcopiesareextra,nominalbankbytesnotpeakmemory.',
        deployment_scope='NewAR01/AF01dialectnotGM01compatibleorinstalled. Immediatefeedbackalgorithmcomparison,nofinitetransportcadence,RF/QSPI/physicalmemory/targetdecoder/hardware30fpsproof. Native25/29.88fpsprecompressedfootage,720x480coded720x405active;noinventednative30capture.')
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
