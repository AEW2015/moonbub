import dataclasses
import unittest
import numpy as np
import selector as s


class Clock:
    def __init__(self):self.ns=0
    def __call__(self):return self.ns
    def add(self,ms):self.ns+=int(ms*1e6)


class SelectiveTests(unittest.TestCase):
    def frame(self):return np.random.default_rng(1001).integers(0,256,(64,80,3),dtype=np.uint8)
    def config(self,**kwargs):return s.Config(rectangles=((0,0,16,16),(32,0,16,16)),**kwargs)

    def test_cap_includes_wrapper_and_encoded_bytes_are_reused(self):
        rgb=self.frame();base=s.hud.gm.Encoder().prepare(rgb,0);calls=[]
        def encoder(a,r):calls.append(r);return s.hud.encode_patch(a,r)
        one=s.hud.encode_patch(rgb,(0,0,16,16))
        cap=s.hud.FRAME.size+4+len(base)+4+len(one)
        d=s.select_frame(base,rgb,self.config(frame_cap=cap),patch_encoder=encoder)
        self.assertEqual(d.format,'GH01');self.assertEqual(len(d.selected),1)
        self.assertEqual(len(calls),2);self.assertEqual(len(d.attempts),2)
        self.assertLessEqual(len(d.packet),cap);self.assertEqual(d.selected_pixels,256)
        _,patches,_=s.hud.parse_frame(d.packet,1)
        self.assertEqual(len(patches),1)
        np.testing.assert_array_equal(patches[0]['words'],s.hud.corpus.rgb565(rgb)[:16,:16])

    def test_no_fitting_patch_falls_back_byte_identical_and_overcap_base_rejects(self):
        rgb=self.frame();base=s.hud.gm.Encoder().prepare(rgb,0)
        d=s.select_frame(base,rgb,self.config(frame_cap=len(base)))
        self.assertEqual(d.packet,base);self.assertEqual(d.format,'GM01');self.assertEqual(d.selected_pixels,0)
        d=s.select_frame(base,rgb,self.config(frame_cap=len(base)-1))
        self.assertFalse(d.accepted);self.assertIsNone(d.packet);self.assertEqual(d.reason,'base_over_cap')
        self.assertEqual(d.attempts,())

    def test_budget_fallback_charges_rejected_work_without_refund(self):
        rgb=self.frame();base=s.hud.gm.Encoder().prepare(rgb,0);clock=Clock();calls=[]
        def costly(a,r):
            calls.append(r);data=s.hud.encode_patch(a,r);clock.add(7);return data
        d=s.select_frame(base,rgb,self.config(work_budget_ms=5),clock_ns=clock,patch_encoder=costly,spent_before_ms=1)
        self.assertEqual(d.packet,base);self.assertTrue(d.deadline_hit)
        self.assertEqual(len(calls),1);self.assertEqual(len(d.attempts),1)
        self.assertEqual(d.service_ms,7);self.assertEqual(d.observed_total_ms,8)
        self.assertFalse(d.attempts[0]['selected_in_output'])
        d=s.select_frame(base,rgb,self.config(work_budget_ms=0),clock_ns=Clock(),patch_encoder=costly)
        self.assertEqual(d.packet,base);self.assertFalse(d.attempts)

    def test_temporal_formats_share_unmodified_yuv_anchor(self):
        enc=s.hud.gm.Encoder();pure=s.hud.gm.Receiver();rx=s.Decoder();rgb=self.frame()
        for i,limit in enumerate((49152,1,49152)):
            source=(rgb+i*5).astype(np.uint8);base=enc.prepare(source,i)
            if limit==1:cfg=self.config(frame_cap=len(base))
            else:cfg=self.config()
            d=s.select_frame(base,source,cfg);actual,info=rx.receive(d.packet);expected,_=pure.receive(base)
            self.assertEqual(info['base_rgb_sha256'],s.hud.hashlib.sha256(expected.tobytes()).hexdigest())
            self.assertEqual(info['base_rgb_sha256'],enc.expected_hash(i))
            for a,b in zip(rx.base._anchor,pure._anchor):np.testing.assert_array_equal(a,b)
            if d.selected:
                for p in d.selected:
                    x,y,w,h=p['rect'];np.testing.assert_array_equal(s.hud.corpus.rgb565(actual)[y:y+h,x:x+w],s.hud.corpus.rgb565(source)[y:y+h,x:x+w])
            self.assertEqual(rx.base.anchor_id,0);enc.ack(i,epoch=1)

    def test_attempt_limit_invalid_patch_and_bad_base(self):
        rgb=self.frame();base=s.hud.gm.Encoder().prepare(rgb,0);calls=[]
        def encoder(a,r):calls.append(r);return s.hud.encode_patch(a,r)
        d=s.select_frame(base,rgb,self.config(max_attempts=1),patch_encoder=encoder)
        self.assertEqual(len(calls),1);self.assertEqual(len(d.attempts),1)
        def bad(a,r):return b'bad'
        with self.assertRaises(ValueError):s.select_frame(base,rgb,self.config(),patch_encoder=bad)
        with self.assertRaises(ValueError):s.select_frame(base[:-1]+bytes([base[-1]^1]),rgb,self.config())
        with self.assertRaises(ValueError):s.Decoder().receive(b'nope')

    def test_bad_patch_and_overcap_do_not_commit_temporal_state(self):
        rgb=self.frame();enc=s.hud.gm.Encoder();rx=s.Decoder()
        base=enc.prepare(rgb,0);d=s.select_frame(base,rgb,self.config());rx.receive(d.packet);enc.ack(0,epoch=1)
        base=enc.prepare(rgb,1);d=s.select_frame(base,rgb,self.config())
        altered=bytearray(d.packet[:-4]);offset=s.hud.FRAME.size+len(base)+4
        altered[offset]=ord('X');bad=s.hud._crc(bytes(altered))
        with self.assertRaises(ValueError):rx.receive(bad)
        self.assertEqual(rx.base.last_frame_id,0);self.assertEqual(rx.base.anchor_id,0)
        capped=s.Decoder(frame_cap=len(d.packet)-1)
        with self.assertRaises(ValueError):capped.receive(d.packet)
        self.assertEqual(capped.base.last_frame_id,-1)
        rx.receive(d.packet);self.assertEqual(rx.base.last_frame_id,1)

    def test_configuration_and_geometry_are_bounded(self):
        cfg=self.config()
        with self.assertRaises(dataclasses.FrozenInstanceError):cfg.frame_cap=1
        for kwargs in ({'frame_cap':49153},{'frame_cap':0},{'max_attempts':5},{'work_budget_ms':-1},{'rectangles':[]}):
            with self.assertRaises(ValueError):s.Config(**kwargs)
        rgb=self.frame();base=s.hud.gm.Encoder().prepare(rgb,0)
        with self.assertRaises(ValueError):s.select_frame(base,rgb,s.Config(rectangles=((0,0,16,16),(8,8,16,16))))
        with self.assertRaises(ValueError):s.select_frame(base,rgb,self.config(),spent_before_ms=-1)


if __name__=='__main__':unittest.main()
