#!/usr/bin/env python3
"""Actual AR03 candidate/admission/commit and GF03 credit transport campaign."""
import hashlib,importlib.util,json,os,platform,time
from pathlib import Path
import numpy as np,PIL,av
import model
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('joint_native_input',HERE.parent/'python-game-service-study/benchmark.py');source=importlib.util.module_from_spec(s);s.loader.exec_module(source)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dependencies():
    frozen=json.loads((HERE.parent/'python-game-candidate-commit-study/results.json').read_text())['source_sha256']
    names={ROOT/raw.split('/moonbub-30fps-study/',1)[-1] for raw in frozen}
    names|={HERE/n for n in ('model.py','gateway.py','framing.py','benchmark.py','verify.py','test_model.py')}
    names|={Path(source.__file__),Path(model.gateway.frozen.__file__),HERE.parent/'python-game-local-refresh-study/model.py'}
    return sorted(names)
def brief(c):
    r=c['result'];p=r['packets'];g=r['gateway'];commits=r['commits'];decoded={x['id']:x for x in commits};w=r['steady_window_ms']
    ids=[] if w is None else [x['id'] for x in r['presented'] if w[0]<=x['at_ms']<w[1]]
    return dict(profile=c['profile'],captures=r['capture_count'],built=len(p),committed=sum(x['committed'] for x in p),
        precommit_rejected=sum(not x['committed'] for x in p),decoded=len(commits),strict=r['presented_strict'],eventual=r['presented_eventual'],
        diagnostic_ids_per_second=r['diagnostic_ids_per_second'],distinct_steady_input_hashes=len({c['manifest']['frame_sha256'][i] for i in ids}),
        distinct_steady_decoded_hashes=len({decoded[i]['rgb_sha256'] for i in ids}),
        actual_data_datagrams=sum(not w['control'] for w in g['wire']),actual_queries=sum(w['control'] for w in g['wire']),
        credits_applied=g['counters'].get('credits_applied',0),maximum_mailbox=g['peak_mailbox'],maximum_tokens=g['peak_tokens'],
        word_errors=sum(x['selected_ui_mismatches'] for x in commits),selected_words=sum(x['selected_exact_pixels'] for x in commits),
        forward_ipv4_udp_bytes=r['forward_ipv4_udp_bytes'],reverse_ipv4_udp_bytes=r['reverse_ipv4_udp_bytes'],
        paid_build_ms=sum(w['service_ms'] for w in r['work'] if w['stage']=='candidate_build'),
        paid_rejected_build_ms=sum(w['service_ms'] for w in r['work'] if w['stage']=='candidate_build' and not next(x for x in p if x['id']==w['id'])['committed']),
        maximum_presented_age_ms=max((x['age_ms'] for x in r['presented']),default=None),drops=r['drops_by_reason'])
def main():
    paths=dependencies();pins={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    frames,manifest=source.native(media/'mass-effect-2600.mp4',n=90,start=4);assert manifest['unique_frame_count']==90
    cases=[];start=time.perf_counter()
    profiles=[('unbudgeted',dict(admission_enabled=False)),('admit200',{}),
              ('admit150_batch8',dict(admission_age_ms=150,aggregate_ms=8)),
              ('admit200_link4',dict(link_mbps=4)),
              ('lost_credit_query',dict(lose_first_packet_credit=True,duplicate_packet_credit=True,aggregate_ms=2)),
              ('lost_refresh_AF',dict(drop_first_refresh_ack=True))]
    for label,changes in profiles:
        cfg=model.Config(codec_mode='gm',feedback_latency_ms=2,decode_age_ms=200,refresh_period=30,**changes)
        c=dict(source='native-regression',profile=label,manifest=manifest,result=model.run(frames,manifest,cfg));cases.append(c)
        print(json.dumps(brief(c)),flush=True)
    images=[np.full((16,32,3),40+i,np.uint8) for i in range(48)];manifest=dict(source='synthetic:flat48',synthetic=True,frame_count=48,frame_sha256=[model.digest(f) for f in images])
    for label,changes in [('forward_loss',dict(drop_packet_frame=8)),('corrupt_AF',dict(corrupt_af_frame=0))]:
        cfg=model.Config(width=32,height=16,codec_mode='gm',ui_rectangles=((0,0,16,8),),feedback_latency_ms=2,decode_age_ms=200,refresh_period=8,promotion_period=4,**changes)
        c=dict(source='synthetic-fault',profile=label,manifest=manifest,result=model.run(images,manifest,cfg));cases.append(c);print(json.dumps(brief(c)),flush=True)
    assert pins=={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
    out=dict(evidence='Actual AR03 candidate→causal admission→commit/discard→serialized GF03/PC18/QC18→reassembly→decode→AF03 publication in one finite controller',
        source_sha256=pins,cases=cases,case_count=len(cases),summary=[brief(c) for c in cases],python_wall_seconds=time.perf_counter()-start,
        versions=dict(python=platform.python_version(),numpy=np.__version__,pillow=PIL.__version__,pyav=av.__version__),
        wire_scope='ActualserializedGF03v3PAYLOAD1008plus16byteepoch/slot/reserved/seqprefix;1055byteUDPdatagrammaxwithin1065DMA. PC18consumedfeedback29bytes/QC18query28bytesincludesCRC. AF03separate43bytes. AllIP/UDP28bytespaid. NewendpointnotinstalledMSV1/GF02.',
        service_scope='ActualPythonBOX/build/commit/discard/wrap/ingress/decode/ACKparse/apply workpaid; ESP240MHz60%CPU+bitwiseCRC/copy/driver/QSPI assumptions, noISA/RFcalibration. GatewayforwardswholeGF03bytes including31byteheader toprospectivetrueFIFO endpoint; oldJPEGbegin/commitregisterprotocolnotused. Sharedreversevirtualwire forcreditsandAF, independentforward/reverse notphysicalWiFiairtime.',
        state_scope='Onlycommittedpacketsreachwire. Discardedbuildspaid,nopubidentityburn. Sourceleasesprotectcandidates. CommitwaitsforstagedACKmutation;RX/ACKpubvisibleonlyafterpaidcompletion,expirywins;GFrouteboundAR03identity;consumedcreditnotdecodedpub.',
        source_scope='Reused90native29.88fpsprecompressedframesat4s,offlinecaptureexcluded,BOXpaid,schedule30IDs/s. Nofreshcorpus/longrun/nativehardwareproof. 48flatfaultframesorderingonly.',
        excluded_scope='FPGAentropycycle/memory/scanline service notintegrated; decodedRGB isPythonreference. NoESPheap/BRAM/DSPfit or jointphysical30fpsqualification.')
    (HERE/'results.json').write_text(json.dumps(out,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
