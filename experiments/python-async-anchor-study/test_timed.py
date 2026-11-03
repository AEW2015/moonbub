import unittest
import numpy as np
from timed import run,Config


class TimedTests(unittest.TestCase):
    def frames(self,count=60):
        return [np.full((18,34,3),40+i%80,np.uint8) for i in range(count)]
    def manifest(self,n):return {'active_rects':[(0,0,34,18)]*n}

    def test_background_control_never_inflates_presentations(self):
        r=run(self.frames(),self.manifest(60))
        self.assertEqual(len(r['presented']),60)
        self.assertGreater(len(r['controls']),2)
        self.assertEqual(r['peaks']['sender_anchors'],2)
        self.assertLessEqual(r['peaks']['slots'],2)
        self.assertLessEqual(r['peaks']['pcredits'],2)
        self.assertEqual(r['unresolved_slots'],[None,None])
        self.assertFalse(r['pending_controls'])
        self.assertGreater(r['control_wire_bytes'],0)

    def test_lost_key_ack_retry_and_dropped_p_recover(self):
        cfg=Config(lost_key_ack_once=True,drop_first_display=True,duplicate_ack_ms=15)
        r=run(self.frames(),self.manifest(60),cfg)
        self.assertEqual(r['presented'][-1]['id'],59)
        self.assertEqual(r['drop_counts']['data_loss'],1)
        self.assertTrue(any(x['retry'] for x in r['packets']))
        self.assertTrue(any(x['kind']=='ack' and not x['accepted'] for x in r['acks']))
        self.assertFalse(r['pending_controls']);self.assertEqual(r['unresolved_slots'],[None,None])

    def test_cap_failure_never_sends_oversized_key(self):
        r=run(self.frames(4),self.manifest(4),Config(frame_cap=10))
        self.assertFalse(r['presented'])
        self.assertFalse(any('send_ms' in p for p in r['packets']))
        self.assertFalse(r['disposition']['pending'])
        self.assertEqual(len(r['disposition']['dropped']),4)

    def test_slow_decoder_is_a_rate_limit(self):
        r=run(self.frames(),self.manifest(60),Config(decode_ms=50))
        self.assertLess(len(r['presented']),60)
        self.assertLessEqual(r['peaks']['buffers'],3)
        self.assertLessEqual(r['peaks']['packet_bytes'],98304)


if __name__=='__main__':unittest.main()
