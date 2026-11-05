"""Directed prediction parity and readonly-bank/physical-backing checks."""
import unittest
from unittest.mock import patch
import numpy as np
import verify as v

class PredictionProof(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  arrays=[]
  for shape in((480,720),(240,360),(240,360)):
   yy,xx=np.indices(shape);arrays.append(((xx+2*yy)%256).astype(np.int16))
  cls.reference=v.f.f.normalize(tuple(arrays))
  for p in cls.reference:p.setflags(write=False)
  cls.vectors=np.zeros((15,23,2),np.int8)
 def test_key_has_readonly_shared_two_byte_scalar(self):
  prediction=v.check_key(v.subject.key_prediction())
  self.assertEqual(sum(p.nbytes for p in prediction),1036800)
  with self.assertRaises(ValueError):v.base(prediction[0]).setflags(write=True)
  for p in prediction:
   with self.assertRaises(ValueError):p[0,0]=0
 def test_zero_returns_borrowed_bank_without_legacy_prediction(self):
  before=[p.copy()for p in self.reference]
  with patch.object(v.subject.h.m,'predict',side_effect=AssertionError('legacy zero prediction forbidden')):
   result=v.subject.predict(self.reference,self.vectors,32)
  for a,b in zip(result,self.reference,strict=True):self.assertIs(a,b);self.assertFalse(a.flags.writeable)
  v.same(result,before)
 def test_nonzero_and_fractional_vectors_match_frozen_legacy(self):
  for bs in(16,32):
   hh=(480+bs-1)//bs;ww=(720+bs-1)//bs
   for dx,dy in((1,1),(-1,-1),(4,-4),(18,-18)):
    mv=np.empty((hh,ww,2),np.int8);mv[:,:,0]=dx;mv[:,:,1]=dy
    want=v.m.predict(self.reference,mv,bs);got=v.subject.predict(self.reference,mv,bs)
    v.same(got,want)
    self.assertTrue(all(not np.shares_memory(a,b)for a,b in zip(got,self.reference)))
 def test_writable_or_out_of_domain_reference_rejected(self):
  for value in(-1,256):
   bad=list(self.reference);p=bad[0].copy();p[0,0]=value;p.setflags(write=False);bad[0]=p
   with self.assertRaises(ValueError):v.subject.predict(tuple(bad),self.vectors,32)
  for dtype in(np.uint8,np.float64,np.int32):
   bad=list(self.reference);bad[0]=bad[0].astype(dtype);bad[0].setflags(write=False)
   with self.assertRaises(ValueError):v.subject.predict(tuple(bad),self.vectors,32)
  bad=list(self.reference);bad[0]=bad[0].copy()
  with self.assertRaises(ValueError):v.subject.predict(tuple(bad),self.vectors,32)
  bad=list(self.reference);bad[0]=bad[0][:-1]
  with self.assertRaises(ValueError):v.subject.predict(tuple(bad),self.vectors,32)
 def test_malformed_vectors_do_not_borrow_a_reference(self):
  for vectors in(self.vectors.astype(np.int16),self.vectors[:-1],np.full((15,23,2),33,np.int8)):
   with self.assertRaises(ValueError):v.subject.predict(self.reference,vectors,32)
  for block in(0,31,True):
   with self.assertRaises(ValueError):v.subject.predict(self.reference,self.vectors,block)
 def test_borrowed_prediction_does_not_redefine_publication_or_ownership(self):
  # A caller's readonly bank contract is not protection from privileged writes.
  refs=tuple(p.copy()for p in self.reference)
  for p in refs:p.setflags(write=False)
  borrowed=v.subject.predict(refs,self.vectors,32);before=borrowed[0][0,0]
  refs[0].setflags(write=True);refs[0][0,0]=int(before)^1;refs[0].setflags(write=False)
  self.assertEqual(borrowed[0][0,0],int(before)^1)

if __name__=='__main__':unittest.main()
