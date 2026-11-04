#!/usr/bin/env python3
"""Fixed coefficient gate: measured-host AR02 exact UI and acknowledged references."""
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
    paths=[HERE/name for name in ('model.py','cadence_codec.py','benchmark.py','test_model.py','test_gate.py','test_benchmark.py','verify.py','gate-config.json','copy-origin.json')]
    paths += [Path(source.__file__),Path(rc.__file__),Path(rc.frozen.__file__),Path(rc.old.__file__),Path(rc.overlap_codec.__file__),
              Path(rc.sr.__file__),Path(rc.fast_codec.__file__),Path(gm.__file__),Path(gm.roi.__file__),
              Path(gm.mt.__file__),Path(gm.ft.__file__),Path(gm.token_coeff.__file__),Path(gm.word_coeff.__file__),
              Path(gm.word_coeff.frozen_codec.__file__),Path(model.transport.__file__),Path(model.corpus.__file__),
              Path(ui_plugin.__file__),Path(ui_plugin.frozen_cache.__file__),Path(ui_plugin.hybrid.__file__),
              Path(ui_plugin.row.__file__),Path(ui_plugin.hp.__file__),
              HERE.parent/'python-game-overlap-reference-study/model.py',
              HERE.parent/'python-game-unified-stream-study/model.py',
              HERE.parent/'python-game-unified-stream-study/results.json']
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
                gate_evaluations=sum(p['info']['gate']['evaluated'] for p in packets),
                gate_eligible=sum(p['info']['gate']['evaluated'] and p['info']['gate']['allow_sr'] for p in packets),
                gate_service_ms=sum(p['info']['gate_ms'] for p in packets),
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



def exact_pair(a,b):
    out=pair(a,b)
    aa={p['id']:p for p in a['result']['packets'] if p['admitted']}
    bb={p['id']:p for p in b['result']['packets'] if p['admitted']}
    matched=[i for i in sorted(aa.keys()&bb.keys()) if all(aa[i][k]==bb[i][k] for k in ('key','promoted','reference_bank','reference_id','reference_tag'))]
    ca={c['id']:c for c in a['result']['commits']};cb={c['id']:c for c in b['result']['commits']}
    decoded=[i for i in matched if i in ca and i in cb]
    assert all(ca[i]['base_rgb_sha256']==cb[i]['base_rgb_sha256'] for i in decoded)
    out['matched_reference_ids']=matched
    out['matched_reference_base_exact_ids']=decoded
    out['matched_reference_base_mismatches']=0
    same_ui=[i for i in matched if i in ca and i in cb and ca[i]['info']['patches']==cb[i]['info']['patches']]
    assert all(ca[i]['rgb_sha256']==cb[i]['rgb_sha256'] for i in same_ui)
    out['matched_reference_same_ui_exact_display_ids']=same_ui
    out['warning']='Minimum only among actually serialized candidates; skipped SR lengths are unknown. Finite timing may change admission and reference history; compare common IDs with the same reference/promotion. No cross-profile byte-only quality claim.'
    return out


def main():
    gate_config=json.loads((HERE/'gate-config.json').read_text())
    assert gate_config['threshold']==0.90 and gate_config['sample_blocks_per_plane']==64
    paths=dependencies();pins={str(p):sha(p) for p in paths};cases=[];pairs=[];started=time.perf_counter()
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    prior=json.loads((HERE.parent/'python-game-unified-stream-study/results.json').read_text())
    prior_case=next(c for c in prior['cases'] if c['source']=='mass-effect-2600-heldout180')
    prior_manifest=prior_case['manifest']
    profiles=[('gm_ui','gm'),('exact_ui','exact'),('gated_ui','gated')]
    for index,clip in enumerate(('mass-effect-combat','mass-effect-2600')):
        frames,manifest=source.native(media/(clip+'.mp4'),n=60,start=1)
        assert len(frames)==60
        local={}
        for name,mode in (profiles if index==0 else list(reversed(profiles))):
            c=run_case(frames,manifest,clip,name,mode,True);cases.append(c);local[name]=c
            print(json.dumps(brief(c)),flush=True)
        pairs += [exact_pair(local['gm_ui'],local['exact_ui']),exact_pair(local['gm_ui'],local['gated_ui']),exact_pair(local['exact_ui'],local['gated_ui'])]
    frames,manifest=source.native(media/'mass-effect-2600.mp4',n=60,start=10.04)
    assert len(frames)==60, 'No padding/repetition allowed'
    assert manifest['source_sha256']==prior_manifest['source_sha256']
    assert len(set(manifest['selected_pts']))==60
    assert not set(manifest['selected_pts'])&set(prior_manifest['selected_pts'])
    assert min(manifest['selected_pts'])>max(prior_manifest['selected_pts'])==119600
    scope=dict(prior_source_sha256=prior_manifest['source_sha256'],new_source_sha256=manifest['source_sha256'],
               prior_selected_pts=prior_manifest['selected_pts'],new_selected_pts=manifest['selected_pts'],
               prior_last_time_seconds=max(prior_manifest['selected_times_seconds']),
               new_selected_times_seconds=manifest['selected_times_seconds'],
               new_window_start_seconds=10.04,native_frames=60,
               split_correction='start10.0 overlapped prior final PTS119600; corrected to10.04 before timing; fixed0.90 gate not retuned',
               source_scoped_identities_disjoint=True,
               new_unique_frame_hashes=manifest['unique_frame_count'],
               new_repeated_hash_count=len(manifest['frame_sha256'])-len(set(manifest['frame_sha256'])),
               shared_prior_new_hash_count=len(set(manifest['frame_sha256'])&set(prior_manifest['frame_sha256'])),
               meaning='New temporal window only; same video title/precompressed file, not a new title or physical capture')
    local={}
    for name,mode in (profiles[1],profiles[2],profiles[0]):
        c=run_case(frames,manifest,'mass-effect-2600-new60-10.04s',name,mode,True)
        cases.append(c);local[name]=c;print(json.dumps(brief(c)),flush=True)
    pairs += [exact_pair(local['gm_ui'],local['exact_ui']),exact_pair(local['gm_ui'],local['gated_ui']),exact_pair(local['exact_ui'],local['gated_ui'])]
    assert pins=={str(p):sha(p) for p in paths},'executed sources changed'
    result=dict(evidence='Fixed sparse coefficient gate for exact SR work; measured-host finite Python model only',
                source_sha256=pins,gate_config=gate_config,validation_scope=scope,
                cases=cases,case_count=len(cases),summary=[brief(c) for c in cases],pairs=pairs,
                total_python_wall_seconds=time.perf_counter()-started,
                versions=dict(python=platform.python_version(),numpy=np.__version__,pillow=PIL.__version__,pyav=av.__version__),
                gate_scope='After one GM quantization, at most64 current evenly spaced coefficient blocks per plane; all3 AC-allzero fractions>=0.90 enables real exactSR encode; otherwise GM only. No future/uncodedSR length oracle; no prune; minimum among EVALUATED complete inner payloads only.',
                timing_scope='Actual BOX/map/GM/gate/eligibleSR losers/UI/fullvalidation/packetize/feed/decoder/ACK expiry work paid. Oracle hashes and metrics excluded. Independent serialized virtual servers, not native concurrency or target timing.',
                transport_scope='Inherited GF02 frame batch model: assumed8Mb/s forward/reverse,160Mb/sQSPI,10msfeedback,60Hzvblank; no sockets/RF/QSPIframing/SDRAM/CDC/scanout.',
                source_scope='Native files25/29.88fps extracted offline;720x480 coded canvas,720x405 active, hypothetically scheduled30IDs/s. No padding or source FPS uplift claim.',
                quality_scope='GM/exact/gated same coefficients given SAME reference/map; selectedUI exact originalRGB565. History may diverge under measured costs; paired comparisons report common reference/promotion IDs.',
                memory_scope='Inherited staged twoYUVbanks/peer,threehosttransactions,twoGFingress,fourfeedbackdescriptors,three displayroles; temporary arrays/cache/scratch extra; not hardwarefit/peakmemory.',
                limits='One fixed screen and one new60frame temporal window; host microbenchmark variation; all-off/no gain is a valid negative result. Not a hardware30fps proof.')
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
