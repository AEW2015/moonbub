#!/usr/bin/env python3
"""Actual packet, independent quality/admission and exact fixed-reference replay."""
import argparse
import json
import numpy as np
import helpers as h


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--archives-only',action='store_true');args=parser.parse_args()
    data=h.load(h.HERE/'results.json');assert data['schema']=='gamebub-split-v33'
    assert data['causal_campaign'] is False and data['physical_30fps_proven'] is False
    for path,sha in data['source_sha256'].items():assert h.sha(h.ROOT/path)==sha,path
    checked=frames=selected=0
    for case,inp in h.cases():
        ref=None
        for prior,src in zip(case['rows'][:12],inp['rows'][:12]):
            row=next(r for r in data['rows'] if r['scene']==case['scene'] and r['id']==prior['id'])
            source,original=h.n.source(src),h.n.original(src)
            assert row['source_sha256']==src['common_yuv420_u8_sha256']
            assert h.digest(b''.join(a.astype('u1').tobytes() for a in source))==row['source_sha256']
            tag=h.m.base.ZERO_TAG if ref is None else h.m.C.reference_tag(ref)
            assert tag.hex()==row['reference_tag']==prior['reference_tag']
            hud=h.raw(row['hud_packet'],h.ROOT/row['hud_packet']['directory'])
            control=row['control_baseline']
            control_packet=h.raw(control['base_packet'],h.HERE)
            assert control_packet==h.raw(prior['base_packet'],h.h.V32)
            control_pixels,_=h.m.decode(control_packet,ref,expected_epoch=25,
                expected_reference_id=None if row['key'] else row['reference_id'])
            control_hybrid=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(control_pixels)),
                tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS))
            assert h.n.metric(original,control_hybrid)==control['hybrid']==prior['hybrid']
            assert control['complete_bytes']==prior['body_bytes']
            assert h.raw(control['packet'],h.HERE)==h.raw(prior['packet'],h.h.V32)
            if not args.archives_only:
                parent=h.adaptive.analyze_with(h.m.base,source,ref,epoch=25,frame_id=prior['id'],reference_id=prior['reference_id'],
                    block_size=32,motion_mode='block',motion_precision='half',penalty=0,search_policy='adaptive_zero2')
                child=h.split.analyze16(h.m,h.adaptive,parent,ref)
                q=h.m.roi.declared_map(720,480,h.n.ROIS,8,row['background'])
                encoded=[h.band.encode_with(h.m,parent,q,policy='band_strict'),h.m.encode_prepared(child,q),
                         h.band.encode_with(h.m,child,q,policy='band_strict')]
            attempts=[row['baseline']]+row['trials']
            for i,a in enumerate(attempts):
                packet,pair=h.raw(a['base_packet'],h.HERE),h.raw(a['packet'],h.HERE)
                assert len(pair)==len(packet)+len(hud)+60==a['complete_bytes']
                if len(pair)<=49152:
                    meta=h.protocol.parse_pair(pair);assert meta['base']==packet and meta['hud']==hud
                    assert meta['base_meta']['block_size']==(32 if i==0 else 16)
                else:
                    try:h.protocol.parse_pair(pair)
                    except ValueError:pass
                    else:raise AssertionError('overcap accepted')
                pixels,meta=h.m.decode(packet,ref,expected_epoch=25,expected_reference_id=None if row['key'] else row['reference_id'])
                assert [h.n.digest(v) for v in pixels]==a['output_plane_sha256']
                bare=h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels))
                hybrid=h.n.overlay(bare,tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS))
                assert h.n.metric(original,hybrid)==a['hybrid'] and h.n.digest(hybrid)==a['hybrid_sha256']
                assert meta['plane_lengths']==tuple(a['residual_plane_bytes'])
                assert meta['block_size']==a['block_size']
                if not args.archives_only:
                    assert packet==encoded[i][0]
                    for av,bv in zip(pixels,encoded[i][1]):np.testing.assert_array_equal(av,bv)
                if i:
                    parent_qualified=len(pair)<=49152 and len(pair)<attempts[0]['complete_bytes'] and a['hybrid']['active_squared_error']<=attempts[0]['hybrid']['active_squared_error']
                    assert parent_qualified==a['qualifies_against_parent32']
                    qualified=len(pair)<=49152 and len(pair)<control['complete_bytes'] and a['hybrid']['active_squared_error']<=control['hybrid']['active_squared_error']
                    assert qualified==a['qualified']
                checked+=1
            winner=min([control]+[a for a in attempts[1:] if a['qualified']],key=lambda a:a['complete_bytes'])
            assert winner['kind']==row['selected_kind'] and winner['complete_bytes']==row['selected_complete_bytes']
            selected+=winner is not control
            ref,_=h.m.decode(h.raw(prior['base_packet'],h.h.V32),ref,expected_epoch=25,
                expected_reference_id=None if row['key'] else row['reference_id'])
            frames+=1
    assert frames==24 and checked==72 and selected==data['summary']['selected_split_frames']
    assert sum(r['selected_complete_bytes'] for r in data['rows'])==data['summary']['selected_complete_bytes']
    print(json.dumps(dict(source_frames=frames,verified_actual_packets=checked,qualified_selected_frames=selected,
                         exact_fixed_reference_reencode=not args.archives_only)))


if __name__=='__main__':main()
