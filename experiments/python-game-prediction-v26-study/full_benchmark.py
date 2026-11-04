#!/usr/bin/env python3
"""Full48 causal actual-byte/SSE selection with CP2F/JA2F acceptance."""
from pathlib import Path
import json,time,math
import numpy as np
import benchmark as b
import full_pair_model as p
HERE=b.HERE
m=p.base


def pins():
    paths={b.ROOT/name for name in b.n.load(HERE/'results.json')['source_sha256']}
    paths|=set(HERE.glob('*.py'))
    paths|={HERE/'results.json',b.CAPPED/'results.json',HERE.parent/'python-game-rdo-counter-v26-study/model.py'}
    old=b.n.load(b.n.V24/'results.json');prior=b.n.load(b.CAPPED/'results.json')
    for inp in old['inputs']:
        for row in inp['rows']:
            for key in ('common_yuv420_u8','original_rgb565'):paths.add(b.n.V24/row[key]['path'])
    for case in prior['cases']:
        if case['profile']=='capped_key_zero_rdo1':
            for row in case['rows']:paths.add(b.CAPPED/row['hud_packet']['path'])
    return {path.relative_to(b.ROOT).as_posix():b.n.sha(path) for path in sorted(paths)}


def pair_bytes(base,hud,fid,slot,key):
    flags=p.PUBLISH|(p.KEY if key else 0);source=p.NO_SLOT if key else slot;destination=0 if key else 1-slot
    return p.seal(p.PAIR.pack(b'CP2F',1,flags,25,fid,source,destination,len(base),len(hud),p.digest(base),p.digest(hud))+base+hud)


def attempt(prepared,qmap,kind,bg,hud,original,ref,refid,slot):
    began=time.perf_counter_ns();packet,expected,work=m.encode_prepared(prepared,qmap,rdo_lambda=1)
    encode_ms=(time.perf_counter_ns()-began)/1e6
    began=time.perf_counter_ns();decoded,meta=m.decode(packet,ref,expected_epoch=25,expected_reference_id=None if prepared.key else refid)
    verify_decode_ms=(time.perf_counter_ns()-began)/1e6
    for a,c in zip(decoded,expected):np.testing.assert_array_equal(a,c)
    began=time.perf_counter_ns();bare=m.C.corpus.rgb565(m.ft.planes_to_rgb(decoded))
    hybrid=b.n.overlay(bare,tuple(original[y:y+h,x:x+w] for x,y,w,h in b.n.RECTS))
    quality=b.n.metric(original,hybrid);quality_ms=(time.perf_counter_ns()-began)/1e6
    began=time.perf_counter_ns();pair=pair_bytes(packet,hud,prepared.frame_id,slot,prepared.key)
    fits=len(pair)<=p.CAP
    if fits:p.parse_pair(pair)
    else:
        try:p.parse_pair(pair)
        except ValueError:pass
        else:raise AssertionError('overcap CP2F accepted')
    bind_validate_ms=(time.perf_counter_ns()-began)/1e6
    desc=dict(kind=kind,background=bg,base_packet=b.blob(packet),packet=b.blob(pair),base_bytes=len(packet),complete_bytes=len(pair),cap_fit=fits,
              work=work,encode_ms=encode_ms,verify_decode_ms=verify_decode_ms,quality_ms=quality_ms,bind_validate_ms=bind_validate_ms,
              hybrid=quality,reconstructed_tag=meta['reconstructed_tag'].hex(),bare_rgb565_sha256=b.n.digest(bare),hybrid_rgb565_sha256=b.n.digest(hybrid))
    return desc,pair,decoded,hybrid


def summarize(rows,frozen):
    error=sum(r['hybrid']['active_squared_error'] for r in rows);samples=sum(r['hybrid']['active_channel_samples'] for r in rows)
    total=sum(r['body_bytes'] for r in rows);old=frozen['joint_summary'];base=sum(r['base_bytes'] for r in rows)
    return dict(frames=len(rows),complete_bytes=total,coded_body_Mbps_at30=total*240/len(rows)/1e6,base_bytes=base,
                hud_bytes=sum(r['hud_bytes'] for r in rows),binding_bytes=sum(r['binding_bytes'] for r in rows),
                max_complete_bytes=max(r['body_bytes'] for r in rows),cap_fit_frames=sum(r['body_bytes']<=p.CAP for r in rows),
                active_squared_error=error,active_channel_samples=samples,active_mse=error/samples,
                active_psnr_db=10*math.log10(65025/(error/samples)),hud_word_errors=sum(r['hybrid']['hud_word_errors'] for r in rows),
                selected_half32_frames=sum(r['selected_kind']=='half32' for r in rows),selected_zero_frames=sum(r['selected_kind']=='zero' for r in rows),
                causal_quality_gate_failures=sum(a.get('quality_eligible') is False for r in rows for a in r['attempts']),
                coarse_fallback_frames=[r['id'] for r in rows if r['selected_background']==32],
                paid_candidate_encodes=sum(len(r['attempts']) for r in rows),paid_analyses=sum(len(r['analyses']) for r in rows),
                rejected_cap_attempts=sum(not a['cap_fit'] for r in rows for a in r['attempts']),
                mean_paid_base_analysis_encode_ms=sum(r['paid_base_analysis_encode_ms'] for r in rows)/len(rows),
                mean_receiver_ms=sum(r['receive_ms'] for r in rows)/len(rows),
                mean_offline_attempt_verify_ms=sum(a['verify_decode_ms'] for r in rows for a in r['attempts'])/len(rows),
                search_sample_operations=sum(a['search']['sad_sample_operations'] for r in rows for a in r['analyses'].values()),
                search_reference_fetches=sum(a['search'].get('reference_sample_fetches',0) for r in rows for a in r['analyses'].values()),
                motion_map_pack_ms=sum(a['motion_map']['pack_wall_ms'] for r in rows for a in r['analyses'].values()),
                reference_sample_fetches_selected=sum(next(a for a in r['attempts'] if a['selected'])['work']['decoder_reference_sample_reads'] for r in rows),
                ack_bytes=sum(r['ack']['raw_bytes'] for r in rows),frozen_v25_complete_bytes=old['complete_bytes'],frozen_v25_active_mse=old['active_mse'],
                byte_saving_vs_frozen_v25=1-total/old['complete_bytes'],at_least_frozen_v25_aggregate_quality=error/samples<=old['active_mse'])


def campaign(inp,frozen):
    receiver=p.Receiver(epoch=25);ref=None;refid=m.NO_REF;slot=0;rows=[]
    for srcrow,oldrow in zip(inp['rows'],frozen['rows']):
        fid=srcrow['id'];key=fid%24==0
        if key:ref=None;refid=m.NO_REF;slot=0
        src=b.n.source(srcrow);original=b.n.original(srcrow);hud=b.n.raw(oldrow['hud_packet'],b.CAPPED)
        analyses={};prepared={}
        policies=('zero',) if key else ('zero','half32')
        for kind in policies:
            prepared[kind]=m.analyze_planes(src,ref,epoch=25,frame_id=fid,reference_id=refid,block_size=32,
                                           motion_mode='zero' if kind=='zero' else 'block',motion_precision='half',penalty=0)
            analyses[kind]=prepared[kind].work
        attempts=[];selected=None
        for bg in (16,32):
            qmap=m.roi.declared_map(720,480,b.n.ROIS,8,bg);candidates=[]
            for kind in policies:
                outcome=attempt(prepared[kind],qmap,kind,bg,hud,original,ref,refid,slot)
                attempts.append(outcome[0]);candidates.append(outcome)
            zero=candidates[0][0];base_sse=zero['hybrid']['active_squared_error']
            for desc,*_ in candidates:desc['quality_eligible']=desc['hybrid']['active_squared_error']<=base_sse
            eligible=[c for c in candidates if c[0]['cap_fit'] and c[0]['quality_eligible']]
            if eligible:
                selected=min(eligible,key=lambda c:c[0]['complete_bytes']);break
        assert selected is not None,'all bounded candidates rejected'
        desc,pair,expected,expected_hybrid=selected
        for a in attempts:a['selected']=a is desc
        began=time.perf_counter_ns();decoded,patches,ack=receiver.receive(pair);receive_ms=(time.perf_counter_ns()-began)/1e6
        began=time.perf_counter_ns();ackmeta=p.validate_ack(ack,pair);ack_ms=(time.perf_counter_ns()-began)/1e6
        for a,c in zip(decoded,expected):np.testing.assert_array_equal(a,c)
        for patch,(x,y,w,h) in zip(patches,b.n.RECTS):np.testing.assert_array_equal(patch['words'],original[y:y+h,x:x+w])
        bare=m.C.corpus.rgb565(m.ft.planes_to_rgb(decoded));hybrid=b.n.overlay(bare,tuple(x['words'] for x in patches))
        np.testing.assert_array_equal(hybrid,expected_hybrid)
        row=dict(id=fid,key=key,reference_id=refid,source_slot=p.NO_SLOT if key else slot,destination_slot=0 if key else 1-slot,
                 selected_kind=desc['kind'],selected_background=desc['background'],base_packet=desc['base_packet'],packet=desc['packet'],
                 body_bytes=len(pair),base_bytes=desc['base_bytes'],hud_bytes=len(hud),binding_bytes=p.PAIR.size+4,
                 hud_packet=dict(directory=b.CAPPED.relative_to(b.ROOT).as_posix(),**oldrow['hud_packet']),
                 ack=b.blob(ack),ack_meta=ackmeta,attempts=attempts,analyses=analyses,
                 paid_base_analysis_encode_ms=sum(a['analysis_wall_ms'] for a in analyses.values())+sum(a['encode_ms'] for a in attempts),
                 retained_hud_encode_ms=oldrow['hud_encode_ms'],receive_ms=receive_ms,ack_validation_ms=ack_ms,
                 hybrid=desc['hybrid'],hybrid_rgb565_sha256=b.n.digest(hybrid),reconstructed_tag=desc['reconstructed_tag'])
        if fid in (0,1,24):row['golden_hybrid_rgb565']=b.blob(hybrid.astype('<u2').tobytes())
        rows.append(row);ref=decoded;refid=fid;slot=row['destination_slot']
        print(json.dumps(dict(scene=inp['scene'],id=fid,selected=desc['kind'],background=desc['background'],bytes=len(pair),mse=desc['hybrid']['active_mse'],attempts=len(attempts))),flush=True)
    return dict(scene=inp['scene'],policy='causal-actual-byte-zero-or-half32-SSE-gate',rows=rows,summary=summarize(rows,frozen))


def main():
    before=pins();old=b.n.load(b.n.V24/'results.json');prior=b.n.load(b.CAPPED/'results.json')
    result=dict(schema='gamebub-fractional-full-v26',source_sha256=before,cases=[],
                scope=['Actual GM26version2+HU25 bound in distinct CP2F packets with JA2F acknowledgements, strict49152B complete cap, epoch25 for retainedHUDcompatibility.',
                       'Keys0/24 independent. Everyacceptedframe publishes; source references are exact last decoded/ACKed reconstructions, never originals.',
                       'Each nonkey source separately analyzes/encodes zero and half32 on the same accepted reference. Half may win only actualsmallercompletebytes and activeRGB565hybridSSE<=currentzero.',
                       'ROI8/bg16 attempted first; only if no qualityeligiblecandidatefitscompletecap, ROI8/bg32 attempted using preparedanalysis. Alllosingpackets/coefficients/work retained.',
                       'ExactHUD bytes retained from frozenv25 and decoded against own accepted HUD state; originalencode cost recorded separately and not remeasured.',
                       'FastRDO is an isolatedadapter using provenbatchedexactCP02counts; frozen transform/ROI/inverse/entropy and predictor model files unchanged.',
                       'Offline retained48framewindows,720x480coded/720x405active. Rates are nominal30fps projections, no physical30fps/nativeFPGA/ESP32claim.'])
    for inp in old['inputs']:
        frozen=next(c for c in prior['cases'] if c['scene']==inp['scene'] and c['profile']=='capped_key_zero_rdo1')
        result['cases'].append(campaign(inp,frozen));assert pins()==before,'dependency changed'
        (HERE/'full_results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
    (HERE/'full_sourcepins.json').write_text(json.dumps(before,indent=2)+'\n')
if __name__=='__main__':main()
