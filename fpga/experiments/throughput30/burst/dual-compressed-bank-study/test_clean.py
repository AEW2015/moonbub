#!/usr/bin/env python3
import importlib.util,os,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('clean_study',Path(__file__).resolve().parent/'clean-study.py');clean=importlib.util.module_from_spec(spec);spec.loader.exec_module(clean)
fixtures=Path(os.environ['FIXTURE_DIR'])

class CleanTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.result=clean.run(fixtures);cls.raw,cls.info=clean.make(fixtures);cls.events=clean.source.assign(cls.raw)
 def test_distinct_hash_verified_workload(self):
  self.assertEqual(len({x['sha256'] for x in self.info}),3);self.assertEqual(len(self.events),85)
 def test_zero_release_both_present_all(self):
  c=self.result['cases']['zero_release']
  for k in ('one_bank','two_bank_32KiB'):self.assertEqual([x['id'] for x in c[k]['presented']],[0,1,2]);self.assertEqual(c[k]['dropped'],[])
 def test_sampled_release_improves_modeled_presentations(self):
  c=self.result['cases']['sampled_max_release'];a,b=c['one_bank'],c['two_bank_32KiB']
  self.assertEqual([x['id'] for x in a['presented']],[0,2]);self.assertEqual([(x['id'],x['reason']) for x in a['dropped']],[(1,'busy_begin')])
  self.assertEqual([x['id'] for x in b['presented']],[0,1,2]);self.assertEqual(b['dropped'],[])
  self.assertEqual([x['crc32'] for x in b['presented']],[x['crc32'] for x in self.info])
 def test_two_bank_capacity_limit(self):
  r=clean.model.two_bank(self.events,bank_bytes=26000);self.assertEqual(r['presented'],[]);self.assertEqual([x['reason'] for x in r['dropped']],['oversized_frame']*3)
 def test_slow_service_overflow_is_bounded(self):
  c=self.result['cases']['slow_service_stress']
  for k in ('one_bank','two_bank_32KiB'):
   self.assertEqual(c[k]['presented'],[]);self.assertEqual([x['reason'] for x in c[k]['dropped']],['queue_full']*3);self.assertLessEqual(c[k]['event_fifo_highwater_slots'],5)
 def test_corrupt_byte_rejected_in_both_models(self):
  events=[dict(x) for x in self.events];e=next(x for x in events if x['id']==0 and x['type']=='D');b=bytearray(e['body']);b[-1]^=1;e['body']=bytes(b)
  with self.assertRaisesRegex(ValueError,'commit CRC/length'):clean.source.simulate(events,0)
  with self.assertRaisesRegex(ValueError,'commit CRC/length'):clean.model.two_bank(events,release_cycles=0)
 def test_future_frame_schedule_overlap_is_not_hidden(self):
  self.assertGreater(self.events[-1]['at'],3*clean.source.PERIOD_NUM//clean.source.PERIOD_DEN)
if __name__=='__main__':unittest.main()
