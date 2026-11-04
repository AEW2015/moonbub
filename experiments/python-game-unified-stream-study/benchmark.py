#!/usr/bin/env python3
"""Measured-host AR02 codec choice, exact UI and acknowledged references."""
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
spec=importlib.util.spec_from_file_location('unified_native_inputs',HERE.parent/'python-game-service-study/benchmark.py')
source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dependencies():
    rc=model.rc;gm=rc.gm
    import ui_plugin
    paths=[HERE/name for name in ('model.py','benchmark.py','test_model.py','verify.py')]
    paths += [Path(source.__file__),Path(rc.__file__),Path(rc.old.__file__),Path(rc.overlap_codec.__file__),
              Path(rc.sr.__file__),Path(rc.fast_codec.__file__),Path(gm.__file__),Path(gm.roi.__file__),
              Path(gm.mt.__file__),Path(gm.ft.__file__),Path(gm.token_coeff.__file__),Path(gm.word_coeff.__file__),
              Path(gm.word_coeff.frozen_codec.__file__),Path(model.transport.__file__),Path(model.corpus.__file__),
              Path(ui_plugin.__file__),Path(ui_plugin.frozen_cache.__file__),Path(ui_plugin.hybrid.__file__),
              Path(ui_plugin.row.__file__),Path(ui_plugin.hp.__file__),
              HERE.parent/'python-game-overlap-reference-study/model.py']
    return sorted(set(paths))


def brief(case):
    r=case['result'];packets=r['packets'];commits=r['commits']
    sizes=[p['bytes'] for p in packets if p['admitted']]
    return dict(source=case['source'],profile=case['profile'],mode=case['mode'],exact_ui=case['exact_ui'],
                captures=r['capture_count'],prepared=r['prepared'],decoded=len(commits),
                strict=r['presented_strict'],eventual=r['presented_eventual'],
                diagnostic_ids_per_second=r['diagnostic_ids_per_second'],
                accepted_promotions=sum(p['admitted'] and p['promoted'] for p in packets),
                inner_formats={name:sum(p['admitted'] and p['info']['inner_codec']==name for p in packets) for name in ('GM01','SR01')},
                actual_inner_candidates=sum(len(p['info']['inner_attempts']) for p in packets),
                forward_transform_calls=sum(p['info']['forward_calls'] for p in packets),
                selected_exact_pixels_total=sum(c['selected_exact_pixels'] for c in commits),
                selected_ui_mismatches=sum(c['selected_ui_mismatches'] for c in commits),
                selected_pixels_per_decoded=None if not commits else sum(c['selected_exact_pixels'] for c in commits)/len(commits),
                mean_frame_bytes=None if not sizes else float(np.mean(sizes)),
                encode_service_ms=sum(p['encode_service_ms'] for p in packets),
                decode_service_ms=sum(w['service_ms'] for w in r['work'] if w['stage'].startswith('decode_')),
                forward_ipv4_udp_bytes=r['forward_ipv4_udp_bytes'],reverse_ipv4_udp_bytes=r['reverse_ipv4_udp_bytes'],
                active_rgb565_mse_mean=None if not commits else float(np.mean([c['active_rgb565_mse'] for c in commits])),
                max_presented_age_ms=max((p['age_ms'] for p in r['presented']),default=None),
                admission_wait_ms=r['admission_wait_ms'],drops=r['drops_by_reason'])


def run_case(frames,manifest,label,profile,mode,ui,refresh=0,**faults):
    cfg=model.Config(codec_mode=mode,exact_ui=ui,refresh_period=refresh,**faults)
    result=model.run(frames,manifest,cfg)
    assert not result['unresolved_ids'] and all(x is None for x in result['unresolved_sender_slots'])
    assert not result['unresolved_encoder_pending'] and not result['unresolved_ingress']
    assert not result['unresolved_receiver_readers'] and not result['unresolved_decode']
    return dict(source=label,profile=profile,mode=mode,exact_ui=ui,manifest=manifest,result=result)


def pair(a,b):
    aa={p['id']:p for p in a['result']['packets']};bb={p['id']:p for p in b['result']['packets']}
    ca={p['id']:p for p in a['result']['commits']};cb={p['id']:p for p in b['result']['commits']}
    common=sorted(aa.keys()&bb.keys());delivered=sorted(ca.keys()&cb.keys())
    same_choice=[i for i in common if all(aa[i][k]==bb[i][k] for k in ('key','promoted','reference_bank','reference_id','reference_tag'))]
    return dict(source=a['source'],left_profile=a['profile'],right_profile=b['profile'],
                common_admitted_ids=[i for i in common if aa[i]['admitted'] and bb[i]['admitted']],
                common_decoded_ids=delivered,same_reference_and_promotion_ids=same_choice,
                mean_common_decoded_mse_delta=None if not delivered else float(np.mean([cb[i]['active_rgb565_mse']-ca[i]['active_rgb565_mse'] for i in delivered])),
                strict_delta=b['result']['presented_strict']-a['result']['presented_strict'],
                eventual_delta=b['result']['presented_eventual']-a['result']['presented_eventual'],
                caveat='Same input hashes, remeasured costs and possibly different admission/ref histories. UI coverage and quality must be compared before interpreting byte deltas.')


def main():
    paths=dependencies();pins={str(p):sha(p) for p in paths};cases=[];pairs=[];started=time.perf_counter()
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    profiles=[('gm_base','gm',False),('exact_base','exact',False),('gm_ui','gm',True),('exact_ui','exact',True)]
    for index,clip in enumerate(('mass-effect-combat','mass-effect-2600')):
        frames,manifest=source.native(media/(clip+'.mp4'),n=60,start=1);local={}
        for name,mode,ui in (profiles if index==0 else list(reversed(profiles))):
            c=run_case(frames,manifest,clip,name,mode,ui);cases.append(c);local[name]=c
            print(json.dumps(brief(c)),flush=True)
        pairs += [pair(local['gm_base'],local['exact_base']),pair(local['gm_ui'],local['exact_ui'])]
    frames,manifest=source.native(media/'mass-effect-2600.mp4',n=180,start=4)
    assert len(frames)==180;long={}
    for name,mode,refresh in [('gm_ui','gm',0),('exact_ui','exact',0),('prune4_ui','prune4',0),('exact_ui_refresh30','exact',30)]:
        c=run_case(frames,manifest,'mass-effect-2600-heldout180',name,mode,True,refresh=refresh)
        cases.append(c);long[name]=c;print(json.dumps(brief(c)),flush=True)
    pairs += [pair(long['gm_ui'],long['exact_ui']),pair(long['exact_ui'],long['prune4_ui']),pair(long['exact_ui'],long['exact_ui_refresh30'])]
    yy,xx=np.indices((480,720));images=[]
    for i in range(24):
        rgb=np.stack(((xx//8+i)%180+20,(yy//8+i)%140+20,np.full_like(xx,70+i)),axis=-1).astype(np.uint8)
        for x,y,w,h in model.Config().ui_rectangles:rgb[y:y+h,x:x+w]=[30,70,110]
        images.append(rgb)
    manifest=dict(source='synthetic:unified-fault-gradient-static-ui24',synthetic=True,frame_count=len(images),
                  frame_sha256=[model.digest(f) for f in images],input_scope='Synthetic full720x480+staticconfiguredUI;notnative capture')
    for name,faults in [('promotion_ack_loss',dict(drop_first_promotion_ack=True)),
                        ('conflicting_promotion_feedback',dict(conflict_first_promotion_feedback=True))]:
        c=run_case(images,manifest,'synthetic-fault24',name,'exact',True,promotion_period=8,**faults)
        cases.append(c);print(json.dumps(brief(c)),flush=True)
    assert pins=={str(p):sha(p) for p in paths},'executed sources changed'
    result=dict(evidence='One AR02/AF02 stream combines GM/SR selection,acknowledgedrefs andexactUI;measured-host finite model only',
                source_sha256=pins,cases=cases,case_count=len(cases),summary=[brief(c) for c in cases],pairs=pairs,
                total_python_wall_seconds=time.perf_counter()-started,
                versions=dict(python=platform.python_version(),numpy=np.__version__,pillow=PIL.__version__,pyav=av.__version__),
                protocol_scope='Complete AR02 frame cap49152includesinnerGM/SR andlength-prefixedHP/HRpatches;AF02bindsouterCRC+decodedYUVpublicationtag.UIaffectsdisplayonly.',
                timing_scope='ActualBOX/map/prepare/reject/GM+SRlosers/UIcache+validation/packetize/feed/decodebegin+complete+abort/AFparse+apply/expirecostpaid.No fixedtape. Independentserializedvirtualservers notnative/sharedCPUexecution.',
                transport_scope='GF02frame-batchedwire/feedwithassumed8Mb/sforward/reverse,160Mb/sQSPI,10msfeedback,60Hzvblank.Norealsockets/RF/QSPIframing/SDRAM/CDC/scanout.',
                source_scope='Allcodedcanvases720x480;nativeactive720x405. Precompressed25/29.88fpsfiles extractedoffline,thenhypotheticallyscheduled30IDs/s;actualBOXpaid,desktopacquisitionunmeasured.',
                quality_scope='Exactmode preservesGMcoefficients givenSAMEprediction/map;changinghistoriesmaychangequality.Prune4localYUVboundagainstquantizedGMgivenitsownpredictor,notlosslessororiginal-sourceglobalbound.SelectedUIwordsareexactoriginalRGB565.',
                comparison_scope='CommonIDsetsandreferencechoicesretained;notadditivepriorgains,notbase-onlyversusUIFPSattribution.UIcoveragecanchangeifsmallerbaseadmitsmorepatches;comparecoveragebeforebytes.',
                memory_scope='2retainedYUVbanks/peer,3hosttransactions,2actualGFingress,4feedbackdescriptors,3displayrolespluscodecsource/scratch/output/UIcacheandcopiesextra.Notpeakmemory/hardwarefit.',
                publication_scope='SemanticACK/decoderpublicationstageduntilpaidcompletion;expiry/deadlinewins,readpinsretained. Workcountersnotrefunded.Single-threadedoraclemodel,notnativeconcurrencyAPI.')
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
