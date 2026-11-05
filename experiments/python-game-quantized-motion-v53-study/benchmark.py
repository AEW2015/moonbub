#!/usr/bin/env python3
"""Shared analyses, two quantized MB selectors, actual whole-packet admission."""
import json,platform,time
import numpy as np
import helpers as h
model=h.bound('quantmotion53_owned_model',h.HERE/'model.py',h)

def fork(rx):
    out=h.rx.Receiver();out.ref,out.rid,out.hud,out.last=rx.ref,rx.rid,rx.hud,rx.last;return out

def hashes(p):
    return dict(prediction_sha256=h.digest(b''.join(v.astype('<i2').tobytes()for v in p.prediction)),
        raw_coefficients_sha256=h.digest(b''.join(v.astype('<i2').tobytes()for v in p.raw_coefficients)),
        source_sha256=h.digest(b''.join(v.astype('<i2').tobytes()for v in p.source)))

def archive_candidate(p,quality,display_sha,received,materialization):
    prepared=p['prepared'];mw,mh=h.m.base._grid(720,480,32)
    vectors=np.zeros((mh,mw,2),np.int8)if prepared.key else h.m.base.unpack_vectors(prepared.vector_bytes,mw,mh)
    options=[]
    for option in p['attempts']:
        row=dict(option);row['legacy_payload']=h.blob(row['legacy_payload']);row['trials']=[]
        for trial in option['trials']:
            t=dict(trial);t['packet']=h.blob(t['packet']);row['trials'].append(t)
        options.append(row)
    return dict(packet=h.blob(p['packet']),complete_bytes=len(p['packet']),cap_fit=len(p['packet'])<=49152,
        cs37_intermediate=h.blob(p['cs37']),intermediate_bytes=len(p['cs37']),coefficients=[h.blob(v.astype('<i2').tobytes())for v in p['coefficients']],
        qmap=h.blob(h.m.roi.pack_map(h.m.roi.declared_map(720,480,h.n.ROIS,8,16))),vector_bytes=h.blob(prepared.vector_bytes),vector_map=h.blob(vectors.tobytes()),
        nonzero_vectors=int(np.count_nonzero(np.any(vectors!=0,axis=2))),reference_tag=prepared.reference_tag.hex(),
        normalized_tag=h.m.C.reference_tag(p['normalized']).hex(),quality=quality,display_sha256=display_sha,received_on_fork=received,
        prepared_evidence=hashes(prepared),materialization_work=materialization,proposal_work=p['proposal_work'],transcode_work=p['transcode_work'],
        encode_ms=p['encode_ms'],attempts=options)

def summary(rows):
    accepted=[r for r in rows if r['accepted']];n=sum(r['quality']['active_channel_samples']for r in accepted);sse=sum(r['quality']['active_squared_error']for r in accepted)
    return dict(attempted_frames=len(rows),accepted_frames=len(accepted),selected_counts={p:sum(r['selected_policy']==p for r in accepted)for p in model.POLICIES},
        complete_bytes=sum(r['complete_bytes']for r in accepted),active_squared_error=sse,active_channel_samples=n,active_mse=sse/n if n else None,
        hud_word_errors=sum(r['quality']['hud_word_errors']for r in accepted),exact_hud_words=21120*len(accepted),
        fixed_zero_complete_bytes=sum(r['fixed_zero_control']['complete_bytes']for r in rows),
        fixed_zero_active_squared_error=sum(r['fixed_zero_control']['quality']['active_squared_error']for r in rows),
        paid_sender_ms=sum(r['paid_sender_ms']for r in rows),paid_policy_with_receive_quality_ms=sum(r['paid_policy_with_receive_quality_ms']for r in rows),
        paid_candidate_packets=3*len(rows),paid_AB38_encode_calls=18*len(rows),shared_forward_plane_calls=6*len(rows),
        selected_MB_maps={p:sum(r['macroblock_selected_counts'][p]for r in rows)for p in model.POLICIES[1:]},
        final_overcap_candidates=sum(not c['cap_fit']for r in rows for c in r['candidates'].values()),prefix_stopped=bool(rows and not rows[-1]['accepted']))

def main():
    manifest=h.load(h.SOURCE/'manifest.json');controls=h.load(h.CONTROL/'results.json');goldens=h.load(h.GOLDEN/'results.json');cases=[]
    for source_case,control_case,golden_case in zip(manifest['cases'],controls['cases'],goldens['cases'],strict=True):
        scene=control_case['scene'];rx=h.rx.Receiver();rows=[]
        for source_row,control_row,golden_row in zip(source_case['frames'][:24],control_case['rows'][:24],golden_case['rows'][:24],strict=True):
            fid=source_row['id'];key=fid%24==0;rid=h.m.NO_REF if key else rx.rid;reference=None if key else rx.ref
            t=time.perf_counter_ns();canvas=np.frombuffer(h.raw(source_row['canvas_rgb24'],h.SOURCE),np.uint8).reshape(480,720,3).copy()
            original=h.m.C.corpus.rgb565(canvas).astype(np.uint16);source=tuple(np.asarray(v,dtype=np.int16)for v in h.m.ft.rgb_to_planes(canvas));read_ms=(time.perf_counter_ns()-t)/1e6
            assert h.digest(canvas.tobytes())==source_row['canvas_rgb_sha256'];assert h.digest(original.astype('<u2').tobytes())==source_row['rgb565_sha256']
            source_hash=h.digest(b''.join(p.astype('<i2').tobytes()for p in source));hud=h.raw(control_row['hud_packets']['HX33_selected'],h.CONTROL)
            began=time.perf_counter_ns();zero,grid,q,costs,maps,grid_vectors,shared=model.prepare(source,reference,frame_id=fid,reference_id=rid)
            prepared={'zero':zero};material={'zero':dict(materialize_ms=0.,repeated_search_calls=0,repeated_forward_plane_calls=0)}
            for name in model.POLICIES[1:]:prepared[name],unused,material[name]=model.mix(zero,grid,maps[name],grid_vectors)
            proposals={};probes={};qualities={};displays={}
            for name in model.POLICIES:
                p=model.encode(prepared[name],q,hud);proposals[name]=p
                if len(p['packet'])<=49152:
                    probe=fork(rx);pixels,patches,meta,count=probe.receive(p['packet']);probes[name]=probe
                    for a,b in zip(pixels,p['normalized'],strict=True):np.testing.assert_array_equal(a,b)
                    for a,b in zip(meta['coefficients'],p['coefficients'],strict=True):np.testing.assert_array_equal(a,b)
                    for patch,(x,y,w,hh)in zip(patches,h.n.RECTS,strict=True):np.testing.assert_array_equal(patch['words'],original[y:y+hh,x:x+w])
                    words=tuple(patch['words']for patch in patches)
                else:pixels=p['normalized'];words=tuple(original[y:y+hh,x:x+w]for x,y,w,hh in h.n.RECTS)
                display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),words);qualities[name]=h.n.metric(original,display);displays[name]=h.n.digest(display)
            assert source_hash==h.digest(b''.join(p.astype('<i2').tobytes()for p in source))
            gate={name:(len(proposals[name]['packet']),qualities[name]['active_squared_error'])for name in model.POLICIES};chosen=model.choose(gate)
            paid_policy_ms=(time.perf_counter_ns()-began)/1e6
            candidates={name:archive_candidate(proposals[name],qualities[name],displays[name],name in probes,material[name])for name in model.POLICIES}
            row=dict(id=fid,key=key,reference_id=rid,reference_tag=zero.reference_tag.hex(),source_canvas_object=source_row['canvas_rgb24'],source_rgb_sha256=source_row['canvas_rgb_sha256'],
                source_rgb565_sha256=source_row['rgb565_sha256'],source_yuv_i16_sha256=source_hash,source_pts=source_row['pts'],source_timestamp_fraction=source_row['timestamp_fraction'],
                hud_source_packet=control_row['hud_packets']['HX33_selected'],hud_packet=h.blob(hud),hud_bytes=len(hud),shared_original_hud_generation_ms=control_row['hud_generation_ms'],source_read_conversion_ms=read_ms,
                shared_analysis_work=shared,shared_prepared_evidence={'zero':hashes(zero),'global_grid':hashes(grid)},
                macroblock_costs=h.blob(costs.astype('<i8').tobytes()),macroblock_cost_shape=list(costs.shape),macroblock_cost_fields=['source_YUV_SSE','fine_coefficient_bits','motion_proxy_bits'],
                macroblock_maps={name:h.blob(maps[name].astype(np.uint8).tobytes())for name in maps},macroblock_selected_counts={name:int(maps[name].sum())for name in maps},
                global_vector_map=h.blob(grid_vectors.tobytes()),global_vector_bytes=h.blob(grid.vector_bytes),candidates=candidates,
                guard={name:dict(complete_bytes=gate[name][0],active_source_RGB565_SSE=gate[name][1])for name in gate},selected_policy=chosen,accepted=chosen is not None,
                paid_sender_ms=shared['shared_prepare_ms']+sum(material[name]['materialize_ms']for name in model.POLICIES[1:])+sum(p['encode_ms']for p in proposals.values()),
                paid_policy_with_receive_quality_ms=paid_policy_ms,
                fixed_zero_control=dict(packet=golden_row['packet'],complete_bytes=golden_row['complete_bytes'],quality=golden_row['quality'],normalized_tag=golden_row['normalized_tag']))
            if chosen is not None:
                rx=probes[chosen];c=candidates[chosen];row.update(packet=c['packet'],complete_bytes=c['complete_bytes'],quality=c['quality'],normalized_tag=c['normalized_tag'],display_sha256=c['display_sha256'])
            else:row['rejection']='No admissible fitting mixed candidate and zero overcap; stop without publication'
            rows.append(row);print(json.dumps(dict(scene=scene,frame=fid,selected=chosen,MBs=row['macroblock_selected_counts'],guard=row['guard'])),flush=True)
            if chosen is None:break
        cases.append(dict(scene=scene,requested_source_frames=24,rows=rows,summary=summary(rows)));print(json.dumps(dict(scene=scene,summary=cases[-1]['summary'])),flush=True)
    result=dict(schema='gamebub-quantized-motion-v53',source_sha256=h.pins(),cases=cases,
        parameters=dict(width=720,height=480,block_size=32,chroma_MB_size=16,key_interval=24,roi_scale=8,background_scale=16,rdo_lambda=1,avoid_rects=h.n.ROIS,hud_rects=h.n.RECTS,
            candidate_order=list(model.POLICIES),proxy_fields=['source_YUV_SSE','fine_coefficient_bits','motion_proxy_bits'],proxy_lambda=4,nonzero_MB_motion_bits=16,
            hidden='Exclude all64samples and coefficientbits of canonical-safe full8x8blocks; residualzero and normalized128',
            final_guard='candidate bytes<=zero AND sourceRGB565SSE<=zero AND onestrict; minimum(bytes,SSE,order); tieszero; final49152 cap'),
        physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,environment=dict(python=platform.python_version(),numpy=np.__version__),
        scope=['96first24freshcanvases, sharedzero/gridanalysis at actualselectedref,2mixedselectors andzero actualsenders; all3packets and18AB38alternatives/frame retained/paid.',
            'Pre-RDO quantizedinverseYUVSSE+fineCP02bits are proxies; originalwholeplaneRDO/legacyreversion then actualAB38/wholeRGB565guard mayreject.',
            'MixedPrepared prediction/rawforward assembled by aligned8x8blocks; no repeatedsearch/forward. Privateownedsource copied and actualmixedMVmap packed.',
            'Onlyselectedreceiverfork publishes; localguard doesnotguaranteefuturegain versusseparatefixedzerohistory. Allhistoryqualitymeasured.',
            'Paidpolicyclockincludes sharedanalysis/proxy/mix/allencodes/receives/sourcequalitychecks; sourceconversion/sharedHUDgeneration/archiveIO separate. NoFPS/hardware/nativefrontierclaim.'])
    (h.HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
