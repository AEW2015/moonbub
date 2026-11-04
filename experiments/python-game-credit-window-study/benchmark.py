#!/usr/bin/env python3
"""Measured-wall credit sensitivity with all three exact execution optimizations."""
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
import adapter
import model

HERE=Path(__file__).resolve().parent
check_spec=importlib.util.spec_from_file_location('credit_evidence_check',HERE/'verify.py')
verify=importlib.util.module_from_spec(check_spec);check_spec.loader.exec_module(verify)
spec=importlib.util.spec_from_file_location('credit_native_inputs',HERE.parent/'python-game-service-study/benchmark.py')
source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dependencies():
    import cache_admission
    paths=[HERE/name for name in ('model.py','adapter.py','benchmark.py','test_credit_window.py','verify.py','copy-origin.json')]
    paths += [Path(source.__file__),Path(cache_admission.__file__),Path(adapter.ui_cache.__file__),
        Path(adapter.fast_codec.__file__),Path(model.gc.__file__),Path(model.normal_controller.__file__),
        Path(model.cheap_gate.__file__),Path(model.cheap_gate.exact.__file__),Path(model.transport.__file__),
        Path(model.corpus.__file__),Path(model.gc.roi.__file__),Path(model.gc.mt.__file__),Path(model.gc.ft.__file__),
        Path(model.gc.token_coeff.__file__),Path(model.gc.word_coeff.__file__),Path(model.gc.word_coeff.frozen_codec.__file__),
        Path(adapter.hybrid.__file__),Path(adapter.hybrid.row.__file__),Path(adapter.hybrid.hp.__file__),
        HERE.parent/'python-coupled-study/validation.py',HERE.parent/'python-game-execution-study/model.py']
    return sorted(set(paths))


def run_case(frames,manifest,name,window,refresh=30):
    config=model.Config(width=720,height=480,fps=30,controller='normal',
        decoder_service='python_wall',transport_cpu=True,resize_cpu=True,
        refresh_period=refresh,sender_slots=window,credit_window=window)
    r=model.run(frames,manifest,config,
        controller_factory=adapter.make_controller(credit_window=window),
        receiver_factory=lambda:adapter.DecoderState(frame_cap=config.frame_cap,fast=True),
        service_tape=None)
    source.check_drained(r)
    case=dict(source=name,credit_window=window,refresh_period=refresh,manifest=manifest,result=r)
    verify.check_case(case)
    return case


def brief(c):
    r=c['result'];packets=r['packets']
    patches=[a for p in packets for a in p.get('hybrid',{}).get('attempts',[])]
    details=[a['candidate_details'] for a in patches]
    return dict(source=c['source'],credit_window=c['credit_window'],refresh_period=c['refresh_period'],
        captures=r['capture_count'],prepared=r['prepared'],strict=r['presented_strict'],eventual=r['presented_eventual'],
        diagnostic_ids_per_second=r['metrics']['steady_fps'],diagnostic_window_ms=r['steady_window_ms'],
        max_presented_age_ms=max(p['age_ms'] for p in r['presented']) if r['presented'] else None,
        p_credit_wait_ms=r['encoder_admission_wait_ms'].get('p_credit_limit',0.),
        encoder_wait_ms=r['encoder_admission_wait_ms'].get('encoder_busy',0.),
        refresh_wait_ms=r['encoder_admission_wait_ms'].get('refresh_drain',0.),
        peak_sender=r['peak_sender_slots'],peak_credits=r['peak_credits'],peak_ingress=r['peak_ingress_slots'],
        peak_framebuffer_roles=r['peak_framebuffer_roles'],
        base_cache_hits=sum(bool(a.get('cache_hit')) for p in packets for a in p['attempts']),
        patch_attempts=len(patches),patch_cache_hits=sum(x['cache_hit'] for x in details),
        ui_cache_entries_max=max((x['cache_entries'] for x in details),default=0),
        ui_cache_persistent_bytes_max=max((x['persistent_cache_bytes'] for x in details),default=0),
        selected_rgb565_mismatches=sum(c['selected_rgb565_mismatches'] for c in r['commits']),
        decoded_active_rgb565_mse_mean=float(np.mean([c['active_rgb565_mse'] for c in r['commits']])) if r['commits'] else None,
        decoded_active_rgb565_mse_p95=float(np.percentile([c['active_rgb565_mse'] for c in r['commits']],95)) if r['commits'] else None,
        full_ingress_rejections=sum(p.get('ingress_error')=='GF02 busy' for p in packets),
        encode_wall_ms=sum(p['encode_wall_ms'] for p in packets),
        decode_wall_ms=sum(p.get('decode_wall_ms',0) for p in packets),drops=r['drops_by_reason'])


def compare(a,b):
    aa={p['id']:p for p in a['result']['packets']};bb={p['id']:p for p in b['result']['packets']}
    common=sorted(aa.keys()&bb.keys())
    same_anchor=[i for i in common if aa[i]['acked_anchor_at_prepare']==bb[i]['acked_anchor_at_prepare']
                 and aa[i]['force_key']==bb[i]['force_key']]
    same_packet=[i for i in common if aa[i].get('packet_sha256') is not None
                 and aa[i].get('packet_sha256')==bb[i].get('packet_sha256')]
    ca={c['id']:c for c in a['result']['commits']};cb={c['id']:c for c in b['result']['commits']}
    decoded=sorted(ca.keys()&cb.keys())
    return dict(source=a['source'],a_window=a['credit_window'],b_window=b['credit_window'],
        a_refresh=a['refresh_period'],b_refresh=b['refresh_period'],common_prepared_ids=common,
        same_anchor_and_forced_key_ids=same_anchor,same_packet_ids=same_packet,common_decoded_ids=decoded,
        common_decoded_active_mse_delta_mean=float(np.mean([cb[i]['active_rgb565_mse']-ca[i]['active_rgb565_mse'] for i in decoded])) if decoded else None,
        strict_delta=b['result']['presented_strict']-a['result']['presented_strict'],
        eventual_delta=b['result']['presented_eventual']-a['result']['presented_eventual'],
        scope='Same inputs, separately observedwalltimes anddifferentcausaladmission/refhistories; quantizeridentitydoesnotimplyqualityidentity.')


def main():
    pins={str(p):sha(p) for p in dependencies()};cases=[];start=time.perf_counter()
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    for index,clip in enumerate(('mass-effect-combat','mass-effect-2600')):
        frames,manifest=source.native(media/(clip+'.mp4'),n=60,start=1)
        for window in ((2,3) if index==0 else (3,2)):
            case=run_case(frames,manifest,clip,window);cases.append(case);print(json.dumps(brief(case)),flush=True)
    frames,manifest=source.native(media/'mass-effect-2600.mp4',n=180,start=4)
    assert len(frames)==180
    for window,refresh in ((2,30),(3,30),(3,0)):
        case=run_case(frames,manifest,'mass-effect-2600-heldout180',window,refresh)
        cases.append(case);print(json.dumps(brief(case)),flush=True)
    assert pins=={str(p):sha(p) for p in dependencies()},'executed code changed during benchmark'
    pairs=[]
    for name in ('mass-effect-combat','mass-effect-2600','mass-effect-2600-heldout180'):
        group=[c for c in cases if c['source']==name and c['refresh_period']==30]
        pairs.append(compare(next(c for c in group if c['credit_window']==2),next(c for c in group if c['credit_window']==3)))
    pairs.append(compare(cases[-2],cases[-1]))
    result=dict(evidence='Seven actual-wall720x480@30 credit/refresh software scenarios; all3 exact execution optimizations enabled',
        source_sha256=pins,case_count=len(cases),cases=cases,summary=[brief(c) for c in cases],pairs=pairs,
        total_python_wall_seconds=time.perf_counter()-start,
        versions=dict(python=platform.python_version(),numpy=np.__version__,pillow=PIL.__version__,pyav=av.__version__),
        policy_scope='Main paired2/3PCsender+Pcredit windows; sameACKed-key/sourcepayloadcache,exactUIcache,fastpixel-exactdecoder. Third180-IDwindow3initialonly is separately labeled6sprobe,not adefaultrefreshqualification.',
        cost_scope='Everyactualprepare/reject,decode,BOXresize,transportfeed/failure/feedbackcostpaiditsobservedPythonwall; nofixedtape or assumeddecode. Independent virtualservers are not a sharedCPU hardwareexecution proof.',
        memory_scope='OnlyPCsender/credit logicalboundschange2to3. Receiveringressfixed2x49152 andframebufferroles3. Oneextra49152-byte logicalsendercapacity,pluspendingGM/outerpacket/caches/arrays/queues/objectoverheadextra. This doesnotraise targetRAM/physicalmemoryfitproof.',
        comparison_scope='Same source/hash/policy,remeasuredhostwallcosts canchangehistories; countsarerun-specific andnotisolatedstatisticalpolicy effects. All3optimizationsmeanthisisnotnumericallycomparableaswindow-onlydifferenceagainstparentexecutionstudywithoutUIcache.',
        source_scope='Offline native25/29.88fpsprecompressedrelatedclips,notlive30distinctcapture;720x405BOXcontentwithin720x480canvas;2x60IDsfrom1splus180IDsfrom4s.',
        timing_scope='Forward/reverse8Mb/s,QSPI160Mb/s,10msfeedback,60Hzvblank,150msdecodeage+nextvblank assumed; nosockets/ESP32/DMA/CDC/scanout or hardware30fpsproof.',
        full_ingress_scope='ActualGF02busy failuresarechargedfeedcalls,generateNACK/drain,notdiscardedfree. Separatepassingregressionsforce3senders/twoingressbusy,lateACKduringparse,loss/corruptionandreadpinrecovery.')
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
