import dataclasses
import unittest

import numpy as np

from controller import Config,Controller,codec


class ControllerTests(unittest.TestCase):
    def frame(self):
        yy,xx=np.mgrid[:64,:80]
        return np.stack(((xx*7+yy*3)%256,(xx*5+yy*9)%256,(xx*11+yy*2)%256),axis=2).astype(np.uint8)

    def config(self,cap=49152,policy='priority'):
        return Config(frame_cap=cap,policy=policy,rectangles=((0,0,16,16),))

    def test_normal_admission_once_and_roi_floor(self):
        enc=codec.Encoder();controller=Controller(enc,self.config());rgb=self.frame()
        decision=controller.prepare(rgb,0)
        self.assertTrue(decision.accepted);self.assertEqual(decision.selected,'normal')
        self.assertEqual(len(decision.attempts),1);self.assertEqual(decision.analyze_calls,1)
        self.assertEqual(decision.forward_calls,3);self.assertEqual(enc.forward_calls,3)
        parsed=codec.parse(decision.packet,1)
        self.assertEqual(int(parsed['scale_map'][0,0]),8)
        self.assertEqual(set(np.unique(parsed['scale_map'])),{8,16})
        actual,_=codec.Receiver().receive(decision.packet)
        self.assertEqual(codec.hashlib.sha256(actual.tobytes()).hexdigest(),enc.expected_hash(0))

    def test_actual_fallback_reuses_transform_and_matches_naive(self):
        rgb=self.frame();probe=Controller(config=self.config());maps=probe.maps(rgb)
        p=probe.encoder.analyze(rgb,0)
        normal=probe.encoder.encode_candidate(p,maps[0][1]);fallback=probe.encoder.encode_candidate(p,maps[1][1])
        self.assertLess(len(fallback.packet),len(normal.packet))
        cap=len(fallback.packet)
        shared=Controller(config=self.config(cap));naive=Controller(config=self.config(cap))
        a=shared.prepare(rgb,0);b=naive.prepare(rgb,0,reuse=False)
        self.assertEqual(a.packet,b.packet);self.assertEqual(a.selected,'fallback')
        self.assertEqual(len(a.attempts),2);self.assertEqual(a.analyze_calls,1);self.assertEqual(b.analyze_calls,2)
        self.assertEqual(a.forward_calls,3);self.assertEqual(b.forward_calls,6)
        parsed=codec.parse(a.packet,1)
        self.assertEqual(int(parsed['scale_map'][0,0]),8)
        self.assertEqual(set(np.unique(parsed['scale_map'])),{8,32})

    def test_both_failures_pay_work_without_reference_credit_mutation(self):
        rgb=self.frame();enc=codec.Encoder();c=Controller(enc,self.config(1))
        d=c.prepare(rgb,0)
        self.assertFalse(d.accepted);self.assertEqual(len(d.attempts),2)
        self.assertEqual(d.forward_calls,3);self.assertGreater(d.service_ms,0)
        self.assertEqual(enc.pending,{});self.assertEqual(enc.last_issued,-1);self.assertIsNone(enc.anchor_id)
        self.assertEqual(enc.forward_calls,3)
        Controller(enc,self.config()).prepare(rgb,0)
        enc.ack(0,epoch=1)
        old=enc.anchor_id
        d=c.prepare(rgb+1,1)
        self.assertFalse(d.accepted);self.assertEqual(enc.pending,{})
        self.assertEqual(enc.anchor_id,old);self.assertEqual(enc.last_issued,0)

    def test_small_edge_map_and_foreign_or_stale_candidates(self):
        rgb=np.full((18,34,3),71,np.uint8)
        enc=codec.Encoder();c=Controller(enc,Config(rectangles=((0,0,16,16),)))
        p=enc.analyze(rgb,0);m=c.maps(rgb)[0][1];candidate=enc.encode_candidate(p,m)
        other=codec.Encoder()
        with self.assertRaises(ValueError):other.commit(candidate)
        enc.commit(candidate)
        with self.assertRaises(ValueError):enc.commit(candidate)
        with self.assertRaises(ValueError):enc.encode_candidate(p,m)
        enc.ack(0,epoch=1)
        self.assertEqual(m.shape,(2,3))

    def test_immutable_and_invalid_configuration(self):
        cfg=Config()
        with self.assertRaises(dataclasses.FrozenInstanceError):cfg.frame_cap=1
        for kwargs in ({'frame_cap':0},{'frame_cap':1.0},{'policy':'oracle'},{'motion_mode':'future'}, {'rectangles':[]}):
            with self.assertRaises(ValueError):Config(**kwargs)


if __name__=='__main__':unittest.main()
