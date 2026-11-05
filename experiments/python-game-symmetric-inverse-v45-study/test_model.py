import unittest
import numpy as np
import model as m
class Symmetric(unittest.TestCase):
 def test_every_basis_signed_extremes(self):
  for k in range(64):
   for value in(-522240,-8192,-1,1,8192,522240):
    a=np.zeros((8,8),np.int64);a.flat[k]=value;np.testing.assert_array_equal(m.inverse(a),m.ft.inverse(a));out,work=m.scalar_sparse(a);np.testing.assert_array_equal(out,m.ft.inverse(a));w=m.logical_work(a);self.assertEqual(work['total_products'],w['sparse_symmetric_products'])
 def test_random_and_rounding_boundaries(self):
  rng=np.random.default_rng(45);a=rng.integers(-522240,522241,(1000,8,8),dtype=np.int64);np.testing.assert_array_equal(m.inverse(a),m.ft.inverse(a))
  for tile in a[:20]:np.testing.assert_array_equal(m.scalar_sparse(tile)[0],m.ft.inverse(tile))
 def test_zero_dc_and_dense_bounds(self):
  for value in(-522240,0,522240):
   a=np.full((8,8),value,np.int64);out,w=m.scalar_sparse(a);np.testing.assert_array_equal(out,m.ft.inverse(a));bounds=m.interval_bounds();self.assertLessEqual(w['max_first_accumulator_magnitude'],bounds['first_accumulator_absolute_bound']);self.assertLessEqual(w['max_second_accumulator_magnitude'],bounds['second_accumulator_absolute_bound'])
 def test_shortcuts_exact_and_paid(self):
  for v in(-522240,-16384,-8192,-1,0,1,8192,16384,522240):
   a=np.zeros((8,8),np.int64);a[0,0]=v;out,w=m.scalar_shortcuts(a);np.testing.assert_array_equal(out,m.ft.inverse(a));self.assertEqual(w['total_products'],2 if v else 0)
 def test_invalid_domains(self):
  for a in(np.zeros((4,4),int),np.zeros((8,8),float),np.full((8,8),522241,int)):
   with self.assertRaises(ValueError):m.inverse(a)
if __name__=='__main__':unittest.main()
