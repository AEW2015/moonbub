#!/usr/bin/env python3
"""Replay actual masked causal packets and every native AU against original RGB."""
import json
import time
import numpy as np
import helpers as h


def offline_coefficients(data):
    schedule_path=h.HERE.parent/'python-game-schedule-v32-study/model.py'
    schedule=h.module('opaque34_offline_schedule',schedule_path)
    prior=h.load(h.HERE.parent/'python-game-global-v33-study/results.json')['cases'];cases=[]
    for case in data['cases']:
        control=next(c for c in prior if c['scene']==case['scene'] and c['policy']=='band_control');rows=[]
        for row,old in zip(case['rows'],control['rows'],strict=True):
            outputs={}
            for name,packet in (('masked',h.raw(row['base_packet'],h.HERE)),
                                ('control',h.raw(old['base_packet'],h.HERE.parent/'python-game-global-v33-study'))):
                meta=h.m.parse(packet);kinds=[]
                for a in meta['coefficients']:
                    a=a.reshape(-1,64);kinds.extend(int(v) for v in np.where(np.any(a[:,1:]!=0,axis=1),2,np.where(a[:,0]!=0,1,0)))
                assert len(kinds)==8100
                timed=schedule.schedule(kinds,2);assert schedule.validate(timed)
                outputs[name]=dict(zero=kinds.count(0),dc=kinds.count(1),general=kinds.count(2),
                    two_bank_inverse_component_cycles=timed['done_cycles'],
                    conditional_ms_at_unclosed_100MHz=timed['done_cycles']/100000)
            rows.append(dict(id=row['id'],**outputs))
        summary={name:{kind:sum(r[name][kind] for r in rows) for kind in ('zero','dc','general')} for name in ('masked','control')}
        cases.append(dict(scene=case['scene'],rows=rows,summary=summary))
    return dict(schema='gamebub-opaque-offline-coefficients-v34',cases=cases,
        source_sha256={schedule_path.relative_to(h.ROOT).as_posix():h.sha(schedule_path)},
        paid_encoder_work=False,clock_MHz_assumed_unclosed=100,
        scope='Offline exact decoded coefficient counts and frozen two-bank inverse-component dependency model only. '
              'Exactly8100blocks/frame; no entropy/reference/color/HUD/CRC/network/display service, physical fit or native-FPS claim.')


def main():
    data=h.load(h.HERE/'results.json');assert data['schema']=='gamebub-opaque-v34'
    assert data['source_sha256']==h.pins() and data['producer_sha256']==h.producer_pins()
    inputs=h.load(h.n.V24/'results.json')['inputs'];frames=attempts=native_frames=negative=0;mask_samples=[]
    root_cases=h.load(h.V34/'results.json')['cases']
    for case in data['cases']:
        inp=next(i for i in inputs if i['scene']==case['scene']);rx=h.p.Receiver();ref=None;control_ref=None
        control=next(c for c in root_cases if c['scene']==case['scene'] and c['policy']=='control')
        for src,row,control_row in zip(inp['rows'],case['rows'],control['rows'],strict=True):
            source,masked,original,patches=h.source(src)
            start=time.perf_counter_ns();timed=h.mask.mask_source(source,h.n.RECTS);mask_ms=(time.perf_counter_ns()-start)/1e6
            for a,b in zip(timed,masked):np.testing.assert_array_equal(a,b)
            mask_samples.append(dict(scene=case['scene'],id=row['id'],mask_only_ms=mask_ms))
            assert row['original_control_bytes']==control_row['body_bytes']
            assert row['original_control_hybrid']==control_row['hybrid']
            if row['key']:control_ref=None
            control_packet=h.raw(control_row['base_packet'],h.V34)
            control_ref,_=h.m.decode(control_packet,control_ref,expected_epoch=25,
                expected_reference_id=None if row['key'] else control_row['reference_id'])
            control_display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(control_ref)),patches)
            assert h.n.metric(original,control_display)==control_row['hybrid']
            assert len(control_packet)+row['hud_bytes']+60==row['original_control_bytes']
            outside=np.ones((480,720),bool)
            for x,y,w,hh in h.n.RECTS:outside[y:y+hh,x:x+w]=False
            np.testing.assert_array_equal(h.m.ft.planes_to_rgb(source)[outside],h.m.ft.planes_to_rgb(masked)[outside])
            assert row['source_sha256']==h.digest(b''.join(v.astype('u1').tobytes() for v in source))
            assert row['masked_source_sha256']==h.digest(b''.join(v.astype('u1').tobytes() for v in masked))
            audit=h.requested_full_mask_audit(source,patches);assert audit==row['requested_full_mask_audit']
            negative+=not audit['visible_precodec_equal']
            if row['key']:ref=None
            tag=h.m.base.ZERO_TAG if ref is None else h.m.C.reference_tag(ref)
            assert tag.hex()==row['reference_tag']
            groups={}
            for a in row['attempts']:
                pair=h.raw(a['packet'],h.HERE);packet=h.raw(a['base_packet'],h.HERE)
                assert len(pair)==a['complete_bytes']==len(packet)+row['hud_bytes']+60
                if len(pair)<=49152:
                    meta=h.p.parse_pair(pair);assert meta['base']==packet
                else:
                    try:h.p.parse_pair(pair)
                    except ValueError:pass
                    else:raise AssertionError('overcap accepted')
                pixels,_=h.m.decode(packet,ref,expected_epoch=25,expected_reference_id=None if row['key'] else row['reference_id'])
                display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),patches)
                assert h.n.metric(original,display)==a['hybrid'] and h.n.digest(display)==a['hybrid_sha256']
                groups.setdefault(a['background'],[]).append(a);attempts+=1
            selected=None
            for bg in (16,32):
                if bg not in groups:break
                chosen,_=h.select30.select_tier(groups[bg],'band_strict')
                if chosen is not None:selected=chosen;break
            assert selected['kind']==row['selected_kind'] and selected['packet']==row['packet']
            pair=h.raw(row['packet'],h.HERE);pixels,parts,ack=rx.receive(pair)
            h.p.validate_ack(ack,pair);assert ack==h.raw(row['ack'],h.HERE)
            for part,expected in zip(parts,patches,strict=True):np.testing.assert_array_equal(part['words'],expected)
            display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),tuple(p['words'] for p in parts))
            assert h.n.metric(original,display)==row['hybrid'] and h.n.digest(display)==row['hybrid_sha256']
            ref=pixels;frames+=1
        assert [r['id'] for r in case['rows']]==list(range(48))
        assert [r['id'] for r in case['rows'] if r['key']]==[0,24]
        assert sum(r['body_bytes'] for r in case['rows'])==case['summary']['complete_bytes']
        assert sum(r['original_control_bytes'] for r in case['rows'])==case['baseline_summary']['complete_bytes']
    for case in data['native_cases']:
        if not case['supported']:continue
        packets=[dict(pts=r['pts'],dts=r['dts'],is_key=r['key'],data=h.raw(r['access_unit'],h.HERE)) for r in case['rows']]
        extras=h.raw(case['extradata'],h.HERE);outputs,work=h.standard.decode(packets,extras,case['encoder'])
        assert [p['pts'] for p in packets]==[p['dts'] for p in packets]==list(range(48))
        assert [p['pts'] for p in packets if p['is_key']]==[0,24]
        assert work['frames_only_at_decode_flush']==0 and all(c['output_pts']==[c['packet_pts']] for c in work['decode_calls'])
        inp=next(i for i in inputs if i['scene']==case['scene'])
        for src,row in zip(inp['rows'],case['rows'],strict=True):
            original=h.n.original(src);patches=tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS)
            display=h.n.overlay(outputs[row['id']],patches)
            assert h.n.metric(original,display)==row['hybrid'] and h.n.digest(display)==row['hybrid_sha256']
            hud=h.raw(row['hud_packet'],h.HUD)
            assert row['body_bytes']==row['access_unit_bytes']+len(hud)+60+(len(extras) if row['id']==0 else 0)
            native_frames+=1
        assert sum(r['body_bytes'] for r in case['rows'])==case['summary']['complete_bytes']
    assert frames==96 and len(data['cases'])==2
    evidence=offline_coefficients(data)
    path=h.HERE/'offline_coefficients.json'
    if path.exists():assert h.load(path)==evidence
    else:path.write_text(json.dumps(evidence,separators=(',',':'))+'\n')
    cost=h.HERE/'offline_mask_cost.json'
    if not cost.exists():cost.write_text(json.dumps(dict(mask_only_ms_samples=mask_samples,
        mean_mask_only_ms=sum(r['mask_only_ms'] for r in mask_samples)/96,
        sample_boundary='One postcampaign source-mask-only sample per retained source; includes copies and stores, excludes fixtures/color/equivalence proof/encoding.',
        logical_uint8_source_bytes=518400,actual_int16_source_bytes=1036800,
        logical_additional_masked_plane_bytes=518400,actual_additional_int16_masked_plane_bytes=1036800,
        constant_stores_per_frame=30712,luma_constant_stores=21120,chroma_constant_stores=9592,
        additional_decoder_format_or_state_bytes=0),separators=(',',':'))+'\n')
    print(json.dumps(dict(causal_custom_frames=frames,actual_custom_attempts=attempts,native_decoded_frames=native_frames,
        requested_full_mask_visible_failures=negative,safe_mask_visible_equivalence_frames=frames,
        safe_mask_exact_RGB8_outside_equivalence=True,original_source_metrics=True,all_actual_au_and_packet_archives=True,
        offline_coefficient_blocks_compared=96*8100*2)))


if __name__=='__main__':main()
