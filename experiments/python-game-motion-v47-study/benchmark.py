#!/usr/bin/env python3
"""Four fresh 24-frame cohorts, two independent fixed motion-policy histories."""
import json,platform,time
import numpy as np
import helpers as h
model=h.bound('motion47_owned_model',h.HERE/'model.py',h)

def archive_attempts(attempts):
    result=[]
    for a in attempts:
        b=dict(a);b['legacy_payload']=h.blob(b['legacy_payload']);b['trials']=[]
        for trial in a['trials']:
            t=dict(trial);t['packet']=h.blob(t['packet']);b['trials'].append(t)
        result.append(b)
    return result

def summary(rows):
    accepted=[r for r in rows if r['accepted']];samples=sum(r['quality']['active_channel_samples']for r in accepted);sse=sum(r['quality']['active_squared_error']for r in accepted)
    return dict(attempted_frames=len(rows),accepted_frames=len(accepted),rejected_frames=len(rows)-len(accepted),
        complete_bytes=sum(r['complete_bytes']for r in accepted),maximum_complete_bytes=max((r['complete_bytes']for r in accepted),default=None),
        active_squared_error=sse,active_channel_samples=samples,active_mse=sse/samples if samples else None,
        exact_hud_words=21120*len(accepted),hud_word_errors=sum(r['quality']['hud_word_errors']for r in accepted),
        intermediate_overcap_frames=sum(r['proposal_work']['intermediate_overcap']for r in rows),
        final_overcap_frames=sum(not r['cap_fit']for r in rows),nonzero_vectors=sum(r['nonzero_vectors']for r in rows),
        sad_sample_operations=sum(r['analysis_work']['search']['sad_sample_operations']for r in rows),
        paid_AB38_encode_calls=6*len(rows),paid_sender_ms=sum(r['sender_ms']for r in rows),
        mean_sender_ms=sum(r['sender_ms']for r in rows)/len(rows),
        prefix_stopped=bool(rows and not rows[-1]['accepted']))

def main():
    manifest=h.load(h.SOURCE/'manifest.json');controls=h.load(h.CONTROL/'results.json');goldens=h.load(h.GOLDEN/'results.json');cases=[]
    for source_case,control_case,golden_case in zip(manifest['cases'],controls['cases'],goldens['cases'],strict=True):
        scene=control_case['scene'];assert scene==golden_case['scene'];frames=source_case['frames'][:24]
        assert [r['id']for r in frames]==list(range(24))
        for policy in('zero','global_grid'):
            rx=h.rx.Receiver();rows=[]
            for source_row,control_row,golden_row in zip(frames,control_case['rows'][:24],golden_case['rows'][:24],strict=True):
                fid=source_row['id'];key=fid%24==0;rid=h.m.NO_REF if key else rx.rid;reference=None if key else rx.ref
                start=time.perf_counter_ns();canvas_raw=h.raw(source_row['canvas_rgb24'],h.SOURCE)
                canvas=np.frombuffer(canvas_raw,np.uint8).reshape(480,720,3).copy();original=h.m.C.corpus.rgb565(canvas).astype(np.uint16)
                source=tuple(np.asarray(v,dtype=np.int16)for v in h.m.ft.rgb_to_planes(canvas));read_convert_ms=(time.perf_counter_ns()-start)/1e6
                assert h.digest(canvas.tobytes())==source_row['canvas_rgb_sha256']
                assert h.digest(original.astype('<u2').tobytes())==source_row['rgb565_sha256']
                source_hash=h.digest(b''.join(v.astype('<i2').tobytes()for v in source))
                hud=h.raw(control_row['hud_packets']['HX33_selected'],h.CONTROL)
                q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
                began=time.perf_counter_ns()
                if policy=='zero':prepared=h.analysis.analyze_planes(source,reference,epoch=25,frame_id=fid,reference_id=rid,block_size=32,motion_mode='zero',penalty=0,motion_precision='half')
                else:prepared=h.global_search.analyze_with(h.m,source,reference,epoch=25,frame_id=fid,reference_id=rid,block_size=32,policy='global_grid',avoid_rects=h.n.ROIS)
                analysis_ms=(time.perf_counter_ns()-began)/1e6
                intermediate,normalized,coefficients,payloads,proposal_work=model.encode_proposal(prepared,q,hud)
                packet,attempts,transcode_work=model.transcode(intermediate,coefficients,payloads)
                sender_ms=(time.perf_counter_ns()-began)/1e6
                assert source_hash==h.digest(b''.join(v.astype('<i2').tobytes()for v in source))
                mw,mh=h.m.base._grid(720,480,32)
                vectors=np.zeros((mh,mw,2),np.int8)if key else h.m.base.unpack_vectors(prepared.vector_bytes,mw,mh)
                cap_fit=len(packet)<=49152
                row=dict(id=fid,source_id=fid,source_canvas_object=source_row['canvas_rgb24'],source_rgb_sha256=source_row['canvas_rgb_sha256'],
                    source_rgb565_sha256=source_row['rgb565_sha256'],source_yuv_i16_sha256=source_hash,
                    source_pts=source_row['pts'],source_timestamp_fraction=source_row['timestamp_fraction'],
                    key=key,reference_id=rid,reference_tag=prepared.reference_tag.hex(),
                    hud_source_packet=control_row['hud_packets']['HX33_selected'],hud_packet=h.blob(hud),hud_bytes=len(hud),
                    shared_original_hud_generation_ms=control_row['hud_generation_ms'],
                    vector_bytes=h.blob(prepared.vector_bytes),vector_map=h.blob(vectors.tobytes()),nonzero_vectors=int(np.count_nonzero(np.any(vectors!=0,axis=2))),
                    qmap=h.blob(h.m.roi.pack_map(q)),cs37_intermediate=h.blob(intermediate),intermediate_bytes=len(intermediate),
                    packet=h.blob(packet),complete_bytes=len(packet),cap_fit=cap_fit,accepted=False,
                    analysis_ms=analysis_ms,analysis_work=prepared.work,proposal_work=proposal_work,transcode_work=transcode_work,
                    sender_ms=sender_ms,source_read_conversion_ms=read_convert_ms,attempts=archive_attempts(attempts),
                    coefficients=[h.blob(c.astype('<i2').tobytes())for c in coefficients],zero_golden_packet=golden_row['packet'])
                if cap_fit:
                    decoded,patches,meta,count=rx.receive(packet)
                    for a,b in zip(decoded,normalized,strict=True):np.testing.assert_array_equal(a,b)
                    for a,b in zip(meta['coefficients'],coefficients,strict=True):np.testing.assert_array_equal(a,b)
                    for patch,(x,y,w,hh)in zip(patches,h.n.RECTS,strict=True):np.testing.assert_array_equal(patch['words'],original[y:y+hh,x:x+w])
                    display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(decoded)),tuple(p['words']for p in patches))
                    quality=h.n.metric(original,display);assert quality['hud_word_errors']==0
                    if policy=='zero':assert packet==h.raw(golden_row['packet'],h.GOLDEN)
                    row.update(accepted=True,normalized_tag=h.m.C.reference_tag(decoded).hex(),display_sha256=h.n.digest(display),quality=quality,binary_planes=count)
                else:
                    row['rejection']='final complete CS38 packet exceeds49152; this policy prefix stops without changing base or HUD state'
                rows.append(row)
                print(json.dumps(dict(scene=scene,policy=policy,frame=fid,bytes=len(packet),accepted=row['accepted'],nonzero_vectors=row['nonzero_vectors'],mse=row.get('quality',{}).get('active_mse'))),flush=True)
                if not cap_fit:break
            cases.append(dict(scene=scene,policy=policy,requested_source_frames=24,rows=rows,summary=summary(rows)))
            print(json.dumps(dict(scene=scene,policy=policy,summary=cases[-1]['summary'])),flush=True)
    result=dict(schema='gamebub-motion-v47',source_sha256=h.pins(),cases=cases,
        parameters=dict(width=720,height=480,block_size=32,key_interval=24,roi_scale=8,background_scale=16,rdo_lambda=1,avoid_rects=h.n.ROIS,hud_rects=h.n.RECTS,
            global_policy='global_grid',coarse_grid=list(range(-16,17,4)),local_offsets=[-4,0,4],quiet_threshold=2,local_stride=4,global_coarse_stride=16,
            halfpel_refinement=False,plane_selection='shortest actual legacy/fullAB38/compactAB38; stable ties legacy then full then compact',final_cap=49152),
        physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        scope=['96 actual fresh source frames attempted through two own-history policies, up to192 actual complete packet proposals. Prefix stops on final cap failure; no hidden fallback or publication.',
            'Global search uses each policy own accepted canonical reference. Global and zero histories and distortion may differ; this is not a lossless or same-history comparison.',
            'Original global RDO/legacy reversion is preserved before hidden suppression. Actual full and compact AB38 options plus legacy fallback are retained and all6 encodes/frame paid.',
            'Intermediate CS37 cap is locally deferred until final complete CS38 selection; overcap intermediate bytes are retained and are not claimed valid public CS37 inputs.',
            'Sender clock includes analysis/search/prediction/forward/quantization/RDO/legacy entropy/reconstruction/normalization/all6AB38 encodes/wrapping. Source read/conversion, already paid shared HUD generation, receive/metrics and archives are separate.',
            'No native re-encode, real-time/FPS, hardware resource fit, or standards superiority claim.'])
    (h.HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
