import dataclasses
import unittest
import numpy as np
from timed import Config,run


class TimedTests(unittest.TestCase):
    def frames(self,n=12):return [np.full((16,32,3),80+i,np.uint8) for i in range(n)]

    def test_finite_slots_hash_checks_and_commit(self):
        r=run(self.frames(),{},Config(feedback_ms=20,refresh_period=5))
        self.assertEqual(r['presented_eventual'],12)
        self.assertLessEqual(r['peak_pending_credits'],2)
        self.assertLessEqual(r['peak_framebuffers'],3)
        self.assertTrue(all(x is None for x in r['unresolved_slots']))
        self.assertFalse(r['unresolved_pending'])

    def test_p_loss_and_lost_ack_preserve_later_decodability(self):
        r=run(self.frames(20),{},Config(data_loss_ids=(4,),ack_loss_ids=(7,),refresh_period=0,ack_timeout_ms=70))
        self.assertEqual(r['drops_by_reason']['data_loss'],1)
        self.assertNotIn('receiver_rejected',r['drops_by_reason'])
        self.assertEqual(r['presented'][-1]['id'],19)
        self.assertGreaterEqual(sum(x['kind']=='timeout' for x in r['ack_events']),2)

    def test_lost_initial_anchor_ack_recovers_after_timeout(self):
        r=run(self.frames(20),{},Config(ack_loss_ids=(0,),ack_timeout_ms=100))
        self.assertGreater(r['keyframes'],1)
        self.assertEqual(r['presented'][-1]['id'],19)

    def test_corrupt_p_rejects_then_later_anchor_p_recovers(self):
        r=run(self.frames(20),{},Config(corruption_ids=(7,),refresh_period=0))
        self.assertEqual(r['drops_by_reason']['receiver_rejected'],1)
        self.assertEqual(r['presented'][-1]['id'],19)

    def test_cap_is_checked_on_actual_encoded_bytes(self):
        r=run(self.frames(),{},Config(frame_cap=1))
        self.assertEqual(r['transmitted'],0)
        self.assertEqual(r['drops_by_reason']['cap'],12)

    def test_optional_backoff_changes_next_capture_and_is_bounded(self):
        r=run(self.frames(6),{},Config(frame_cap=1,cap_backoff_max=32))
        self.assertEqual([x['quant_scale'] for x in r['packets']],[8,16,32,32,32,32])
        self.assertEqual(r['final_quant_scale'],32)
        self.assertTrue(all(x['key'] for x in r['packets']))

    def test_overload_skips_real_captures_and_count_is_not_shifted(self):
        r=run(self.frames(20),{},Config(decode_ms=80))
        self.assertTrue(r['drops_by_reason'])
        self.assertLess(r['presented_strict'],20)
        self.assertLess(r['prepared'],20)

    def test_invalid_rates(self):
        for cfg in (Config(link_mbps=0),Config(window=0),Config(feedback_ms=-1)):
            with self.assertRaises(ValueError):run(self.frames(),{},cfg)


if __name__=='__main__':unittest.main()
