#!/usr/bin/env python3
"""Independent original-source metrics, guards, costs, causal and AU replay."""
import math
import json
import numpy as np
import helpers as h
from controller import choose,complete
b=h.module('guard35_explicit_benchmark',h.HERE/'benchmark.py')

def main():
    data=h.load(h.HERE/'results.json');assert data['schema']=='gamebub-controller-v35';complete(data['cases'])
    for path,digest in data['source_sha256'].items():assert h.sha(h.ROOT/path)==digest,path
    inputs=h.load(h.n.V24/'results.json')['inputs'];prior=h.load(h.HERE.parent/'python-game-controller-v34-study/results.json')['cases']
    frames=attempts=words=exact_controls=masked_frames=0
    for case in data['cases']:
        inp=next(c for c in inputs if c['scene']==case['scene']);old=next(c for c in prior if c['scene']==case['scene'] and c['policy']=='control')
        rx=h.p.Receiver();ref=None;rid=h.m.NO_REF;slot=0
        for row,src,control in zip(case['rows'],inp['rows'],old['rows'],strict=True):
            key=row['id']%24==0
            if key:ref=None;rid=h.m.NO_REF;slot=0
            tag=h.m.base.ZERO_TAG.hex() if key else h.m.C.reference_tag(ref).hex()
            assert row['key']==key and row['reference_id']==rid and row['reference_tag']==tag
            assert row['source_sha256']==src['common_yuv420_u8_sha256']
            assert row['source_slot']==(255 if key else slot) and row['destination_slot']==(0 if key else 1-slot)
            original=h.n.original(src);parts=tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS)
            if case['policy']=='guarded_core8':
                source=h.n.source(src);info={};masked=h.mask.mask_source(source,h.n.RECTS,policy='core8',work=info)
                assert info==row['mask_work'] and h.digest(b''.join(p.astype('u1').tobytes() for p in masked))==row['masked_source_sha256']
                before,after=h.m.ft.planes_to_rgb(source),h.m.ft.planes_to_rgb(masked);visible=np.ones((480,720),bool)
                for x,y,w,hh in h.n.RECTS:visible[y:y+hh,x:x+w]=False
                np.testing.assert_array_equal(before[visible],after[visible])
            else:assert row['mask_ms']==0 and row['masked_source_sha256'] is None and not row['mask_used']
            selected=None;expected_groups=[]
            for a in row['attempts']:
                packet,base=h.raw(a['packet']),h.raw(a['base_packet']);meta=h.p.parse_pair(packet)
                assert meta['base']==base and len(packet)==a['complete_bytes']==a['base_bytes']+row['hud_bytes']+60 and len(base)==a['base_bytes']
                pixels,bm=h.m.decode(base,ref,expected_epoch=25,expected_reference_id=None if key else rid)
                assert bm['reference_tag'].hex()==tag
                np.testing.assert_array_equal(bm['scale_map'],h.m.roi.declared_map(720,480,h.n.ROIS,8,a['background']))
                metric,sha=b.metric(pixels,original,parts);assert metric==a['hybrid'] and sha==a['hybrid_sha256']
                reads=0 if key else h.m.taps.predict_with_info(ref,bm['vectors'],32)[1]['reference_sample_fetches']
                assert reads==a['work']['decoder_reference_sample_reads']
                attempts+=1
            backgrounds=sorted({a['background'] for a in row['attempts']});assert backgrounds in ([16],[16,32])
            for bg in backgrounds:
                group=[a for a in row['attempts'] if a['background']==bg];kinds=['zero'] if key else ['zero','half32']
                expected=kinds+[k+'_band' for k in kinds]
                mask_kinds=['mask_'+k for k in expected] if case['policy']=='guarded_core8' else []
                assert [a['kind'] for a in group]==expected+mask_kinds
                controls,children=group[:len(expected)],group[len(expected):]
                flags=[(a['cap_fit'],a['quality_eligible']) for a in controls]
                shadow,_=h.select30.select_tier(controls,'band_strict')
                assert flags==[(a['cap_fit'],a['quality_eligible']) for a in controls]
                flags=[(a['cap_fit'],a['quality_eligible'],a['qualified']) for a in children]
                chosen=choose(shadow,children)
                assert flags==[(a['cap_fit'],a['quality_eligible'],a['qualified']) for a in children]
                if chosen is not None:
                    assert selected is None and bg==backgrounds[-1];selected=chosen
                    assert row['shadow_kind']==shadow['kind'] and row['shadow_complete_bytes']==shadow['complete_bytes'] and row['shadow_source_sse']==shadow['hybrid']['active_squared_error']
                expected_groups.extend(f'{bg}:{f}:{k}' for f in (('orig','mask') if children else ('orig',)) for k in kinds)
            assert [g['id'] for g in row['encode_groups']]==expected_groups and len(set(expected_groups))==len(expected_groups)
            assert selected is not None and [a for a in row['attempts'] if a['selected']]==[selected]
            assert row['selected_kind']==selected['kind'] and row['mask_used']==selected['kind'].startswith('mask_')
            assert row['body_bytes']==selected['complete_bytes']<=row['shadow_complete_bytes']
            assert row['hybrid']==selected['hybrid'] and row['hybrid']['active_squared_error']<=row['shadow_source_sse']
            paid=row['mask_ms']+sum(v['wall_ms'] for v in row['analyses'].values())+sum(g['wall_ms'] for g in row['encode_groups'])+row['selection_ms']
            paid+=sum(a['quality_ms']+a['bind_ms'] for a in row['attempts'])
            assert math.isclose(paid,row['paid_policy_ms'],abs_tol=1e-9)
            pair=h.raw(row['packet']);pixels,patches,ack=rx.receive(pair);h.p.validate_ack(ack,pair)
            assert ack==h.raw(row['ack']) and pair==h.raw(selected['packet']) and len(pair)==row['body_bytes']
            for actual,expected in zip(patches,parts,strict=True):np.testing.assert_array_equal(actual['words'],expected)
            metric,sha=b.metric(pixels,original,tuple(p['words'] for p in patches));assert metric==row['hybrid'] and sha==row['hybrid_sha256']
            if case['policy']=='control':
                assert pair==h.raw(control['packet'],h.HERE.parent/'python-game-controller-v34-study') and row['hybrid']==control['hybrid'];exact_controls+=1
            ref,rid,slot=pixels,row['id'],row['destination_slot'];frames+=1;words+=21120;masked_frames+=row['mask_used']
        assert b.total(case['rows'])==case['summary']
    native_frames=0
    keys=[(c['scene'],c['codec'],c['parameter']) for c in data['native_cases']];assert len(keys)==len(set(keys))
    for case in data['native_cases']:
        target=next(c for c in data['cases'] if c['scene']==case['scene'] and c['policy']=='guarded_core8')
        inp=next(c for c in inputs if c['scene']==case['scene'])
        assert [r['id'] for r in case['rows']]==list(range(48))
        packets=[dict(pts=r['pts'],dts=r['dts'],is_key=r['key'],data=h.raw(r['access_unit'])) for r in case['rows']]
        extra=h.raw(case['extradata']);out,dec=h.standard.decode(packets,extra,case['codec'])
        assert [p['pts'] for p in packets]==[p['dts'] for p in packets]==list(range(48)) and [p['pts'] for p in packets if p['is_key']]==[0,24]
        assert not dec['frames_only_at_decode_flush'] and all(v['output_pts']==[v['packet_pts']] for v in dec['decode_calls'])
        for src,row,tr in zip(inp['rows'],case['rows'],target['rows'],strict=True):
            source=h.n.source(src)
            if tr['mask_used']:source=h.mask.mask_source(source,h.n.RECTS,policy='core8')
            assert row['mask_used']==tr['mask_used'] and row['source_sha256']==h.digest(b''.join(v.astype('u1').tobytes() for v in source))
            original=h.n.original(src);parts=tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS)
            display=h.n.overlay(out[row['id']],parts)
            assert h.n.metric(original,display)==row['hybrid'] and h.n.digest(display)==row['hybrid_sha256']
            au=h.raw(row['access_unit']);hu=h.raw(row['hud_packet'],h.HUD)
            assert len(au)==row['access_unit_bytes'] and len(hu)==row['hud_bytes']
            assert row['extradata_bytes_charged']==(len(extra) if row['id']==0 else 0)
            assert row['body_bytes']==len(au)+len(hu)+60+row['extradata_bytes_charged']
            native_frames+=1
        sm=case['summary'];assert sum(r['body_bytes'] for r in case['rows'])==sm['complete_bytes']
        assert sum(r['hybrid']['active_squared_error'] for r in case['rows'])/sum(r['hybrid']['active_channel_samples'] for r in case['rows'])==sm['active_mse']
    for scene in ('mass-effect-2600','mass-effect-7200'):
        target=next(c['summary'] for c in data['cases'] if c['scene']==scene and c['policy']=='guarded_core8')
        for codec in ('libx265','libsvtav1'):
            assert any(c['scene']==scene and c['codec']==codec and c['summary']['active_mse']<=target['active_mse'] and c['summary']['cap_fit'] for c in data['native_cases'])
    assert frames==192 and words==4055040 and exact_controls==96
    print(json.dumps(dict(accepted_CP34_frames=frames,actual_candidates=attempts,exact_HUD_words=words,legacy_control_packet_parity=exact_controls,
                         masked_admissions=masked_frames,native_trace_decodes=native_frames,source_pins=len(data['source_sha256']),physical30fps_proven=False)))
if __name__=='__main__':main()
