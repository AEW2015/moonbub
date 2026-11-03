import dataclasses
import unittest
import numpy as np

from model import Config,run
from policy import PolicyConfig


class ModelTests(unittest.TestCase):
    def test_restore_returns_to_fine_after_cap_burst(self):
        rng=np.random.default_rng(6)
        frames=[np.full((16,32,3),70,np.uint8) for _ in range(60)]
        frames[28:33]=[rng.integers(0,256,(16,32,3),dtype=np.uint8) for _ in range(5)]
        results={}
        for mode in ('backoff','restore'):
            cfg=Config(frame_cap=220,policy=PolicyConfig(mode=mode,headroom_fraction=.95))
            results[mode]=run(frames,{},cfg)
            self.assertTrue(results[mode]['disposition_conserved'])
        self.assertEqual(results['backoff']['final_quant_scale'],32)
        self.assertEqual(results['restore']['final_quant_scale'],8)
        self.assertGreaterEqual(sum(e['kind']=='restore' for e in results['restore']['policy_events']),2)
        self.assertEqual(results['restore']['presented'][-1]['id'],59)

    def test_quality_is_bounded_and_cap_trials_are_charged(self):
        frames=[np.full((16,32,3),80,np.uint8) for _ in range(12)]
        r=run(frames,{},Config(frame_cap=1,policy=PolicyConfig(mode='restore')))
        self.assertEqual(r['transmitted'],0)
        self.assertEqual(r['drops_by_reason']['cap'],12)
        self.assertEqual(r['final_quant_scale'],32)
        self.assertTrue(all(x['quant_scale']<=32 for x in r['packets']))
        self.assertTrue(r['disposition_conserved'])

    def test_finite_actual_codec_and_ack_loss(self):
        frames=[np.full((16,32,3),80+i,np.uint8) for i in range(20)]
        r=run(frames,{},Config(ack_loss_ids=(7,),data_loss_ids=(4,),refresh_period=0,ack_timeout_ms=70))
        self.assertEqual(r['presented'][-1]['id'],19)
        self.assertNotIn('receiver_rejected',r['drops_by_reason'])
        self.assertLessEqual(r['peak_pending_credits'],2)
        self.assertLessEqual(r['peak_framebuffers'],3)
        self.assertEqual(r['unresolved_slots'],[None,None])
        self.assertFalse(r['unresolved_pending'])

    def test_cuts_do_not_directly_lower_quality(self):
        frames=[np.zeros((16,32,3),np.uint8) for _ in range(4)]+[np.full((16,32,3),255,np.uint8) for _ in range(8)]
        r=run(frames,{},Config(policy=PolicyConfig(mode='fixed')))
        self.assertEqual(r['final_quant_scale'],8)
        self.assertTrue(any(e['kind']=='scene_cut' for e in r['policy_events']))
        self.assertGreaterEqual(r['keyframes'],2)

    def test_invalid_initial_scale(self):
        with self.assertRaises(ValueError):run([np.zeros((16,16,3),np.uint8)],{},Config(quant_scale=16))


if __name__=='__main__':unittest.main()
