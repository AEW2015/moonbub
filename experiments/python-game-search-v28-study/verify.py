#!/usr/bin/env python3
"""Replay all saved candidate packets against actual accepted GM27 references."""
import hashlib
import json
import numpy as np
import benchmark as b


def main():
    data = b.load(b.HERE/'results.json')
    for name,digest in data['source_sha256'].items():
        assert b.sha(b.ROOT/name)==digest, name
    if (b.HERE/'sourcepins.json').exists():
        for name,digest in b.load(b.HERE/'sourcepins.json').items():
            assert b.sha(b.ROOT/name)==digest, name
    inp = b.load(b.n.V24/'results.json')['inputs']
    ref = None; refid = b.s.m.NO_REF; receiver = None; scene = None
    count = 0
    for row in data['rows']:
        if row['scene']!=scene:
            scene=row['scene']; ref=None; refid=b.s.m.NO_REF; receiver=b.p.Receiver(epoch=25)
        assert row['reference_id']==refid
        assert row['reference_tag']==(None if ref is None else b.s.m.C.reference_tag(ref).hex())
        sr = next(r for i in inp if i['scene']==scene for r in i['rows'] if r['id']==row['id'])
        original = b.n.original(sr)
        for policy,v in row['variants'].items():
            packet,pair = (b.n.raw(v[k],b.HERE) for k in ('base_packet','packet'))
            parsed = b.p.parse_pair(pair)
            assert parsed['base']==packet and v['complete_bytes']==len(pair) and v['base_bytes']==len(packet)
            decoded,meta = b.s.m.decode(packet,ref,expected_epoch=25,expected_reference_id=None if ref is None else refid)
            assert meta['reconstructed_tag'].hex()==v['reconstructed_tag']
            bare = b.s.m.C.corpus.rgb565(b.s.m.ft.planes_to_rgb(decoded))
            hybrid = b.n.overlay(bare,tuple(original[y:y+h,x:x+w] for x,y,w,h in b.n.RECTS))
            assert b.n.metric(original,hybrid)==v['hybrid']
            assert b.n.digest(hybrid)==v['hybrid_rgb565_sha256']
            if ref is not None:
                vectors = b.s.m.unpack_vectors(bytes.fromhex(v['vector_bytes']),23,15)
                assert np.max(np.abs(vectors.astype(np.int32)))<=18
                search = v['analysis']['search']
                if policy!='exhaustive':
                    cs,rs = b.s.POLICIES[policy]
                    ns = lambda st: sum((h+st-1)//st*((w+st-1)//st) for h,w in ((480,720),(240,360),(240,360)))
                    assert search['sad_sample_operations']==81*ns(cs)+25*ns(rs)
                    assert search['reference_sample_fetches']==81*ns(cs)+100*ns(rs)
                    assert search['candidate_block_cost_evaluations']==106*23*15
            else:
                assert v['analysis']['search']['sad_sample_operations']==0
            count+=1
        accepted = b.n.raw(row['accepted_packet'],b.V27)
        ref,patches,ack = receiver.receive(accepted)
        b.p.validate_ack(ack,accepted); refid=row['id']
        for patch,(x,y,w,h) in zip(patches,b.n.RECTS): np.testing.assert_array_equal(patch['words'],original[y:y+h,x:x+w])
    assert count==96
    for policy,summary in data['summaries'].items():
        variants=[r['variants'][policy] for r in data['rows']]
        assert summary['complete_bytes']==sum(v['complete_bytes'] for v in variants)
        assert summary['active_mse']==sum(v['hybrid']['active_squared_error'] for v in variants)/sum(v['hybrid']['active_channel_samples'] for v in variants)
    print(json.dumps(dict(verified_candidate_packets=count,verified_accepted_references=24,source_pins=len(data['source_sha256']),exact_hud=True)))


if __name__=='__main__': main()
