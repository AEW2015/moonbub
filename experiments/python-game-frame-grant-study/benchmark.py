#!/usr/bin/env python3
"""Actual frame-slot protocol campaign; paired historical fixed service model."""
import hashlib,importlib.util,json,os,platform,time
from pathlib import Path
import numpy as np,PIL,av
import model,frame_credit
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('grant_native_input',HERE.parent/'python-game-service-study/benchmark.py');source=importlib.util.module_from_spec(s);s.loader.exec_module(source)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dependencies():
    frozen=json.loads((HERE.parent/'python-game-joint-admission-study/results.json').read_text())['source_sha256']
    names={ROOT/raw.split('/moonbub-30fps-study/',1)[-1] for raw in frozen}
    names|={HERE/n for n in ('model.py','gateway.py','frame_credit.py','framing.py','benchmark.py','verify.py','test_model.py','test_grants.py')}
    names|={Path(source.__file__),HERE.parent/'python-game-joint-admission-study/results.json'}
    return sorted(names)
def brief(c):
    r=c['result'];p=r['packets'];g=r['gateway'];f=r['frame_grants'];commits=r['commits'];decoded={x['id']:x for x in commits};window=r['steady_window_ms']
    ids=[] if window is None else [x['id'] for x in r['presented'] if window[0]<=x['at_ms']<window[1]]
    gaps=[b['at_ms']-a['at_ms'] for a,b in zip(r['presented'],r['presented'][1:])]
    busy=sum(p['feed_errors'].count('GF03 busy') for p in r['packets'])
    rejected={p['id'] for p in p if 'discard_service_ms' in p}
    return dict(profile=c['profile'],captures=r['capture_count'],built=len(p),committed=sum(x['committed'] for x in p),precommit_rejected=len(rejected),uncommitted_held=sum(not x['committed'] and x['id'] not in rejected for x in p),
        decoded=len(commits),strict=r['presented_strict'],eventual=r['presented_eventual'],diagnostic_ids_per_second=r['diagnostic_ids_per_second'],
        distinct_window_input_hashes=len({c['manifest']['frame_sha256'][i] for i in ids}),distinct_window_decoded_hashes=len({decoded[i]['rgb_sha256'] for i in ids}),
        maximum_gap_ms=max(gaps,default=None),maximum_presented_age_ms=max((x['age_ms'] for x in r['presented']),default=None),
        receiver_busy_feed_rejections=busy,receiver_nack_frames=r['drops_by_reason'].get('receiver_nack',0),
        data_datagrams=sum(not w['control'] for w in g['wire']),frame_control_datagrams=sum(w.get('frame_control',False) for w in g['wire']),
        frame_control_forward_bytes=sum(w['bytes'] for w in g['wire'] if w.get('frame_control')),
        frame_control_reverse_bytes=sum(w['bytes'] for w in r['feedback'] if w['kind']=='wire' and w['channel']=='frame'),
        packet_credit_queries=sum(w['control'] and not w.get('frame_control',False) for w in g['wire']),
        forward_ipv4_udp_bytes=r['forward_ipv4_udp_bytes'],reverse_ipv4_udp_bytes=r['reverse_ipv4_udp_bytes'],
        maximum_mailbox=g['peak_mailbox'],maximum_data_tokens=g['peak_tokens'],maximum_frame_owners=None if f is None else f['peak_receiver'],
        safe_stop=False if f is None else f['safe_stop'],safe_stop_reason=None if f is None else f['safe_stop_reason'],
        selected_words=sum(x['selected_exact_pixels'] for x in commits),word_errors=sum(x['selected_ui_mismatches'] for x in commits),
        paid_build_service_ms=sum(w['service_ms'] for w in r['work'] if w['stage']=='candidate_build'),
        paid_discarded_build_service_ms=sum(w['service_ms'] for w in r['work'] if w['stage']=='candidate_build' and w['id'] in rejected),drops=r['drops_by_reason'])
def pair(a,b):
    sa,sb=brief(a),brief(b)
    return dict(baseline=a['profile'],grants=b['profile'],same_input_hashes=a['manifest']['frame_sha256']==b['manifest']['frame_sha256'],
        same_service_profile=a['result']['config']['service_profile']==b['result']['config']['service_profile']=='v18_median',
        baseline_busy_rejections=sa['receiver_busy_feed_rejections'],grants_busy_rejections=sb['receiver_busy_feed_rejections'],
        baseline_eventual=sa['eventual'],grants_eventual=sb['eventual'],baseline_diagnostic_rate=sa['diagnostic_ids_per_second'],grants_diagnostic_rate=sb['diagnostic_ids_per_second'],
        limitation='Fixed historicalPython stagecost policycomparison; packet/referencehistoriescanchange. Baseline uses6 data tokens,grants uses5 plus1reservedcontrolmailboxslot. Separatepartition-onlycontrol isolates that tradeoff on primaryclip. NottargetCPU/RFcalibration.')
class Clock:
    def __init__(self):self.value=0
    def __call__(self):v=self.value;self.value+=1000000;return v

def main():
    paths=dependencies();pins={p.relative_to(ROOT).as_posix():sha(p) for p in paths};start=time.perf_counter()
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    cases=[];pairs=[]
    for name in ('mass-effect-2600.mp4','mass-effect-7200.mp4'):
        frames,manifest=source.native(media/name,n=90,start=4);assert manifest['unique_frame_count']==90
        prefix=name.removesuffix('.mp4')
        profiles=[('fixed_base6',dict(frame_grants_enabled=False,service_profile='v18_median')),('fixed_grants5',dict(service_profile='v18_median'))]
        if name=='mass-effect-2600.mp4':profiles.insert(1,('fixed_serialized_grants5',dict(service_profile='v18_median',frame_finish_ack=False)));profiles.insert(1,('fixed_partition5',dict(frame_grants_enabled=False,packet_data_tokens=5,service_profile='v18_median')));profiles.append(('measured_grants5',{}))
        native=[]
        for label,changes in profiles:
            cfg=model.Config(codec_mode='gm',feedback_latency_ms=2,decode_age_ms=200,refresh_period=30,**changes)
            c=dict(source='native-regression',profile=prefix+'/'+label,manifest=manifest,result=model.run(frames,manifest,cfg));cases.append(c);native.append(c);print(json.dumps(brief(c)),flush=True)
        pairs.append(pair(native[0],next(c for c in native if c['profile'].endswith('/fixed_grants5'))))
    images=[np.full((16,32,3),40+i,np.uint8) for i in range(32)];manifest=dict(source='synthetic:flat32',synthetic=True,frame_count=32,frame_sha256=[model.digest(f) for f in images])
    for label,changes in [('lost_grant',dict(lose_first_frame_grant=True)),('lost_release',dict(lose_first_frame_release=True)),
                          ('packet_credit_blackhole',dict(lose_all_packet_credits=True)),('dropped_fragment',dict(drop_packet_frame=8)),
                          ('duplicate_release_and_lost_credit',dict(duplicate_frame_release=True,lose_first_packet_credit=True,aggregate_ms=8))]:
        cfg=model.Config(width=32,height=16,codec_mode='gm',ui_rectangles=((0,0,16,8),),feedback_latency_ms=2,decode_age_ms=250,refresh_period=8,promotion_period=4,**changes)
        c=dict(source='synthetic-fault',profile=label,manifest=manifest,result=model.run(images,manifest,cfg,clock_ns=Clock()));cases.append(c);print(json.dumps(brief(c)),flush=True)
    assert pins=={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
    out=dict(evidence='Actual AR03 candidate→CRC-boundFG19frame-slotgrant→commit/cancel→GF03/PC18→FINISHdrain→release, distinctfromAF03pub; pairedfixedhistoricalservice comparison',
        source_sha256=pins,case_count=len(cases),cases=cases,summary=[brief(c) for c in cases],fixed_cost_pairs=pairs,
        python_wall_seconds=time.perf_counter()-start,versions=dict(python=platform.python_version(),numpy=np.__version__,pillow=PIL.__version__,pyav=av.__version__),
        wire_scope='FG19 32bytefields+4CRC=36bytes+28IPv4UDP, REQUEST/GRANT/CANCEL/CANCELED/FINISH/FINISHED/RELEASE. Sharedgatewayforwardwire+mailboxworker and sharedreversewire. FiveDATAtokensreserveonesixthmailboxslotforoneFG19orQC18control. ExistingGF03/PC18/QC18/AF03actualbytes retained. NoMSV1/firmwarecompatibility.',
        state_scope='Atmost2receiverframeowners boundepoch/frame/nonce/total/bodyCRC. Sendercommitsonlyreceivedgrant namingahost-known-freeslot. FINISHemittedonlyafterallPC18permitsreturn; FINISHEDreturnscontroltokenonly. Receiverthenwaitsingress+decode/read drain beforeRELEASE freesframeowner. SerializedcontrolprofileholdsFINISHuntilRELEASE. No senderfutureRXpeek. Precommit/noDATApostcommit cancelonly. Wrongkind/slot/identity stalecontrolsnonmutating. Lostunknowncontrolstopsboundedwithoutinventingcapacity; thosecasesintentionallyretainowners.',
        service_scope='fixedv18_median:historicalPythonpooledmediansms resize3.25972,build29.4824,decode_begin23.87022,commit.09932,packetize.03485,decode_complete.01377,ack_apply.00672; otheractualPythonstages .005ms. IndependentvirtualserversnotonesharedCPUschedule. ESP240MHz60%CPU,CRC/copy/driver,40MHzquadwrite,8KiBFIFO2MBsdrain,wire assumptions uncalibrated. Measuredprofile actualPythonstagecosts. Route/controlparse/build andallforward/reversewirepaid.',
        source_scope='Twoexistingprecompressednative1280x72029.88fps90framewindowsat4seconds,scheduled30IDs/s; reusedregressionnotfreshheldout. Offlinecaptureexcluded,BOXpaid. Syntheticfaultsareordering-only.',
        excluded_scope='NoESP32ISA/heap/RFcalibration,FPGAentropycycle/SDRAM/scanlineintegration,DSP/BRAMfit,nativecodec/bitstreamorphysical30fps proof.')
    (HERE/'results.json').write_text(json.dumps(out,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
