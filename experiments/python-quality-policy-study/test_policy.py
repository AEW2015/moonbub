import dataclasses
import unittest
import numpy as np

from policy import PolicyConfig, QualityPolicy


class PolicyTests(unittest.TestCase):
    def test_backoff_bound_and_fixed_control(self):
        p=QualityPolicy()
        for i in range(20):p.cap_failure(i,p.scale)
        self.assertEqual(p.scale,32)
        self.assertEqual(sum(x['kind']=='backoff' for x in p.events),2)
        fixed=QualityPolicy(PolicyConfig(mode='fixed'))
        fixed.cap_failure(1,8)
        self.assertEqual(fixed.scale,8)

    def test_hysteresis_restores_one_step_with_cooldown(self):
        p=QualityPolicy()
        p.cap_failure(1,8);p.cap_failure(2,16)
        for i in range(3,8):p.acknowledged(i,32,1000,49152,30)
        self.assertEqual(p.scale,32)
        p.acknowledged(8,32,1000,49152,30)
        self.assertEqual(p.scale,16)
        for i in range(9,14):p.acknowledged(i,16,1000,49152,30)
        self.assertEqual(p.scale,16)
        p.acknowledged(14,16,1000,49152,30)
        self.assertEqual(p.scale,8)

    def test_no_restore_without_headroom_or_from_old_scale(self):
        p=QualityPolicy();p.cap_failure(0,8)
        for i in range(1,20):p.acknowledged(i,16,30000,49152,30)
        self.assertEqual(p.scale,16)
        for i in range(20,40):p.acknowledged(i,8,10,49152,1)
        self.assertEqual(p.scale,16)
        for i in range(40,60):p.acknowledged(i,16,1000,49152,100)
        self.assertEqual(p.scale,16)

    def test_restore_trial_failure_counts_new_backoff(self):
        p=QualityPolicy(PolicyConfig(successes_required=1,cooldown_frames=2))
        p.cap_failure(0,8);p.acknowledged(2,16,100,49152,10)
        self.assertEqual(p.scale,8)
        p.cap_failure(3,8)
        self.assertEqual(p.scale,16)
        self.assertEqual([x['kind'] for x in p.events],['backoff','restore','backoff'])

    def test_cut_is_causal_and_never_coarsens(self):
        p=QualityPolicy();a=np.zeros((16,16,3),np.uint8)
        self.assertFalse(p.observe_capture(a,0))
        self.assertTrue(p.observe_capture(a+255,1))
        self.assertEqual(p.scale,8)
        self.assertFalse(p.observe_capture(a,2))
        with self.assertRaises(ValueError):p.observe_capture(a,2)

    def test_invalid_configuration(self):
        for kwargs in ({'ladder':(8,16,64)},{'mode':'other'},{'successes_required':0},
                       {'headroom_fraction':1.0},{'cut_threshold':float('nan')}):
            with self.assertRaises(ValueError):QualityPolicy(dataclasses.replace(PolicyConfig(),**kwargs))


if __name__=='__main__':unittest.main()
