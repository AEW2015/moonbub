import unittest
import numpy as np
import model as m
class Stream(unittest.TestCase):
 def test_full_filter_all_presets_and_cache(self):
  rng=np.random.default_rng(64);a=rng.integers(96,113,(480,720),dtype=np.uint8);a.setflags(write=False);mask=np.zeros((480,720),bool);mask[100:130,60:200]=True;mask.setflags(write=False)
  for p in m.full.PRESETS:
   expected,w=m.full.filtered_luma(a,mask,p);reader=m.FilteredRows(a,mask,p);rows=[];last=None;copy=None
   for y,row in enumerate(reader):
    if last is not None:np.testing.assert_array_equal(last,copy)
    np.testing.assert_array_equal(row,expected[y]);self.assertFalse(row.flags.writeable);self.assertLessEqual(len(reader.cache),4);self.assertLessEqual(len(reader.pending),1);last=row;copy=row.copy();rows.append(row)
   work=reader.work();self.assertEqual(work['Y_rows_loaded'],480);self.assertLessEqual(work['maximum_lookahead_rows'],2)
   for key in('vertical_changed_edges','horizontal_changed_edges','changed_luma_samples'):self.assertEqual(work[key],w[key])
 def test_lazy_pause_and_bad_input(self):
  a=np.full((480,720),128,np.uint8);a.setflags(write=False);mask=np.zeros_like(a,bool);mask.setflags(write=False);reader=m.FilteredRows(a,mask,m.full.PRESETS[-1]);self.assertEqual(reader.loads,0);next(reader);snapshot=reader.work();self.assertEqual(reader.work(),snapshot)
  with self.assertRaises(ValueError):m.FilteredRows(a.copy(),mask,m.full.PRESETS[-1])
 def test_owned_configuration_and_static_mask(self):
  a=np.full((480,720),100,np.uint8);a[:,8:]=104;a.setflags(write=False);mask=np.zeros_like(a,bool)
  with self.assertRaises(ValueError):m.FilteredRows(a,mask,m.full.PRESETS[-1])
  mask.setflags(write=False);preset=dict(m.full.PRESETS[-1]);reader=m.FilteredRows(a,mask,preset);preset['strength']=0;self.assertEqual(reader.preset['strength'],3)
  with self.assertRaises(TypeError):reader.preset['strength']=0
  expected,_=m.full.filtered_luma(a,mask,m.full.PRESETS[-1]);np.testing.assert_array_equal(np.stack(list(reader)),expected)
if __name__=='__main__':unittest.main()
