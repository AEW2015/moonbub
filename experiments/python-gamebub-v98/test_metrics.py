import unittest
import numpy as np
from metrics import displayed, sequence_quality, distribution, pareto


class MetricsTests(unittest.TestCase):
    def test_identity_and_rgb565_floor(self):
        a = np.zeros((8, 8, 3), np.uint8)
        a[:] = (127, 63, 241)
        b = displayed(a)
        self.assertEqual(tuple(b[0, 0]), (123, 60, 247))
        q = sequence_quality([a, a], [a, a], [0, 0, 8, 8], [[0, 0, 4, 4]])
        self.assertAlmostEqual(q['pooled']['active']['mse'], (16+9+36)/3)
        self.assertEqual(q['temporal_error_mse_max'], 0)
        exact = sequence_quality([b], [b], [0, 0, 8, 8], [[0, 0, 4, 4]])
        self.assertEqual(exact['pooled']['active']['mse'], 0)
        self.assertIsNone(exact['pooled']['active']['psnr_db'])

    def test_roi_and_temporal_error(self):
        a = np.zeros((8, 8, 3), np.uint8)
        b = a.copy()
        b[:4, :4] = 255
        q = sequence_quality([a, a], [a, b], [0, 0, 8, 8], [[0, 0, 4, 4]])
        self.assertEqual(q['pooled']['roi']['mse'], 65025/2)
        self.assertEqual(q['pooled']['background']['mse'], 0)
        self.assertEqual(q['temporal_error_mse_max'], 65025/4)

    def test_masks_and_frame_count_rejected(self):
        a = np.zeros((8, 8, 3), np.uint8)
        with self.assertRaises(ValueError):
            sequence_quality([a], [], [0, 0, 8, 8], [[0, 0, 4, 4]])
        with self.assertRaises(ValueError):
            sequence_quality([a], [a], [0, 0, 9, 8], [[0, 0, 4, 4]])

    def test_frontier_and_tail(self):
        rows = [dict(case_id='a', coded_bytes=10, active_mse=1, roi_mse=2),
                dict(case_id='b', coded_bytes=11, active_mse=2, roi_mse=2),
                dict(case_id='c', coded_bytes=12, active_mse=.5, roi_mse=3)]
        self.assertEqual(pareto(rows), ['a', 'c'])
        self.assertEqual(distribution([3, 1, 2])['p95_nearest_rank'], 3)


if __name__ == '__main__':
    unittest.main()
