#!/usr/bin/env python3
"""Independent quantized MB costs, actual mixed-MV semantics and packet guard.

Current reconstructed references only. Proxies are not marginal whole-plane
rates, and a current-frame guard does not prove future quality against zero.
"""
from pathlib import Path
from dataclasses import replace
import importlib.util,json,math,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value
proof=module('quant53_frozen47_proof',HERE.parent/'python-game-motion-v47-study/verify.py')
prior=module('quant53_frozen50_proof',HERE.parent/'python-game-guarded-motion-v50-study/verify.py')
fine=module('quant53_independent39_finebits',HERE.parent/'python-game-signal-v39-study/verify.py')
m,f,n,direct=proof.m,proof.f,proof.n,proof.direct
raw,digest=proof.raw,proof.digest

def no_new_encoder():
    forbidden={HERE/'model.py',HERE/'benchmark.py'}
    assert not any(Path(getattr(v,'__file__','')).resolve()in forbidden for v in list(sys.modules.values())if getattr(v,'__file__',None))

def fork(receiver):
    result=direct.Receiver();result.ref,result.rid,result.hud,result.last=receiver.ref,receiver.rid,receiver.hud,receiver.last
    return result

def prepared_hashes(prepared):
    return dict(prediction_sha256=digest(b''.join(v.astype('<i2').tobytes()for v in prepared.prediction)),
        raw_coefficients_sha256=digest(b''.join(v.astype('<i2').tobytes()for v in prepared.raw_coefficients)),
        source_sha256=digest(b''.join(v.astype('<i2').tobytes()for v in prepared.source)))

def mb_costs(source,prepared,qmap):
    coeff=m.base._quantize(prepared.raw_coefficients,qmap,720,480)
    rebuilt=m.gm.reconstruct(coeff,prepared.prediction,qmap,720,480)
    costs=np.zeros((15,23,3),np.int64)
    for axis,(src,pixels,blocks,safe)in enumerate(zip(source,rebuilt,coeff,f.f.safe_blocks(),strict=True)):
        bh,bw=src.shape[0]//8,src.shape[1]//8;span=4 if axis==0 else 2
        errors=((src.astype(np.int64)-pixels.astype(np.int64))**2).reshape(bh,8,bw,8).transpose(0,2,1,3).reshape(-1,8,8).sum(axis=(1,2))
        bits=fine.fine_bits(blocks);mask=safe.reshape(-1);errors[mask]=0;bits[mask]=0
        ids=((np.arange(bh)[:,None]//span)*23+np.arange(bw)[None,:]//span).reshape(-1)
        np.add.at(costs[...,0].reshape(-1),ids,errors);np.add.at(costs[...,1].reshape(-1),ids,bits)
        for index in sorted({0,len(blocks)//2,len(blocks)-1}):assert fine.scalar_fine_bits(blocks[index])==fine.fine_bits(blocks[index:index+1])[0]
    vectors=np.zeros((15,23,2),np.int8)if prepared.key else m.base.unpack_vectors(prepared.vector_bytes,23,15)
    costs[...,2]=16*np.any(vectors!=0,axis=2)
    return costs

def selectors(costs):
    if costs.shape!=(15,23,2,3)or costs.dtype!=np.int64 or np.any(costs<0):raise ValueError('exact two-policy MB cost tensor')
    z,g=costs[:,:,0],costs[:,:,1];zb=z[...,1]+z[...,2];gb=g[...,1]+g[...,2]
    score0=z[...,0]+4*zb;score1=g[...,0]+4*gb
    a=(score1<score0)
    b=(g[...,0]<=z[...,0])&(gb<=zb)&((g[...,0]<z[...,0])|(gb<zb))
    return a.astype(np.uint8),b.astype(np.uint8)

def materialize(source,reference,zero,grid,selected):
    if selected.shape!=(15,23)or selected.dtype!=np.uint8 or np.any(selected>1):raise ValueError('exact binary MB selection')
    gv=np.zeros((15,23,2),np.int8)if grid.key else m.base.unpack_vectors(grid.vector_bytes,23,15)
    vectors=np.where(selected[...,None]!=0,gv,0).astype(np.int8)
    actual_prediction=tuple(np.full_like(p,128)for p in source)if zero.key else m.predict(reference,vectors,32)
    actual_raw=m.base.old._forward(source,actual_prediction)
    for axis,(zpred,gpred,zraw,graw,pred,coeff)in enumerate(zip(zero.prediction,grid.prediction,zero.raw_coefficients,grid.raw_coefficients,actual_prediction,actual_raw,strict=True)):
        span=32 if axis==0 else 16;bh,bw=zpred.shape[0]//8,zpred.shape[1]//8
        pixelmap=np.repeat(np.repeat(selected,span,axis=0),span,axis=1)[:zpred.shape[0],:zpred.shape[1]]
        mixed=np.where(pixelmap!=0,gpred,zpred);np.testing.assert_array_equal(mixed,pred)
        blockmap=np.repeat(np.repeat(selected,span//8,axis=0),span//8,axis=1)[:bh,:bw].reshape(-1)
        mixedraw=np.where(blockmap[:,None,None]!=0,graw,zraw);np.testing.assert_array_equal(mixedraw,coeff)
    vector=b''if zero.key else m.base.pack_vectors(vectors)
    p=replace(zero,motion_mode='block',vector_bytes=vector,prediction=actual_prediction,raw_coefficients=actual_raw)
    return p,vectors

def candidate_check(record,prepared,source,original,hud,incoming,fid,rid):
    reference=None if fid%24==0 else incoming.ref
    assert record['prepared_evidence']==prepared_hashes(prepared)
    assert record['reference_tag']==prepared.reference_tag.hex()
    vector=raw(record['vector_bytes'],HERE);assert vector==prepared.vector_bytes
    vectors=np.zeros((15,23,2),np.int8)if reference is None else m.base.unpack_vectors(vector,23,15)
    np.testing.assert_array_equal(np.frombuffer(raw(record['vector_map'],HERE),np.int8).reshape(15,23,2),vectors)
    assert record['nonzero_vectors']==int(np.count_nonzero(np.any(vectors!=0,axis=2)))
    qmap=m.roi.declared_map(720,480,n.ROIS,8,16);assert raw(record['qmap'],HERE)==m.roi.pack_map(qmap)
    coeffs,reversions=proof.selected_coefficients(prepared,qmap)
    for coeff,desc in zip(coeffs,record['coefficients'],strict=True):np.testing.assert_array_equal(coeff,np.frombuffer(raw(desc,HERE),'<i2').reshape(coeff.shape))
    work=record['proposal_work'];assert work['original_rdo_reversions']==reversions
    assert work['original_global_RDO_reversion_before_hidden']is work['intermediate_cap_deferred']is True
    intermediate,canonical,payloads,legacy=proof.expected_intermediate(prepared,qmap,coeffs,hud)
    assert raw(record['cs37_intermediate'],HERE)==intermediate
    assert record['intermediate_bytes']==work['intermediate_bytes']==len(intermediate)
    assert work['intermediate_overcap']==(len(intermediate)>49152)
    selected=[]
    assert len(record['attempts'])==3
    for axis,(attempt,coeff,safe,payload,choices)in enumerate(zip(record['attempts'],coeffs,f.f.safe_blocks(),payloads,legacy,strict=True)):
        assert attempt['plane']==axis and raw(attempt['legacy_payload'],HERE)==payload and attempt['old_bytes']==len(payload)
        assert len(attempt['trials'])==2;options=[payload]
        for compact,trial in zip((False,True),attempt['trials'],strict=True):
            assert trial['compact']==compact;encoded=raw(trial['packet'],HERE)
            expected=coeff[~safe.reshape(-1)]if compact else coeff;bw=1 if compact else(90 if axis==0 else 45)
            np.testing.assert_array_equal(proof.rxproof.adapter.decoder.decode(encoded,len(expected),bw),expected)
            option=bytes([6 if compact else 5])+encoded;assert trial['payload_bytes']==len(option);options.append(option)
        winner=proof.actual_winner(options);selected.append(options[winner]);assert attempt['selected']==winner and attempt['selected_bytes']==len(options[winner])
        detail=work['planes'][axis];assert detail['rdo_reverted']==reversions[axis]
        assert detail['fullgrid_payload_bytes']==len(choices[0])and detail['compact_payload_bytes']==len(choices[1])
        assert detail['selected_payload_bytes']==len(payload)and detail['implicit_selected']==(len(choices[1])<len(choices[0]))
    packet=raw(record['packet'],HERE);assert packet==proof.final_from_options(intermediate,selected)
    assert record['complete_bytes']==record['transcode_work']['final_bytes']==len(packet)
    fit=len(packet)<=49152;assert record['cap_fit']==record['received_on_fork']==record['transcode_work']['final_cap_fit']==fit
    assert record['transcode_work']['AB38_encode_calls']==6
    assert type(record['encode_ms'])in(int,float)and math.isfinite(record['encode_ms'])and record['encode_ms']>0
    assert record['encode_ms']>=work['encode_ms']+record['transcode_work']['transcode_ms']
    assert record['transcode_work']['transcode_ms']>=sum(t['encode_ms']for a in record['attempts']for t in a['trials'])
    probe=None
    if fit:
        probe=fork(incoming)
        with proof.rxproof.no_reencode():pixels,parts,meta,count=probe.receive(packet)
        old=proof.rxproof.adapter.Receiver();old.frozen.ref,old.frozen.rid,old.frozen.hud,old.frozen.last=incoming.ref,incoming.rid,incoming.hud,incoming.last
        oldpixels,oldparts,oldmeta,oldcount=old.receive(packet)
        proof.rxproof.equal_planes(pixels,canonical);proof.rxproof.equal_planes(pixels,oldpixels);proof.rxproof.equal_hud(parts,oldparts);proof.rxproof.equal_meta(meta,oldmeta)
        proof.rxproof.equal_planes(meta['coefficients'],coeffs);np.testing.assert_array_equal(meta['vectors'],vectors);np.testing.assert_array_equal(meta['qmap'],qmap)
        assert count==oldcount
        assert meta['reference_tag']==prepared.reference_tag and meta['reference_id']==rid
        words=[]
        for patch,(x,y,w,hh)in zip(parts,n.RECTS,strict=True):
            np.testing.assert_array_equal(patch['words'],original[y:y+hh,x:x+w]);words.append(patch['words'])
    else:
        # No public receiver is asked to accept an over-cap intermediate/final.
        pixels=canonical;words=[original[y:y+hh,x:x+w]for x,y,w,hh in n.RECTS]
    display=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(pixels)),tuple(words));quality=n.metric(original,display)
    assert quality==record['quality']and quality['hud_word_errors']==0
    assert n.digest(display)==record['display_sha256']and m.C.reference_tag(pixels).hex()==record['normalized_tag']
    return packet,quality,probe

POLICIES=('zero','mixed_score4','mixed_pareto')
def choose(outcomes):
    if set(outcomes)!=set(POLICIES):raise ValueError('exact declared actual proposal menu')
    for packet,sse in outcomes.values():
        if type(packet)is not bytes or not packet or type(sse)is not int or sse<0:raise ValueError('actual bytes and integer source SSE')
    zp,zs=outcomes['zero'];eligible=[]
    for name in POLICIES[1:]:
        packet,sse=outcomes[name]
        if len(packet)<=49152 and len(packet)<=len(zp)and sse<=zs and(len(packet)<len(zp)or sse<zs):eligible.append(name)
    if eligible:return min(eligible,key=lambda name:(len(outcomes[name][0]),outcomes[name][1],POLICIES.index(name)))
    return 'zero'if len(zp)<=49152 else None

def check_summary(summary,rows):
    accepted=[r for r in rows if r['accepted']];samples=sum(r['quality']['active_channel_samples']for r in accepted);sse=sum(r['quality']['active_squared_error']for r in accepted)
    expected=dict(attempted_frames=len(rows),accepted_frames=len(accepted),selected_counts={p:sum(r['selected_policy']==p for r in accepted)for p in POLICIES},
        complete_bytes=sum(r['complete_bytes']for r in accepted),active_squared_error=sse,active_channel_samples=samples,active_mse=sse/samples if samples else None,
        hud_word_errors=sum(r['quality']['hud_word_errors']for r in accepted),exact_hud_words=21120*len(accepted),
        fixed_zero_complete_bytes=sum(r['fixed_zero_control']['complete_bytes']for r in rows),fixed_zero_active_squared_error=sum(r['fixed_zero_control']['quality']['active_squared_error']for r in rows),
        paid_sender_ms=sum(r['paid_sender_ms']for r in rows),paid_policy_with_receive_quality_ms=sum(r['paid_policy_with_receive_quality_ms']for r in rows),
        paid_candidate_packets=3*len(rows),paid_AB38_encode_calls=18*len(rows),shared_forward_plane_calls=6*len(rows),
        selected_MB_maps={p:sum(r['macroblock_selected_counts'][p]for r in rows)for p in POLICIES[1:]},
        final_overcap_candidates=sum(not c['cap_fit']for r in rows for c in r['candidates'].values()),prefix_stopped=bool(rows and not rows[-1]['accepted']))
    assert summary==expected

def main():
    no_new_encoder();data=json.loads((HERE/'results.json').read_text());assert data['schema']=='gamebub-quantized-motion-v53'
    for name in('physical_30fps_proven','new_RTL_implemented','HEVC_AV1_superiority_proven'):assert data[name]is False
    pins=data['source_sha256']
    for path,want in pins.items():assert digest((ROOT/path).read_bytes())==want,path
    p=data['parameters'];assert(p['width'],p['height'],p['block_size'],p['chroma_MB_size'],p['key_interval'],p['roi_scale'],p['background_scale'],p['rdo_lambda'],p['proxy_lambda'],p['nonzero_MB_motion_bits'])==(720,480,32,16,24,8,16,1,4,16)
    fields=['source_YUV_SSE','fine_coefficient_bits','motion_proxy_bits']
    assert p['candidate_order']==list(POLICIES)and p['proxy_fields']==fields
    assert tuple(map(tuple,p['avoid_rects']))==n.ROIS and tuple(map(tuple,p['hud_rects']))==n.RECTS
    manifest=json.loads((proof.SOURCE/'manifest.json').read_text());controls=json.loads((proof.CONTROL/'results.json').read_text());goldens=json.loads((proof.BINARY/'results.json').read_text())
    assert len(data['cases'])==4 and {c['scene']for c in data['cases']}=={c['scene']for c in controls['cases']}
    frames=proposals=words=fixed_count=stopped=zero_goldens=0;selected_counts=dict.fromkeys(POLICIES,0);mb_counts=dict.fromkeys(POLICIES[1:],0)
    for case in data['cases']:
        assert case['requested_source_frames']==24
        source_case=next(c for c in manifest['cases']if Path(c['media_file']).stem==case['scene'])
        control=next(c for c in controls['cases']if c['scene']==case['scene']);golden=next(c for c in goldens['cases']if c['scene']==case['scene'])
        rows=case['rows'];assert 1<=len(rows)<=24 and [r['id']for r in rows]==list(range(len(rows)))
        rx,fixed=direct.Receiver(),direct.Receiver();zero_history=True
        for index,row in enumerate(rows):
            src,old,gold=source_case['frames'][index],control['rows'][index],golden['rows'][index];fid=row['id'];key=fid%24==0
            reference=None if key else rx.ref;rid=m.NO_REF if key else rx.rid;tag=bytes(16)if key else m.C.reference_tag(reference)
            assert row['key']==key and row['reference_id']==rid and row['reference_tag']==tag.hex()
            assert row['source_canvas_object']==src['canvas_rgb24']and row['source_rgb_sha256']==src['canvas_rgb_sha256']and row['source_rgb565_sha256']==src['rgb565_sha256']
            assert row['source_pts']==src['pts']and row['source_timestamp_fraction']==src['timestamp_fraction']
            canvas=np.frombuffer(raw(src['canvas_rgb24'],proof.SOURCE),np.uint8).reshape(480,720,3).copy();assert digest(canvas.tobytes())==src['canvas_rgb_sha256']
            original=m.C.corpus.rgb565(canvas).astype(np.uint16);assert digest(original.astype('<u2').tobytes())==src['rgb565_sha256']
            source=tuple(np.asarray(v,np.int16)for v in m.ft.rgb_to_planes(canvas));assert digest(b''.join(v.astype('<i2').tobytes()for v in source))==row['source_yuv_i16_sha256']
            assert row['hud_source_packet']==old['hud_packets']['HX33_selected'];hud=raw(row['hud_source_packet'],proof.CONTROL)
            assert raw(row['hud_packet'],HERE)==hud and row['hud_bytes']==len(hud)and row['shared_original_hud_generation_ms']==old['hud_generation_ms']
            zero=proof.preparation(source,reference,fid,rid,'zero');grid=proof.preparation(source,reference,fid,rid,'global_grid')
            proof.check_search(grid,source,reference,'global_grid')
            assert row['shared_prepared_evidence']==dict(zero=prepared_hashes(zero),global_grid=prepared_hashes(grid))
            shared=row['shared_analysis_work'];assert shared['shared_search_calls']==(0 if key else 1)
            assert shared['shared_forward_plane_calls']==shared['proxy_quantized_planes']==6 and shared['proxy_inverse_reconstructions']==2 and shared['macroblocks']==345
            assert shared['shared_analysis_ms']>0 and shared['shared_prepare_ms']>=shared['shared_analysis_ms']
            assert shared['source_analysis']['zero']['search']['sad_sample_operations']==0
            if not key:assert shared['source_analysis']['global_grid']['search']==grid.work['search']
            gv=np.zeros((15,23,2),np.int8)if key else m.base.unpack_vectors(grid.vector_bytes,23,15)
            assert raw(row['global_vector_bytes'],HERE)==grid.vector_bytes
            np.testing.assert_array_equal(np.frombuffer(raw(row['global_vector_map'],HERE),np.int8).reshape(15,23,2),gv)
            q=m.roi.declared_map(720,480,n.ROIS,8,16);cost=np.stack((mb_costs(source,zero,q),mb_costs(source,grid,q)),axis=2)
            assert row['macroblock_cost_shape']==[15,23,2,3]and row['macroblock_cost_fields']==fields
            np.testing.assert_array_equal(np.frombuffer(raw(row['macroblock_costs'],HERE),'<i8').reshape(15,23,2,3),cost)
            amap,bmap=selectors(cost);maps=dict(zip(POLICIES[1:],(amap,bmap),strict=True));prepared={'zero':zero}
            assert set(row['macroblock_maps'])==set(row['macroblock_selected_counts'])==set(POLICIES[1:])
            for name in POLICIES[1:]:
                archive=np.frombuffer(raw(row['macroblock_maps'][name],HERE),np.uint8).reshape(15,23)
                np.testing.assert_array_equal(archive,maps[name]);assert row['macroblock_selected_counts'][name]==int(maps[name].sum());mb_counts[name]+=int(maps[name].sum())
                prepared[name],actual_vectors=materialize(source,reference,zero,grid,maps[name])
                actual=np.frombuffer(raw(row['candidates'][name]['vector_map'],HERE),np.int8).reshape(15,23,2);np.testing.assert_array_equal(actual,actual_vectors)
                material=row['candidates'][name]['materialization_work']
                assert material['mixed_macroblocks']==int(maps[name].sum())and material['nonzero_vectors']==int(np.count_nonzero(np.any(actual_vectors!=0,axis=2)))
                assert material['shared_analysis_paid']is True and material['repeated_search_calls']==material['repeated_forward_plane_calls']==0
                assert material['prediction_array_bytes']==material['source_array_bytes']==1036800 and material['raw_coefficient_array_bytes']==4147200
                assert material['materialize_ms']>0
            assert set(row['candidates'])==set(POLICIES);before=proof.rxproof.snapshot(rx);outcomes={}
            for name in POLICIES:
                outcomes[name]=candidate_check(row['candidates'][name],prepared[name],source,original,hud,rx,fid,rid)
                proof.rxproof.unchanged(rx,before);proposals+=1
            values={name:(packet,quality['active_squared_error'])for name,(packet,quality,probe)in outcomes.items()}
            chosen=choose(values);guard={name:dict(complete_bytes=len(packet),active_source_RGB565_SSE=error)for name,(packet,error)in values.items()}
            assert row['guard']==guard and row['selected_policy']==chosen and row['accepted']==(chosen is not None)
            paid=shared['shared_prepare_ms']+sum(row['candidates'][name]['materialization_work']['materialize_ms']for name in POLICIES[1:])+sum(c['encode_ms']for c in row['candidates'].values())
            assert row['paid_sender_ms']==paid and row['paid_policy_with_receive_quality_ms']>=paid>0
            baseline_packet=raw(gold['packet'],proof.BINARY)
            if zero_history:assert outcomes['zero'][0]==baseline_packet;zero_goldens+=1
            with proof.rxproof.no_reencode():base,bhud,bmeta,_=fixed.receive(baseline_packet)
            base_display=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(base)),tuple(v['words']for v in bhud));base_quality=n.metric(original,base_display)
            assert row['fixed_zero_control']==dict(packet=gold['packet'],complete_bytes=len(baseline_packet),quality=base_quality,normalized_tag=m.C.reference_tag(base).hex())
            assert base_quality==gold['quality'];fixed_count+=1
            if chosen is None:
                assert index==len(rows)-1 and 'rejection'in row and 'packet'not in row
                proof.rxproof.unchanged(rx,before);stopped+=1;break
            packet,quality,selected=outcomes[chosen];assert selected is not None
            assert raw(row['packet'],HERE)==packet and row['packet']==row['candidates'][chosen]['packet']
            assert row['complete_bytes']==len(packet)<=49152 and row['quality']==quality
            assert row['normalized_tag']==m.C.reference_tag(selected.ref).hex()and row['display_sha256']==row['candidates'][chosen]['display_sha256']
            selected_counts[chosen]+=1;zero_history=zero_history and chosen=='zero';rx=selected;frames+=1;words+=21120
        if rows[-1]['accepted']:assert len(rows)==24
        check_summary(case['summary'],rows);summary=case['summary']
        print(json.dumps(dict(scene=case['scene'],selected_counts=summary['selected_counts'],
            bytes_delta_to_separate_zero=summary['complete_bytes']-summary['fixed_zero_complete_bytes'],
            source_SSE_delta_to_separate_zero=summary['active_squared_error']-summary['fixed_zero_active_squared_error'])),flush=True)
    assert proposals==3*(frames+stopped);no_new_encoder()
    print(json.dumps(dict(accepted_selected_frames=frames,actual_proposals=proposals,independent_AB38_alternatives=proposals*6,
        selected_reference_chains=4,separate_zero_reference_chains=4,selected_counts=selected_counts,proxy_selected_macroblocks=mb_counts,
        fixed_zero_controls=fixed_count,identical_context_zero_byte_goldens=zero_goldens,exact_selected_HUD_words=words,source_pins=len(pins),stopped_prefixes=stopped,
        new_encoder_imported=False,source_proxy_costs_and_actual_mixed_predictions_forward_rederived=True,exact_integer_source_RGB565_SSE_guard=True,
        all_losers_paid=True,global_future_nonregression_claim=False,physical_30fps_proven=False)))
if __name__=='__main__':main()
