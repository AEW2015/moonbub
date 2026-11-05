import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
BASE = json.loads((HERE / 'baseline.json').read_text())


class BaselineTests(unittest.TestCase):
    def test_exact_mse_and_inclusive_cap(self):
        accounting = BASE['accounting']
        self.assertEqual(accounting['frames_per_scene'], 48)
        self.assertEqual(accounting['binding_bytes_per_frame'], 60)
        for scene in BASE['scenes'].values():
            for point in scene.values():
                self.assertEqual(point['samples'], 48 * 720 * 405 * 3)
                self.assertAlmostEqual(point['sse'] / point['samples'], point['mse'], places=14)
                self.assertLessEqual(point['max_frame_bytes'], accounting['cap_bytes_per_frame'])

    def test_standard_points_share_hud_and_meet_custom_mean_mse(self):
        for scene in BASE['scenes'].values():
            custom = scene['custom_band_control']
            custom_mse = custom['sse'] / custom['samples']
            for codec in ('av1', 'hevc'):
                point = scene[codec]
                self.assertTrue(BASE['accounting']['all_points_include_same_current_hud'])
                self.assertLessEqual(point['sse'] / point['samples'], custom_mse)
                self.assertLessEqual(point['max_frame_bytes'], BASE['accounting']['cap_bytes_per_frame'])

    def test_completed_v33_comparison_has_no_motion_policy_superiority(self):
        import audit
        report = audit.audit()
        self.assertEqual(report['global_motion']['accepted_frames'], 288)
        for scene in ('mass-effect-2600', 'mass-effect-7200'):
            control = report['cohorts'][f'{scene}/band_control']
            for policy in ('global_cross', 'global_grid'):
                row = report['cohorts'][f'{scene}/{policy}']
                self.assertGreater(row['v32_hud_wire_complete_bytes'], control['v32_hud_wire_complete_bytes'])
                self.assertGreater(row['active_mse'], control['active_mse'])
            for policy in ('band_control', 'global_cross', 'global_grid'):
                points = report['same_current_HUD_standard_operating_points'][scene][policy]['selected_same_current_HUD']
                self.assertEqual(set(points), {'libsvtav1', 'libx265'})

    def test_split_probe_keeps_raw_negative_result_and_actual_control_guard(self):
        import audit
        split = audit.audit()['split_fixed_reference']
        self.assertEqual(split['source_frames'], 24)
        self.assertEqual(split['selected_split_frames'], [
            ['mass-effect-7200', 5], ['mass-effect-7200', 7],
            ['mass-effect-7200', 8], ['mass-effect-7200', 10], ['mass-effect-7200', 11]])
        self.assertEqual(split['complete_byte_saving'], 1811)
        self.assertGreater(split['raw_split16_band_complete_byte_delta_vs_control'], 0)
        self.assertGreater(split['raw_split16_frames_with_rgb_regression'], 0)
        self.assertTrue(split['no_causal_or_cross_study_combined_gain_claim'])


if __name__ == '__main__':
    unittest.main()
