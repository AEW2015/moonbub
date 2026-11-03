import dataclasses
import struct
import unittest
import numpy as np
import rate_motion as r


class RateMotionTests(unittest.TestCase):
    def rgb(self):return np.random.default_rng(1201).integers(0,256,(32,64,3),dtype=np.uint8)
    def scale(self):return np.full((2,4),16,np.uint8)
    def ack(self,enc,packet):
        i=r.identity(packet);return enc.ack(i['frame_id'],epoch=i['epoch'],frame_crc=i['body_tag'])
    def key(self,enc,rgb=None):
        d=enc.prepare(self.rgb() if rgb is None else rgb,0,scale_map=self.scale());self.ack(enc,d.packet);return d

    def test_preview_is_credit_reference_free_and_commit_is_selected_only(self):
        enc=r.Encoder();preview=enc.preview(self.rgb(),0,scale_map=self.scale())
        self.assertFalse(enc.pending);self.assertEqual(enc.last_issued,-1);self.assertIsNone(enc._anchor)
        selected=r.select(preview);self.assertEqual(len(selected.packet),min(len(c.packet) for c in preview.candidates))
        self.assertEqual(preview.common_stages['shared_key_reconstruction_count'],1)
        for c in preview.candidates:np.testing.assert_array_equal(c.key_planes[0],selected.key_planes[0])
        packet=enc.commit(preview,selected);self.assertEqual(set(enc.pending),{0})
        self.assertIsNone(enc._anchor);self.assertFalse(enc.can_prepare())
        with self.assertRaises(ValueError):enc.commit(preview,preview.candidates[-1])
        self.ack(enc,packet);self.assertEqual(enc.anchor_id,0)
        with self.assertRaises(ValueError):enc.commit(preview,selected)

    def test_key_pixels_match_frozen_gm_and_candidate_modes_independent(self):
        rgb=self.rgb();enc=r.Encoder(modes=('gm_zero','gm_global','bm_block'))
        p=enc.preview(rgb,0,scale_map=self.scale())
        expected=r.gm.Encoder().prepare(rgb,0,scale_map=self.scale())
        expected_rgb,_=r.gm.Receiver().receive(expected)
        for candidate in p.candidates:
            actual,info=r.Decoder().receive(candidate.packet);np.testing.assert_array_equal(actual,expected_rgb)
            self.assertEqual(info['key'],True)
        self.assertEqual(p.candidates[0].packet[r.HEADER.size:-4],expected)
        self.assertEqual(p.candidates[1].packet[r.HEADER.size:-4],expected)

    def test_all_cap_rejection_never_advances_even_after_expensive_preview(self):
        enc=r.Encoder();d=enc.prepare(self.rgb(),0,scale_map=self.scale(),frame_cap=100)
        self.assertFalse(d.accepted);self.assertFalse(enc.pending);self.assertEqual(enc.last_issued,-1)
        self.assertIsNone(enc._anchor);self.assertEqual(len(d.attempts),2)
        self.assertGreater(d.service_ms,0);self.assertTrue(all(not a['fits'] for a in d.attempts))
        self.key(enc);d=enc.prepare(self.rgb(),1,scale_map=self.scale(),frame_cap=100)
        self.assertFalse(d.accepted);self.assertEqual(enc.last_issued,0);self.assertEqual(enc.anchor_id,0)
        self.assertFalse(enc.pending);self.assertEqual(enc.read_pins,0)
        self.assertTrue(enc.prepare(self.rgb(),1,scale_map=self.scale()).accepted)

    def test_ack_requires_outer_tag_session_and_live_selected_identity(self):
        enc=r.Encoder();d=enc.prepare(self.rgb(),0,scale_map=self.scale());identity=r.identity(d.packet)
        inner=d.packet[r.HEADER.size:-4];inner_tag=r.zlib.crc32(inner[:-4])
        self.assertNotEqual(identity['body_tag'],inner_tag)
        for kwargs in ({'epoch':2,'frame_crc':identity['body_tag']},{'epoch':1,'frame_crc':inner_tag},
                       {'epoch':1,'frame_crc':identity['body_tag']^1}):
            with self.assertRaises(ValueError):enc.ack(0,**kwargs)
            self.assertIsNone(enc._anchor);self.assertIn(0,enc.pending)
        self.assertFalse(enc.ack(7,epoch=1,frame_crc=identity['body_tag']))
        self.assertTrue(enc.expire(0));self.assertFalse(self.ack(enc,d.packet));self.assertIsNone(enc._anchor)
        d=enc.prepare(self.rgb(),1,scale_map=self.scale());self.assertTrue(d.key);self.ack(enc,d.packet)
        self.assertEqual(enc.anchor_id,1)

    def test_two_credits_key_drain_and_p_expiration_keep_canonical_anchor(self):
        enc=r.Encoder();self.key(enc);anchor=enc._anchor
        a=enc.prepare(self.rgb(),1,scale_map=self.scale());b=enc.prepare(self.rgb(),2,scale_map=self.scale())
        self.assertEqual(enc.read_pins,2);self.assertFalse(enc.can_prepare())
        with self.assertRaises(ValueError):enc.preview(self.rgb(),3,scale_map=self.scale(),force_key=True)
        self.assertTrue(enc.expire(1));self.assertIs(enc._anchor,anchor);self.assertEqual(enc.read_pins,1)
        self.ack(enc,b.packet);self.assertEqual(enc.read_pins,0)
        d=enc.prepare(self.rgb(),3,scale_map=self.scale(),force_key=True)
        self.assertIs(enc._anchor,anchor);self.assertEqual(enc.anchor_id,0)
        self.assertFalse(enc.can_prepare());self.ack(enc,d.packet);self.assertEqual(enc.anchor_id,3)

    def test_mixed_gm_bm_temporal_decode_and_frozen_oracles(self):
        enc=r.Encoder(modes=('gm_zero','gm_global','bm_block'));rx=r.Decoder();rgb=self.rgb()
        for frame,chosen in enumerate((0,2,1,2,0)):
            source=np.roll(rgb,2*frame,axis=1);preview=enc.preview(source,frame,scale_map=self.scale(),force_key=frame==3)
            # Every preview is evaluated against the one ACKed key, even losers.
            for candidate in preview.candidates:
                oracle=(r.bm.Receiver() if candidate.mode=='bm_block' else r.gm.Receiver())
                oracle.anchor_id,oracle._anchor=enc.anchor_id,enc._anchor
                expected,_=oracle.receive(candidate.packet[r.HEADER.size:-4])
                independent=r.Decoder();independent.anchor_id,independent._anchor=enc.anchor_id,enc._anchor
                actual,_=independent.receive(candidate.packet)
                np.testing.assert_array_equal(actual,expected)
            candidate=preview.candidates[chosen];packet=enc.commit(preview,candidate);actual,info=rx.receive(packet)
            self.assertEqual(r.hashlib.sha256(actual.tobytes()).hexdigest(),enc.expected_hash(frame))
            if not info['key']:self.assertEqual(rx.anchor_id,enc.anchor_id)
            self.ack(enc,packet)
            for a,b in zip(rx._anchor,enc._anchor):np.testing.assert_array_equal(a,b)
        with self.assertRaises(ValueError):rx.receive(packet)

    def test_bad_outer_inner_body_and_reference_fail_atomically(self):
        enc=r.Encoder();d=enc.prepare(self.rgb(),0,scale_map=self.scale());rx=r.Decoder()
        with self.assertRaises(ValueError):rx.receive(d.packet[:-1]+bytes([d.packet[-1]^1]))
        fields=list(r.HEADER.unpack_from(d.packet));fields[4]+=1
        wrong=r._seal(r.HEADER.pack(*fields)+d.packet[r.HEADER.size:-4])
        with self.assertRaises(ValueError):rx.receive(wrong)
        inner=bytearray(d.packet[r.HEADER.size:-4]);inner[-8]^=127;inner=r._seal(bytes(inner[:-4]))
        corrupt=r._seal(d.packet[:r.HEADER.size]+inner)
        with self.assertRaises(ValueError):rx.receive(corrupt)
        self.assertEqual(rx.last_frame_id,-1);self.assertIsNone(rx._anchor)
        with self.assertRaises(ValueError):r.Decoder(epoch=2).receive(d.packet)
        with self.assertRaises(ValueError):r.Decoder(frame_cap=len(d.packet)-1).receive(d.packet)
        rx.receive(d.packet);self.ack(enc,d.packet)
        p=enc.prepare(self.rgb(),1,scale_map=self.scale())
        with self.assertRaises(ValueError):r.Decoder().receive(p.packet)

    def test_foreign_forged_and_stale_preview_candidate_ownership(self):
        a=r.Encoder();b=r.Encoder();rgb=self.rgb();p=a.preview(rgb,0,scale_map=self.scale());other=b.preview(rgb,0,scale_map=self.scale())
        with self.assertRaises(ValueError):a.commit(other,other.candidates[0])
        with self.assertRaises(ValueError):a.commit(p,other.candidates[0])
        forged=dataclasses.replace(p.candidates[0])
        with self.assertRaises(ValueError):a.commit(p,forged)
        with self.assertRaises(ValueError):a.commit(dataclasses.replace(p),p.candidates[0])
        selected=r.select(p);packet=a.commit(p,selected);self.ack(a,packet)
        stale=a.preview(rgb,1,scale_map=self.scale());d=a.prepare(rgb,2,scale_map=self.scale())
        with self.assertRaises(ValueError):a.commit(stale,stale.candidates[0])

    def test_static_zero_residual_and_all_losing_work_paid(self):
        enc=r.Encoder();rgb=np.full((32,64,3),128,np.uint8);self.key(enc,rgb)
        d=enc.prepare(rgb,1,scale_map=self.scale())
        self.assertEqual(d.selected_mode,'bm_block')
        self.assertEqual(len(d.attempts),2);self.assertTrue(d.attempts[1]['stages']['zero_residual'])
        self.assertGreater(d.attempts[1]['stages']['search']['luma_sad_samples'],0)
        self.assertGreater(d.attempts[0]['stages']['transform_quantize_ms'],0)
        self.assertGreaterEqual(d.service_ms,sum(a['stages']['candidate_total_ms'] for a in d.attempts))
        rgb,_=r.Decoder().receive(self.key(r.Encoder(),rgb).packet)

if __name__=='__main__':unittest.main()
