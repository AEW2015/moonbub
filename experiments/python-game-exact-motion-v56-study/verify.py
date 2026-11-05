#!/usr/bin/env python3
"""Independent post-RDO exact-YUV motion mixture and zero-reference induction.

No new producer import. Exact all-plane canonical output, not source SSE alone,
is the eligibility rule; the final actual-byte guard preserves zero's history.
"""
from pathlib import Path
from dataclasses import replace
import importlib.util,json,math,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value
core=module('exactmotion56_frozen53_proof',HERE.parent/'python-game-quantized-motion-v53-study/verify.py')
proof=core.proof;m,f,n,direct=core.m,core.f,core.n,core.direct
raw,digest=proof.raw,proof.digest

def no_new_encoder():
    forbidden={HERE/'model.py',HERE/'benchmark.py'}
    assert not any(Path(getattr(v,'__file__','')).resolve()in forbidden for v in list(sys.modules.values())if getattr(v,'__file__',None))

def post_bits(coefficients,vectors):
    result=np.zeros((15,23,2),np.int64)
    for axis,(coeff,safe)in enumerate(zip(coefficients,f.f.safe_blocks(),strict=True)):
        bh,bw=((60,90)if axis==0 else(30,45));span=4 if axis==0 else 2
        assert not np.any(coeff[safe.reshape(-1)])
        values=core.fine.fine_bits(coeff);values[safe.reshape(-1)]=0
        ids=((np.arange(bh)[:,None]//span)*23+np.arange(bw)[None,:]//span).reshape(-1)
        np.add.at(result[...,0].reshape(-1),ids,values)
    result[...,1]=16*np.any(vectors!=0,axis=2)
    return result

def exact_selection(zero,grid,zero_coeff,grid_coeff,grid_vectors):
    differences=np.zeros((15,23,3),np.int64)
    for by in range(15):
        for bx in range(23):
            for axis,(zp,gp)in enumerate(zip(zero,grid,strict=True)):
                span=32 if axis==0 else 16;y,x=by*span,bx*span
                differences[by,bx,axis]=np.count_nonzero(zp[y:y+span,x:x+span]!=gp[y:y+span,x:x+span])
    eligible=np.any(grid_vectors!=0,axis=2)&~np.any(differences,axis=2)
    costs=np.stack((post_bits(zero_coeff,np.zeros_like(grid_vectors)),post_bits(grid_coeff,grid_vectors)),axis=2)
    selected=eligible&(costs[:,:,1].sum(axis=2)<costs[:,:,0].sum(axis=2))
    return selected.astype(np.uint8),eligible.astype(np.uint8),differences,costs

def mix(prepared_zero,prepared_grid,zero_coeff,grid_coeff,selected,reference):
    if selected.dtype!=np.uint8 or selected.shape!=(15,23)or np.any(selected>1):raise ValueError('fixed binary exact MB map')
    grid_vectors=np.zeros((15,23,2),np.int8)if prepared_grid.key else m.base.unpack_vectors(prepared_grid.vector_bytes,23,15)
    vectors=np.where(selected[...,None]!=0,grid_vectors,0).astype(np.int8)
    prediction=tuple(np.full_like(p,128)for p in prepared_zero.prediction)if prepared_zero.key else m.predict(reference,vectors,32)
    coefficients=[]
    for axis,(cz,cg,zp,gp,actual)in enumerate(zip(zero_coeff,grid_coeff,prepared_zero.prediction,prepared_grid.prediction,prediction,strict=True)):
        span=32 if axis==0 else 16;bh,bw=zp.shape[0]//8,zp.shape[1]//8
        pixelmap=np.repeat(np.repeat(selected,span,axis=0),span,axis=1)[:zp.shape[0],:zp.shape[1]]
        np.testing.assert_array_equal(actual,np.where(pixelmap!=0,gp,zp))
        blockmap=np.repeat(np.repeat(selected,span//8,axis=0),span//8,axis=1)[:bh,:bw].reshape(-1)
        coefficients.append(np.where(blockmap[:,None,None]!=0,cg,cz).astype(np.int16))
    vector_bytes=b''if prepared_zero.key else m.base.pack_vectors(vectors)
    prepared=replace(prepared_zero,prediction=prediction,vector_bytes=vector_bytes,motion_mode='block')
    return prepared,tuple(coefficients),vectors

def choose(zero,candidate):
    if type(zero)is not bytes or type(candidate)is not bytes or not zero or not candidate or len(zero)>49152:raise ValueError('actual packets and qualified fitting zero')
    return 'mixed'if len(candidate)<=49152 and len(candidate)<len(zero)else'zero'

def source_check(record,prepared,source,original,hud,incoming,fid,rid):
    reference=None if fid%24==0 else incoming.ref
    assert record['prediction_sha256']==digest(b''.join(v.astype('<i2').tobytes()for v in prepared.prediction))
    vector=raw(record['vector_bytes'],HERE);assert vector==prepared.vector_bytes
    vectors=np.zeros((15,23,2),np.int8)if reference is None else m.base.unpack_vectors(vector,23,15)
    np.testing.assert_array_equal(np.frombuffer(raw(record['vector_map'],HERE),np.int8).reshape(15,23,2),vectors)
    qmap=m.roi.declared_map(720,480,n.ROIS,8,16)
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
    fit=len(packet)<=49152;assert record['cap_fit']==record['transcode_work']['final_cap_fit']==fit;assert fit
    assert record['transcode_work']['AB38_encode_calls']==6
    assert type(record['encode_ms'])in(int,float)and math.isfinite(record['encode_ms'])and record['encode_ms']>0
    assert record['encode_ms']>=work['encode_ms']+record['transcode_work']['transcode_ms']
    assert record['transcode_work']['transcode_ms']>=sum(t['encode_ms']for a in record['attempts']for t in a['trials'])
    probe=None
    if fit:
        probe=core.fork(incoming)
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
    return packet,quality,probe,coeffs

def mixed_check(record,prepared,coeffs,vectors,q,hud,incoming,original,zero_normalized):
    for coeff,desc in zip(coeffs,record['coefficients'],strict=True):np.testing.assert_array_equal(coeff,np.frombuffer(raw(desc,HERE),'<i2').reshape(coeff.shape))
    assert raw(record['vector_bytes'],HERE)==prepared.vector_bytes
    np.testing.assert_array_equal(np.frombuffer(raw(record['vector_map'],HERE),np.int8).reshape(15,23,2),vectors)
    assert record['prediction_sha256']==digest(b''.join(v.astype('<i2').tobytes()for v in prepared.prediction))
    intermediate,canonical,legacy,options=proof.expected_intermediate(prepared,q,coeffs,hud)
    proof.rxproof.equal_planes(canonical,zero_normalized);selected=[]
    for axis,(attempt,coeff,safe,old,pair)in enumerate(zip(record['attempts'],coeffs,f.f.safe_blocks(),legacy,options,strict=True)):
        assert attempt['plane']==axis and raw(attempt['legacy_payload'],HERE)==old and attempt['old_bytes']==len(old)
        assert attempt['fullgrid_legacy_bytes']==len(pair[0])and attempt['compact_legacy_bytes']==len(pair[1]);choices=[old]
        assert len(attempt['trials'])==2
        for compact,trial in zip((False,True),attempt['trials'],strict=True):
            assert trial['compact']==compact;encoded=raw(trial['packet'],HERE);expected=coeff[~safe.reshape(-1)]if compact else coeff
            width=1 if compact else(90 if axis==0 else 45)
            np.testing.assert_array_equal(proof.rxproof.adapter.decoder.decode(encoded,len(expected),width),expected)
            payload=bytes([6 if compact else 5])+encoded;assert trial['payload_bytes']==len(payload);choices.append(payload)
        winner=proof.actual_winner(choices);selected.append(choices[winner]);assert attempt['selected']==winner and attempt['selected_bytes']==len(choices[winner])
    packet=raw(record['packet'],HERE);assert packet==proof.final_from_options(intermediate,selected)
    assert record['complete_bytes']==len(packet)and record['cap_fit']==(len(packet)<=49152)
    work=record['serialize_work']
    assert work['source_quantize_calls']==work['source_RDO_calls']==work['source_reversion_calls']==0
    assert work['legacy_plane_plans']==work['AB38_encode_calls']==6 and work['legacy_plane_constructions']==3 and work['output_inverse_reconstructions']==1 and work['canonical_output_exact_zero']is True
    assert work['serialize_ms']>=sum(t['encode_ms']for a in record['attempts']for t in a['trials'])
    probe=None
    if len(packet)<=49152:
        probe=core.fork(incoming)
        with proof.rxproof.no_reencode():pixels,parts,meta,count=probe.receive(packet)
        old=proof.rxproof.adapter.Receiver();old.frozen.ref,old.frozen.rid,old.frozen.hud,old.frozen.last=incoming.ref,incoming.rid,incoming.hud,incoming.last
        oldpixels,oldparts,oldmeta,oldcount=old.receive(packet)
        proof.rxproof.equal_planes(pixels,canonical);proof.rxproof.equal_planes(pixels,oldpixels);proof.rxproof.equal_hud(parts,oldparts);proof.rxproof.equal_meta(meta,oldmeta)
        proof.rxproof.equal_planes(meta['coefficients'],coeffs);np.testing.assert_array_equal(meta['vectors'],vectors);np.testing.assert_array_equal(meta['qmap'],q)
        assert count==oldcount;words=tuple(v['words']for v in parts)
    else:pixels=canonical;words=tuple(original[y:y+hh,x:x+w]for x,y,w,hh in n.RECTS)
    display=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(pixels)),words);quality=n.metric(original,display)
    assert quality==record['quality']and quality['hud_word_errors']==0
    assert n.digest(display)==record['display_sha256']and m.C.reference_tag(pixels).hex()==record['normalized_tag']
    return packet,quality,probe

def check_summary(summary,rows):
    samples=sum(r['quality']['active_channel_samples']for r in rows);sse=sum(r['quality']['active_squared_error']for r in rows)
    expected=dict(frames=len(rows),selected_mixed_frames=sum(r['selected_policy']=='mixed'for r in rows),
        complete_bytes=sum(r['complete_bytes']for r in rows),fixed_zero_complete_bytes=sum(r['fixed_zero_control']['complete_bytes']for r in rows),
        active_squared_error=sse,active_channel_samples=samples,active_mse=sse/samples,exact_hud_words=21120*len(rows),hud_word_errors=sum(r['quality']['hud_word_errors']for r in rows),
        nonzero_grid_MB=sum(r['nonzero_grid_MB']for r in rows),eligible_MB=sum(r['selection_work']['eligible_nonzero_MB']for r in rows),proxy_selected_MB=sum(r['selection_work']['selected_MB']for r in rows),
        paid_AB38_encode_calls=18*len(rows),source_RDO_calls=2*len(rows),mixed_RDO_calls=0,paid_sender_ms=sum(r['paid_sender_ms']for r in rows),
        paid_policy_with_receive_quality_ms=sum(r['paid_policy_with_receive_quality_ms']for r in rows),final_overcap_candidates=sum(not p['cap_fit']for r in rows for p in r['proposals'].values()))
    assert summary==expected

def main():
    no_new_encoder();data=json.loads((HERE/'results.json').read_text());assert data['schema']=='gamebub-exact-motion-v56'
    for name in('physical_30fps_proven','new_RTL_implemented','HEVC_AV1_superiority_proven'):assert data[name]is False
    pins=data['source_sha256']
    for path,want in pins.items():assert digest((ROOT/path).read_bytes())==want,path
    p=data['parameters'];assert(p['width'],p['height'],p['block_size'],p['chroma_MB_size'],p['key_interval'],p['roi_scale'],p['background_scale'],p['rdo_lambda'])==(720,480,32,16,24,8,16,1)
    assert tuple(map(tuple,p['avoid_rects']))==n.ROIS and tuple(map(tuple,p['hud_rects']))==n.RECTS
    manifest=json.loads((proof.SOURCE/'manifest.json').read_text());controls=json.loads((proof.CONTROL/'results.json').read_text());goldens=json.loads((proof.BINARY/'results.json').read_text())
    assert len(data['cases'])==4 and {c['scene']for c in data['cases']}=={c['scene']for c in controls['cases']}
    frames=eligible_count=proxy_count=accepted_mixed=words=0
    for case in data['cases']:
        source_case=next(c for c in manifest['cases']if Path(c['media_file']).stem==case['scene']);control=next(c for c in controls['cases']if c['scene']==case['scene']);golden=next(c for c in goldens['cases']if c['scene']==case['scene'])
        rows=case['rows'];assert len(rows)==24 and [r['id']for r in rows]==list(range(24));rx,fixed=direct.Receiver(),direct.Receiver()
        for index,row in enumerate(rows):
            src,old,gold=source_case['frames'][index],control['rows'][index],golden['rows'][index];fid=row['id'];key=fid%24==0
            assert rx.rid==fixed.rid and rx.last==fixed.last
            if not key:proof.rxproof.equal_planes(rx.ref,fixed.ref);proof.rxproof.equal_hud(rx.hud,fixed.hud)
            reference=None if key else rx.ref;rid=m.NO_REF if key else rx.rid;tag=bytes(16)if key else m.C.reference_tag(reference)
            assert row['key']==key and row['reference_id']==rid and row['reference_tag']==tag.hex()
            assert row['source_canvas_object']==src['canvas_rgb24']and row['source_rgb_sha256']==src['canvas_rgb_sha256']and row['source_rgb565_sha256']==src['rgb565_sha256']
            assert row['source_pts']==src['pts']and row['source_timestamp_fraction']==src['timestamp_fraction']
            canvas=np.frombuffer(raw(src['canvas_rgb24'],proof.SOURCE),np.uint8).reshape(480,720,3).copy();assert digest(canvas.tobytes())==src['canvas_rgb_sha256']
            original=m.C.corpus.rgb565(canvas).astype(np.uint16);assert digest(original.astype('<u2').tobytes())==src['rgb565_sha256']
            source=tuple(np.asarray(v,np.int16)for v in m.ft.rgb_to_planes(canvas));assert digest(b''.join(v.astype('<i2').tobytes()for v in source))==row['source_yuv_i16_sha256']
            assert row['hud_source_packet']==old['hud_packets']['HX33_selected'];hud=raw(row['hud_source_packet'],proof.CONTROL)
            assert raw(row['hud_packet'],HERE)==hud and row['hud_bytes']==len(hud)and row['shared_original_hud_generation_ms']==old['hud_generation_ms']
            q=m.roi.declared_map(720,480,n.ROIS,8,16);assert raw(row['qmap'],HERE)==m.roi.pack_map(q)
            pz=proof.preparation(source,reference,fid,rid,'zero');pg=proof.preparation(source,reference,fid,rid,'global_grid');proof.check_search(pg,source,reference,'global_grid')
            assert set(row['proposals'])=={'zero','global_grid','mixed'}
            if not key:assert row['proposals']['global_grid']['analysis_work']['search']==pg.work['search']
            before=proof.rxproof.snapshot(rx)
            zero=source_check(row['proposals']['zero'],pz,source,original,hud,rx,fid,rid);proof.rxproof.unchanged(rx,before)
            grid=source_check(row['proposals']['global_grid'],pg,source,original,hud,rx,fid,rid);proof.rxproof.unchanged(rx,before)
            zp,zq,zrx,zc=zero;gp,gq,grx,gc=grid;assert zrx is not None and grx is not None
            gv=np.zeros((15,23,2),np.int8)if key else m.base.unpack_vectors(pg.vector_bytes,23,15)
            np.testing.assert_array_equal(np.frombuffer(raw(row['global_vector_map'],HERE),np.int8).reshape(15,23,2),gv)
            assert row['nonzero_grid_MB']==int(np.count_nonzero(np.any(gv!=0,axis=2)))
            selected,eligible,difference,cost=exact_selection(zrx.ref,grx.ref,zc,gc,gv)
            np.testing.assert_array_equal(np.frombuffer(raw(row['eligible_macroblocks'],HERE),np.uint8).reshape(15,23),eligible)
            np.testing.assert_array_equal(np.frombuffer(raw(row['selected_macroblocks'],HERE),np.uint8).reshape(15,23),selected)
            assert row['difference_shape']==[15,23,3]and row['cost_shape']==[15,23,2,2]and row['cost_fields']==['post_RDO_visible_fine_bits','nonzero_MV_proxy_bits']
            np.testing.assert_array_equal(np.frombuffer(raw(row['canonical_difference_counts'],HERE),'<i8').reshape(15,23,3),difference)
            np.testing.assert_array_equal(np.frombuffer(raw(row['macroblock_costs'],HERE),'<i8').reshape(15,23,2,2),cost)
            sw=row['selection_work'];assert sw['eligible_nonzero_MB']==int(eligible.sum())and sw['selected_MB']==int(selected.sum())and sw['fine_bits_post_RDO']is sw['hidden_bits_excluded']is True and sw['motion_proxy_bits']==16
            pm,mc,mv=mix(pz,pg,zc,gc,selected,reference)
            mixwork=row['mix_work'];assert mixwork['post_RDO_coefficient_mixture']is True
            for name in('source_quantize_calls','source_RDO_calls','source_reversion_calls','source_forward_calls'):assert mixwork[name]==0
            mixed=mixed_check(row['proposals']['mixed'],pm,mc,mv,q,hud,rx,original,zrx.ref);proof.rxproof.unchanged(rx,before)
            cp,cq,crx=mixed;assert cq==zq;chosen=choose(zp,cp);assert row['selected_policy']==chosen
            packet,quality,chosen_rx=(zp,zq,zrx)if chosen=='zero'else mixed;assert chosen_rx is not None
            assert raw(row['packet'],HERE)==packet and row['packet']==row['proposals'][chosen]['packet']and row['complete_bytes']==len(packet)<=49152
            assert row['quality']==quality and row['normalized_tag']==m.C.reference_tag(chosen_rx.ref).hex()and row['display_sha256']==row['proposals'][chosen]['display_sha256']
            paid=row['shared_analysis_ms']+row['proposals']['zero']['encode_ms']+row['proposals']['global_grid']['encode_ms']+sw['selection_ms']+mixwork['materialize_ms']+row['proposals']['mixed']['serialize_work']['serialize_ms']
            assert row['paid_sender_ms']==paid and row['paid_policy_with_receive_quality_ms']>=paid>0
            baseline=raw(gold['packet'],proof.BINARY);assert zp==baseline
            with proof.rxproof.no_reencode():base,bhud,bmeta,_=fixed.receive(baseline)
            proof.rxproof.equal_planes(chosen_rx.ref,base);proof.rxproof.equal_hud(chosen_rx.hud,bhud)
            display=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(base)),tuple(v['words']for v in bhud));base_quality=n.metric(original,display)
            assert row['fixed_zero_control']==dict(packet=gold['packet'],complete_bytes=len(baseline),quality=base_quality,normalized_tag=m.C.reference_tag(base).hex())
            assert quality==base_quality==gold['quality']and n.digest(display)==row['display_sha256']==gold['display_sha256']
            rx=chosen_rx;frames+=1;eligible_count+=int(eligible.sum());proxy_count+=int(selected.sum());accepted_mixed+=chosen=='mixed';words+=21120
        check_summary(case['summary'],rows)
        print(json.dumps(dict(scene=case['scene'],eligible_MB=case['summary']['eligible_MB'],proxy_selected_MB=case['summary']['proxy_selected_MB'],selected_mixed=case['summary']['selected_mixed_frames'],bytes_saved=case['summary']['fixed_zero_complete_bytes']-case['summary']['complete_bytes'])),flush=True)
    assert frames==96;no_new_encoder()
    print(json.dumps(dict(exact_causal_selected_frames=frames,source_proposals=frames*2,mixed_proposals=frames,independent_AB38_alternatives=frames*18,
        exact_zero_byte_goldens=frames,exact_future_reference_induction=True,eligible_nonzero_MB=eligible_count,proxy_selected_MB=proxy_count,accepted_mixed=accepted_mixed,
        exact_selected_HUD_words=words,source_pins=len(pins),new_encoder_imported=False,mixed_quantization_or_RDO_reapplied=False,physical_30fps_proven=False)))
if __name__=='__main__':main()
