#!/usr/bin/env python3
"""Independent archived decode/quality/admission; optional exact re-encoding."""
import argparse
import json
import numpy as np
import helpers as h


def independent_selection(parent,budget):
    """Screen parent prediction directly, without calling selective scorer."""
    ch,cw=(parent.height+15)//16,(parent.width+15)//16
    cost=np.zeros((ch,cw),np.int64);count=np.zeros_like(cost)
    for plane,(src,pred) in enumerate(zip(parent.source,parent.prediction)):
        bs=16 if plane==0 else 8;weight=1 if plane==0 else 2
        for y in range(ch):
            for x in range(cw):
                a=src[y*bs:(y+1)*bs:4,x*bs:(x+1)*bs:4].astype(np.int64)
                b=pred[y*bs:(y+1)*bs:4,x*bs:(x+1)*bs:4].astype(np.int64)
                cost[y,x]+=weight*int(np.abs(a-b).sum());count[y,x]+=weight*a.size
    means=cost/np.maximum(count,1)
    ph,pw=(parent.height+31)//32,(parent.width+31)//32
    scores=np.zeros((ph,pw));active=np.zeros((ph,pw),bool)
    for y in range(ph):
        for x in range(pw):
            sl=np.s_[2*y:2*y+2,2*x:2*x+2];a=means[sl]
            mean=int(cost[sl].sum())/max(int(count[sl].sum()),1)
            scores[y,x]=mean+float(a.max()-a.min());active[y,x]=mean>2
    order=sorted(range(ph*pw),key=lambda i:(-scores.ravel()[i],i))
    mask=np.zeros(ph*pw,bool);mask[order[:(ph*pw*budget+99)//100]]=True
    return scores,mask.reshape(ph,pw),active & mask.reshape(ph,pw)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--archives-only',action='store_true');args=parser.parse_args()
    data=h.load(h.HERE/'results.json');assert data['schema']=='gamebub-selective-v34'
    assert data['causal_campaign'] is False and data['physical_30fps_proven'] is False
    assert data['uniform_GM27_motion_map'] and not data['HM34_dependency']
    for path,sha in data['source_sha256'].items():assert h.sha(h.ROOT/path)==sha,path
    assert h.load(h.HERE/'sourcepins.json')==data['source_sha256']
    checked=frames=0;selected={label:0 for label in ('full','25','50')}
    for case,inp in h.cases():
        ref=None
        for prior,src in zip(case['rows'][:12],inp['rows'][:12]):
            row=next(r for r in data['rows'] if r['scene']==case['scene'] and r['id']==prior['id'])
            source,original=h.n.source(src),h.n.original(src)
            assert h.digest(b''.join(a.astype('u1').tobytes() for a in source))==row['source_sha256']==src['common_yuv420_u8_sha256']
            tag=h.m.base.ZERO_TAG if ref is None else h.m.C.reference_tag(ref)
            assert tag.hex()==row['reference_tag']==prior['reference_tag']
            hud=h.raw(row['hud_packet'],h.ROOT/row['hud_packet']['directory'])
            control=row['control_baseline'];control_packet=h.raw(control['base_packet'],h.HERE)
            assert control_packet==h.raw(prior['base_packet'],h.h.h.V32)
            control_pixels,_=h.m.decode(control_packet,ref,expected_epoch=25,
                expected_reference_id=None if row['key'] else row['reference_id'])
            control_hybrid=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(control_pixels)),
                tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS))
            assert h.n.metric(original,control_hybrid)==control['hybrid']==prior['hybrid']
            assert control['complete_bytes']==prior['body_bytes']
            assert h.raw(control['packet'],h.HERE)==h.raw(prior['packet'],h.h.h.V32)
            attempts=[row['baseline']]+row['trials']
            encoded=[];prepared=[]
            if not args.archives_only:
                parent=h.adaptive.analyze_with(h.m.base,source,ref,epoch=25,frame_id=prior['id'],reference_id=prior['reference_id'],
                    block_size=32,motion_mode='block',motion_precision='half',penalty=0,search_policy='adaptive_zero2')
                full=h.split.analyze16(h.m,h.adaptive,parent,ref)
                prepared=[parent,full,full]
                for budget in (25,50):
                    child=h.selective.analyze16(h.m,h.adaptive,parent,ref,budget=budget)
                    prepared.extend((child,child))
                    if not parent.key:
                        scores,mask,active=independent_selection(parent,budget)
                        work=row['selective_analysis'][str(budget)]['search']
                        np.testing.assert_array_equal(scores,work['group_scores'])
                        np.testing.assert_array_equal(mask,work['selected_group_mask'])
                        np.testing.assert_array_equal(active,work['active_group_mask'])
                        pv=h.m.base.unpack_vectors(parent.vector_bytes,(parent.width+31)//32,(parent.height+31)//32)
                        cv=h.m.base.unpack_vectors(child.vector_bytes,(parent.width+15)//16,(parent.height+15)//16)
                        inherit=np.repeat(np.repeat(pv,2,axis=0),2,axis=1)[:cv.shape[0],:cv.shape[1]]
                        cm=np.repeat(np.repeat(active,2,axis=0),2,axis=1)[:cv.shape[0],:cv.shape[1]]
                        np.testing.assert_array_equal(cv[~cm],inherit[~cm])
                q=h.m.roi.declared_map(720,480,h.n.ROIS,8,row['background'])
                for p,a in zip(prepared,attempts):
                    encoded.append(h.m.encode_prepared(p,q) if a['mode']=='incumbent' else h.band.encode_with(h.m,p,q,policy='band_strict'))
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
                assert meta['vector_bytes']==a['motion_bytes'] and meta['block_size']==a['block_size']
                assert len(pair)<=49152 if a['cap_fit'] else len(pair)>49152
                if not args.archives_only:
                    assert packet==encoded[i][0]
                    assert h.m.decoder_tap_counts(prepared[i])['reference_sample_fetches']==a['work']['decoder_reference_sample_reads']
                    for av,bv in zip(pixels,encoded[i][1]):np.testing.assert_array_equal(av,bv)
                if i:
                    parent_qualified=len(pair)<=49152 and len(pair)<attempts[0]['complete_bytes'] and a['hybrid']['active_squared_error']<=attempts[0]['hybrid']['active_squared_error']
                    assert parent_qualified==a['qualifies_against_parent32']
                    qualified=len(pair)<=49152 and len(pair)<control['complete_bytes'] and a['hybrid']['active_squared_error']<=control['hybrid']['active_squared_error']
                    assert qualified==a['qualified']
                checked+=1
            for label,prefix in (('full','full16_'),('25','selective25_'),('50','selective50_')):
                winner=min([control]+[a for a in attempts[1:] if a['kind'].startswith(prefix) and a['qualified']],key=lambda a:a['complete_bytes'])
                assert winner['kind']==row['selections'][label]['kind']
                assert winner['complete_bytes']==row['selections'][label]['complete_bytes']
                assert winner['hybrid']==row['selections'][label]['hybrid']
                selected[label]+=winner is not control
            assert row['all_paid_host_ms']>=row['parent_analysis_ms']+row['full_analysis_ms']+sum(row['selective_analysis_ms'].values())
            ref=control_pixels;frames+=1
    assert frames==24 and checked==168
    for label in selected:
        assert selected[label]==data['summary'][label]['selected_frames']
        assert sum(r['selections'][label]['complete_bytes'] for r in data['rows'])==data['summary'][label]['selected_complete_bytes']
        assert sum(r['selections'][label]['hybrid']['active_squared_error'] for r in data['rows'])==data['summary'][label]['selected_source_rgb_sse']
    print(json.dumps(dict(source_frames=frames,verified_actual_packets=checked,qualified_selected_frames=selected,
                         exact_fixed_reference_reencode=not args.archives_only,independent_screen_verification=not args.archives_only)))


if __name__=='__main__':main()
