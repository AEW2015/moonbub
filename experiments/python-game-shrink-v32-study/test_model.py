import unittest
import numpy as np
import model as b
from types import SimpleNamespace

class ShrinkTests(unittest.TestCase):
 def test_real_nonzero_shrink_menu_and_low_frequency_roi_guards(self):
  m=b.m;q=m.roi.declared_map(64,64,((0,0,16,16),),8,16)
  coeff=np.zeros((64,8,8),np.int16);coeff[:,0,0]=5
  coeff.reshape(-1,64)[:,m.ft.ZIGZAG[6]]=3
  coeff.reshape(-1,64)[:,m.ft.ZIGZAG[21]]=2
  coeff.reshape(-1,64)[:,m.ft.ZIGZAG[25]]=-1
  target=coeff.copy();positions=m.ft.ZIGZAG[6:]
  target.reshape(-1,64)[:,positions]-=np.sign(target.reshape(-1,64)[:,positions]).astype(np.int16)
  pred=(np.full((64,64),128,np.int16),np.full((32,32),128,np.int16),np.full((32,32),128,np.int16))
  source=b.reconstruct_plane(m,target,pred[0],q,64,64,0)
  p=SimpleNamespace(width=64,height=64,prediction=pred,source=(source,pred[1],pred[2]))
  baseline=b.reconstruct_plane(m,coeff,pred[0],q,64,64,0)
  menu,work=b.candidates(m,p,q,coeff,0,baseline,'shrink_strict')
  self.assertLessEqual(len(menu),5)
  protect=b.protected_blocks(m,q,64,64,0)
  shrunk=next(v for label,v in menu if label=='shrink_ac1')
  self.assertTrue(np.any((shrunk!=coeff)&(shrunk!=0)))
  for _,v in menu:
   np.testing.assert_array_equal(v[protect],coeff[protect])
   np.testing.assert_array_equal(v.reshape(-1,64)[:,m.ft.ZIGZAG[:6]],coeff.reshape(-1,64)[:,m.ft.ZIGZAG[:6]])
   self.assertTrue(np.all(np.abs(v.astype(np.int32))<=np.abs(coeff.astype(np.int32))))
   rebuilt=b.reconstruct_plane(m,v,pred[0],q,64,64,0)
   self.assertTrue(np.all(m.base.old._block_sse(source.astype(np.int64)-rebuilt)<=m.base.old._block_sse(source.astype(np.int64)-baseline)))
  self.assertEqual(work['candidate_inverse_plane_calls'],4)
 def test_plane_reconstruction_exact_frozen(self):
  m=b.m;rng=np.random.default_rng(30);q=m.roi.declared_map(64,64,(),8,16)
  src=tuple(m.ft.rgb_to_planes(rng.integers(0,256,(64,64,3),dtype=np.uint8)))
  p=m.base.analyze_planes(src,None,block_size=32);c=m.base._quantize(p.raw_coefficients,q,64,64)
  old=m.gm.reconstruct(c,p.prediction,q,64,64)
  for i in range(3):np.testing.assert_array_equal(old[i],b.reconstruct_plane(m,c[i],p.prediction[i],q,64,64,i))
 def test_strict_budget_dc_protection_and_decoder(self):
  m=b.m;rng=np.random.default_rng(301);ref=None;q=m.roi.declared_map(64,64,((0,0,16,16),),8,16)
  for fid in range(3):
   src=tuple(m.ft.rgb_to_planes(rng.integers(0,256,(64,64,3),dtype=np.uint8)))
   p=m.base.analyze_planes(src,ref,epoch=1,frame_id=fid,reference_id=m.NO_REF if ref is None else fid-1,block_size=32,motion_mode='zero')
   baseline,baseout,_=m.encode_prepared(p,q)
   basecoeff=m.parse(baseline)['coefficients']
   for policy in b.POLICIES:
    packet,out,work=b.encode_prepared(p,q,policy=policy);meta=m.parse(packet)
    self.assertLessEqual(len(packet),len(baseline))
    decoded,_=m.decode(packet,ref,expected_epoch=1,expected_reference_id=None if fid==0 else fid-1)
    for i,(a,c) in enumerate(zip(out,decoded)):
     np.testing.assert_array_equal(a,c)
     protected=b.protected_blocks(m,q,64,64,i)
     np.testing.assert_array_equal(meta['coefficients'][i][protected],basecoeff[i][protected])
     np.testing.assert_array_equal(meta['coefficients'][i][:,0,0],basecoeff[i][:,0,0])
     for old_sse,new_sse in zip(m.base.old._block_sse(src[i].astype(np.int64)-baseout[i]),m.base.old._block_sse(src[i].astype(np.int64)-a)):
      extra=0 if policy=='shrink_strict' else min(int(old_sse)//100,64)
      self.assertLessEqual(new_sse,old_sse+extra)
   ref=baseout
 def test_halo_and_invalid_policy_ownership(self):
  m=b.m;q=m.roi.declared_map(64,64,((0,0,16,16),),8,16)
  halo=b.protected_blocks(m,q,64,64,1).reshape(4,4)
  self.assertTrue(halo[:2,:2].all());self.assertFalse(halo[-1,-1])
  with self.assertRaises(ValueError):b.encode_prepared(None,q,policy='arbitrary')
  with self.assertRaises(ValueError):b.encode_prepared(None,q)
 def test_candidate_input_coefficients_not_mutated(self):
  m=b.m;src=tuple(m.ft.rgb_to_planes(np.random.default_rng(303).integers(0,256,(64,64,3),dtype=np.uint8)));q=m.roi.declared_map(64,64,(),8,16)
  p=m.base.analyze_planes(src,None);before=tuple(v.copy() for v in p.raw_coefficients)
  b.encode_prepared(p,q)
  for a,c in zip(before,p.raw_coefficients):np.testing.assert_array_equal(a,c)
if __name__=='__main__':unittest.main()
