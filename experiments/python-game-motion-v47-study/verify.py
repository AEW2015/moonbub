#!/usr/bin/env python3
"""Independent own-reference motion qualification, without the new encoder.

Frozen global33 search is replayed against each policy's actual accepted decoded
reference. Actual CS37 and all retained arithmetic alternatives are checked;
zero and motion policies are separate causal histories, not a lossless pair.
"""
from pathlib import Path
from dataclasses import replace
import hashlib,importlib.util,json,math,struct,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SOURCE=HERE.parent/'python-game-source-v40-study'
CONTROL=HERE.parent/'python-game-control-qual-v40-study'
BINARY=HERE.parent/'python-game-binary-qual-v40-study'

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value
rxproof=module('motion47_frozen_directrx43_proof',HERE.parent/'python-game-direct-rx-v43-study/verify.py')
f,m=rxproof.f,rxproof.m;n=f.f.n
direct=rxproof.direct_module()
global_search=module('motion47_frozen_global33_search',HERE.parent/'python-game-global-v33-study/model.py')
raw,digest=rxproof.raw,rxproof.digest

def no_new_encoder():
    forbidden={HERE/'model.py',HERE/'benchmark.py'}
    assert not any(Path(getattr(v,'__file__','')).resolve()in forbidden for v in list(sys.modules.values())if getattr(v,'__file__',None))

def quiet_mask(source,reference):
    costs=np.zeros((15,23),np.int64);counts=np.zeros_like(costs)
    for plane,(src,ref)in enumerate(zip(source,reference,strict=True)):
        bs,weight=(32,1)if plane==0 else(16,2)
        for y in range(0,src.shape[0],4):
            for x in range(0,src.shape[1],4):
                costs[y//bs,x//bs]+=weight*abs(int(src[y,x])-int(ref[y,x]));counts[y//bs,x//bs]+=weight
    return costs<=2*counts

def preparation(source,reference,fid,rid,policy):
    if policy=='zero':
        return m.analyze_planes(source,reference,epoch=25,frame_id=fid,reference_id=rid,block_size=32,motion_mode='zero',penalty=0,motion_precision='half')
    if policy!='global_grid':raise ValueError('declared frozen motion policy')
    return global_search.analyze_with(m,source,reference,epoch=25,frame_id=fid,reference_id=rid,block_size=32,policy='global_grid',avoid_rects=n.ROIS)

def selected_coefficients(prepared,qmap):
    """Original RDO and whole-plane legacy-size reversion BEFORE hidden zero."""
    original=m.base._quantize(prepared.raw_coefficients,qmap,720,480)
    pruned,rdo=m.counter.rdo_skip(prepared,original,qmap,1)
    selected=[];reversions=[]
    for axis,coeff in enumerate(pruned):
        bw=90 if axis==0 else 45
        plan=m.legacy_plan(coeff,bw);reverted=False
        if not np.array_equal(coeff,original[axis]):
            prior=m.legacy_plan(original[axis],bw)
            if prior['bytes']<plan['bytes']:coeff=original[axis];reverted=True
        result=coeff.copy();result[f.f.safe_blocks()[axis].reshape(-1)]=0
        selected.append(result);reversions.append(reverted)
    return tuple(selected),reversions

def plane_payloads(coefficients):
    entropy=f.f.frozen.shared.entropy;payloads=[];options=[]
    for axis,(coeff,safe)in enumerate(zip(coefficients,f.f.safe_blocks(),strict=True)):
        bw=90 if axis==0 else 45
        plan=entropy._plane_plan(coeff,bw,m);full,*_=entropy._construct(coeff,bw,plan,m)
        visible=coeff[~safe.reshape(-1)];plan=entropy._plane_plan(visible,1,m)
        compact,*_=entropy._construct(visible,1,plan,m);compact=b'\x04'+compact
        chosen=compact if len(compact)<len(full)else full
        payloads.append(chosen);options.append((full,compact))
    return payloads,options

def expected_intermediate(prepared,qmap,coefficients,hud):
    payloads,options=plane_payloads(coefficients)
    rebuilt=m.gm.reconstruct(coefficients,prepared.prediction,qmap,720,480);canonical=f.f.normalize(rebuilt)
    quant=m.roi.pack_map(qmap);vectors=prepared.vector_bytes
    inner=rxproof.seal(m.HEADER.pack(b'GS37',m.VERSION,int(prepared.key),25,prepared.frame_id,prepared.reference_id,
        720,480,32,m.base.LIMIT,prepared.reference_tag,m.C.reference_tag(rebuilt),len(quant),len(vectors),*(len(p)for p in payloads))+quant+vectors+b''.join(payloads))
    outer=f.HEADER.pack(b'CS37',1,2+int(prepared.key),25,prepared.frame_id,prepared.reference_id,720,480,f.PROFILE,
        prepared.reference_tag,m.C.reference_tag(canonical),len(inner),len(hud))
    return rxproof.seal(outer+inner+hud),canonical,payloads,options

def check_search(prepared,source,reference,policy):
    if reference is None:return
    if policy=='zero':assert not np.any(m.base.unpack_vectors(prepared.vector_bytes,23,15));return
    work=prepared.work['search'];vectors=m.base.unpack_vectors(prepared.vector_bytes,23,15)
    quiet=quiet_mask(source,reference)
    assert work['quiet_blocks']==int(quiet.sum()) and work['active_blocks']==int((~quiet).sum())
    assert not np.any(vectors[quiet]) and not np.any(vectors%4)
    assert work['global_coarse_stride']==16 and work['local_stride']==4
    assert work['refinement_candidate_maps']==0
    assert work['candidate_vectors']==len(work['score_calls'])
    assert work['sad_sample_operations']==work['source_sample_fetches']==sum(v['samples']for v in work['score_calls'])
    assert work['reference_sample_fetches']==sum(v['reference_gathers']for v in work['score_calls'])

def actual_winner(options):
    if len(options)!=3 or any(type(p)is not bytes or not p for p in options):raise ValueError('three actual nonempty byte options')
    return min(range(3),key=lambda i:len(options[i]))

def final_from_options(intermediate,payloads):
    outer,fields,maps,_,hud=rxproof.original_parts(intermediate)
    fields[0]=b'GS38';fields[14:17]=map(len,payloads)
    inner=rxproof.seal(m.HEADER.pack(*fields)+maps+b''.join(payloads));outer[0]=b'CS38';outer[8]=direct.PROFILE;outer[11]=len(inner)
    return rxproof.seal(f.HEADER.pack(*outer)+inner+hud)

def check_summary(summary,rows):
    accepted=[r for r in rows if r['accepted']];samples=sum(r['quality']['active_channel_samples']for r in accepted);sse=sum(r['quality']['active_squared_error']for r in accepted)
    expected=dict(attempted_frames=len(rows),accepted_frames=len(accepted),rejected_frames=len(rows)-len(accepted),
        complete_bytes=sum(r['complete_bytes']for r in accepted),maximum_complete_bytes=max((r['complete_bytes']for r in accepted),default=None),
        active_squared_error=sse,active_channel_samples=samples,active_mse=sse/samples if samples else None,
        exact_hud_words=21120*len(accepted),hud_word_errors=sum(r['quality']['hud_word_errors']for r in accepted),
        intermediate_overcap_frames=sum(r['intermediate_bytes']>49152 for r in rows),final_overcap_frames=sum(r['complete_bytes']>49152 for r in rows),
        nonzero_vectors=sum(r['nonzero_vectors']for r in rows),sad_sample_operations=sum(r['analysis_work']['search']['sad_sample_operations']for r in rows),
        paid_AB38_encode_calls=6*len(rows),paid_sender_ms=sum(r['sender_ms']for r in rows),mean_sender_ms=sum(r['sender_ms']for r in rows)/len(rows),
        prefix_stopped=bool(rows and not rows[-1]['accepted']))
    assert summary==expected

def main():
    no_new_encoder();data=json.loads((HERE/'results.json').read_text())
    assert data['schema']=='gamebub-motion-v47'
    for key in('physical_30fps_proven','new_RTL_implemented','HEVC_AV1_superiority_proven'):assert data[key]is False
    pins=data['source_sha256']
    for path,want in pins.items():assert digest((ROOT/path).read_bytes())==want,path
    parameters=data['parameters']
    assert (parameters['width'],parameters['height'],parameters['block_size'],parameters['key_interval'],parameters['roi_scale'],parameters['background_scale'],parameters['rdo_lambda'],parameters['final_cap'])==(720,480,32,24,8,16,1,49152)
    assert tuple(map(tuple,parameters['avoid_rects']))==n.ROIS and tuple(map(tuple,parameters['hud_rects']))==n.RECTS
    assert parameters['global_policy']=='global_grid' and parameters['coarse_grid']==list(range(-16,17,4)) and parameters['local_offsets']==[-4,0,4]
    assert parameters['quiet_threshold']==2 and parameters['local_stride']==4 and parameters['global_coarse_stride']==16 and parameters['halfpel_refinement']is False
    manifest=json.loads((SOURCE/'manifest.json').read_text());control=json.loads((CONTROL/'results.json').read_text());goldens=json.loads((BINARY/'results.json').read_text())
    expected_cases={(c['scene'],p)for c in control['cases']for p in('zero','global_grid')}
    assert len(data['cases'])==8 and {(c['scene'],c['policy'])for c in data['cases']}==expected_cases
    attempts=accepted=stopped=golden_count=trials=motion_searches=words=overcap_intermediates=0
    for case in data['cases']:
        scene,policy=case['scene'],case['policy'];src_case=next(c for c in manifest['cases']if Path(c['media_file']).stem==scene)
        ctrl=next(c for c in control['cases']if c['scene']==scene);gold=next(c for c in goldens['cases']if c['scene']==scene)
        rows=case['rows'];assert case['requested_source_frames']==24 and 1<=len(rows)<=24
        assert [r['id']for r in rows]==list(range(len(rows)))
        rx,oracle=direct.Receiver(),rxproof.adapter.Receiver()
        for index,row in enumerate(rows):
            src,old,golden=src_case['frames'][index],ctrl['rows'][index],gold['rows'][index];fid=row['id'];key=fid%24==0
            reference=None if key else rx.ref;rid=m.NO_REF if key else rx.rid;tag=bytes(16)if key else m.C.reference_tag(reference)
            assert row['source_id']==fid==src['id'] and row['source_canvas_object']==src['canvas_rgb24']
            assert row['source_rgb_sha256']==src['canvas_rgb_sha256'] and row['source_rgb565_sha256']==src['rgb565_sha256']
            assert row['source_pts']==src['pts'] and row['source_timestamp_fraction']==src['timestamp_fraction']
            assert row['key']==key and row['reference_id']==rid and row['reference_tag']==tag.hex()
            canvas=np.frombuffer(raw(src['canvas_rgb24'],SOURCE),np.uint8).reshape(480,720,3).copy()
            assert digest(canvas.tobytes())==src['canvas_rgb_sha256']
            original=m.C.corpus.rgb565(canvas).astype(np.uint16);assert digest(original.astype('<u2').tobytes())==src['rgb565_sha256']
            source=tuple(np.asarray(p,np.int16)for p in m.ft.rgb_to_planes(canvas))
            assert digest(b''.join(p.astype('<i2').tobytes()for p in source))==row['source_yuv_i16_sha256']
            assert row['hud_source_packet']==old['hud_packets']['HX33_selected'];hud=raw(row['hud_source_packet'],CONTROL)
            assert raw(row['hud_packet'],HERE)==hud and row['hud_bytes']==len(hud)
            assert row['shared_original_hud_generation_ms']==old['hud_generation_ms']
            prepared=preparation(source,reference,fid,rid,policy);check_search(prepared,source,reference,policy)
            if policy=='global_grid'and not key:
                assert prepared.work['search']==row['analysis_work']['search'];motion_searches+=1
            vector=raw(row['vector_bytes'],HERE);assert vector==prepared.vector_bytes
            vectors=np.zeros((15,23,2),np.int8)if key else m.base.unpack_vectors(vector,23,15)
            np.testing.assert_array_equal(np.frombuffer(raw(row['vector_map'],HERE),np.int8).reshape(15,23,2),vectors)
            assert row['nonzero_vectors']==int(np.count_nonzero(np.any(vectors!=0,axis=2)))
            qmap=m.roi.declared_map(720,480,n.ROIS,8,16);assert raw(row['qmap'],HERE)==m.roi.pack_map(qmap)
            coeffs,reversions=selected_coefficients(prepared,qmap)
            assert row['proposal_work']['original_rdo_reversions']==reversions
            assert row['proposal_work']['original_global_RDO_reversion_before_hidden']is True
            assert row['proposal_work']['intermediate_cap_deferred']is True
            for c,d in zip(coeffs,row['coefficients'],strict=True):np.testing.assert_array_equal(c,np.frombuffer(raw(d,HERE),'<i2').reshape(c.shape))
            expected,canonical,payloads,legacy_options=expected_intermediate(prepared,qmap,coeffs,hud)
            intermediate=raw(row['cs37_intermediate'],HERE);assert intermediate==expected
            assert row['intermediate_bytes']==row['proposal_work']['intermediate_bytes']==len(intermediate)
            assert row['proposal_work']['intermediate_overcap']==(len(intermediate)>49152);overcap_intermediates+=len(intermediate)>49152
            chosen=[]
            for axis,(record,coeff,safe,payload,oldoptions)in enumerate(zip(row['attempts'],coeffs,f.f.safe_blocks(),payloads,legacy_options,strict=True)):
                assert record['plane']==axis and raw(record['legacy_payload'],HERE)==payload and record['old_bytes']==len(payload)
                assert len(record['trials'])==2;options=[payload]
                for compact,trial in zip((False,True),record['trials'],strict=True):
                    assert trial['compact']==compact;encoded=raw(trial['packet'],HERE)
                    wanted=coeff[~safe.reshape(-1)]if compact else coeff;bw=1 if compact else(90 if axis==0 else 45)
                    np.testing.assert_array_equal(rxproof.adapter.decoder.decode(encoded,len(wanted),bw),wanted)
                    option=bytes([6 if compact else 5])+encoded;assert trial['payload_bytes']==len(option);options.append(option);trials+=1
                winner=actual_winner(options);chosen.append(options[winner])
                assert record['selected']==winner and record['selected_bytes']==len(options[winner])
                proposal=row['proposal_work']['planes'][axis]
                assert proposal['rdo_reverted']==reversions[axis]
                assert proposal['fullgrid_payload_bytes']==len(oldoptions[0])and proposal['compact_payload_bytes']==len(oldoptions[1])
                assert proposal['selected_payload_bytes']==len(payload)and proposal['implicit_selected']==(len(oldoptions[1])<len(oldoptions[0]))
            packet=raw(row['packet'],HERE);assert packet==final_from_options(intermediate,chosen)
            assert row['complete_bytes']==row['transcode_work']['final_bytes']==len(packet)
            cap=len(packet)<=49152;assert row['cap_fit']==row['accepted']==row['transcode_work']['final_cap_fit']==cap
            assert row['transcode_work']['AB38_encode_calls']==6
            assert all(type(row[k])in(int,float)and math.isfinite(row[k])and row[k]>0 for k in('sender_ms','analysis_ms','source_read_conversion_ms'))
            assert row['sender_ms']>=row['analysis_ms']+row['proposal_work']['encode_ms']+row['transcode_work']['transcode_ms']
            assert row['transcode_work']['transcode_ms']>=sum(t['encode_ms']for a in row['attempts']for t in a['trials'])
            assert row['zero_golden_packet']==golden['packet'];attempts+=1
            if not cap:
                assert index==len(rows)-1 and 'rejection'in row and 'quality'not in row
                stopped+=1;break
            with rxproof.no_reencode():out,parts,meta,count=rx.receive(packet)
            oldout,oldparts,oldmeta,oldcount=oracle.receive(packet)
            rxproof.equal_planes(out,canonical);rxproof.equal_planes(out,oldout);rxproof.equal_hud(parts,oldparts);rxproof.equal_meta(meta,oldmeta)
            rxproof.equal_planes(meta['coefficients'],coeffs);np.testing.assert_array_equal(meta['vectors'],vectors);np.testing.assert_array_equal(meta['qmap'],qmap)
            assert count==oldcount==row['binary_planes']
            for patch,(x,y,w,hh)in zip(parts,n.RECTS,strict=True):np.testing.assert_array_equal(patch['words'],original[y:y+hh,x:x+w])
            display=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(out)),tuple(p['words']for p in parts));quality=n.metric(original,display)
            assert quality==row['quality']and quality['hud_word_errors']==0
            assert n.digest(display)==row['display_sha256']and m.C.reference_tag(out).hex()==row['normalized_tag']
            if policy=='zero':assert packet==raw(golden['packet'],BINARY);golden_count+=1
            accepted+=1;words+=21120
        if rows[-1]['accepted']:assert len(rows)==24
        check_summary(case['summary'],rows)
        print(json.dumps(dict(scene=scene,policy=policy,attempted=len(rows),accepted=case['summary']['accepted_frames'])),flush=True)
    no_new_encoder();assert trials==attempts*6 and accepted+stopped==attempts
    print(json.dumps(dict(proposed_frames=attempts,accepted_causal_frames=accepted,reference_chains=8,zero_control_byte_goldens=golden_count,
        independent_global_grid_searches=motion_searches,independent_AB38_alternatives=trials,exact_HUD_words=words,intermediate_overcap=overcap_intermediates,
        stopped_policy_prefixes=stopped,source_pins=len(pins),new_encoder_imported=False,own_histories_replayed=True,lossless_motion_vs_zero_claim=False,physical_30fps_proven=False)))
if __name__=='__main__':main()
