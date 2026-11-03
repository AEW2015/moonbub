import struct
import unittest
from unittest.mock import patch
import numpy as np
import hybrid_codec as h


class Clock:
    def __init__(self):self.ns=0
    def __call__(self):return self.ns
    def add(self,ms):self.ns+=int(ms*1e6)


class HybridTests(unittest.TestCase):
    def rgb(self):return np.random.default_rng(1101).integers(0,256,(64,80,3),dtype=np.uint8)
    def cfg(self,**kw):return h.Config(rectangles=((0,0,16,16),(32,0,16,16)),**kw)

    def test_actual_packet_cap_reuses_encoded_patches_and_base_fallback(self):
        rgb=self.rgb();base=h.gm.Encoder().prepare(rgb,0);calls=[]
        one=h.hp.encode_patch(rgb,(0,0,16,16));cap=22+len(base)+4+len(one)
        def encode(a,r,p):calls.append(r);return h._encode_patch(a,r,p)
        d=h.select_frame(base,rgb,self.cfg(frame_cap=cap,patch_policy='hp01'),patch_encoder=encode)
        self.assertEqual(len(calls),2);self.assertEqual(d.format,'HG01');self.assertEqual(len(d.selected),1)
        self.assertEqual(len(d.packet),cap);self.assertEqual(d.attempts[1]['fits'],False)
        fallback=h.select_frame(base,rgb,self.cfg(frame_cap=len(base)))
        self.assertEqual(fallback.packet,base);self.assertEqual(fallback.format,'GM01')
        reject=h.select_frame(base,rgb,self.cfg(frame_cap=len(base)-1))
        self.assertIsNone(reject.packet);self.assertEqual(reject.reason,'base_over_cap');self.assertFalse(reject.attempts)

    def test_fast_preflight_and_extract_identity_without_entropy_parse(self):
        rgb=self.rgb();base=h.gm.Encoder(epoch=31).prepare(rgb,7)
        with patch.object(h.gm,'parse',side_effect=AssertionError('sender must not entropy decode')):
            d=h.select_frame(base,rgb,self.cfg())
            raw,identity=h.extract_base(d.packet,epoch=31)
            self.assertEqual(raw,base);self.assertEqual(identity['frame_id'],7)
            self.assertEqual(identity['epoch'],31);self.assertTrue(identity['key'])
            self.assertEqual(identity['patch_count'],len(d.selected));self.assertEqual(identity['format'],'HG01')
        with self.assertRaises(ValueError):h.base_identity(d.packet,epoch=32)
        with self.assertRaises(ValueError):h.base_identity(d.packet,frame_cap=len(d.packet)-1)
        with self.assertRaises(ValueError):h.extract_base(base[:-1]+bytes([base[-1]^1]))

    def test_late_observed_budget_pays_all_rejected_work(self):
        rgb=self.rgb();base=h.gm.Encoder().prepare(rgb,0);clock=Clock();calls=[]
        def costly(a,r,p):
            calls.append(r);packet,details=h._encode_patch(a,r,p);clock.add(7)
            return packet,details
        d=h.select_frame(base,rgb,self.cfg(work_budget_ms=5),spent_before_ms=1,clock_ns=clock,patch_encoder=costly)
        self.assertEqual(d.packet,base);self.assertTrue(d.deadline_hit)
        self.assertEqual(d.service_ms,7);self.assertEqual(d.observed_total_ms,8)
        self.assertEqual(len(d.attempts),1);self.assertEqual(d.attempts[0]['encode_ms'],7)
        self.assertFalse(d.attempts[0]['selected_in_output'])
        self.assertIn(d.attempts[0]['candidate_details']['candidate_count'],(2,3))
        clock=Clock();d=h.select_frame(base,rgb,self.cfg(work_budget_ms=0),clock_ns=clock)
        self.assertFalse(d.attempts);self.assertEqual(d.packet,base)

    def test_malformed_patch_and_base_reject_before_anchor_commit(self):
        rgb=self.rgb();base=h.gm.Encoder().prepare(rgb,0);d=h.select_frame(base,rgb,self.cfg())
        good,patches,_=h.row.parse_frame(d.packet,1)
        p=h.row.choose_patch(rgb,(0,0,16,16))[0]
        bad_patch=p[:-1]+bytes([p[-1]^1]);bad=h.row.wrap(base,[bad_patch],80,64)
        rx=h.Decoder()
        with self.assertRaises(ValueError):rx.receive(bad)
        self.assertEqual(rx.base.last_frame_id,-1);self.assertIsNone(rx.base._anchor)
        fields=h.gm.HEADER.unpack_from(base);position=h.gm.HEADER.size+fields[12]
        body=bytearray(base[:-4]);body[position]^=255;bad_base=h.row._seal(bytes(body))
        # CRC/header preflight intentionally accepts an invalid coefficient body.
        h.base_identity(bad_base)
        with self.assertRaises(ValueError):rx.receive(h.row.wrap(bad_base,[p],80,64))
        self.assertEqual(rx.base.last_frame_id,-1);self.assertIsNone(rx.base._anchor)
        with self.assertRaises(ValueError):h.Decoder(epoch=2).receive(d.packet)
        with self.assertRaises(ValueError):h.Decoder(frame_cap=len(d.packet)-1).receive(d.packet)
        rx.receive(d.packet);self.assertEqual(rx.base.last_frame_id,0)

    def test_temporal_mixed_packets_exact_overlay_and_key_ownership(self):
        source=self.rgb();enc=h.gm.Encoder();rx=h.Decoder();plain=h.gm.Receiver()
        owner=h.gm.Encoder();foreign=owner.analyze(source,0)
        with self.assertRaises(ValueError):enc.encode_candidate(foreign,np.full((4,5),16,np.uint8))
        for i in range(5):
            rgb=(source+i*7).astype(np.uint8);base=enc.prepare(rgb,i,force_key=i==3)
            if i in (0,3):
                self.assertFalse(enc.can_prepare());self.assertTrue(enc.pending[i]['key'])
            cfg=self.cfg(max_attempts=0 if i==1 else 4)
            d=h.select_frame(base,rgb,cfg);actual,info=rx.receive(d.packet);control,_=plain.receive(base)
            self.assertEqual(info['base_rgb_sha256'],enc.expected_hash(i))
            self.assertEqual(info['base_rgb_sha256'],h.hashlib.sha256(control.tobytes()).hexdigest())
            for a,b in zip(rx.base._anchor,plain._anchor):np.testing.assert_array_equal(a,b)
            self.assertEqual(rx.base.anchor_id,3 if i>=3 else 0)
            for p in d.selected:
                x,y,w,hh=p['rect'];np.testing.assert_array_equal(h.hp.corpus.rgb565(actual)[y:y+hh,x:x+w],h.hp.corpus.rgb565(rgb)[y:y+hh,x:x+w])
            if i==1:self.assertEqual(d.packet,base)
            enc.ack(i,epoch=1)
        with self.assertRaises(ValueError):rx.receive(d.packet)

    def test_geometry_overlap_profile_and_bad_clock(self):
        rgb=self.rgb();base=h.gm.Encoder().prepare(rgb,0)
        for config in (h.Config(rectangles=((0,0,16,16),(8,8,16,16))),h.Config(rectangles=((79,0,2,2),))):
            with self.assertRaises(ValueError):h.select_frame(base,rgb,config)
        for kw in ({'frame_cap':49153},{'patch_policy':'magic'},{'max_attempts':5},{'work_budget_ms':float('nan')}):
            with self.assertRaises(ValueError):h.Config(**kw)
        with self.assertRaises(ValueError):h.select_frame(base,rgb[:32],self.cfg())
        with self.assertRaises(ValueError):h.select_frame(base,rgb,self.cfg(),spent_before_ms=-1)
        with self.assertRaises(ValueError):h.Decoder().receive(b'GH01')
        clock=iter((10,9))
        with self.assertRaises(ValueError):h.select_frame(base,rgb,self.cfg(),clock_ns=lambda:next(clock))

    def test_hp_only_and_row_choose_same_exact_pixels(self):
        rgb=np.full((64,80,3),(32,50,64),np.uint8);base=h.gm.Encoder().prepare(rgb,0)
        hp=h.select_frame(base,rgb,h.Config(rectangles=((0,0,80,32),),patch_policy='hp01'))
        row=h.select_frame(base,rgb,h.Config(rectangles=((0,0,80,32),),patch_policy='adaptive_row'))
        self.assertLessEqual(len(row.packet),len(hp.packet));self.assertTrue(any(p['format']=='HR01' for p in row.selected))
        a,_=h.Decoder().receive(hp.packet);b,_=h.Decoder().receive(row.packet)
        np.testing.assert_array_equal(a,b)
        for attempt in row.attempts:
            detail=attempt['candidate_details'];self.assertEqual(attempt['patch_bytes'],min(detail['hp01_bytes'],detail['hr01_bytes']))

if __name__=='__main__':unittest.main()
