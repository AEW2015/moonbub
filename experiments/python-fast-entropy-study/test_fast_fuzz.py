"""Additional deterministic sparse/dense context coverage for CP02 compatibility."""
import unittest

import numpy as np

import fast_coeff as fast


class CompatibilityCampaign(unittest.TestCase):
    def test_eighty_coefficient_families_preserve_complete_packets(self):
        rng=np.random.default_rng(5302026)
        for case in range(80):
            width=int(rng.integers(1,16));rows=int(rng.integers(1,8))
            amplitude=(1,4,31,255,2048)[case%5]
            density=(0,.001,.005,.01,.1,.5,1)[case%7]
            a=rng.integers(-amplitude,amplitude+1,(width*rows,8,8),dtype=np.int16)
            a[rng.random(a.shape)>density]=0
            if case%3==0:
                a[:,0,0]=rng.integers(-2048,2049,len(a),dtype=np.int16)
            expected=fast.frozen.encode_coefficients(a,width)
            actual=fast.encode_coefficients(a,width)
            self.assertEqual(actual,expected,case)
            self.assertTrue(np.array_equal(fast.frozen.decode_coefficients(actual,len(a),width),a),case)


if __name__=='__main__':unittest.main()
