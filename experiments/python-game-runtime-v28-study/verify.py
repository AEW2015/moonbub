#!/usr/bin/env python3
"""Retained v28 same-wire, source-pixel, policy and tap accounting replay."""
from pathlib import Path
import importlib.util
import json
import sys
import hashlib
import zlib
import numpy as np
import model as m
import protocol as p

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('runtime28_verify_helpers',HERE/'benchmark.py')
b=importlib.util.module_from_spec(spec);sys.modules[spec.name]=b;spec.loader.exec_module(b)


def raw(d,folder=HERE):
    q=Path(d['path']);assert not q.is_absolute() and '..' not in q.parts
    assert 0<d['raw_bytes']<=1000000
    packed=(folder/q).read_bytes();assert hashlib.sha256(packed).hexdigest()==d['stored_sha256']
    dc=zlib.decompressobj();out=dc.decompress(packed,d['raw_bytes']+1)
    assert dc.eof and not dc.unused_data and not dc.unconsumed_tail and len(out)==d['raw_bytes']
    assert hashlib.sha256(out).hexdigest()==d['raw_sha256'];return out


def pins(data):
    for path,sha in data['source_sha256'].items():
        q=Path(path);assert not q.is_absolute() and '..' not in q.parts
        assert hashlib.sha256((ROOT/q).read_bytes()).hexdigest()==sha,path


def main():
    data=b.load(HERE/'results.json');parity=b.load(HERE/'parity.json');pins(data);pins(parity)
    assert len(data['cases'])==6 and data['schema']=='gamebub-runtime-v28'
    old=b.load(b.OLD/'results.json')['cases'];inputs=b.load(b.n.V24/'results.json')['inputs']
    parity_frames=0
    for c in parity['cases']:
        baseline=next(x for x in old if x['scene']==c['scene'] and x['policy']=='unified_causal')
        ref=None
        for r,prior in zip(c['rows'],baseline['rows']):
            packet=raw(r['packet']);assert packet==raw(prior['base_packet'],b.OLD)
            out,meta=m.decode(packet,None if r['key'] else ref,expected_epoch=25,expected_reference_id=None if r['key'] else r['reference_id'])
            assert meta['reconstructed_tag'].hex()==r['reconstructed_tag']==prior['reconstructed_tag'];ref=out;parity_frames+=1
    pairs=attempts=words=exact=0
    for c in data['cases']:
        baseline=next(x for x in old if x['scene']==c['scene'] and x['policy']=='unified_causal')
        inp=next(x for x in inputs if x['scene']==c['scene']);rx=p.Receiver(epoch=25);ref=None;refid=m.NO_REF;slot=0
        assert [r['id'] for r in c['rows']]==list(range(48))
        for r,src,prior in zip(c['rows'],inp['rows'],baseline['rows']):
            key=r['id']%24==0
            if key:ref=None;refid=m.NO_REF;slot=0
            assert r['key']==key and r['reference_id']==refid and r['source_slot']==(255 if key else slot)
            assert r['destination_slot']==(0 if key else 1-slot)
            original=b.n.original(src);selected=[a for a in r['attempts'] if a['selected']];assert len(selected)==1
            for a in r['attempts']:
                bp=raw(a['base_packet']);pair=raw(a['packet']);assert len(bp)==a['base_bytes']
                assert len(pair)==a['complete_bytes']==len(bp)+r['hud_bytes']+60 and a['cap_fit']==(len(pair)<=49152)
                out,meta=m.decode(bp,ref,expected_epoch=25,expected_reference_id=None if key else refid)
                hybrid=b.n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(out)),tuple(original[y:y+h,x:x+w] for x,y,w,h in b.n.RECTS))
                assert b.n.metric(original,hybrid)==a['hybrid'] and b.n.digest(hybrid)==a['hybrid_rgb565_sha256']
                np.testing.assert_array_equal(meta['scale_map'],m.roi.declared_map(720,480,b.n.ROIS,8,a['background']))
                if a['kind']=='zero':assert not np.any(meta['vectors'])
                if key:assert a['work']['decoder_reference_sample_reads']==0
                else:
                    _,taps=m.taps.predict_with_info(ref,meta['vectors'],32)
                    assert taps['reference_sample_fetches']==a['work']['decoder_reference_sample_reads']
                if not a['cap_fit']:
                    state=rx.last_frame_id
                    try:rx.receive(pair)
                    except ValueError:pass
                    else:raise AssertionError('overcap received')
                    assert rx.last_frame_id==state
                attempts+=1
            chosen=None
            for bg in sorted({a['background'] for a in r['attempts']}):
                group=[a for a in r['attempts'] if a['background']==bg]
                assert [a['kind'] for a in group]==(['zero'] if key else ['zero','half32'])
                zero_sse=group[0]['hybrid']['active_squared_error']
                for a in group:assert a['quality_eligible']==(a['hybrid']['active_squared_error']<=zero_sse)
                eligible=[a for a in group if a['cap_fit'] and a['quality_eligible']]
                if eligible:chosen=min(eligible,key=lambda a:a['complete_bytes']);break
            assert chosen==selected[0]
            packet=raw(r['packet']);meta=p.parse_pair(packet)
            hud=raw(r['hud_packet'],ROOT/r['hud_packet']['directory'])
            assert meta['base']==raw(r['base_packet']) and meta['hud']==hud
            out,patches,ack=rx.receive(packet);assert ack==raw(r['ack']);p.validate_ack(ack,packet)
            for v,(x,y,w,h) in zip(patches,b.n.RECTS):np.testing.assert_array_equal(v['words'],original[y:y+h,x:x+w]);words+=w*h
            hybrid=b.n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(out)),tuple(v['words'] for v in patches))
            assert b.n.digest(hybrid)==r['hybrid_rgb565_sha256'] and b.n.metric(original,hybrid)==r['hybrid']
            assert len(packet)==r['body_bytes']==r['base_bytes']+r['hud_bytes']+60<=49152
            paid=sum(a['analysis_wall_ms'] for a in r['analyses'].values())+sum(a['encode_ms'] for a in r['attempts'])
            service=paid+sum(a['quality_ms']+a['bind_ms'] for a in r['attempts'])
            assert abs(paid-r['paid_base_encode_ms'])<1e-8 and abs(service-r['base_policy_service_ms'])<1e-8
            if c['policy']=='exhaustive':
                assert packet==raw(prior['packet'],b.OLD) and ack==raw(prior['ack'],b.OLD)
                assert r['hybrid']==prior['hybrid'] and r['hybrid_rgb565_sha256']==prior['hybrid_rgb565_sha256'];exact+=1
            ref,refid,slot=out,r['id'],0 if key else 1-slot;pairs+=1
        assert b.summarize(c['rows'],baseline)==c['summary']
    assert parity_frames==96 and pairs==288 and exact==96 and words==288*21120
    print(json.dumps(dict(source_pins=len(data['source_sha256']),paired_native_wire_parity_frames=parity_frames,
                          accepted_pairs=pairs,candidate_attempts=attempts,exact_v27_full_controller_frames=exact,
                          exact_hud_words=words,all_source_pixels_tags_selection_and_taps_replayed=True,physical_30fps_proven=False)))


if __name__=='__main__':main()
