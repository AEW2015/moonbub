#!/usr/bin/env python3
import unittest
from study import evaluate,classify,percentile

def e(fid,index,count,at):return {'fid':fid,'index':index,'count':count,'at':at}

class TimerTests(unittest.TestCase):
 def test_equal_deadline_times_out_before_arrival(self):
  r=evaluate([e(0,0,2,0),e(0,1,2,10)],1,10);self.assertEqual(r[0]['kind'],'timeout');self.assertEqual(r[0]['at'],10)
 def test_before_deadline_completed(self):
  self.assertEqual(evaluate([e(0,0,2,0),e(0,1,2,9)],1,10)[0]['kind'],'complete')
 def test_timer_resets_for_each_accepted_packet(self):
  self.assertEqual(evaluate([e(0,0,3,0),e(0,1,3,9),e(0,2,3,18)],1,10)[0]['kind'],'complete')
 def test_missing_final_times_out(self):
  r=evaluate([e(0,0,3,0),e(0,1,3,7)],1,10)[0];self.assertEqual((r['kind'],r['at'],r['last_accepted']),('timeout',17,7))
 def test_early_timeout_is_distinguishable_from_missing_eof(self):
  r=evaluate([e(0,0,3,0),e(0,1,3,12)],1,10)[0];self.assertEqual(r['accepted_count'],1);self.assertEqual(r['kind'],'timeout')
 def test_new_sof_supersedes_missing_final_before_timeout(self):
  r=evaluate([e(0,0,2,0),e(1,0,1,5)],2,10);self.assertEqual([x['kind'] for x in r],['superseded','complete'])
 def test_missing_middle_detected_on_next_offset(self):
  r=evaluate([e(0,0,3,0),e(0,2,3,5)],1,10);self.assertEqual(r[0]['kind'],'sequence_error')
 def test_missing_sof_never_starts_timer(self):
  self.assertEqual(evaluate([e(0,1,2,0)],1,10)[0]['kind'],'no_start')
 def test_frame_classification_distinguishes_reorder_and_missing(self):
  frames=[bytes(2048)]*10
  self.assertEqual(classify([e(0,0,2,0),e(0,1,2,1),e(1,1,2,2)],2,frames),['complete_ordered','missing_sof'])
  self.assertEqual(classify([e(0,1,2,0),e(0,0,2,1)],1,frames),['complete_reordered'])
 def test_percentile_empty_and_upper(self):
  self.assertIsNone(percentile([],95));self.assertEqual(percentile([1,2,3],95),3)
if __name__=='__main__':unittest.main()
