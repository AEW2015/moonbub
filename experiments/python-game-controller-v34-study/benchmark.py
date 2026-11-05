#!/usr/bin/env python3
"""Actual GM34/CP34/HX33 causal campaign with all candidate costs retained."""
import json
import math
import time
import numpy as np
import helpers as h
from controller import choose

def elapsed(fn):
    start=time.perf_counter_ns();out=fn();return out,(time.perf_counter_ns()-start)/1e6

def attempt(packet,pixels,work,kind,bg,hud,original,state,group,wrap_ms=0.):
    ref,refid,slot,fid,key=state['ref'],state['refid'],state['slot'],state['fid'],state['key']
    (decoded,meta),debug_ms=elapsed(lambda:h.frame.decode(packet,ref,expected_epoch=25,expected_reference_id=None if key else refid))
    for a,b in zip(decoded,pixels,strict=True):np.testing.assert_array_equal(a,b)
    start=time.perf_counter_ns()
    hybrid=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS))
    metric=h.n.metric(original,hybrid);quality_ms=(time.perf_counter_ns()-start)/1e6
    start=time.perf_counter_ns();p=h.p
    pair=p.seal(p.PAIR.pack(b'CP34',1,p.PUBLISH|(p.KEY if key else 0),25,fid,p.NO_SLOT if key else slot,0 if key else 1-slot,
                           len(packet),len(hud),p.digest(packet),p.digest(hud))+packet+hud)
    fits=len(pair)<=p.CAP
    if fits:p.parse_pair(pair)
    else:
        try:p.parse_pair(pair)
        except ValueError:pass
        else:raise AssertionError('overcap CP34 accepted')
    bind_ms=(time.perf_counter_ns()-start)/1e6
    return dict(kind=kind,background=bg,encode_group=group,base_packet=h.blob(packet),packet=h.blob(pair),
                base_bytes=len(packet),complete_bytes=len(pair),cap_fit=fits,wire_magic=packet[:4].decode(),
                block_size=meta['block_size'],motion_bytes=meta['vector_bytes'],residual_bytes=sum(meta['plane_lengths']),
                qmap_bytes=meta['qmap_bytes'],work=work,wrap_ms=wrap_ms,quality_ms=quality_ms,bind_ms=bind_ms,
                offline_debug_decode_ms=debug_ms,hybrid=metric,hybrid_sha256=h.n.digest(hybrid),
                reconstructed_tag=meta['reconstructed_tag'].hex())

def summary(rows):
    n=len(rows);sse=sum(r['hybrid']['active_squared_error'] for r in rows);samples=sum(r['hybrid']['active_channel_samples'] for r in rows)
    return dict(frames=n,complete_bytes=sum(r['body_bytes'] for r in rows),base_bytes=sum(r['base_bytes'] for r in rows),
                hud_bytes=sum(r['hud_bytes'] for r in rows),binding_bytes=60*n,
                nominal_Mbps_at30=sum(r['body_bytes'] for r in rows)*240/n/1e6,
                active_squared_error=sse,active_channel_samples=samples,active_mse=sse/samples,
                maximum_complete_bytes=max(r['body_bytes'] for r in rows),exact_hud_words=21120*n,
                actual_candidate_frames=sum(len(r['attempts']) for r in rows),shared_pair_calls=sum(len(r['encode_groups']) for r in rows),
                selected_child_frames=sum(r['selected_kind'].startswith('child') for r in rows),
                selected_GM34_frames=sum(r['wire_magic']=='GM34' for r in rows),
                control_shadow_bytes=sum(r['shadow_complete_bytes'] for r in rows),
                control_shadow_sse=sum(r['shadow_source_sse'] for r in rows),
                mean_paid_policy_ms=sum(r['paid_policy_ms'] for r in rows)/n,
                mean_analysis_ms=sum(sum(a['wall_ms'] for a in r['analyses'].values()) for r in rows)/n,
                mean_shared_encode_ms=sum(sum(g['wall_ms'] for g in r['encode_groups']) for r in rows)/n,
                mean_HM34_pack_verify_ms=sum(r['component_ms'] for r in rows)/n,
                mean_receiver_ms=sum(r['receive_ms'] for r in rows)/n,
                selected_decoder_reference_reads=sum(a['work']['decoder_reference_sample_reads'] for r in rows for a in r['attempts'] if a['selected']))

def frame(src,old_hud,policy,state):
    fid=src['id'];key=fid%24==0
    if key:state.update(ref=None,refid=h.m.NO_REF,slot=0)
    state.update(fid=fid,key=key);ref,refid=state['ref'],state['refid']
    source,original=h.n.source(src),h.n.original(src)
    hud=h.raw(old_hud['packet'],h.HERE.parent/'python-game-hud-runs-v33-study')
    kinds=('zero',) if key else ('zero','half32');prepared={};analyses={}
    for kind in kinds:
        prep,wall=elapsed(lambda:h.adaptive.analyze_with(h.m.base,source,ref,epoch=25,frame_id=fid,reference_id=refid,
                    block_size=32,motion_mode='zero' if kind=='zero' else 'block',motion_precision='half',penalty=0,search_policy='adaptive_zero2'))
        prepared[kind]=prep;analyses[kind]=dict(wall_ms=wall,work=prep.work)
    child=motion=None;component_ms=0.;component_info=None
    if not key and policy!='control':
        fn=(lambda:h.full.analyze16(h.m,h.adaptive,prepared['half32'],ref)) if policy=='hierarchy_full' else (lambda:h.selective.analyze16(h.m,h.adaptive,prepared['half32'],ref,budget=25))
        child,wall=elapsed(fn);analyses['child']=dict(wall_ms=wall,work=child.work)
        start=time.perf_counter_ns()
        parent_vectors=h.m.base.unpack_vectors(prepared['half32'].vector_bytes,23,15)
        child_vectors=h.m.base.unpack_vectors(child.vector_bytes,45,30)
        motion,component_info=h.frame.prepare_motion(parent_vectors,child_vectors,720,480)
        component_ms=(time.perf_counter_ns()-start)/1e6
    attempts=[];groups=[];chosen=shadow=None;selection_ms=0.
    for bg in (16,32):
        q=h.m.roi.declared_map(720,480,h.n.ROIS,8,bg);bykind={}
        for kind in kinds:
            pair,wall=elapsed(lambda:h.shared.encode_pair(h.m,prepared[kind],q));group=f'{bg}:{kind}'
            groups.append(dict(id=group,wall_ms=wall,shared=pair[0][2]['shared_pair']))
            bykind[kind]=[attempt(*triple,kind+('_band' if i else ''),bg,hud,original,state,group) for i,triple in enumerate(pair)]
        controls=[bykind[k][0] for k in kinds]+[bykind[k][1] for k in kinds]
        start=time.perf_counter_ns();shadow,_=h.select30.select_tier(controls,'band_strict');selection_ms+=(time.perf_counter_ns()-start)/1e6
        children=[]
        if child is not None:
            pair,wall=elapsed(lambda:h.shared.encode_pair(h.m,child,q));group=f'{bg}:child'
            groups.append(dict(id=group,wall_ms=wall,shared=pair[0][2]['shared_pair']))
            for i,triple in enumerate(pair):
                packet,pixels,work=triple;kind='child'+('_band' if i else '')
                children.append(attempt(packet,pixels,work,kind,bg,hud,original,state,group))
                encoded,wrap_ms=elapsed(lambda:h.frame.wrap(packet,motion))
                children.append(attempt(encoded,pixels,work,kind+'_HM34',bg,hud,original,state,group,wrap_ms))
        attempts.extend(controls+children)
        start=time.perf_counter_ns();chosen=choose(shadow,children);selection_ms+=(time.perf_counter_ns()-start)/1e6
        if chosen is not None:break
    assert chosen is not None
    for a in attempts:a['selected']=a is chosen
    pair=h.raw(chosen['packet']);(pixels,patches,ack),receive_ms=elapsed(lambda:state['rx'].receive(pair))
    _,ack_ms=elapsed(lambda:h.p.validate_ack(ack,pair))
    for patch,(x,y,w,hh) in zip(patches,h.n.RECTS,strict=True):np.testing.assert_array_equal(patch['words'],original[y:y+hh,x:x+w])
    hybrid=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),tuple(v['words'] for v in patches))
    assert h.n.metric(original,hybrid)==chosen['hybrid'] and h.n.digest(hybrid)==chosen['hybrid_sha256']
    paid=sum(v['wall_ms'] for v in analyses.values())+sum(g['wall_ms'] for g in groups)+component_ms+selection_ms
    paid+=sum(a['wrap_ms']+a['quality_ms']+a['bind_ms'] for a in attempts)
    destination=0 if key else 1-state['slot']
    row=dict(id=fid,key=key,reference_id=refid,reference_tag=prepared['zero'].reference_tag.hex(),
             source_slot=h.p.NO_SLOT if key else state['slot'],destination_slot=destination,
             source_sha256=src['common_yuv420_u8_sha256'],hud_packet=old_hud['packet'],hud_bytes=len(hud),binding_bytes=60,
             packet=chosen['packet'],base_packet=chosen['base_packet'],ack=h.blob(ack),base_bytes=chosen['base_bytes'],body_bytes=len(pair),
             wire_magic=chosen['wire_magic'],selected_kind=chosen['kind'],selected_background=chosen['background'],
             reconstructed_tag=chosen['reconstructed_tag'],hybrid=chosen['hybrid'],hybrid_sha256=chosen['hybrid_sha256'],
             shadow_kind=shadow['kind'],shadow_complete_bytes=shadow['complete_bytes'],shadow_source_sse=shadow['hybrid']['active_squared_error'],
             analyses=analyses,encode_groups=groups,component_ms=component_ms,component_info=component_info,
             selection_ms=selection_ms,attempts=attempts,paid_policy_ms=paid,receive_ms=receive_ms,ack_ms=ack_ms)
    state.update(ref=pixels,refid=fid,slot=destination);return row

def main():
    before=h.pins();inputs=h.load(h.n.V24/'results.json')['inputs']
    hud=h.load(h.HERE.parent/'python-game-hud-runs-v33-study/results.json')['cases']
    prior=h.load(h.HERE.parent/'python-game-global-v33-study/results.json')['cases'];cases=[]
    for inp in inputs:
        hu=next(v for v in hud if v['scene']==inp['scene']);old=next(v for v in prior if v['scene']==inp['scene'] and v['policy']=='band_control')
        states={k:dict(rx=h.p.Receiver(),ref=None,refid=h.m.NO_REF,slot=0) for k in h.POLICIES};rows={k:[] for k in h.POLICIES}
        for src,old_hud in zip(inp['rows'],hu['rows'],strict=True):
            shift=src['id']%3;order=h.POLICIES[shift:]+h.POLICIES[:shift]
            for policy in order:rows[policy].append(frame(src,old_hud,policy,states[policy]))
            if (src['id']+1)%12==0:print(json.dumps(dict(scene=inp['scene'],frames_per_policy=src['id']+1)),flush=True)
        for row,pr in zip(rows['control'],old['rows'],strict=True):
            assert h.raw(row['base_packet'])==h.raw(pr['base_packet'],h.HERE.parent/'python-game-global-v33-study') and row['hybrid']==pr['hybrid']
        for policy in h.POLICIES:
            item=dict(scene=inp['scene'],policy=policy,rows=rows[policy],summary=summary(rows[policy]));cases.append(item)
            print(json.dumps(dict(scene=inp['scene'],policy=policy,summary=item['summary'])),flush=True)
        assert h.pins()==before,'source changed during campaign'
        result=dict(schema='gamebub-controller-v34',parent_commit='9c29165b816d49e2dec1c153712d1293b4781c6b',source_sha256=before,cases=cases,
                    geometry=dict(coded=[720,480],active=[720,405],maximum_HUD_words=21120,cap=49152),
                    physical_30fps_proven=False,new_RTL_implemented=False,
                    scope=['Actual mixed GM27/GM34 frames and CP34/HX33/JA34 atomic host receiver; three separate accepted decoded histories.',
                           'Shared encoder pair work and HM34 motion preparation each charged once; every losing frame is serialized/scored/bound/retained.',
                           'Child admission requires a fitting same-history complete control shadow, strictly fewer bytes and current RGB SSE no higher.',
                           'Policy25 preset chosen before selective fixed-reference results; same two reused48frame windows, no heldout performance claim.',
                           'Paid wall excludes fixture read/conversion, preencoded HX33 generation, offline debug decode, artifact IO, network and display.',
                           'In-process profile and publication-gate model only; no live negotiation, native ESP32/FPGA fit, RF/QSPI or physical30fps proof.'])
        (h.HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
