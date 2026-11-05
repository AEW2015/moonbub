import unittest
import numpy as np
import model as m

class WideTests(unittest.TestCase):
 def test_narrow_math_matches_existing_predictor(self):
  rng=np.random.default_rng(32);ref=tuple(m.runtime.ft.rgb_to_planes(rng.integers(0,256,(64,64,3),dtype=np.uint8)))
  v=rng.integers(-18,19,(2,2,2),dtype=np.int8)
  for a,b in zip(m.predict(ref,v),m.runtime.taps.predict(ref,v,32)):np.testing.assert_array_equal(a,b)
 def test_wide_negative_edges_scalar(self):
  ref=(np.arange(4096,dtype=np.int16).reshape(64,64)%256,np.arange(1024,dtype=np.int16).reshape(32,32)%256,np.full((32,32),70,np.int16))
  v=np.array([[[-68,-67],[64,65]],[[33,-35],[-41,39]]],np.int8);out=m.predict(ref,v)
  for plane,(image,pred) in enumerate(zip(ref,out)):
   den,bs=(2,32) if plane==0 else (4,16)
   for y,x in ((0,0),(0,image.shape[1]-1),(image.shape[0]-1,0),(image.shape[0]-1,image.shape[1]-1),(17,19)):
    dx,dy=map(int,v[y//bs,x//bs]);ix,fx=divmod(dx,den);iy,fy=divmod(dy,den)
    value=0
    for a,wx in ((0,den-fx),(1,fx)):
     for b,wy in ((0,den-fy),(1,fy)):value+=wx*wy*int(image[min(max(y+iy+b,0),image.shape[0]-1),min(max(x+ix+a,0),image.shape[1]-1)])
    self.assertEqual(int(pred[y,x]),(value+den*den//2)//(den*den))
  with self.assertRaises(ValueError):m.runtime.taps.predict(ref,v,32)
 def test_quiet_search_and_bad_vectors(self):
  ref=(np.full((64,64),100,np.int16),np.full((32,32),128,np.int16),np.full((32,32),128,np.int16));v=np.zeros((2,2,2),np.int8)
  out,work=m.estimate(ref,ref,v);np.testing.assert_array_equal(out,v);self.assertEqual(work['active_blocks'],0)
  with self.assertRaises(ValueError):m.predict(ref,np.full((2,2,2),69,np.int8))
  with self.assertRaises(ValueError):m.estimate(ref,ref,np.full((2,2,2),19,np.int8))
 def test_incumbent_sampled_cost_never_worsened(self):
  rng=np.random.default_rng(3201);ref=tuple(m.runtime.ft.rgb_to_planes(rng.integers(0,256,(64,64,3),dtype=np.uint8)));src=tuple(np.roll(v,12,axis=1) for v in ref)
  v=np.zeros((2,2,2),np.int8);out,work=m.estimate(src,ref,v)
  self.assertLessEqual(work['final_sampled_cost'],work['incumbent_sampled_cost']);self.assertLessEqual(int(np.abs(out.astype(np.int16)).max()),68)
  self.assertEqual(work['coarse_candidates'],289);self.assertEqual(work['refinement_candidates'],81)
if __name__=='__main__':unittest.main()
