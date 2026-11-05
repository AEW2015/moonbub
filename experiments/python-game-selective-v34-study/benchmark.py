#!/usr/bin/env python3
"""Paid 24-input fixed-reference selective refinement; all actual packets kept."""
import json
import platform
import time
import numpy as np
import helpers as h


def elapsed(fn):
    began=time.perf_counter_ns();value=fn();return value,(time.perf_counter_ns()-began)/1e6


def attempt(kind,prepared,q,ref,prior,original,hud,mode='band'):
    fn=(lambda:h.m.encode_prepared(prepared,q)) if mode=='incumbent' else (lambda:h.band.encode_with(h.m,prepared,q,policy='band_strict'))
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
    return dict(kind=kind,mode=mode,block_size=prepared.block_size,base_packet=h.blob(packet),packet=h.blob(pair),
        base_bytes=len(packet),complete_bytes=len(pair),cap_fit=fits,cp27_profile_accepted=fits,
        motion_bytes=envelope['vector_bytes'],residual_bytes=sum(envelope['plane_lengths']),
        residual_plane_bytes=list(envelope['plane_lengths']),qmap_bytes=envelope['qmap_bytes'],
        hybrid=metric,hybrid_sha256=h.n.digest(hybrid),output_plane_sha256=[h.n.digest(a) for a in pixels],
        encode_ms=encode_ms,quality_ms=quality_ms,bind_ms=bind_ms,offline_decode_ms=decode_ms,work=work)


def qualify(a,control):
    return a['cap_fit'] and a['complete_bytes']<control['complete_bytes'] and a['hybrid']['active_squared_error']<=control['hybrid']['active_squared_error']


def main():
    before=h.pins();rows=[]
    oldrows=h.load(h.h.HERE/'results.json')['rows']
    for case,inp in h.cases():
        ref=None
        for prior,srcrow in zip(case['rows'][:12],inp['rows'][:12]):
            source,original=h.n.source(srcrow),h.n.original(srcrow)
            hud=h.raw(prior['hud_packet'],h.ROOT/prior['hud_packet']['directory'])
            # Actual accepted control is v32 band_control, also the v33 control
            # parity lineage. Decode it offline; candidates never update history.
            began=time.perf_counter_ns()
            control_packet=h.raw(prior['base_packet'],h.h.h.V32)
            control_pixels,_=h.m.decode(control_packet,ref,expected_epoch=25,
                expected_reference_id=None if prior['key'] else prior['reference_id'])
            control_hybrid=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(control_pixels)),
                tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS))
            control_metric=h.n.metric(original,control_hybrid)
            assert control_metric==prior['hybrid']
            control_meta=h.m.parse_metadata(control_packet)
            control=dict(kind='accepted_control',base_packet=h.blob(control_packet),packet=h.blob(h.raw(prior['packet'],h.h.h.V32)),
                complete_bytes=prior['body_bytes'],base_bytes=len(control_packet),hybrid=control_metric,
                motion_bytes=control_meta['vector_bytes'],residual_bytes=sum(control_meta['plane_lengths']))
            offline_control_ms=(time.perf_counter_ns()-began)/1e6
            bg=prior['selected_background'];q=h.m.roi.declared_map(720,480,h.n.ROIS,8,bg)
            parent,parent_ms=elapsed(lambda:h.adaptive.analyze_with(h.m.base,source,ref,
                epoch=25,frame_id=prior['id'],reference_id=prior['reference_id'],block_size=32,
                motion_mode='block',motion_precision='half',penalty=0,search_policy='adaptive_zero2'))
            baseline=attempt('parent32_band',parent,q,ref,prior,original,hud)
            old=next(r for r in oldrows if r['scene']==case['scene'] and r['id']==prior['id'])
            assert h.raw(baseline['base_packet'],h.HERE)==h.raw(old['baseline']['base_packet'],h.h.HERE)
            full,full_ms=elapsed(lambda:h.split.analyze16(h.m,h.adaptive,parent,ref))
            trials=[attempt('full16_'+mode,full,q,ref,prior,original,hud,mode) for mode in ('incumbent','band')]
            for idx,a in enumerate(trials):
                assert h.raw(a['base_packet'],h.HERE)==h.raw(old['trials'][idx]['base_packet'],h.h.HERE)
            analyses={};analysis_ms={};selections={}
            for budget in (25,50):
                child,ms=elapsed(lambda:h.selective.analyze16(h.m,h.adaptive,parent,ref,budget=budget))
                analyses[str(budget)]=child.work;analysis_ms[str(budget)]=ms
                for mode in ('incumbent','band'):
                    a=attempt('selective'+str(budget)+'_'+mode,child,q,ref,prior,original,hud,mode)
                    a['budget_percent']=budget;trials.append(a)
            for trial in trials:
                trial['qualifies_against_parent32']=qualify(trial,baseline)
                trial['qualified']=qualify(trial,control)
            for label,prefix in (('full','full16_'),('25','selective25_'),('50','selective50_')):
                selected=min([control]+[a for a in trials if a['kind'].startswith(prefix) and a['qualified']],key=lambda a:a['complete_bytes'])
                selections[label]=dict(kind=selected['kind'],complete_bytes=selected['complete_bytes'],hybrid=selected['hybrid'])
            all_attempts=[baseline]+trials
            row=dict(scene=case['scene'],id=prior['id'],key=prior['key'],reference_id=prior['reference_id'],
                reference_tag=parent.reference_tag.hex(),source_sha256=srcrow['common_yuv420_u8_sha256'],
                background=bg,hud_packet=prior['hud_packet'],hud_bytes=len(hud),binding_bytes=60,
                source_slot=prior['source_slot'],destination_slot=prior['destination_slot'],
                parent_analysis=parent.work,full_analysis=full.work,selective_analysis=analyses,
                parent_analysis_ms=parent_ms,full_analysis_ms=full_ms,selective_analysis_ms=analysis_ms,
                baseline=baseline,control_baseline=control,offline_control_decode_metric_ms=offline_control_ms,
                trials=trials,selections=selections,
                all_paid_host_ms=parent_ms+full_ms+sum(analysis_ms.values())+sum(a['encode_ms']+a['quality_ms']+a['bind_ms'] for a in all_attempts))
            rows.append(row)
            ref=control_pixels
            print(json.dumps(dict(scene=case['scene'],frame=prior['id'],control_bytes=control['complete_bytes'],
                trials=[(a['kind'],a['complete_bytes'],a['qualified']) for a in trials])),flush=True)
    summary=dict(frames=len(rows),raw_trial_packets=6*len(rows),all_actual_probe_packets=7*len(rows),
        control_complete_bytes=sum(r['control_baseline']['complete_bytes'] for r in rows),
        control_source_rgb_sse=sum(r['control_baseline']['hybrid']['active_squared_error'] for r in rows),
        mean_all_paid_host_ms=sum(r['all_paid_host_ms'] for r in rows)/len(rows),
        parent_search_samples=sum(r['parent_analysis']['search']['sad_sample_operations'] for r in rows),
        all_under_cap_cp27_profiles_accepted=all(a['cp27_profile_accepted'] for r in rows for a in [r['baseline']]+r['trials']))
    for label,prefix in (('full','full16_'),('25','selective25_'),('50','selective50_')):
        group=[a for r in rows for a in r['trials'] if a['kind'].startswith(prefix)]
        bands=[a for a in group if a['mode']=='band']
        analysis=[r['full_analysis'] if label=='full' else r['selective_analysis'][label] for r in rows]
        timing=[r['full_analysis_ms'] if label=='full' else r['selective_analysis_ms'][label] for r in rows]
        summary[label]=dict(selected_frames=sum(r['selections'][label]['kind']!='accepted_control' for r in rows),
            qualified_raw_trials=sum(a['qualified'] for a in group),
            qualified_against_parent32_trials=sum(a['qualifies_against_parent32'] for a in group),
            selected_complete_bytes=sum(r['selections'][label]['complete_bytes'] for r in rows),
            selected_source_rgb_sse=sum(r['selections'][label]['hybrid']['active_squared_error'] for r in rows),
            raw_band_complete_bytes=sum(a['complete_bytes'] for a in bands),
            raw_band_source_rgb_sse=sum(a['hybrid']['active_squared_error'] for a in bands),
            raw_band_motion_bytes=sum(a['motion_bytes'] for a in bands),
            raw_band_residual_bytes=sum(a['residual_bytes'] for a in bands),
            raw_band_decoder_reference_reads=sum(a['work']['decoder_reference_sample_reads'] for a in bands),
            refinement_search_samples=sum(a['search']['sad_sample_operations'] for a in analysis),
            refinement_reference_reads=sum(a['search']['reference_sample_fetches'] for a in analysis),
            mean_analysis_ms=sum(timing)/len(rows),
            mean_additional_host_ms=(sum(timing)+sum(a['encode_ms']+a['quality_ms']+a['bind_ms'] for a in group))/len(rows))
    assert h.pins()==before
    data=dict(schema='gamebub-selective-v34',source_sha256=before,summary=summary,rows=rows,
        uniform_GM27_motion_map=True,HM34_dependency=False,physical_30fps_proven=False,causal_campaign=False,
        environment=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform()),
        scope=['24 retained inputs, actual prior accepted v32 band_control reference, also v33 control parity lineage. Trial selection never updates history.',
            'Admission compares actual complete CP27 bytes and decoded current-source RGB SSE to actual accepted control. All losses retained.',
            'Paid includes parent search/analysis and parent base encode; full v33 child analysis and both incumbent/band encodes; selective25/50 analysis and both incumbent/band encodes; RGB metrics and CP27 binding.',
            'No HM34 accounting: all costs are actual uniform GM27 maps. Selection uses current source, reference and parent predictor only, never acceptance quality.',
            'Excludes fixture read/conversion, retained HU25 generation, retained control decode/metric extraction, debug decode, archives, transport/display. One host timing sample per frame.',
            'Fixed-reference training probe only. No causal, fps, combined-gain or hardware claim.'])
    (h.HERE/'results.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n')
    (h.HERE/'sourcepins.json').write_text(json.dumps(before,indent=2)+'\n')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
