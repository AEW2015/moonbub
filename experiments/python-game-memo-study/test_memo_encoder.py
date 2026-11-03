import unittest
from unittest.mock import patch
import numpy as np
import memo_encoder as m


class MemoTests(unittest.TestCase):
    def setUp(self):self.rgb=np.full((32,64,3),[40,60,80],np.uint8)
    def pair(self,frames,maps=None,modes=None,keys=()):
        a=m.gm.Encoder();b=m.Encoder();rx=m.gm.Receiver();packets=[]
        for i,rgb in enumerate(frames):
            kwargs={'quant_scale':16,'force_key':i in keys,'mode':'zero' if modes is None else modes[i]}
            if maps is not None:kwargs['scale_map']=maps[i]
            pa=a.prepare(rgb,i,**kwargs);pb=b.prepare(rgb,i,**kwargs)
            self.assertEqual(pa,pb);rx.receive(pb);packets.append(pb)
            a.ack(i,epoch=1);b.ack(i,epoch=1)
            for x,y in zip(a._anchor,b._anchor):np.testing.assert_array_equal(x,y)
        return b,packets

    def test_repeated_p_payload_exact_and_hit_skips_transforms(self):
        enc=m.Encoder();enc.prepare(self.rgb,0,quant_scale=16);enc.ack(0,epoch=1)
        enc.prepare(self.rgb,1,quant_scale=16);enc.ack(1,epoch=1)
        with patch.object(m.gm.ft,'forward',side_effect=AssertionError('cache hit must not transform')):
            p=enc.prepare(self.rgb,2,quant_scale=16)
        self.assertTrue(enc.last_memo_info['hit']);self.assertEqual(enc.last_memo_info['forward_transform_calls'],0)
        self.assertEqual(m.gm.parse(p,1)['frame_id'],2)

    def test_pixels_maps_mode_refresh_and_external_mutation_invalidate(self):
        rng=np.random.default_rng(12);frames=[self.rgb.copy() for _ in range(7)]
        frames[3][0,0]=[255,0,0];frames[4]=frames[3].copy()
        maps=[np.full((2,4),16,np.uint8) for _ in frames];maps[4][0,0]=8;maps[5]=maps[4].copy()
        modes=['zero']*5+['global','global']
        enc,packets=self.pair(frames,maps,modes,keys=(0,6))
        self.assertFalse(enc.last_memo_info['hit'])
        enc=m.Encoder();source=self.rgb.copy();enc.prepare(source,0,quant_scale=16);enc.ack(0,epoch=1)
        enc.prepare(source,1,quant_scale=16);enc.ack(1,epoch=1);source[0,0]=[240,0,0]
        enc.prepare(source,2,quant_scale=16);self.assertFalse(enc.last_memo_info['hit'])

    def test_expired_p_can_reuse_payload_but_unacked_key_cannot(self):
        enc=m.Encoder();enc.prepare(self.rgb,0,quant_scale=16)
        with self.assertRaises(ValueError):enc.prepare(self.rgb,1,quant_scale=16)
        enc.ack(0,epoch=1);enc.prepare(self.rgb,1,quant_scale=16);enc.expire(1)
        p=enc.prepare(self.rgb,2,quant_scale=16);self.assertTrue(enc.last_memo_info['hit'])
        self.assertEqual(m.gm.parse(p,1)['reference_id'],0)
        enc.ack(2,epoch=1);enc.prepare(self.rgb,3,quant_scale=16,force_key=True);enc.expire(3)
        self.assertEqual(enc.cache_bytes(),0);self.assertIsNone(enc._anchor)
        enc.prepare(self.rgb,4,quant_scale=16);self.assertTrue(enc.last_memo_info['key'])

    def test_cache_hits_obey_credit_monotonic_and_stale_preview_guards(self):
        enc=m.Encoder();enc.prepare(self.rgb,0,quant_scale=16);enc.ack(0,epoch=1)
        enc.prepare(self.rgb,1,quant_scale=16);enc.ack(1,epoch=1)
        prepared=enc.analyze(self.rgb,2)
        enc.prepare(self.rgb,2,quant_scale=16);enc.prepare(self.rgb,3,quant_scale=16)
        with self.assertRaises(ValueError):enc.prepare(self.rgb,4,quant_scale=16)
        with self.assertRaises(ValueError):enc.prepare(self.rgb,2,quant_scale=16)
        with self.assertRaises(ValueError):enc.encode_candidate(prepared,np.full((2,4),16,np.uint8))
        with self.assertRaises(ValueError):enc.ack(2,epoch=2)
        self.assertEqual(enc.anchor_id,0)

    def test_random_and_repeated_sequence_byte_exact(self):
        rng=np.random.default_rng(123);frames=[]
        for i in range(12):
            frames.append(frames[-1].copy() if i%3 else rng.integers(0,256,(32,64,3),dtype=np.uint8))
        enc,packets=self.pair(frames,keys=(0,6))
        self.assertEqual(len(packets),12);self.assertLess(enc.cache_bytes(),64*32*3+128*48+4096)


if __name__=='__main__':unittest.main()
