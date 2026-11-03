from pathlib import Path
import sys
import unittest
import numpy as np
import bounded_math as bm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'python-motion-study'))
import motion_codec as mt


class ResidualArithmeticTests(unittest.TestCase):
    def test_key_and_prediction_coefficients_and_planes_match(self):
        rng=np.random.default_rng(608)
        for h,w in ((2,2),(18,34),(64,80)):
            source=bm.frozen.rgb_to_planes(rng.integers(0,256,(h,w,3),dtype=np.uint8))
            for pred in ([np.full_like(p,128) for p in source],
                         [rng.integers(0,256,p.shape,dtype=np.int16) for p in source]):
                for scale in (1,8,32,128):
                    old=mt.residual_coefficients(source,pred,scale)
                    fast=bm.residual_coefficients(source,pred,scale)
                    for a,b in zip(old,fast):np.testing.assert_array_equal(a,b)
                    for a,b in zip(mt.reconstruct(old,pred,scale),bm.reconstruct(fast,pred,scale)):
                        np.testing.assert_array_equal(a,b)

    def test_full_dequant_range_not_silently_narrowed(self):
        prediction=[np.full((8,8),128,np.int16)]
        for coefficient in (-2048,2048):
            coeff=[np.full((1,8,8),coefficient,np.int16)]
            np.testing.assert_array_equal(mt.reconstruct(coeff,prediction,128)[0],
                                          bm.reconstruct(coeff,prediction,128)[0])


if __name__=='__main__':unittest.main()
