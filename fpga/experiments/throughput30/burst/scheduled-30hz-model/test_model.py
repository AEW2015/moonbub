#!/usr/bin/env python3
import unittest
import model

class ModelTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.events=model.assign(model.load_events())
 def test_sampled_busy_drops_new_frame_preserving_prior_pending(self):
  r=model.simulate(self.events,3397969)
  self.assertEqual([x['id'] for x in r['presented']],[0,2]);self.assertEqual([(x['id'],x['reason']) for x in r['dropped']],[(1,'busy_begin')])
  self.assertLess(r['dropped'][0]['cycle'],r['presented'][0]['present_cycle']);self.assertLessEqual(r['event_fifo_highwater_bytes'],5*1039)
 def test_zero_release_accepts_guest_abort_and_next_frame(self):
  r=model.simulate(self.events,0);self.assertEqual([x['id'] for x in r['presented']],[0,2]);self.assertEqual([(x['id'],x['reason']) for x in r['dropped']],[(1,'recorded_guest_abort')])
  self.assertEqual([x['crc32'] for x in r['presented']],['eceeb9c5','1ea3e1d5'])
 def test_queue_overflow_drops_whole_frames_without_publication(self):
  r=model.simulate(self.events,3397969,service_us_per_kib=2000);self.assertEqual(r['presented'],[]);self.assertEqual({x['id'] for x in r['dropped']},{0,1,2});self.assertTrue(all(x['reason']=='queue_full' for x in r['dropped']));self.assertLessEqual(r['event_fifo_highwater_bytes'],5*1039)
 def test_corrupt_data_cannot_commit(self):
  events=[dict(x) for x in self.events];e=next(x for x in events if x['id']==0 and x['type']=='D');b=bytearray(e['body']);b[-1]^=1;e['body']=bytes(b)
  with self.assertRaisesRegex(ValueError,'commit CRC/length'):model.simulate(events,0)
 def test_source_frame2_tail_overlaps_next_nominal_30hz_capture(self):
  self.assertEqual(self.events[-1]['type'],'C');self.assertGreater(self.events[-1]['at'],3*model.PERIOD_NUM//model.PERIOD_DEN)
if __name__=='__main__':unittest.main()
