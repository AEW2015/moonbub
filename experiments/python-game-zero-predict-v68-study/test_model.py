import unittest
from unittest.mock import patch
import numpy as np
import helpers as h
model=h.module('zero68_owned_model',h.HERE/'model.py')
class Tests(unittest.TestCase):
 def setUp(self):
  self.ref=tuple((np.arange(np.prod(s)).reshape(s)%256).astype(np.int16)for s in model.SHAPES)
  for p in self.ref:p.setflags(write=False)
  self.v=np.zeros((15,23,2),np.int8)
 def test_key(self):
  p=model.key_prediction();self.assertTrue(all(not a.flags.writeable and a.strides==(0,0)and np.all(a==128)for a in p));self.assertEqual(p[0].base.nbytes,2);self.assertTrue(all(np.shares_memory(p[0],a)for a in p))
  with self.assertRaises(ValueError):p[0].setflags(write=True)
 def test_zero_no_old(self):
  with patch.object(h.m,'predict',side_effect=AssertionError('old forbidden')):self.assertIs(model.predict(self.ref,self.v,32),self.ref)
 def test_fractional_fallback(self):
  for mv in ((1,-1),(-3,7),(4,0)):
   v=self.v.copy();v[0,0]=mv;expected=h.m.predict(self.ref,v,32)
   with patch.object(h.m,'predict',wraps=h.m.predict)as spy:actual=model.predict(self.ref,v,32)
   self.assertEqual(spy.call_count,1)
   for a,b in zip(expected,actual):np.testing.assert_array_equal(a,b)
 def test_invalid(self):
  for v,bs in ((self.v.astype(np.int16),32),(self.v[:-1],32),(self.v,17)):
   with self.assertRaises(ValueError):model.predict(self.ref,v,bs)
  for ref in (list(self.ref),(self.ref[0].copy(),*self.ref[1:]),(self.ref[0].astype(np.uint8),*self.ref[1:])):
   with self.assertRaises(ValueError):model.predict(ref,self.v,32)
  bad=self.ref[0].copy();bad[0,0]=256;bad.setflags(write=False)
  with self.assertRaises(ValueError):model.predict((bad,*self.ref[1:]),self.v,32)
if __name__=='__main__':unittest.main()
