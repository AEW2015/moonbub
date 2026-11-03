#!/usr/bin/env python3
import math
import unittest
from model import MAX_PAYLOAD, VIDEO, IP_UDP_BYTES, Scenario, run

JPEGS=[bytes([i])*26000 for i in range(10)]
TIMINGS=[{'arrival_cycle':0,'present_cycle':2_000_000,'commit_cycle':100,
          'pending_cycle':1_000_100,'upload_cycles':1000} for _ in range(10)]

class TransportModelTests(unittest.TestCase):
    def test_lossless_and_real_wire_overhead(self):
        r=run(JPEGS,TIMINGS,Scenario(rate_bps=50_000_000),count=30,collect=True)
        self.assertEqual(r['captured'],30);self.assertEqual(r['presented'],30)
        self.assertEqual(r['presented_ids'],list(range(30)))
        self.assertEqual(r['packets_lost'],0);self.assertEqual(r['packet_rejects'],0)
        packet_count=math.ceil(26000/MAX_PAYLOAD)
        self.assertEqual(r['packets_sent'],30*packet_count)
        self.assertEqual(r['wire_bytes'],30*(26000+packet_count*(VIDEO.size+IP_UDP_BYTES)))
    def test_overloaded_latest_slot_is_bounded(self):
        r=run(JPEGS,TIMINGS,Scenario(rate_bps=4_000_000),count=120)
        self.assertGreater(r['sender_replaced'],0);self.assertLess(r['presented'],120)
        self.assertEqual(r['sender_queue_highwater_frames'],1)
        self.assertLessEqual(r['sender_queue_highwater_bytes'],26000)
    def test_all_packet_loss_is_not_presentation(self):
        r=run(JPEGS,TIMINGS,Scenario(rate_bps=50_000_000,loss_ppm=1_000_000),count=10)
        self.assertEqual(r['packets_lost'],r['packets_sent'])
        self.assertEqual(r['received_complete'],0);self.assertEqual(r['presented'],0)
    def test_deadline_discards_complete_stale_frames(self):
        r=run(JPEGS,TIMINGS,Scenario(rate_bps=8_000_000,receiver_age_ms=1),count=10)
        self.assertEqual(r['received_complete'],10);self.assertEqual(r['receiver_expired'],10)
        self.assertEqual(r['presented'],0)
    def test_jitter_reordering_is_not_silently_accepted(self):
        r=run(JPEGS,TIMINGS,Scenario(rate_bps=8_000_000,jitter_us=5000,seed=5),count=30)
        self.assertGreater(r['packet_rejects'],0);self.assertLess(r['received_complete'],30)
    def test_zero_rate_rejected(self):
        with self.assertRaises(ValueError):run(JPEGS,TIMINGS,Scenario(rate_bps=0),count=1)

if __name__=='__main__':unittest.main()
