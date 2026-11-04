#!/usr/bin/env python3
"""Direct unified fractional/EC26 encoding; causal and fixed-history controls."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import platform
import sys
import time
import zlib
import numpy as np
import model as m
import protocol as p

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OLD=HERE.parent/'python-game-prediction-v26-study'
spec=importlib.util.spec_from_file_location('unified27_native',HERE.parent/'python-game-native-motion-v25-study/benchmark.py')
n=importlib.util.module_from_spec(spec);sys.modules[spec.name]=n;spec.loader.exec_module(n)


def load(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def raw(d,folder=HERE):return n.raw(d,folder)


def blob(data):
    stored=zlib.compress(data,9);name='objects/'+hashlib.sha256(stored).hexdigest()+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(stored)
    return dict(path=name,raw_bytes=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),stored_sha256=hashlib.sha256(stored).hexdigest())


def pins():
    prior=load(OLD/'full_results.json');paths={ROOT/name for name in prior['source_sha256']}
    paths|={OLD/'full_results.json',n.V24/'results.json'}
    paths|=set(HERE.glob('*.py'))|{HERE/'README.md',HERE/'SCHEMA.md'}
    for folder in ('python-game-decoder-v27-study',):
        paths.add(HERE.parent/folder/'model.py')
    for c in prior['cases']:
        for row in c['rows']:
            paths|={OLD/row[key]['path'] for key in ('base_packet','packet','ack')}
            paths.add(ROOT/row['hud_packet']['directory']/row['hud_packet']['path'])
    return {q.relative_to(ROOT).as_posix():sha(q) for q in sorted(paths)}


def attempt(prepared,qmap,kind,bg,hud,original,ref,refid,slot):
    started=time.perf_counter_ns();base,expected,work=m.encode_prepared(prepared,qmap,rdo_lambda=1)
    encode_ms=(time.perf_counter_ns()-started)/1e6
    began=time.perf_counter_ns();decoded,meta=m.decode(base,ref,expected_epoch=25,expected_reference_id=None if prepared.key else refid)
    offline_decode_ms=(time.perf_counter_ns()-began)/1e6
    for a,b in zip(decoded,expected):np.testing.assert_array_equal(a,b)
    began=time.perf_counter_ns();bare=m.C.corpus.rgb565(m.ft.planes_to_rgb(decoded))
    hybrid=n.overlay(bare,tuple(original[y:y+h,x:x+w] for x,y,w,h in n.RECTS));quality=n.metric(original,hybrid)
    quality_ms=(time.perf_counter_ns()-began)/1e6
    source=p.NO_SLOT if prepared.key else slot;dest=0 if prepared.key else 1-slot
    began=time.perf_counter_ns()
    # Serialize even a rejected attempt so admission is measured on actual bytes.
    flags=p.PUBLISH|(p.KEY if prepared.key else 0)
    pair=p.seal(p.PAIR.pack(b'CP27',1,flags,25,prepared.frame_id,source,dest,len(base),len(hud),p.digest(base),p.digest(hud))+base+hud)
    fits=len(pair)<=p.CAP
    if fits:p.parse_pair(pair)
    else:
        try:p.parse_pair(pair)
        except ValueError:pass
        else:raise AssertionError('overcap CP27 accepted')
    bind_ms=(time.perf_counter_ns()-began)/1e6
    info=dict(kind=kind,background=bg,base_packet=blob(base),packet=blob(pair),base_bytes=len(base),complete_bytes=len(pair),cap_fit=fits,
              work=work,encode_ms=encode_ms,offline_decode_ms=offline_decode_ms,quality_ms=quality_ms,bind_ms=bind_ms,
              hybrid=quality,reconstructed_tag=meta['reconstructed_tag'].hex(),bare_rgb565_sha256=n.digest(bare),hybrid_rgb565_sha256=n.digest(hybrid))
    return info,pair,decoded,hybrid


def summarize(rows,prior):
    count=len(rows);total=sum(r['body_bytes'] for r in rows);sse=sum(r['hybrid']['active_squared_error'] for r in rows);samples=sum(r['hybrid']['active_channel_samples'] for r in rows)
    return dict(frames=count,complete_bytes=total,coded_body_Mbps_at30=total*240/count/1e6,
                base_bytes=sum(r['base_bytes'] for r in rows),hud_bytes=sum(r['hud_bytes'] for r in rows),binding_bytes=60*count,
                maximum_complete_bytes=max(r['body_bytes'] for r in rows),cap_fit_frames=sum(r['body_bytes']<=49152 for r in rows),
                exact_hud_words=21120*count,hud_word_errors=sum(r['hybrid']['hud_word_errors'] for r in rows),
                active_squared_error=sse,active_channel_samples=samples,active_mse=sse/samples,active_psnr_db=10*math.log10(65025/(sse/samples)),
                selected_half32_frames=sum(r['selected_kind']=='half32' for r in rows),selected_zero_frames=sum(r['selected_kind']=='zero' for r in rows),
                coarse_fallback_frames=[r['id'] for r in rows if r['selected_background']==32],
                paid_candidate_encodes=sum(len(r['attempts']) for r in rows),paid_analyses=sum(len(r['analyses']) for r in rows),
                rejected_cap_attempts=sum(not a['cap_fit'] for r in rows for a in r['attempts']),
                quality_guard_failures=sum(a.get('quality_eligible') is False for r in rows for a in r['attempts']),
                mean_paid_base_encode_ms=sum(r['paid_base_encode_ms'] for r in rows)/count,
                mean_receiver_ms=sum(r['receive_ms'] for r in rows)/count,
                mean_bind_ms=sum(a['bind_ms'] for r in rows for a in r['attempts'])/count,
                mean_ack_validation_ms=sum(r['ack_validation_ms'] for r in rows)/count,
                mean_offline_candidate_decode_ms=sum(a['offline_decode_ms'] for r in rows for a in r['attempts'])/count,
                ec26_plane_selections=sum(d['selected_mode']=='EC26' for r in rows for a in r['attempts'] for d in a['work']['planes']),
                ec26_construct_calls=sum(a['work']['ec26_construct_calls'] for r in rows for a in r['attempts']),
                legacy_cp02_encode_calls=sum(a['work']['legacy_cp02_encode_calls'] for r in rows for a in r['attempts']),
                frozen_v26_complete_bytes=prior['summary']['complete_bytes'],frozen_v26_active_mse=prior['summary']['active_mse'],
                saving_vs_v26_prediction=1-total/prior['summary']['complete_bytes'],
                at_least_v26_aggregate_quality=sse/samples<=prior['summary']['active_mse'])


def campaign(inp,prior,policy):
    receiver=p.Receiver(epoch=25);ref=None;refid=m.NO_REF;slot=0;rows=[]
    for srcrow,oldrow in zip(inp['rows'],prior['rows']):
        fid=srcrow['id'];key=fid%24==0
        if key:ref=None;refid=m.NO_REF;slot=0
        src=n.source(srcrow);original=n.original(srcrow)
        hud=raw(oldrow['hud_packet'],ROOT/oldrow['hud_packet']['directory'])
        kinds=(oldrow['selected_kind'],) if policy=='frozen_trace' else ('zero',) if key else ('zero','half32')
        analyses={};prepared={}
        for kind in kinds:
            prepared[kind]=m.analyze_planes(src,ref,epoch=25,frame_id=fid,reference_id=refid,block_size=32,
                                           motion_mode='zero' if kind=='zero' else 'block',motion_precision='half',penalty=0)
            analyses[kind]=prepared[kind].work
        attempts=[];selected=None
        backgrounds=(oldrow['selected_background'],) if policy=='frozen_trace' else (16,32)
        for bg in backgrounds:
            qmap=m.roi.declared_map(720,480,n.ROIS,8,bg);candidates=[]
            for kind in kinds:
                out=attempt(prepared[kind],qmap,kind,bg,hud,original,ref,refid,slot);attempts.append(out[0]);candidates.append(out)
            baseline_sse=candidates[0][0]['hybrid']['active_squared_error']
            for a,*_ in candidates:a['quality_eligible']=a['hybrid']['active_squared_error']<=baseline_sse
            eligible=[a for a in candidates if a[0]['cap_fit'] and a[0]['quality_eligible']]
            if eligible:selected=min(eligible,key=lambda a:a[0]['complete_bytes']);break
        assert selected is not None,'all candidates failed'
        info,pair,expected,expected_hybrid=selected
        for a in attempts:a['selected']=a is info
        began=time.perf_counter_ns();decoded,patches,ack=receiver.receive(pair);receive_ms=(time.perf_counter_ns()-began)/1e6
        began=time.perf_counter_ns();ackmeta=p.validate_ack(ack,pair);ack_ms=(time.perf_counter_ns()-began)/1e6
        for a,b in zip(decoded,expected):np.testing.assert_array_equal(a,b)
        for v,(x,y,w,h) in zip(patches,n.RECTS):np.testing.assert_array_equal(v['words'],original[y:y+h,x:x+w])
        hybrid=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(decoded)),tuple(v['words'] for v in patches))
        np.testing.assert_array_equal(hybrid,expected_hybrid)
        if policy=='frozen_trace':
            assert n.digest(hybrid)==oldrow['hybrid_rgb565_sha256'] and info['reconstructed_tag']==oldrow['reconstructed_tag']
            assert len(pair)<=oldrow['body_bytes']
        rows.append(dict(id=fid,key=key,reference_id=refid,source_slot=p.NO_SLOT if key else slot,destination_slot=0 if key else 1-slot,
                         source_common_yuv_sha256=srcrow['common_yuv420_u8_sha256'],selected_kind=info['kind'],selected_background=info['background'],
                         base_packet=info['base_packet'],packet=info['packet'],body_bytes=len(pair),base_bytes=info['base_bytes'],hud_bytes=len(hud),binding_bytes=60,
                         hud_packet=dict(**oldrow['hud_packet']),ack=blob(ack),ack_meta=ackmeta,attempts=attempts,analyses=analyses,
                         paid_base_encode_ms=sum(a['analysis_wall_ms'] for a in analyses.values())+sum(a['encode_ms'] for a in attempts),
                         receive_ms=receive_ms,ack_validation_ms=ack_ms,hybrid=info['hybrid'],hybrid_rgb565_sha256=n.digest(hybrid),
                         reconstructed_tag=info['reconstructed_tag'],fixed_trace_image_parity=policy=='frozen_trace'))
        ref,refid,slot=decoded,fid,0 if key else 1-slot
    result=dict(scene=inp['scene'],policy=policy,rows=rows,summary=summarize(rows,prior),
                scope='Frozen v26 choice trace is a fixed-image entropy control, not a new online mode selector.' if policy=='frozen_trace' else 'Causal actual-byte/SSE selector; all competing analysis and encoding paid.')
    print(json.dumps(dict(scene=result['scene'],policy=policy,summary=result['summary'])),flush=True);return result


def main():
    before=pins();prior=load(OLD/'full_results.json');inputs=load(n.V24/'results.json')['inputs'];cases=[]
    for inp in inputs:
        old=next(c for c in prior['cases'] if c['scene']==inp['scene'])
        for policy in ('frozen_trace','unified_causal'):cases.append(campaign(inp,old,policy))
    assert before==pins(),'source changed'
    data=dict(schema='gamebub-unified-v27',source_sha256=before,cases=cases,
              counts=dict(unique_source_frames=96,accepted_pairs=192,exact_hud_words=192*21120),
              versions=dict(python=platform.python_version(),numpy=np.__version__),
              scope=['Actual direct GM27/CP27/JA27 withEC26block-major andcompactfractionalprediction, exactHU25unchanged.',
                     'Frozen trace isolatesentropyatidenticalimages; causalcontrollerregeneratesreferencehistoryandcapdecisions usingactualnewbytes.',
                     'Ratesproject30IDs/s ontwo reused29.88fpswindows; no nativeESP32/FPGA/RF/physical30fpsorHEVCparityproof.',
                     'CRC/header-onlymetadata validation defersentropy/MVsemantics tofullreceiverdecodebeforepublication. No encoderoptimalitysearch atreceiver.',
                     'Python modelstillallocatesfullplanes; EC26blockiteratorboundsnotfittedRAM/porttimingproof.'])
    (HERE/'results.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n')


if __name__=='__main__':main()
