import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
BASE = json.loads((HERE / 'baseline.json').read_text())


class V34BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import audit
        cls.report = audit.audit()

    def test_exact_integer_sse_mean_mse_and_cap(self):
        a = BASE['accounting']
        expected_samples = a['frames_per_scene'] * 720 * 405 * 3
        for scene in BASE['scenes'].values():
            for label in ('custom_band_control', 'av1', 'hevc'):
                point = scene[label]
                self.assertEqual(point['samples'], expected_samples)
                self.assertAlmostEqual(point['sse'] / point['samples'], point['mse'], places=14)
                self.assertLessEqual(point['max_frame_bytes'], a['cap_bytes_per_frame'])

    def test_standards_use_shared_hx33_accounting_and_beat_baseline_points(self):
        self.assertTrue(BASE['accounting']['same_HX33_hud_for_custom_HEVC_AV1'])
        self.assertTrue(BASE['accounting']['prospective_HX33_accounting'])
        for scene in BASE['scenes'].values():
            custom = scene['custom_band_control']
            self.assertEqual(scene['hud_bytes'] > 0, True)
            for codec in ('av1', 'hevc'):
                point = scene[codec]
                self.assertLess(point['complete_bytes'], custom['complete_bytes'])
                self.assertLessEqual(point['mse'], custom['mse'])

    def test_v34_causal_hierarchy_shows_primary_complex_tradeoff(self):
        report = self.report
        self.assertEqual(report['cohort_rows'], 288)
        primary_control = report['cohorts']['mass-effect-2600/control']
        primary_full = report['cohorts']['mass-effect-2600/hierarchy_full']
        complex_control = report['cohorts']['mass-effect-7200/control']
        complex_full = report['cohorts']['mass-effect-7200/hierarchy_full']
        self.assertLess(primary_full['complete_bytes'], primary_control['complete_bytes'])
        self.assertLess(primary_full['active_mse'], primary_control['active_mse'])
        self.assertLess(complex_full['complete_bytes'], complex_control['complete_bytes'])
        self.assertGreater(complex_full['active_mse'], complex_control['active_mse'])
        self.assertFalse(report['fixed_reference_components']['hierarchy']['causal_campaign'])
        self.assertEqual(report['cohorts']['mass-effect-7200/hierarchy_select25']['selected_child_frames'], 12)

    def test_opaque_safe_mask_negative_full_mask_and_masked_native_comparison(self):
        report = self.report
        for scene in ('mass-effect-2600', 'mass-effect-7200'):
            case = report['opaque_masking'][scene]
            self.assertEqual(case['visible_safe_mask_frames'], 48)
            self.assertEqual(case['full_mask_visible_negative_frames'], 48)
            self.assertTrue(case['historical_HU25_bytes_not_used_for_savings'])
            self.assertGreater(case['corrected_CP34_HX33_control_bytes'], case['complete_bytes'])
            self.assertGreater(case['active_mse'], case['corrected_control_source_sse'] / (48 * 720 * 405 * 3))
            for codec in ('libx265', 'libsvtav1'):
                native = report['opaque_same_processed_native_points'][f'{scene}/{codec}']
                self.assertTrue(native['same_processed_masked_input'])
                self.assertTrue(native['same_HX33_and_60B'])
                self.assertTrue(native['meets_custom_MSE_and_cap'])


if __name__ == '__main__':
    unittest.main()
