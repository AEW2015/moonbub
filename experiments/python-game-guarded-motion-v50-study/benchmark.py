#!/usr/bin/env python3
"""Strict same-reference local guard, evaluated through its OWN causal history."""
import json,platform,time
import numpy as np
import helpers as h
model=h.bound('guard50_owned_model',h.HERE/'model.py',h)

def fork(rx):
    out=h.rx.Receiver();out.ref,out.rid,out.hud,out.last=rx.ref,rx.rid,rx.hud,rx.last;return out

def options_archive(options):
    result=[]
    for option in options:
        copy=dict(option);copy['legacy_payload']=h.blob(copy['legacy_payload']);copy['trials']=[]
        for trial in option['trials']:
            row=dict(trial);row['packet']=h.blob(row['packet']);copy['trials'].append(row)
        result.append(copy)
    return result

def archive_candidate(p,quality,display_sha,received):
    prep=p['prepared'];mw,mh=h.m.base._grid(720,480,32)
    vectors=np.zeros((mh,mw,2),np.int8)if prep.key else h.m.base.unpack_vectors(prep.vector_bytes,mw,mh)
    return dict(packet=h.blob(p['packet']),complete_bytes=len(p['packet']),cap_fit=len(p['packet'])<=49152,
        cs37_intermediate=h.blob(p['cs37']),intermediate_bytes=len(p['cs37']),coefficients=[h.blob(c.astype('<i2').tobytes())for c in p['coefficients']],
        vector_bytes=h.blob(prep.vector_bytes),vector_map=h.blob(vectors.tobytes()),nonzero_vectors=int(np.count_nonzero(np.any(vectors!=0,axis=2))),
        qmap=h.blob(h.m.roi.pack_map(p['qmap'])),reference_tag=prep.reference_tag.hex(),normalized_tag=h.m.C.reference_tag(p['normalized']).hex(),
        quality=quality,display_sha256=display_sha,received_on_fork=received,analysis_ms=p['analysis_ms'],analysis_work=p['analysis_work'],
        proposal_work=p['proposal_work'],transcode_work=p['transcode_work'],sender_ms=p['sender_ms'],attempts=options_archive(p['options']))

def summary(rows):
    accepted=[r for r in rows if r['accepted']];n=sum(r['quality']['active_channel_samples']for r in accepted);sse=sum(r['quality']['active_squared_error']for r in accepted)
    return dict(attempted_frames=len(rows),accepted_frames=len(accepted),selected_grid_frames=sum(r['selected_policy']=='global_grid'for r in accepted),
        complete_bytes=sum(r['complete_bytes']for r in accepted),active_squared_error=sse,active_channel_samples=n,active_mse=sse/n if n else None,
        hud_word_errors=sum(r['quality']['hud_word_errors']for r in accepted),exact_hud_words=21120*len(accepted),
        fixed_zero_complete_bytes=sum(r['fixed_zero_control']['complete_bytes']for r in rows),
        fixed_zero_active_squared_error=sum(r['fixed_zero_control']['quality']['active_squared_error']for r in rows),
        paid_sender_ms=sum(r['paid_sender_ms']for r in rows),paid_policy_with_receive_quality_ms=sum(r['paid_policy_with_receive_quality_ms']for r in rows),
        paid_candidate_packets=2*len(rows),paid_AB38_encode_calls=12*len(rows),
        final_overcap_candidates=sum(not c['cap_fit']for r in rows for c in r['candidates'].values()),prefix_stopped=bool(rows and not rows[-1]['accepted']))

def main():
    manifest=h.load(h.SOURCE/'manifest.json');controls=h.load(h.CONTROL/'results.json');goldens=h.load(h.GOLDEN/'results.json');cases=[]
    for src_case,control_case,golden_case in zip(manifest['cases'],controls['cases'],goldens['cases'],strict=True):
        scene=control_case['scene'];rx=h.rx.Receiver();rows=[]
        for source_row,control_row,golden_row in zip(src_case['frames'][:24],control_case['rows'][:24],golden_case['rows'][:24],strict=True):
            fid=source_row['id'];key=fid%24==0;rid=h.m.NO_REF if key else rx.rid;reference=None if key else rx.ref
            t=time.perf_counter_ns();canvas=np.frombuffer(h.raw(source_row['canvas_rgb24'],h.SOURCE),np.uint8).reshape(480,720,3).copy()
            original=h.m.C.corpus.rgb565(canvas).astype(np.uint16);source=tuple(np.asarray(v,dtype=np.int16)for v in h.m.ft.rgb_to_planes(canvas));read_convert_ms=(time.perf_counter_ns()-t)/1e6
            assert h.digest(canvas.tobytes())==source_row['canvas_rgb_sha256'];assert h.digest(original.astype('<u2').tobytes())==source_row['rgb565_sha256']
            source_hash=h.digest(b''.join(p.astype('<i2').tobytes()for p in source));hud=h.raw(control_row['hud_packets']['HX33_selected'],h.CONTROL)
            began=time.perf_counter_ns();proposals={};probes={};metrics={};displays={}
            for policy in('zero','global_grid'):
                p=model.propose(source,reference,hud,policy=policy,frame_id=fid,reference_id=rid);proposals[policy]=p
                if len(p['packet'])<=49152:
                    probe=fork(rx);pixels,patches,meta,count=probe.receive(p['packet']);probes[policy]=probe
                    for a,b in zip(pixels,p['normalized'],strict=True):np.testing.assert_array_equal(a,b)
                    for a,b in zip(meta['coefficients'],p['coefficients'],strict=True):np.testing.assert_array_equal(a,b)
                    for patch,(x,y,w,hh)in zip(patches,h.n.RECTS,strict=True):np.testing.assert_array_equal(patch['words'],original[y:y+hh,x:x+w])
                    words=tuple(patch['words']for patch in patches)
                else:
                    pixels=p['normalized'];words=tuple(original[y:y+hh,x:x+w]for x,y,w,hh in h.n.RECTS)
                display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),words)
                metrics[policy]=h.n.metric(original,display);displays[policy]=h.n.digest(display)
            assert source_hash==h.digest(b''.join(p.astype('<i2').tobytes()for p in source))
            z,g=proposals['zero'],proposals['global_grid'];zs=metrics['zero']['active_squared_error'];gs=metrics['global_grid']['active_squared_error']
            chosen=model.choose(len(z['packet']),zs,len(g['packet']),gs)
            paid_policy_ms=(time.perf_counter_ns()-began)/1e6
            candidates={p:archive_candidate(proposals[p],metrics[p],displays[p],p in probes)for p in proposals}
            row=dict(id=fid,key=key,reference_id=rid,reference_tag=h.m.C.reference_tag(reference).hex()if reference is not None else bytes(16).hex(),
                source_canvas_object=source_row['canvas_rgb24'],source_rgb_sha256=source_row['canvas_rgb_sha256'],source_rgb565_sha256=source_row['rgb565_sha256'],
                source_yuv_i16_sha256=source_hash,source_pts=source_row['pts'],source_timestamp_fraction=source_row['timestamp_fraction'],
                hud_source_packet=control_row['hud_packets']['HX33_selected'],hud_packet=h.blob(hud),hud_bytes=len(hud),
                shared_original_hud_generation_ms=control_row['hud_generation_ms'],source_read_conversion_ms=read_convert_ms,
                candidates=candidates,selected_policy=chosen,accepted=chosen is not None,
                guard=dict(zero_bytes=len(z['packet']),grid_bytes=len(g['packet']),zero_active_sse=zs,grid_active_sse=gs),
                paid_sender_ms=z['sender_ms']+g['sender_ms'],paid_policy_with_receive_quality_ms=paid_policy_ms,
                fixed_zero_control=dict(packet=golden_row['packet'],complete_bytes=golden_row['complete_bytes'],quality=golden_row['quality'],normalized_tag=golden_row['normalized_tag']))
            if chosen is not None:
                rx=probes[chosen];c=candidates[chosen];row.update(packet=c['packet'],complete_bytes=c['complete_bytes'],quality=c['quality'],normalized_tag=c['normalized_tag'],display_sha256=c['display_sha256'])
            else:row['rejection']='Neither strict-Pareto admitted fitting grid nor fitting zero; prefix stops without publication'
            rows.append(row);print(json.dumps(dict(scene=scene,frame=fid,selected=chosen,guard=row['guard'])),flush=True)
            if chosen is None:break
        cases.append(dict(scene=scene,policy='guarded_zero_global_grid',requested_source_frames=24,rows=rows,summary=summary(rows)))
        print(json.dumps(dict(scene=scene,summary=cases[-1]['summary'])),flush=True)
    result=dict(schema='gamebub-guarded-motion-v50',source_sha256=h.pins(),cases=cases,
        parameters=dict(width=720,height=480,block_size=32,key_interval=24,roi_scale=8,background_scale=16,rdo_lambda=1,avoid_rects=h.n.ROIS,hud_rects=h.n.RECTS,
            policies=['zero','global_grid'],final_cap=49152,guard='grid fits AND grid bytes<=zero bytes AND grid original active RGB565 SSE<=zero SSE AND at leastone strict; else fittingzero; else stop'),
        physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,environment=dict(python=platform.python_version(),numpy=np.__version__),
        scope=['Both actual proposals use the SAME current selected reference; each fitting receive is forked and checked before selection. Only selected state publishes.',
            'Local strict Pareto admission does NOT guarantee future quality/size relative to a separately evolving fixed-zero history. Actual fixed-zero prefix results retained for comparison.',
            'All2analysis+2CS37construction+12AB38encodes perframe are paid. Sender costs exclude receive/quality; paid_policy_with_receive_quality_ms includes them and comparisons, excluding source/HUD IO and archive writes.',
            'Intermediate cap deferred exactly as frozen47; final49152 completeCS38 cap gates acceptance; reject stops prefix without base/HUD advance. Shared prior HX33 generation cost is externally paid.',
            'No targetmemory/FPGAfit/nativefrontier/FPS or hardware claim.'])
    (h.HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
