import unittest
import numpy as np
import model as m
class Filter(unittest.TestCase):
 def test_flat_and_identity(self):
  a=np.full((480,720),100,np.uint8);guard=np.zeros_like(a,bool)
  for preset in m.PRESETS:
   out,w=m.filtered_luma(a,guard,preset);np.testing.assert_array_equal(out,a);self.assertFalse(out.flags.writeable);self.assertEqual(w['changed_luma_samples'],0)
 def test_defined_step_and_ownership(self):
  a=np.full((480,720),100,np.uint8);a[:,8:]=104;copy=a.copy();out,w=m.filtered_luma(a,np.zeros_like(a,bool),m.PRESETS[1]);self.assertTrue(np.all(out[:,7]==101));self.assertTrue(np.all(out[:,8]==103));np.testing.assert_array_equal(a,copy);self.assertEqual(w['vertical_changed_edges'],480)
 def test_guard_and_highcontrast_bypass(self):
  a=np.full((480,720),100,np.uint8);a[:,8:]=104;g=np.zeros_like(a,bool);g[:,8]=True;out,w=m.filtered_luma(a,g,m.PRESETS[3]);np.testing.assert_array_equal(out,a)
  a[:,8:]=140;out,w=m.filtered_luma(a,np.zeros_like(a,bool),m.PRESETS[3]);np.testing.assert_array_equal(out,a)
 def test_invalid(self):
  with self.assertRaises(ValueError):m.filtered_luma(np.zeros((2,2),np.uint8),np.zeros((2,2),bool),m.PRESETS[0])
if __name__=='__main__':unittest.main()
