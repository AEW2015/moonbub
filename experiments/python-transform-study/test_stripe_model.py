import unittest

import numpy as np

import fixed_codec as ft
from stripe_model import render_stripes, sample_layout


class StripeTests(unittest.TestCase):
    def test_reconstruction_matches_full_plane_kernel_at_boundaries(self):
        rng = np.random.default_rng(20261103)
        for h, w in ((2, 2), (18, 34), (34, 18), (480, 720)):
            planes = [rng.integers(0, 256, (h, w), dtype=np.uint8),
                      rng.integers(0, 256, (h//2, w//2), dtype=np.uint8),
                      rng.integers(0, 256, (h//2, w//2), dtype=np.uint8)]
            golden = ft.planes_to_rgb(planes)
            for rows in (2, 8, 16, 32):
                strips = list(render_stripes(planes, rows))
                actual = np.concatenate([x[1] for x in strips])
                self.assertTrue(np.array_equal(actual, golden), (h, w, rows))
                layout = sample_layout(w, h, rows)
                self.assertEqual(max(x[2] for x in strips), layout['peak_decoded_sample_payload_bytes'])

    def test_payload_accounting_includes_next_chroma_row(self):
        result = sample_layout()
        self.assertEqual(result['full_decoded_yuv420_bytes'], 518400)
        self.assertEqual(result['peak_decoded_sample_payload_bytes'], 18000)
        self.assertEqual(result['stripes'], 30)
        self.assertEqual(result['extra_chroma_overlap_sample_bytes'], 29*720)

    def test_bad_geometry_and_samples_fail(self):
        with self.assertRaises(ValueError):
            sample_layout(rows=3)
        with self.assertRaises(ValueError):
            list(render_stripes([np.zeros((4, 4)), np.zeros((2, 2)), np.zeros((2, 2))]))
        with self.assertRaises(ValueError):
            list(render_stripes([np.zeros((4, 4), np.uint8), np.zeros((3, 2), np.uint8), np.zeros((2, 2), np.uint8)]))


if __name__ == '__main__':
    unittest.main()
