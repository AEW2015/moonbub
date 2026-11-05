import importlib.util,sys,unittest
from pathlib import Path
import numpy as np
import model as m
s=importlib.util.spec_from_file_location('rice46_frozen_decoder',Path(__file__).resolve().parents[1]/'python-game-binary-v38-study/decoder.py');d=importlib.util.module_from_spec(s);sys.modules[s.name]=d;s.loader.exec_module(d)
class Search(unittest.TestCase):
 def same(self,a,bw):
  packet,base,trials,work=m.encode(a,bw);gold,_=m.old.encode(a,bw);self.assertEqual(base,gold);self.assertLessEqual(len(packet),len(base));np.testing.assert_array_equal(d.decode(packet,len(a),bw),a)
  for t in trials:self.assertEqual(t['selected'],min(range(len(t['candidates'])),key=lambda i:len(t['candidates'][i]['packet'])))
 def test_zero_ties_and_bounds(self):
  self.same(np.zeros((4,8,8),np.int16),2);self.assertEqual(m.neighbors(0,13),(0,1));self.assertEqual(m.neighbors(13,13),(13,12))
 def test_sparse_and_dense(self):
  rng=np.random.default_rng(46);a=np.zeros((24,8,8),np.int16);a.flat[rng.integers(0,a.size,80)]=rng.integers(-2048,2049,80,dtype=np.int16);self.same(a,6);self.same(rng.integers(-2048,2049,(4,8,8),dtype=np.int16),2)
 def test_invalid(self):
  with self.assertRaises(ValueError):m.encode(np.zeros((4,8,8),float),2)
if __name__=='__main__':unittest.main()
