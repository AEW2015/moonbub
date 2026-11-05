import unittest
import numpy as np
import model as m
import verify as v
class Scalar(unittest.TestCase):
 def test_random_scalar_filter_with_guard_and_corners(self):
  rng=np.random.default_rng(600);a=rng.integers(0,256,(480,720),dtype=np.uint8);guard=np.zeros_like(a,bool);guard[100:150,100:180]=True
  for preset in m.PRESETS:
   out,_=m.filtered_luma(a,guard,preset)
   coords=[(y,x) for y in(0,7,8,15,16,100,104,479) for x in(0,7,8,15,16,100,104,719)]+list(zip(rng.integers(0,480,1000),rng.integers(0,720,1000)))
   for y,x in coords:self.assertEqual(int(out[y,x]),v.scalar(a,guard,preset,int(y),int(x)))
 def test_lowcontrast_grid_scalar(self):
  yy,xx=np.mgrid[:480,:720];a=(100+(xx//8)%4+(yy//8)%3).astype(np.uint8);guard=np.zeros_like(a,bool)
  for preset in m.PRESETS[1:]:
   out,_=m.filtered_luma(a,guard,preset)
   for y in range(5,34):
    for x in range(5,34):self.assertEqual(int(out[y,x]),v.scalar(a,guard,preset,y,x))
if __name__=='__main__':unittest.main()
