#!/usr/bin/env python3
"""Independent same-reference local Pareto guard and selected-history replay.

Both proposal bytes and RGB565 error are measured before selection. A local
choice does not establish future quality relative to a separate zero history.
"""
from pathlib import Path
import hashlib,importlib.util,json,math,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value
proof=module('guarded50_frozen_motion47_proof',HERE.parent/'python-game-motion-v47-study/verify.py')
raw,digest=proof.raw,proof.digest
m,f,n,direct=proof.m,proof.f,proof.n,proof.direct

def no_new_encoder():
    forbidden={HERE/'model.py',HERE/'benchmark.py'}
    assert not any(Path(getattr(v,'__file__','')).resolve()in forbidden for v in list(sys.modules.values())if getattr(v,'__file__',None))

def fork(receiver):
    result=direct.Receiver();result.ref,result.rid,result.hud,result.last=receiver.ref,receiver.rid,receiver.hud,receiver.last
    return result

def choose(zero_packet,zero_sse,grid_packet,grid_sse):
    """Exact actual-byte/integer-SSE Pareto guard; full ties keep zero."""
    if any(type(p)is not bytes or not p for p in(zero_packet,grid_packet))or any(type(s)is not int or s<0 for s in(zero_sse,grid_sse)):
        raise ValueError('actual immutable packets and nonnegative integer RGB565 SSE')
    zb,gb=len(zero_packet),len(grid_packet)
    eligible=gb<=49152 and gb<=zb and grid_sse<=zero_sse and(gb<zb or grid_sse<zero_sse)
    selected='global_grid'if eligible else('zero'if zb<=49152 else None)
    return selected

def candidate_check(record,policy,source,original,hud,incoming,fid,rid):
    reference=None if fid%24==0 else incoming.ref
    prepared=proof.preparation(source,reference,fid,rid,policy);proof.check_search(prepared,source,reference,policy)
    if policy=='global_grid'and reference is not None:assert prepared.work['search']==record['analysis_work']['search']
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
    assert all(type(record[k])in(int,float)and math.isfinite(record[k])and record[k]>0 for k in('sender_ms','analysis_ms'))
    assert record['sender_ms']>=record['analysis_ms']+work['encode_ms']+record['transcode_work']['transcode_ms']
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

def check_summary(summary,rows):
    accepted=[r for r in rows if r['accepted']];samples=sum(r['quality']['active_channel_samples']for r in accepted);sse=sum(r['quality']['active_squared_error']for r in accepted)
    expected=dict(attempted_frames=len(rows),accepted_frames=len(accepted),selected_grid_frames=sum(r['selected_policy']=='global_grid'for r in accepted),
        complete_bytes=sum(r['complete_bytes']for r in accepted),active_squared_error=sse,active_channel_samples=samples,active_mse=sse/samples if samples else None,
        hud_word_errors=sum(r['quality']['hud_word_errors']for r in accepted),exact_hud_words=21120*len(accepted),
        fixed_zero_complete_bytes=sum(r['fixed_zero_control']['complete_bytes']for r in rows),
        fixed_zero_active_squared_error=sum(r['fixed_zero_control']['quality']['active_squared_error']for r in rows),
        paid_sender_ms=sum(r['paid_sender_ms']for r in rows),paid_policy_with_receive_quality_ms=sum(r['paid_policy_with_receive_quality_ms']for r in rows),
        paid_candidate_packets=2*len(rows),paid_AB38_encode_calls=12*len(rows),final_overcap_candidates=sum(not c['cap_fit']for r in rows for c in r['candidates'].values()),
        prefix_stopped=bool(rows and not rows[-1]['accepted']))
    assert summary==expected

def main():
    no_new_encoder();data=json.loads((HERE/'results.json').read_text())
    assert data['schema']=='gamebub-guarded-motion-v50'
    for name in('physical_30fps_proven','new_RTL_implemented','HEVC_AV1_superiority_proven'):assert data[name]is False
    pins=data['source_sha256']
    for path,want in pins.items():assert digest((ROOT/path).read_bytes())==want,path
    p=data['parameters'];assert(p['width'],p['height'],p['block_size'],p['key_interval'],p['roi_scale'],p['background_scale'],p['rdo_lambda'],p['final_cap'])==(720,480,32,24,8,16,1,49152)
    assert p['policies']==['zero','global_grid']and tuple(map(tuple,p['avoid_rects']))==n.ROIS and tuple(map(tuple,p['hud_rects']))==n.RECTS
    manifest=json.loads((proof.SOURCE/'manifest.json').read_text());controls=json.loads((proof.CONTROL/'results.json').read_text());goldens=json.loads((proof.BINARY/'results.json').read_text())
    assert len(data['cases'])==4 and {c['scene']for c in data['cases']}=={c['scene']for c in controls['cases']}
    frames=proposed=words=selected_grid=fixed_controls=stopped=zero_byte_goldens=smaller_grid=lower_error_grid=full_ties=0;comparisons=[]
    for case in data['cases']:
        assert case['policy']=='guarded_zero_global_grid'and case['requested_source_frames']==24
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
            assert set(row['candidates'])=={'zero','global_grid'};before=proof.rxproof.snapshot(rx);outcomes={}
            for policy in('zero','global_grid'):
                outcomes[policy]=candidate_check(row['candidates'][policy],policy,source,original,hud,rx,fid,rid)
                proof.rxproof.unchanged(rx,before);proposed+=1
            zp,zq,zrx=outcomes['zero'];gp,gq,grx=outcomes['global_grid']
            assert zq['active_channel_samples']==gq['active_channel_samples']
            zs,gs=zq['active_squared_error'],gq['active_squared_error'];chosen=choose(zp,zs,gp,gs)
            smaller_grid+=len(gp)<len(zp);lower_error_grid+=gs<zs;full_ties+=len(gp)==len(zp)and gs==zs
            assert row['guard']==dict(zero_bytes=len(zp),grid_bytes=len(gp),zero_active_sse=zs,grid_active_sse=gs)
            assert row['selected_policy']==chosen and row['accepted']==(chosen is not None)
            assert row['paid_sender_ms']==sum(c['sender_ms']for c in row['candidates'].values())
            assert row['paid_policy_with_receive_quality_ms']>=row['paid_sender_ms']>0
            # The fixed zero control has its own independently replayed history.
            baseline_packet=raw(gold['packet'],proof.BINARY)
            if zero_history:assert zp==baseline_packet;zero_byte_goldens+=1
            with proof.rxproof.no_reencode():base,bhud,bmeta,_=fixed.receive(baseline_packet)
            base_display=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(base)),tuple(p['words']for p in bhud));base_quality=n.metric(original,base_display)
            assert row['fixed_zero_control']==dict(packet=gold['packet'],complete_bytes=len(baseline_packet),quality=base_quality,normalized_tag=m.C.reference_tag(base).hex())
            assert base_quality==gold['quality'];fixed_controls+=1
            if chosen is None:
                assert index==len(rows)-1 and 'rejection'in row and 'packet'not in row
                proof.rxproof.unchanged(rx,before);stopped+=1;break
            packet,quality,selected=outcomes[chosen];assert selected is not None
            assert raw(row['packet'],HERE)==packet and row['packet']==row['candidates'][chosen]['packet']
            assert row['complete_bytes']==len(packet)<=49152 and row['quality']==quality
            assert row['normalized_tag']==m.C.reference_tag(selected.ref).hex()and row['display_sha256']==row['candidates'][chosen]['display_sha256']
            if chosen=='global_grid':assert len(gp)<=len(zp)and gs<=zs and(len(gp)<len(zp)or gs<zs);selected_grid+=1
            else:assert chosen=='zero'
            zero_history=zero_history and chosen=='zero'
            rx=selected;frames+=1;words+=21120
        if rows[-1]['accepted']:assert len(rows)==24
        check_summary(case['summary'],rows)
        summary=case['summary'];comparisons.append(dict(scene=case['scene'],selected_grid=summary['selected_grid_frames'],
            bytes_delta_to_separate_zero=summary['complete_bytes']-summary['fixed_zero_complete_bytes'],
            source_SSE_delta_to_separate_zero=summary['active_squared_error']-summary['fixed_zero_active_squared_error']))
        print(json.dumps(comparisons[-1]),flush=True)
    assert proposed==2*(frames+stopped);no_new_encoder()
    print(json.dumps(dict(accepted_selected_frames=frames,actual_proposals=proposed,independent_AB38_alternatives=proposed*6,
        selected_reference_chains=4,separate_zero_reference_chains=4,selected_grid_frames=selected_grid,fixed_zero_controls=fixed_controls,identical_context_zero_byte_goldens=zero_byte_goldens,
        strictly_smaller_grid_packets=smaller_grid,strictly_lower_error_grid_packets=lower_error_grid,full_packet_and_error_ties=full_ties,
        exact_selected_HUD_words=words,source_pins=len(pins),stopped_prefixes=stopped,new_encoder_imported=False,
        exact_integer_source_RGB565_SSE_guard=True,all_losers_paid=True,global_future_nonregression_claim=False,physical_30fps_proven=False)))
if __name__=='__main__':main()
