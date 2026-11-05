#!/usr/bin/env python3
"""Paid fixed-reference hierarchical motion probe on 24 frozen source inputs."""
import json
import platform
import time
import numpy as np
import helpers as h


def elapsed(fn):
    began=time.perf_counter_ns();value=fn();return value,(time.perf_counter_ns()-began)/1e6


def attempt(kind,prepared,q,ref,prior,original,hud):
    fn=(lambda:h.m.encode_prepared(prepared,q)) if kind=='split16_incumbent' else (lambda:h.band.encode_with(h.m,prepared,q,policy='band_strict'))
    (packet,pixels,work),encode_ms=elapsed(fn)
    (decoded,meta),decode_ms=elapsed(lambda:h.m.decode(packet,ref,expected_epoch=25,
        expected_reference_id=None if prior['key'] else prior['reference_id']))
    for a,b in zip(pixels,decoded):np.testing.assert_array_equal(a,b)
    began=time.perf_counter_ns()
    bare=h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels))
    hybrid=h.n.overlay(bare,tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS))
    metric=h.n.metric(original,hybrid)
    quality_ms=(time.perf_counter_ns()-began)/1e6
    began=time.perf_counter_ns();p=h.protocol
    pair=p.seal(p.PAIR.pack(b'CP27',1,p.PUBLISH|(p.KEY if prior['key'] else 0),25,prior['id'],
        prior['source_slot'],prior['destination_slot'],len(packet),len(hud),p.digest(packet),p.digest(hud))+packet+hud)
    fits=len(pair)<=49152
    if fits:
        parsed=p.parse_pair(pair);assert parsed['base_meta']['block_size']==prepared.block_size
    else:
        try:p.parse_pair(pair)
        except ValueError:pass
        else:raise AssertionError('overcap pair accepted')
    bind_ms=(time.perf_counter_ns()-began)/1e6
    envelope=h.m.parse_metadata(packet)
    return dict(kind=kind,block_size=prepared.block_size,base_packet=h.blob(packet),packet=h.blob(pair),
        base_bytes=len(packet),complete_bytes=len(pair),cap_fit=fits,cp27_profile_accepted=fits,
        motion_bytes=envelope['vector_bytes'],residual_bytes=sum(envelope['plane_lengths']),
        residual_plane_bytes=list(envelope['plane_lengths']),qmap_bytes=envelope['qmap_bytes'],
        hybrid=metric,hybrid_sha256=h.n.digest(hybrid),output_plane_sha256=[h.n.digest(a) for a in pixels],
        encode_ms=encode_ms,quality_ms=quality_ms,bind_ms=bind_ms,offline_decode_ms=decode_ms,work=work)


def main():
    before=h.pins();rows=[]
    for case,inp in h.cases():
        ref=None
        for prior,srcrow in zip(case['rows'][:12],inp['rows'][:12]):
            source,original=h.n.source(srcrow),h.n.original(srcrow)
            hud=h.raw(prior['hud_packet'],h.ROOT/prior['hud_packet']['directory'])
            # Retained control decoding/metric extraction is offline evidence,
            # outside the paid new-source probe. It never changes the reference.
            began=time.perf_counter_ns()
            control_packet=h.raw(prior['base_packet'],h.h.V32)
            control_pixels,_=h.m.decode(control_packet,ref,expected_epoch=25,
                expected_reference_id=None if prior['key'] else prior['reference_id'])
            control_hybrid=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(control_pixels)),
                tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS))
            control_metric=h.n.metric(original,control_hybrid)
            assert control_metric==prior['hybrid']
            control_meta=h.m.parse_metadata(control_packet)
            control=dict(kind='v32_control',base_packet=h.blob(control_packet),packet=h.blob(h.raw(prior['packet'],h.h.V32)),
                complete_bytes=prior['body_bytes'],base_bytes=len(control_packet),hybrid=control_metric,
                motion_bytes=control_meta['vector_bytes'],residual_bytes=sum(control_meta['plane_lengths']))
            offline_control_ms=(time.perf_counter_ns()-began)/1e6
            bg=prior['selected_background'];q=h.m.roi.declared_map(720,480,h.n.ROIS,8,bg)
            parent,parent_ms=elapsed(lambda:h.adaptive.analyze_with(h.m.base,source,ref,
                epoch=25,frame_id=prior['id'],reference_id=prior['reference_id'],block_size=32,
                motion_mode='block',motion_precision='half',penalty=0,search_policy='adaptive_zero2'))
            baseline=attempt('parent32_band',parent,q,ref,prior,original,hud)
            old=next(a for a in prior['attempts'] if a['kind']==('zero_band' if prior['key'] else 'half32_band') and a['background']==bg)
            assert h.raw(baseline['base_packet'],h.HERE)==h.raw(old['base_packet'],h.h.V32)
            prepared,split_ms=elapsed(lambda:h.split.analyze16(h.m,h.adaptive,parent,ref))
            trials=[attempt(kind,prepared,q,ref,prior,original,hud) for kind in ('split16_incumbent','split16_band')]
            for trial in trials:
                trial['strictly_smaller']=trial['complete_bytes']<baseline['complete_bytes']
                trial['rgb_no_worse']=trial['hybrid']['active_squared_error']<=baseline['hybrid']['active_squared_error']
                trial['qualifies_against_parent32']=trial['cap_fit'] and trial['strictly_smaller'] and trial['rgb_no_worse']
                trial['qualified']=trial['cap_fit'] and trial['complete_bytes']<control['complete_bytes'] and trial['hybrid']['active_squared_error']<=control['hybrid']['active_squared_error']
                trial['qualifies_against_v32_selected']=trial['qualified']
            selected=min([control]+[t for t in trials if t['qualified']],key=lambda a:a['complete_bytes'])
            all_attempts=[baseline]+trials
            row=dict(scene=case['scene'],id=prior['id'],key=prior['key'],reference_id=prior['reference_id'],
                reference_tag=parent.reference_tag.hex(),source_sha256=srcrow['common_yuv420_u8_sha256'],
                background=bg,hud_packet=prior['hud_packet'],hud_bytes=len(hud),binding_bytes=60,
                source_slot=prior['source_slot'],destination_slot=prior['destination_slot'],
                accepted_v32_complete_bytes=prior['body_bytes'],accepted_v32_hybrid=prior['hybrid'],
                parent_analysis=parent.work,split_analysis=prepared.work,parent_analysis_ms=parent_ms,split_analysis_ms=split_ms,
                baseline=baseline,control_baseline=control,offline_control_decode_metric_ms=offline_control_ms,
                trials=trials,selected_kind=selected['kind'],selected_complete_bytes=selected['complete_bytes'],
                selected_hybrid=selected['hybrid'],
                all_paid_host_ms=parent_ms+split_ms+sum(a['encode_ms']+a['quality_ms']+a['bind_ms'] for a in all_attempts),
                additional_host_ms=split_ms+sum(a['encode_ms']+a['quality_ms']+a['bind_ms'] for a in trials))
            rows.append(row)
            ref,_=h.m.decode(h.raw(prior['base_packet'],h.h.V32),ref,expected_epoch=25,
                expected_reference_id=None if prior['key'] else prior['reference_id'])
            print(json.dumps(dict(scene=case['scene'],frame=prior['id'],selected=row['selected_kind'],
                baseline_bytes=baseline['complete_bytes'],trial_bytes=[a['complete_bytes'] for a in trials],
                qualified=[a['qualified'] for a in trials])),flush=True)
    summary=dict(frames=len(rows),raw_trial_packets=2*len(rows),selected_split_frames=sum(r['selected_kind']!='v32_control' for r in rows),
        qualified_raw_trials=sum(t['qualified'] for r in rows for t in r['trials']),
        qualified_against_parent32_trials=sum(t['qualifies_against_parent32'] for r in rows for t in r['trials']),
        qualified_against_v32_selected_trials=sum(t['qualifies_against_v32_selected'] for r in rows for t in r['trials']),
        baseline_complete_bytes=sum(r['control_baseline']['complete_bytes'] for r in rows),selected_complete_bytes=sum(r['selected_complete_bytes'] for r in rows),
        baseline_source_rgb_sse=sum(r['control_baseline']['hybrid']['active_squared_error'] for r in rows),
        parent32_band_complete_bytes=sum(r['baseline']['complete_bytes'] for r in rows),
        selected_source_rgb_sse=sum(r['selected_hybrid']['active_squared_error'] for r in rows),
        raw16_band_complete_bytes=sum(r['trials'][1]['complete_bytes'] for r in rows),
        raw16_band_source_rgb_sse=sum(r['trials'][1]['hybrid']['active_squared_error'] for r in rows),
        baseline_motion_bytes=sum(r['baseline']['motion_bytes'] for r in rows),
        raw16_band_motion_bytes=sum(r['trials'][1]['motion_bytes'] for r in rows),
        baseline_residual_bytes=sum(r['baseline']['residual_bytes'] for r in rows),
        raw16_band_residual_bytes=sum(r['trials'][1]['residual_bytes'] for r in rows),
        mean_all_paid_host_ms=sum(r['all_paid_host_ms'] for r in rows)/len(rows),
        mean_additional_host_ms=sum(r['additional_host_ms'] for r in rows)/len(rows),
        parent_search_samples=sum(r['parent_analysis']['search']['sad_sample_operations'] for r in rows),
        refinement_search_samples=sum(r['split_analysis']['search']['sad_sample_operations'] for r in rows),
        parent_decoder_reference_reads=sum(r['baseline']['work']['decoder_reference_sample_reads'] for r in rows),
        raw16_band_decoder_reference_reads=sum(r['trials'][1]['work']['decoder_reference_sample_reads'] for r in rows),
        all_under_cap_cp27_profiles_accepted=all(a['cp27_profile_accepted'] for r in rows for a in [r['baseline']]+r['trials']))
    assert h.pins()==before
    data=dict(schema='gamebub-split-v33',parent_commit='293b8b2e3a58db733eddd10c635ec7df29789f70',source_sha256=before,
        summary=summary,rows=rows,unchanged_GM27_wire=True,physical_30fps_proven=False,causal_campaign=False,
        environment=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform()),
        scope=['24 retained inputs, each references actual prior accepted v32 band_control output; trial selection never updates history.',
            'Primary admission baseline is the actual retained accepted v32 controller packet and decoded current-source RGB metric. Parent32 strict-band comparison is separately labelled.',
            'Paid host time includes parent32 analysis and strict-band encode, child16 refinement/analysis, full incumbent16 and strict-band16 encodes, RGB metrics and CP27 binding.',
            'Excludes fixture read/conversion, retained HU25 generation, retained control decode/metric extraction, debug decode, archives, transport and display. One timing sample per frame.',
            'No causal, fps, combined-gain or hardware claim.'])
    (h.HERE/'results.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
