#!/usr/bin/env python3
"""Exact canonical reference induction with post-RDO coefficient mixtures."""
import json,platform,time
import numpy as np
import helpers as h
model=h.bound('exactmotion56_owned_model',h.HERE/'model.py',h)

def fork(rx):
    probe=h.rx.Receiver();probe.ref,probe.rid,probe.hud,probe.last=rx.ref,rx.rid,rx.hud,rx.last;return probe

def options_archive(options):
    result=[]
    for option in options:
        out=dict(option);out['legacy_payload']=h.blob(out['legacy_payload']);out['trials']=[]
        for trial in option['trials']:
            t=dict(trial);t['packet']=h.blob(t['packet']);out['trials'].append(t)
        result.append(out)
    return result

def archive(p,quality,display_hash,kind):
    result=dict(packet=h.blob(p['packet']),complete_bytes=len(p['packet']),cap_fit=len(p['packet'])<=49152,
        coefficients=[h.blob(c.astype('<i2').tobytes())for c in p['coefficients']],normalized_tag=h.m.C.reference_tag(p['normalized']).hex(),
        quality=quality,display_sha256=display_hash,attempts=options_archive(p['attempts']))
    if kind=='mixed':
        result.update(vector_bytes=h.blob(p['vector_bytes']),vector_map=h.blob(p['vectors'].tobytes()),serialize_work=p['serialize_work'],
            prediction_sha256=h.digest(b''.join(v.astype('<i2').tobytes()for v in p['prediction'])))
    else:
        prep=p['prepared'];mw,mh=h.m.base._grid(720,480,32);vectors=np.zeros((mh,mw,2),np.int8)if prep.key else h.m.base.unpack_vectors(prep.vector_bytes,mw,mh)
        result.update(cs37_intermediate=h.blob(p['cs37']),intermediate_bytes=len(p['cs37']),vector_bytes=h.blob(prep.vector_bytes),vector_map=h.blob(vectors.tobytes()),
            proposal_work=p['proposal_work'],transcode_work=p['transcode_work'],encode_ms=p['encode_ms'],analysis_work=prep.work,
            prediction_sha256=h.digest(b''.join(v.astype('<i2').tobytes()for v in prep.prediction)))
    return result

def summary(rows):
    n=sum(r['quality']['active_channel_samples']for r in rows);sse=sum(r['quality']['active_squared_error']for r in rows)
    return dict(frames=len(rows),selected_mixed_frames=sum(r['selected_policy']=='mixed'for r in rows),
        complete_bytes=sum(r['complete_bytes']for r in rows),fixed_zero_complete_bytes=sum(r['fixed_zero_control']['complete_bytes']for r in rows),
        active_squared_error=sse,active_channel_samples=n,active_mse=sse/n,
        exact_hud_words=21120*len(rows),hud_word_errors=sum(r['quality']['hud_word_errors']for r in rows),
        nonzero_grid_MB=sum(r['nonzero_grid_MB']for r in rows),eligible_MB=sum(r['selection_work']['eligible_nonzero_MB']for r in rows),
        proxy_selected_MB=sum(r['selection_work']['selected_MB']for r in rows),
        paid_AB38_encode_calls=18*len(rows),source_RDO_calls=2*len(rows),mixed_RDO_calls=0,
        paid_sender_ms=sum(r['paid_sender_ms']for r in rows),paid_policy_with_receive_quality_ms=sum(r['paid_policy_with_receive_quality_ms']for r in rows),
        final_overcap_candidates=sum(not p['cap_fit']for r in rows for p in r['proposals'].values()))

def main():
    manifest=h.load(h.SOURCE/'manifest.json');controls=h.load(h.CONTROL/'results.json');goldens=h.load(h.GOLDEN/'results.json');cases=[]
    for source_case,control_case,golden_case in zip(manifest['cases'],controls['cases'],goldens['cases'],strict=True):
        scene=control_case['scene'];rx=h.rx.Receiver();rows=[]
        for f,c,gold in zip(source_case['frames'][:24],control_case['rows'][:24],golden_case['rows'][:24],strict=True):
            fid=f['id'];key=fid%24==0;rid=h.m.NO_REF if key else rx.rid;reference=None if key else rx.ref
            t=time.perf_counter_ns();canvas=np.frombuffer(h.raw(f['canvas_rgb24'],h.SOURCE),np.uint8).reshape(480,720,3).copy()
            original=h.m.C.corpus.rgb565(canvas).astype(np.uint16);source=tuple(v.astype(np.int16)for v in h.m.ft.rgb_to_planes(canvas));read_ms=(time.perf_counter_ns()-t)/1e6
            assert h.digest(canvas.tobytes())==f['canvas_rgb_sha256'];assert h.digest(original.astype('<u2').tobytes())==f['rgb565_sha256']
            source_hash=h.digest(b''.join(p.astype('<i2').tobytes()for p in source));hud=h.raw(c['hud_packets']['HX33_selected'],h.CONTROL)
            began=time.perf_counter_ns();start=time.perf_counter_ns()
            pz=h.analysis.analyze_planes(source,reference,frame_id=fid,reference_id=rid)
            pg=h.global_search.analyze_with(h.m,source,reference,frame_id=fid,reference_id=rid,policy='global_grid',avoid_rects=h.n.ROIS)
            analysis_ms=(time.perf_counter_ns()-start)/1e6;q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
            zero=model.source_proposal(pz,q,hud);grid=model.source_proposal(pg,q,hud)
            assert zero['packet']==h.raw(gold['packet'],h.GOLDEN)
            probes={};outputs={}
            for name,p in(('zero',zero),('global_grid',grid)):
                assert len(p['packet'])<=49152,'known fitting source prefix changed'
                probe=fork(rx);pixels,patches,meta,count=probe.receive(p['packet']);probes[name]=probe;outputs[name]=(pixels,patches)
                for a,b in zip(pixels,p['normalized'],strict=True):np.testing.assert_array_equal(a,b)
                for a,b in zip(meta['coefficients'],p['coefficients'],strict=True):np.testing.assert_array_equal(a,b)
            mw,mh=h.m.base._grid(720,480,32);vectors=np.zeros((mh,mw,2),np.int8)if key else h.m.base.unpack_vectors(pg.vector_bytes,mw,mh)
            chosen_MB,eligible,diffs,costs,selection_work=model.selection(zero,grid,vectors)
            coeff,pred,mixed_vectors,mix_work=model.mix(zero,grid,chosen_MB,vectors)
            mixed=model.serialize(pz,coeff,pred,mixed_vectors,q,hud,zero['normalized'])
            if len(mixed['packet'])<=49152:
                probe=fork(rx);pixels,patches,meta,count=probe.receive(mixed['packet']);probes['mixed']=probe;outputs['mixed']=(pixels,patches)
                for a,b in zip(pixels,zero['normalized'],strict=True):np.testing.assert_array_equal(a,b)
                for a,b in zip(meta['coefficients'],coeff,strict=True):np.testing.assert_array_equal(a,b)
            else:outputs['mixed']=(mixed['normalized'],outputs['zero'][1])
            quality={};display_hash={}
            for name,(pixels,patches)in outputs.items():
                for patch,(x,y,w,hh)in zip(patches,h.n.RECTS,strict=True):np.testing.assert_array_equal(patch['words'],original[y:y+hh,x:x+w])
                display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),tuple(p['words']for p in patches))
                quality[name]=h.n.metric(original,display);display_hash[name]=h.n.digest(display)
            assert quality['mixed']==quality['zero'];assert display_hash['mixed']==display_hash['zero']==gold['display_sha256']
            selected=model.choose(len(zero['packet']),len(mixed['packet']));rx=probes[selected]
            assert h.m.C.reference_tag(rx.ref).hex()==gold['normalized_tag']
            assert source_hash==h.digest(b''.join(p.astype('<i2').tobytes()for p in source))
            paid_policy_ms=(time.perf_counter_ns()-began)/1e6
            proposals={name:archive(p,quality[name],display_hash[name],name)for name,p in(('zero',zero),('global_grid',grid),('mixed',mixed))}
            take=proposals[selected]
            row=dict(id=fid,key=key,reference_id=rid,reference_tag=pz.reference_tag.hex(),source_canvas_object=f['canvas_rgb24'],source_rgb_sha256=f['canvas_rgb_sha256'],source_rgb565_sha256=f['rgb565_sha256'],
                source_yuv_i16_sha256=source_hash,source_pts=f['pts'],source_timestamp_fraction=f['timestamp_fraction'],source_read_conversion_ms=read_ms,
                hud_source_packet=c['hud_packets']['HX33_selected'],hud_packet=h.blob(hud),hud_bytes=len(hud),shared_original_hud_generation_ms=c['hud_generation_ms'],
                shared_analysis_ms=analysis_ms,qmap=h.blob(h.m.roi.pack_map(q)),global_vector_map=h.blob(vectors.tobytes()),nonzero_grid_MB=int(np.count_nonzero(np.any(vectors!=0,axis=2))),
                eligible_macroblocks=h.blob(eligible.astype(np.uint8).tobytes()),selected_macroblocks=h.blob(chosen_MB.astype(np.uint8).tobytes()),
                canonical_difference_counts=h.blob(diffs.astype('<i8').tobytes()),difference_shape=list(diffs.shape),
                macroblock_costs=h.blob(costs.astype('<i8').tobytes()),cost_shape=list(costs.shape),cost_fields=['post_RDO_visible_fine_bits','nonzero_MV_proxy_bits'],
                selection_work=selection_work,mix_work=mix_work,proposals=proposals,selected_policy=selected,packet=take['packet'],complete_bytes=take['complete_bytes'],quality=take['quality'],
                normalized_tag=take['normalized_tag'],display_sha256=take['display_sha256'],
                paid_sender_ms=analysis_ms+zero['encode_ms']+grid['encode_ms']+selection_work['selection_ms']+mix_work['materialize_ms']+mixed['serialize_work']['serialize_ms'],
                paid_policy_with_receive_quality_ms=paid_policy_ms,
                fixed_zero_control=dict(packet=gold['packet'],complete_bytes=gold['complete_bytes'],quality=gold['quality'],normalized_tag=gold['normalized_tag']))
            rows.append(row);print(json.dumps(dict(scene=scene,frame=fid,eligible=selection_work['eligible_nonzero_MB'],proxy_MB=selection_work['selected_MB'],zero=len(zero['packet']),mixed=len(mixed['packet']),selected=selected)),flush=True)
        cases.append(dict(scene=scene,rows=rows,summary=summary(rows)));print(json.dumps(dict(scene=scene,summary=cases[-1]['summary'])),flush=True)
    result=dict(schema='gamebub-exact-motion-v56',source_sha256=h.pins(),cases=cases,
        parameters=dict(width=720,height=480,block_size=32,chroma_MB_size=16,key_interval=24,roi_scale=8,background_scale=16,rdo_lambda=1,avoid_rects=h.n.ROIS,hud_rects=h.n.RECTS,
            eligibility='nonzero gridMV AND all canonical normalized YUV samples across full/partial MB slices exactly zero proposal',
            proxy='postRDO fine39 visible coefficientbits+16bits/nonzeroMB; grid onlystrictlysmaller; tieszero',
            mixture='alreadyselectedpostRDO coeffs andprediction; NO quantize/RDO/globalreversion rerun',final_guard='mixed canonicaloutput exactzero AND completebytesstrictlysmaller AND <=49152; elsezero'),
        physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        scope=['All96 first24sourceframes; bothactualsourcezero/globalproposals andpostRDOmixedcandidate retained, all18AB38options/frame paid.',
            'Exactcanonicalreference equality at every acceptedframe keepsfuturehistory identicalzero40 byinduction; sourceRGB565quality/HUD/display remainexact.',
            'Serializer invokeslegacyentropyplans/construction andAB38/reconstruction only; sourcequantize/RDO/reversion excluded andforbidden in scopedtests.',
            'Paidpolicy includes sourceanalysis/2sourceencodes/selection/mixedserialization/receives/qualitychecks; sourceconversion/sharedpriorHUD/archiveIO separate. NoFPS/nativefrontier/hardwareclaim.'])
    (h.HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
