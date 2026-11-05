#!/usr/bin/env python3
"""Guarded transform-core source formation, actual causal CP34 and trace-native."""
import json,platform,time
import numpy as np
import helpers as h
from controller import choose

def elapsed(fn):
    t=time.perf_counter_ns();value=fn();return value,(time.perf_counter_ns()-t)/1e6

def metric(pixels,original,patches):
    display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),patches)
    return h.n.metric(original,display),h.n.digest(display)

def attempt(triple,kind,bg,hud,original,patches,state,group):
    packet,pixels,work=triple;fid,key,slot=state['fid'],state['key'],state['slot']
    start=time.perf_counter_ns();quality,tag=metric(pixels,original,patches);quality_ms=(time.perf_counter_ns()-start)/1e6
    start=time.perf_counter_ns();p=h.p
    pair=p.seal(p.PAIR.pack(b'CP34',1,p.PUBLISH|(p.KEY if key else 0),25,fid,p.NO_SLOT if key else slot,0 if key else 1-slot,
                           len(packet),len(hud),p.digest(packet),p.digest(hud))+packet+hud)
    fits=len(pair)<=49152
    if fits:p.parse_pair(pair)
    else:
        try:p.parse_pair(pair)
        except ValueError:pass
        else:raise AssertionError('overcap accepted')
    bind_ms=(time.perf_counter_ns()-start)/1e6
    return dict(kind=kind,background=bg,encode_group=group,base_packet=h.blob(packet),packet=h.blob(pair),
                complete_bytes=len(pair),base_bytes=len(packet),cap_fit=fits,hybrid=quality,hybrid_sha256=tag,
                quality_ms=quality_ms,bind_ms=bind_ms,work=work)

def total(rows):
    sse=sum(r['hybrid']['active_squared_error'] for r in rows);samples=sum(r['hybrid']['active_channel_samples'] for r in rows)
    return dict(frames=len(rows),complete_bytes=sum(r['body_bytes'] for r in rows),base_bytes=sum(r['base_bytes'] for r in rows),
                hud_bytes=sum(r['hud_bytes'] for r in rows),binding_bytes=60*len(rows),
                active_squared_error=sse,active_channel_samples=samples,active_mse=sse/samples,
                nominal_Mbps_at30=sum(r['body_bytes'] for r in rows)*240/len(rows)/1e6,
                maximum_complete_bytes=max(r['body_bytes'] for r in rows),
                actual_candidate_frames=sum(len(r['attempts']) for r in rows),selected_masked_frames=sum(r['mask_used'] for r in rows),
                source_same_history_shadow_bytes=sum(r['shadow_complete_bytes'] for r in rows),
                source_same_history_shadow_sse=sum(r['shadow_source_sse'] for r in rows),
                mean_paid_policy_ms=sum(r['paid_policy_ms'] for r in rows)/len(rows),
                mean_mask_ms=sum(r['mask_ms'] for r in rows)/len(rows),
                mean_receiver_ms=sum(r['receive_ms'] for r in rows)/len(rows))

def frame(src,hu,policy,state):
    fid=src['id'];key=fid%24==0
    if key:state.update(ref=None,rid=h.m.NO_REF,slot=0)
    state.update(fid=fid,key=key);ref,rid=state['ref'],state['rid']
    source,original=h.n.source(src),h.n.original(src)
    hud=h.raw(hu['packet'],h.HUD);patches=tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS)
    sources={'orig':source};mask_ms=0.;mask_work={};proof_ms=0.;mask_tag=None
    if policy=='guarded_core8':
        masked,mask_ms=elapsed(lambda:h.mask.mask_source(source,h.n.RECTS,policy='core8',work=mask_work))
        sources['mask']=masked;mask_tag=h.digest(b''.join(v.astype('u1').tobytes() for v in masked))
        start=time.perf_counter_ns();before=h.m.ft.planes_to_rgb(source);after=h.m.ft.planes_to_rgb(masked)
        visible=np.ones((480,720),bool)
        for x,y,w,hh in h.n.RECTS:visible[y:y+hh,x:x+w]=False
        np.testing.assert_array_equal(before[visible],after[visible]);proof_ms=(time.perf_counter_ns()-start)/1e6
    kinds=('zero',) if key else ('zero','half32');prepared={};analyses={}
    for family,planes in sources.items():
        for kind in kinds:
            prep,wall=elapsed(lambda:h.adaptive.analyze_with(h.m.base,planes,ref,epoch=25,frame_id=fid,reference_id=rid,
                    block_size=32,motion_mode='zero' if kind=='zero' else 'block',motion_precision='half',penalty=0,search_policy='adaptive_zero2'))
            prepared[(family,kind)]=prep;analyses[f'{family}:{kind}']=dict(wall_ms=wall,work=prep.work)
    attempts=[];groups=[];chosen=shadow=None;selection_ms=0.
    for bg in (16,32):
        q=h.m.roi.declared_map(720,480,h.n.ROIS,8,bg);byfamily={}
        for family in sources:
            bykind={}
            for kind in kinds:
                pair,wall=elapsed(lambda:h.shared.encode_pair(h.m,prepared[(family,kind)],q));gid=f'{bg}:{family}:{kind}'
                groups.append(dict(id=gid,wall_ms=wall,shared=pair[0][2]['shared_pair']))
                bykind[kind]=[attempt(triple,('mask_' if family=='mask' else '')+kind+('_band' if i else ''),bg,hud,original,patches,state,gid) for i,triple in enumerate(pair)]
            byfamily[family]=[bykind[k][0] for k in kinds]+[bykind[k][1] for k in kinds]
        controls=byfamily['orig'];children=byfamily.get('mask',[]);attempts.extend(controls+children)
        start=time.perf_counter_ns();shadow,_=h.select30.select_tier(controls,'band_strict');chosen=choose(shadow,children)
        selection_ms+=(time.perf_counter_ns()-start)/1e6
        if chosen is not None:break
    assert chosen is not None
    for a in attempts:a['selected']=a is chosen
    packet=h.raw(chosen['packet'],h.HERE);(pixels,decoded_hud,ack),receive_ms=elapsed(lambda:state['rx'].receive(packet))
    _,ack_ms=elapsed(lambda:h.p.validate_ack(ack,packet))
    for actual,expected in zip(decoded_hud,patches,strict=True):np.testing.assert_array_equal(actual['words'],expected)
    quality,tag=metric(pixels,original,tuple(v['words'] for v in decoded_hud));assert quality==chosen['hybrid'] and tag==chosen['hybrid_sha256']
    paid=mask_ms+sum(a['wall_ms'] for a in analyses.values())+sum(g['wall_ms'] for g in groups)+selection_ms
    paid+=sum(a['quality_ms']+a['bind_ms'] for a in attempts)
    row=dict(id=fid,key=key,reference_id=rid,reference_tag=prepared[('orig','zero')].reference_tag.hex(),
             source_slot=255 if key else state['slot'],destination_slot=0 if key else 1-state['slot'],
             source_sha256=src['common_yuv420_u8_sha256'],masked_source_sha256=mask_tag,mask_used=chosen['kind'].startswith('mask_'),
             mask_work=mask_work,mask_ms=mask_ms,offline_equivalence_ms=proof_ms,hud_packet=hu['packet'],hud_bytes=len(hud),binding_bytes=60,
             selected_kind=chosen['kind'],selected_background=chosen['background'],packet=chosen['packet'],base_packet=chosen['base_packet'],ack=h.blob(ack),
             body_bytes=len(packet),base_bytes=chosen['base_bytes'],hybrid=quality,hybrid_sha256=tag,
             shadow_kind=shadow['kind'],shadow_complete_bytes=shadow['complete_bytes'],shadow_source_sse=shadow['hybrid']['active_squared_error'],
             analyses=analyses,encode_groups=groups,selection_ms=selection_ms,attempts=attempts,paid_policy_ms=paid,receive_ms=receive_ms,ack_ms=ack_ms)
    state.update(ref=pixels,rid=fid,slot=row['destination_slot']);return row

def native_trace(inp,hudcase,case,name,q):
    planes=[];words=[];patches=[];source_tags=[]
    for src,row in zip(inp['rows'],case['rows'],strict=True):
        source=h.n.source(src)
        if row['mask_used']:source=h.mask.mask_source(source,h.n.RECTS,policy='core8')
        tag=h.digest(b''.join(v.astype('u1').tobytes() for v in source));source_tags.append(tag)
        assert tag==(row['masked_source_sha256'] if row['mask_used'] else row['source_sha256'])
        original=h.n.original(src);planes.append(source);words.append(original);patches.append(tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS))
    encoded,extra,enc=h.standard.encode(planes,name,q);outputs,dec=h.standard.decode(encoded,extra,name)
    assert [v['pts'] for v in encoded]==[v['dts'] for v in encoded]==list(range(48))
    assert [v['pts'] for v in encoded if v['is_key']]==[0,24] and not enc['packets_only_at_flush'] and not dec['frames_only_at_decode_flush']
    assert all(v['emitted_pts']==[v['id']] for v in enc['frame_calls']) and all(v['output_pts']==[v['packet_pts']] for v in dec['decode_calls'])
    rows=[]
    for v,original,parts,hu in zip(encoded,words,patches,hudcase['rows'],strict=True):
        fid=v['pts'];hu_bytes=h.raw(hu['packet'],h.HUD);display=h.n.overlay(outputs[fid],parts);quality=h.n.metric(original,display)
        rows.append(dict(id=fid,pts=fid,dts=v['dts'],key=v['is_key'],source_sha256=source_tags[fid],mask_used=case['rows'][fid]['mask_used'],
                         access_unit=h.blob(v['data']),access_unit_bytes=len(v['data']),extradata_bytes_charged=len(extra) if fid==0 else 0,
                         hud_packet=hu['packet'],hud_bytes=len(hu_bytes),binding_bytes=60,body_bytes=len(v['data'])+len(hu_bytes)+60+(len(extra) if fid==0 else 0),
                         hybrid=quality,hybrid_sha256=h.n.digest(display)))
    samples=sum(r['hybrid']['active_channel_samples'] for r in rows);sse=sum(r['hybrid']['active_squared_error'] for r in rows)
    sm=dict(frames=48,complete_bytes=sum(r['body_bytes'] for r in rows),active_squared_error=sse,active_channel_samples=samples,
            active_mse=sse/samples,maximum_complete_bytes=max(r['body_bytes'] for r in rows),cap_fit=all(r['body_bytes']<=49152 for r in rows))
    return dict(scene=inp['scene'],codec=name,parameter=q,processed='exact_guarded_source_trace',trace_policy=case['policy'],rows=rows,
                extradata=h.blob(extra),encode=enc,decode=dec,summary=sm)

def main():
    before=h.pins();inputs=h.load(h.n.V24/'results.json')['inputs'];hu=h.load(h.HUD/'results.json')['cases']
    prior=h.load(h.HERE.parent/'python-game-controller-v34-study/results.json')['cases'];cases=[];native=[]
    for inp in inputs:
        hudcase=next(v for v in hu if v['scene']==inp['scene']);control=next(v for v in prior if v['scene']==inp['scene'] and v['policy']=='control')
        states={k:dict(rx=h.p.Receiver(),ref=None,rid=h.m.NO_REF,slot=0) for k in h.POLICIES};rows={k:[] for k in h.POLICIES}
        for src,hud in zip(inp['rows'],hudcase['rows'],strict=True):
            order=h.POLICIES if src['id']%2==0 else h.POLICIES[::-1]
            for policy in order:rows[policy].append(frame(src,hud,policy,states[policy]))
            if (src['id']+1)%12==0:print(json.dumps(dict(scene=inp['scene'],frames_per_policy=src['id']+1)),flush=True)
        for row,old in zip(rows['control'],control['rows'],strict=True):
            assert h.raw(row['packet'],h.HERE)==h.raw(old['packet'],h.HERE.parent/'python-game-controller-v34-study') and row['hybrid']==old['hybrid']
        for policy in h.POLICIES:
            item=dict(scene=inp['scene'],policy=policy,rows=rows[policy],summary=total(rows[policy]));cases.append(item)
            print(json.dumps(dict(scene=inp['scene'],policy=policy,summary=item['summary'])),flush=True)
        target=cases[-1]
        for codec,params in (('libx265',(32,28,24,20) if inp['scene']=='mass-effect-2600' else (28,24,20)),
                             ('libsvtav1',(48,38,30,24) if inp['scene']=='mass-effect-2600' else (38,30,24))):
            for q in params:
                item=native_trace(inp,hudcase,target,codec,q);native.append(item)
                print(json.dumps(dict(native=codec,scene=inp['scene'],q=q,summary=item['summary'])),flush=True)
                if item['summary']['active_mse']<=target['summary']['active_mse'] and item['summary']['cap_fit']:break
        assert h.pins()==before,'source changed during campaign'
        output=dict(schema='gamebub-controller-v35',parent_commit='c50df93e313c9402c3741e5f6c921ee40e6f10a3',source_sha256=before,
                    cases=cases,native_cases=native,physical_30fps_proven=False,new_RTL_implemented=False,
                    geometry=dict(coded=[720,480],active=[720,405],exact_HUD_words=21120,cap=49152),
                    scope=['Actual unchanged CP34/HX33/GM27/JA34; original and guardedcore8 policies have independent accepted decoded histories.',
                           'Every core8 candidate competes against the fitting full original-source control winner on the same current reference; strictly fewer bytes and source RGB SSE no higher.',
                           'Paid clocks include mask construction, all analyses/shared encodes/quality/binding/selection; precodec equivalence and archive/fixture/HUD generation excluded explicitly.',
                           'Fresh native codecs consume exactly the selected orig/core8 source trace with identical HX33+60 and extradata once; native binding is accounted, not a CP34 native implementation.',
                           'Local source error guard is not a guarantee against a separate control history after reference divergence; aggregate and per-frame differences are reported.',
                           'Same two reused short gameplay windows; no native ESP32/FPGA/RF/QSPI, physicalFPS or HEVC/AV1 superiority claim.'])
        (h.HERE/'results.json').write_text(json.dumps(output,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
