import unittest
import numpy as np
import bounded_math as bm


class ArithmeticTests(unittest.TestCase):
    def test_forward_extrema_and_seeded_blocks_match(self):
        rng = np.random.default_rng(601)
        a = rng.integers(-255, 256, (1000, 8, 8), dtype=np.int64)
        a[0], a[1] = 255, -255
        a[2] = np.indices((8,8)).sum(0)%2*510-255
        np.testing.assert_array_equal(bm.forward(a), bm.frozen.forward(a))

    def test_inverse_small_safe_and_full_syntax_match(self):
        rng = np.random.default_rng(602)
        for limit in (0, 1, 2167, bm.domain_report()['inverse_int32_max_abs'], bm.MAX_DEQUANT):
            a = rng.integers(-limit, limit+1, (257,8,8), dtype=np.int64)
            a[0], a[1] = limit, -limit
            np.testing.assert_array_equal(bm.inverse(a), bm.frozen.inverse(a))

    def test_exact_dispatch_boundary(self):
        limit = bm.domain_report()['inverse_int32_max_abs']
        self.assertTrue(bm.stage_bounds(limit,'inverse')['int32_safe'])
        self.assertFalse(bm.stage_bounds(limit+1,'inverse')['int32_safe'])
        self.assertTrue(bm.stage_bounds(255,'forward')['int32_safe'])
        self.assertFalse(bm.stage_bounds(bm.MAX_DEQUANT,'inverse')['int32_safe'])

    def test_domain_and_dtype_rejections(self):
        for bad in (np.zeros((8,8)), np.zeros((0,8,8),np.int16), np.zeros((1,8,8)),
                    np.full((1,8,8),256,np.int32), np.full((1,8,8),-(1<<63),np.int64)):
            with self.assertRaises(ValueError):bm.forward(bad)
        with self.assertRaises(ValueError):bm.inverse(np.full((1,8,8),bm.MAX_DEQUANT+1,np.int64))

    def test_constructed_first_pass_bound_attained(self):
        maximum=255
        row=int(np.abs(bm.frozen.Q14).sum(1).argmax())
        a=np.tile(np.sign(bm.frozen.Q14[row])[:,None]*maximum,(1,8))
        first=(bm.frozen.Q14@a+8192)>>14
        self.assertEqual(int(first[row,0]),bm.stage_bounds(maximum,'forward')['first_rounded_abs'])


if __name__=='__main__':unittest.main()
