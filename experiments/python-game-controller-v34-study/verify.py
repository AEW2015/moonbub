#!/usr/bin/env python3
"""Offline frame, source, causal-bank, motion and paid-work replay for CP34."""
import json
import math
import numpy as np
import helpers as h
b=h.module('controller34_benchmark_replay',h.HERE/'benchmark.py')
from controller import choose,complete

def main():
    d=h.load(h.HERE/'results.json');assert d['schema']=='gamebub-controller-v34'
    complete(d['cases']);assert not d['physical_30fps_proven'] and not d['new_RTL_implemented']
    for path,digest in d['source_sha256'].items():assert h.sha(h.ROOT/path)==digest,path
    inputs=h.load(h.n.V24/'results.json')['inputs'];previous=h.load(h.HERE.parent/'python-game-global-v33-study/results.json')['cases']
    pairs=trials=hm_trials=words=controls=searches=0
    for case in d['cases']:
        inp=next(v for v in inputs if v['scene']==case['scene'])
        old=next(v for v in previous if v['scene']==case['scene'] and v['policy']=='band_control')
        ref=None;rid=h.m.NO_REF;slot=0;rx=h.p.Receiver()
        for row,src,prior in zip(case['rows'],inp['rows'],old['rows'],strict=True):
            fid=row['id'];key=fid%24==0
            if key:ref=None;rid=h.m.NO_REF;slot=0
            tag=h.m.base.ZERO_TAG.hex() if key else h.m.C.reference_tag(ref).hex()
            assert row['key']==key and row['reference_id']==rid and row['reference_tag']==tag
            assert row['source_sha256']==src['common_yuv420_u8_sha256']
            assert row['source_slot']==(255 if key else slot) and row['destination_slot']==(0 if key else 1-slot)
            source,original=h.n.source(src),h.n.original(src)
            expected_groups=[];winner=None;decoded={};metas={}
            for a in row['attempts']:
                base,pair=h.raw(a['base_packet']),h.raw(a['packet']);meta=h.p.parse_pair(pair)
                assert meta['base']==base and meta['frame_id']==fid and meta['base_meta']['reference_tag'].hex()==tag
                assert len(pair)==a['complete_bytes']==len(base)+row['hud_bytes']+60
                assert len(base)==a['base_bytes'] and a['wire_magic']==base[:4].decode()
                pixels,bm=h.frame.decode(base,ref,expected_epoch=25,expected_reference_id=None if key else rid)
                assert bm['reconstructed_tag'].hex()==a['reconstructed_tag']
                assert bm['block_size']==a['block_size'] and bm['vector_bytes']==a['motion_bytes']
                assert sum(bm['plane_lengths'])==a['residual_bytes'] and bm['qmap_bytes']==a['qmap_bytes']
                np.testing.assert_array_equal(bm['scale_map'],h.m.roi.declared_map(720,480,h.n.ROIS,8,a['background']))
                hybrid=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS))
                assert h.n.metric(original,hybrid)==a['hybrid'] and h.n.digest(hybrid)==a['hybrid_sha256']
                reads=0 if key else h.m.taps.predict_with_info(ref,bm['vectors'],bm['block_size'])[1]['reference_sample_fetches']
                assert reads==a['work']['decoder_reference_sample_reads']
                k=(a['background'],a['kind']);decoded[k]=pixels;metas[k]=bm;trials+=1
                if a['wire_magic']=='GM34':hm_trials+=1
            backgrounds=sorted({a['background'] for a in row['attempts']});assert backgrounds in ([16],[16,32])
            for bg in backgrounds:
                group=[a for a in row['attempts'] if a['background']==bg]
                kinds=['zero'] if key else ['zero','half32'];control_kinds=kinds+[v+'_band' for v in kinds]
                children_kinds=[] if key or case['policy']=='control' else ['child','child_HM34','child_band','child_band_HM34']
                assert [a['kind'] for a in group]==control_kinds+children_kinds
                controls_group=group[:len(control_kinds)];children=group[len(control_kinds):]
                before=[(a['cap_fit'],a['quality_eligible']) for a in controls_group]
                shadow,_=h.select30.select_tier(controls_group,'band_strict')
                assert before==[(a['cap_fit'],a['quality_eligible']) for a in controls_group]
                old_qualified=[(a['cap_fit'],a['quality_eligible'],a['qualified']) for a in children]
                selected=choose(shadow,children)
                assert old_qualified==[(a['cap_fit'],a['quality_eligible'],a['qualified']) for a in children]
                if selected is not None:
                    assert winner is None and bg==backgrounds[-1];winner=selected
                    assert row['shadow_kind']==shadow['kind'] and row['shadow_complete_bytes']==shadow['complete_bytes']
                    assert row['shadow_source_sse']==shadow['hybrid']['active_squared_error']
                expected_groups.extend(f'{bg}:{k}' for k in kinds)
                if children:
                    expected_groups.append(f'{bg}:child')
                    for kind in ('child','child_band'):
                        lm,hm=metas[(bg,kind)],metas[(bg,kind+'_HM34')]
                        np.testing.assert_array_equal(lm['vectors'],hm['vectors'])
                        for x,y in zip(decoded[(bg,kind)],decoded[(bg,kind+'_HM34')],strict=True):np.testing.assert_array_equal(x,y)
                        assert lm['reference_tag']==hm['reference_tag'] and lm['reconstructed_tag']==hm['reconstructed_tag']
                        for x,y in zip(lm['coefficients'],hm['coefficients'],strict=True):np.testing.assert_array_equal(x,y)
            assert [g['id'] for g in row['encode_groups']]==expected_groups
            assert len(set(expected_groups))==len(expected_groups)
            if not key and case['policy']!='control':
                bg=backgrounds[0];parent=metas[(bg,'half32')]['vectors']
                fn=(lambda:h.full.refine(h.adaptive,source,ref,parent)) if case['policy']=='hierarchy_full' else (lambda:h.selective.refine(h.adaptive,source,ref,parent,budget=25))
                vector,work=fn();actual=row['analyses']['child']['work']['search']
                assert {k:v for k,v in actual.items() if not k.endswith('_ms')}=={k:v for k,v in work.items() if not k.endswith('_ms')}
                np.testing.assert_array_equal(vector,metas[(bg,'child')]['vectors'])
                component,info=h.frame.prepare_motion(parent,vector,720,480);assert info==row['component_info']
                for a in row['attempts']:
                    if a['wire_magic']=='GM34':
                        wire=h.raw(a['base_packet']);start=h.frame.HEADER.size+a['qmap_bytes']
                        assert wire[start:start+a['motion_bytes']]==component.packet
                searches+=1
            else:assert row['component_ms']==0. and row['component_info'] is None
            assert winner is not None and [a for a in row['attempts'] if a['selected']]==[winner]
            assert row['selected_kind']==winner['kind'] and row['hybrid']==winner['hybrid']
            assert row['wire_magic']==winner['wire_magic'] and row['base_bytes']==winner['base_bytes']
            assert row['body_bytes']==winner['complete_bytes']<=row['shadow_complete_bytes']
            assert row['hybrid']['active_squared_error']<=row['shadow_source_sse']
            paid=sum(v['wall_ms'] for v in row['analyses'].values())+sum(g['wall_ms'] for g in row['encode_groups'])+row['component_ms']+row['selection_ms']
            paid+=sum(a['wrap_ms']+a['quality_ms']+a['bind_ms'] for a in row['attempts'])
            assert math.isclose(paid,row['paid_policy_ms'],abs_tol=1e-9)
            pair=h.raw(row['packet']);pixels,patches,ack=rx.receive(pair);h.p.validate_ack(ack,pair)
            assert pair==h.raw(winner['packet']) and ack==h.raw(row['ack']) and len(pair)==row['body_bytes']
            assert row['reconstructed_tag']==h.m.C.reference_tag(pixels).hex()
            for patch,(x,y,w,hh) in zip(patches,h.n.RECTS,strict=True):np.testing.assert_array_equal(patch['words'],original[y:y+hh,x:x+w])
            hybrid=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),tuple(p['words'] for p in patches))
            assert h.n.metric(original,hybrid)==row['hybrid'] and h.n.digest(hybrid)==row['hybrid_sha256']
            if case['policy']=='control':
                assert h.raw(row['base_packet'])==h.raw(prior['base_packet'],h.HERE.parent/'python-game-global-v33-study')
                assert row['hybrid']==prior['hybrid'];controls+=1
            ref,rid,slot=pixels,fid,row['destination_slot'];pairs+=1;words+=21120
        assert b.summary(case['rows'])==case['summary']
    assert pairs==288 and words==6082560 and controls==96 and searches==184
    print(json.dumps(dict(accepted_CP34_frames=pairs,actual_candidate_frames=trials,actual_GM34_candidates=hm_trials,
                         exact_HUD_words=words,exact_legacy_control_base_frames=controls,causal_child_searches=searches,
                         source_pins=len(d['source_sha256']),physical_30fps_proven=False,new_RTL_implemented=False)))
if __name__=='__main__':main()
