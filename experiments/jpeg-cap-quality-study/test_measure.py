"""Focused arithmetic and generated-result checks for the offline study."""
import io
import json
from pathlib import Path
import sys
import unittest

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import measure  # noqa: E402


def encoded_rgb(rgb):
    stream = io.BytesIO()
    Image.fromarray(np.asarray(rgb, dtype=np.uint8), mode='RGB').save(stream, format='PNG')
    return stream.getvalue()


class PsNRMathTests(unittest.TestCase):
    def test_exact_image_is_infinite_psnr_and_reported_as_perfect(self):
        reference = np.array([[[7, 20, 251]]], dtype=np.uint8)
        self.assertIsNone(measure.frame_psnr(reference, encoded_rgb(reference)))
        stats = measure.summarize([None, None])
        self.assertEqual(stats['count'], 2)
        self.assertEqual(stats['finite_psnr_count'], 0)
        self.assertEqual(stats['perfect_match_count'], 2)
        self.assertIsNone(stats['mean_db_finite_only'])

    def test_known_rgb_mse_maps_to_expected_psnr(self):
        reference = np.array([[[0, 0, 0]]], dtype=np.uint8)
        encoded = encoded_rgb([[[1, 0, 0]]])
        expected = 10.0 * np.log10((255.0 ** 2) / (1.0 / 3.0))
        self.assertAlmostEqual(measure.frame_psnr(reference, encoded), expected, places=6)

    def test_summary_ignores_exact_matches_but_preserves_count(self):
        stats = measure.summarize([40.0, None, 50.0])
        self.assertEqual(stats['count'], 3)
        self.assertEqual(stats['finite_psnr_count'], 2)
        self.assertEqual(stats['perfect_match_count'], 1)
        self.assertEqual(stats['mean_db_finite_only'], 45.0)
        self.assertEqual(stats['median_db_finite_only'], 45.0)


class CapPolicyTests(unittest.TestCase):
    def test_cap_is_inclusive_and_prefers_q90_when_it_fits(self):
        cap = measure.CAP_BYTES
        self.assertEqual(measure.choose_policy(cap, cap + 1), ('send_q90', 90))
        self.assertEqual(measure.choose_policy(cap + 1, cap), ('retry_q80', 80))
        self.assertEqual(measure.choose_policy(cap + 1, cap + 1), ('drop_after_retry', None))

    def test_generated_results_match_per_frame_actions_and_cap(self):
        results = json.loads((HERE / 'results.json').read_text())
        with (HERE / 'per-frame.csv').open(newline='') as source:
            import csv
            rows = list(csv.DictReader(source))
        comparison = results['comparison']
        retry = comparison['q90_then_single_q80_retry']
        self.assertEqual(len(rows), results['sample_count'])
        self.assertEqual(sum(r['policy_action'] == 'send_q90' for r in rows), retry['q90_count'])
        self.assertEqual(sum(r['policy_action'] == 'retry_q80' for r in rows), retry['q80_retry_count'])
        self.assertEqual(sum(r['policy_action'] == 'drop_after_retry' for r in rows), retry['dropped_count'])
        self.assertEqual(sum(int(r['q90_bytes']) > measure.CAP_BYTES for r in rows),
                         comparison['fixed_q90_theoretical_all_frames']['over_cap_count'])
        self.assertTrue(all(int(r['selected_bytes']) <= measure.CAP_BYTES for r in rows if r['selected_bytes']))
        self.assertEqual(retry['q90_count'] + retry['q80_retry_count'] + retry['dropped_count'], len(rows))


if __name__ == '__main__':
    unittest.main()
