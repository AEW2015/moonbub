import unittest
import numpy as np
import model as m
class Error(unittest.TestCase):
 def test_identity(self):
  a=np.zeros((480,720,3),np.uint8);d=m.Diagnostics(());d.add(a,a);d.add(a,a);s=d.summary();self.assertEqual(s['active_MSE'],0);self.assertEqual(s['coordinate_temporal_error_change_MSE'],0);self.assertEqual(s['grid8_error_jump_MSE'],0)
 def test_constant_error_not_temporal_change(self):
  a=np.full((480,720,3),100,np.uint8);b=np.full_like(a,103);d=m.Diagnostics(());d.add(a,b);d.add(a+1,b+1);s=d.summary();self.assertEqual(s['active_MSE'],9);self.assertEqual(s['coordinate_temporal_error_change_MSE'],0);self.assertEqual(s['grid8_error_jump_MSE'],0)
 def test_error_step_and_grid_jump(self):
  a=np.full((480,720,3),100,np.uint8);b=a.copy();b[:,8:]=104;d=m.Diagnostics(());d.add(a,a);r=d.add(a,b);self.assertGreater(r['grid8_error_jump_SSE'],0);self.assertEqual(r['nongrid_error_jump_SSE'],0);self.assertEqual(r['coordinate_temporal_error_change_SSE'],r['active_SSE'])
 def test_bounds(self):
  with self.assertRaises(ValueError):m.Diagnostics(()).summary()
  with self.assertRaises(ValueError):m.Diagnostics(()).add(np.zeros((2,2,3),np.uint8),np.zeros((2,2,3),np.uint8))
if __name__=='__main__':unittest.main()
