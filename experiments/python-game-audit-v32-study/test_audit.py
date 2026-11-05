import unittest
from unittest.mock import patch

import audit


class V32AuditHelperTests(unittest.TestCase):
    def test_complete_packet_cap_includes_binding_and_hud(self):
        self.assertEqual(audit.complete_body_bytes(40_000, 9_092), 49_152)
        self.assertTrue(audit.under_cap(49_152))
        self.assertFalse(audit.under_cap(49_153))
        with self.assertRaises(ValueError):
            audit.complete_body_bytes(-1, 0)
        with self.assertRaises(ValueError):
            audit.under_cap(True)

    def test_integer_quality_guards_have_no_rounding(self):
        self.assertTrue(audit.strict_or_budget_guard(100, 100, 'shrink_strict'))
        self.assertFalse(audit.strict_or_budget_guard(101, 100, 'shrink_strict'))
        self.assertTrue(audit.strict_or_budget_guard(101, 100, 'shrink_budget'))
        self.assertFalse(audit.strict_or_budget_guard(102, 100, 'shrink_budget'))
        with self.assertRaises(ValueError):
            audit.strict_or_budget_guard(0, 0, 'adaptive_control')

    def test_standard_points_add_current_hud_and_choose_cap_fitting_quality_point(self):
        rows = []
        for fid in range(48):
            rows.append(dict(id=fid, coded_access_unit_bytes=100,
                             hybrid=dict(metric=dict(active_squared_error=40,
                                                     active_channel_samples=10,
                                                     active_mse=4.0))))
        standard = dict(schema='gamebub-standard-compare-v24', cases=[
            dict(scene='scene', codec='HEVC', profile='qA', rows=rows),
        ])
        checked = audit.standard_operating_points(standard, 'scene',
                                                  {fid: 50 for fid in range(48)}, 4.0)
        point = checked['selected_same_current_HUD']['HEVC']
        self.assertEqual(point['complete_bytes'], 48 * (100 + 50 + 60))
        self.assertTrue(checked['qualifying_fit_exists'])
        too_large_hud = {fid: audit.CAP for fid in range(48)}
        no_fit = audit.standard_operating_points(standard, 'scene', too_large_hud, 4.0)
        self.assertFalse(no_fit['qualifying_fit_exists'])
        self.assertEqual(no_fit['selected_same_current_HUD'], {})
        with self.assertRaises(ValueError):
            audit.standard_operating_points(standard, 'scene', {fid: -1 for fid in range(48)}, 4.0)

    def test_false_baseline_packet_parity_is_rejected(self):
        current = dict(packet={'path': 'p'}, ack={'path': 'a'}, hybrid={'active_mse': 1.0},
                       hybrid_rgb565_sha256='image')
        baseline = dict(packet={'path': 'bp'}, ack={'path': 'ba'}, hybrid={'active_mse': 1.0},
                        hybrid_rgb565_sha256='image')
        blobs = {'p': b'pair', 'bp': b'different', 'a': b'ack', 'ba': b'ack'}
        with patch.object(audit, 'read_object', side_effect=lambda d, _: blobs[d['path']]):
            with self.assertRaises(ValueError):
                audit.verify_packet_parity(current, baseline, audit.STUDY, audit.V30_STUDY)
        blobs['bp'] = b'pair'
        with patch.object(audit, 'read_object', side_effect=lambda d, _: blobs[d['path']]):
            audit.verify_packet_parity(current, baseline, audit.STUDY, audit.V30_STUDY)

    def test_selection_and_quality_gates_reject_wrong_candidate(self):
        shadow = dict(kind='half32_band', complete_bytes=100,
                      hybrid=dict(active_squared_error=100))
        saving = dict(kind='zero_shrink', complete_bytes=90, cap_fit=True,
                      quality_eligible=True, selected=False,
                      hybrid=dict(active_squared_error=100))
        self.assertIs(audit._select_from_shadow(shadow, [saving], 'shrink_strict'), saving)
        wrong_quality_flag = dict(saving, quality_eligible=False)
        with self.assertRaises(ValueError):
            audit._select_from_shadow(shadow, [wrong_quality_flag], 'shrink_strict')
        selected_no_saving = dict(saving, complete_bytes=100, selected=True)
        with self.assertRaises(ValueError):
            audit._select_from_shadow(shadow, [selected_no_saving], 'shrink_strict')
        overcap = dict(saving, complete_bytes=90, cap_fit=False)
        self.assertIs(audit._select_from_shadow(shadow, [overcap], 'shrink_strict'), shadow)

    def test_reference_chain_rejects_missing_or_invalid_predecessor(self):
        self.assertEqual(audit.expected_reference_tag(0, None), bytes(16).hex())
        self.assertEqual(audit.expected_reference_tag(1, '11' * 16), '11' * 16)
        for bad in (None, 'bad', '00' * 15):
            with self.assertRaises(ValueError):
                audit.expected_reference_tag(1, bad)

    def test_metric_and_cost_validation_rejects_false_or_nonfinite_values(self):
        metric = dict(active_squared_error=25, active_channel_samples=5, active_mse=5.0)
        self.assertEqual(audit.integer_metric(metric), (25, 5, 5.0))
        metric['active_mse'] = 4.9
        with self.assertRaises(ValueError):
            audit.integer_metric(metric)
        for cost in (-0.1, float('nan'), float('inf'), True, '2'):
            self.assertFalse(audit.finite_nonnegative(cost))


if __name__ == '__main__':
    unittest.main()
