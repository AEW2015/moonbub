"""Independent analytical/dispatch review, separate from benchmarked kernels."""
import unittest
from unittest import mock

import numpy as np

import bounded_math as bm


class ArithmeticReviewTests(unittest.TestCase):
    def test_inverse_first_pass_extreme_including_negative_rounding(self):
        matrix = bm.frozen.Q14
        column = max(range(8), key=lambda j: sum(abs(int(matrix[i, j])) for i in range(8)))
        signs = np.array([1 if matrix[i, column] >= 0 else -1 for i in range(8)], np.int64)
        for maximum in (255, bm.domain_report()['inverse_int32_max_abs'], bm.MAX_DEQUANT):
            for sign in (-1, 1):
                row = signs * maximum * sign
                # Python integer sum is independent of NumPy accumulator dtype.
                raw = sum(int(row[i]) * int(matrix[i, column]) for i in range(8))
                rounded = (raw + 8192) // 16384
                bounds = bm.stage_bounds(maximum, 'inverse')
                self.assertLessEqual(abs(raw + 8192), bounds['first_acc_abs_including_bias'])
                self.assertLessEqual(abs(rounded), bounds['first_rounded_abs'])
                if sign == 1:
                    self.assertEqual(rounded, bounds['first_rounded_abs'])

    def test_declared_full_domain_multiplies_fit_asymmetric_dsp_operands(self):
        q = bm.frozen.Q14
        constant_bits = max(abs(int(v)) for v in q.flat).bit_length() + 1
        inverse_input = bm.frozen.MAX_COEFF * 255
        column_l1 = max(sum(abs(int(q[i, j])) for i in range(8)) for j in range(8))
        inverse_first = (inverse_input * column_l1 + 8192) // 16384
        inverse_second_acc = inverse_first * column_l1 + 8192
        self.assertLessEqual(constant_bits, 18)
        self.assertLessEqual(inverse_input.bit_length() + 1, 25)
        self.assertLessEqual(inverse_first.bit_length() + 1, 25)
        self.assertLessEqual(inverse_second_acc.bit_length() + 1, 48)
        self.assertEqual(inverse_first.bit_length() + 1, 22)
        self.assertEqual(inverse_second_acc.bit_length() + 1, 37)

    def test_large_domain_uses_frozen_int64_fallback(self):
        coefficients = np.full((1, 8, 8), bm.MAX_DEQUANT, np.int64)
        original = bm.frozen.inverse
        with mock.patch.object(bm.frozen, 'inverse', wraps=original) as fallback:
            actual = bm.inverse(coefficients)
            fallback.assert_called_once()
            np.testing.assert_array_equal(actual, original(coefficients))

    def test_dispatch_safe_boundary_matches_adversarial_column_signs(self):
        q = bm.frozen.Q14
        limit = bm.domain_report()['inverse_int32_max_abs']
        blocks = []
        for column in range(8):
            signs = np.sign(q[:, column]).astype(np.int64)
            blocks.extend((np.tile(signs * limit, (8, 1)), -np.tile(signs * limit, (8, 1))))
        a = np.stack(blocks)
        np.testing.assert_array_equal(bm.inverse(a), bm.frozen.inverse(a))


if __name__ == '__main__':
    unittest.main()
