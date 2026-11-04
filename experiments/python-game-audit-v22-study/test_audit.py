import unittest
import audit


class V22AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit.build_audit()

    def test_pins_replays_and_saved_verifier_evidence(self):
        self.assertEqual(self.result['source_pins']['joint'], 57)
        self.assertGreaterEqual(self.result['source_pins']['gap'], 700)
        self.assertEqual(self.result['source_pins']['projection'], 3)
        self.assertEqual(self.result['source_test_counts'], {'joint': 21, 'gap': 10})
        self.assertEqual(self.result['stored_joint_pair_packets_parsed'], 96)

    def test_fixed_profile_control_reproduces_v21_bytes_and_quality(self):
        rows = {r['scene']: r for r in self.result['base_profile_quality_comparison']}
        self.assertEqual(rows['mass-effect-2600']['fixed_bytes'], 934451)
        self.assertEqual(rows['mass-effect-7200']['fixed_bytes'], 2017112)
        self.assertAlmostEqual(rows['mass-effect-2600']['fixed_mse'], 14.428984744131993)
        self.assertAlmostEqual(rows['mass-effect-7200']['fixed_mse'], 34.09208026120256)
        self.assertEqual(self.result['scope']['fixed_v20_profiles'].split(';')[1].strip(),
                         'image/bytes control, omits v20 controller search, not a fair timing or deployable causal policy baseline')

    def test_adaptive_quality_cost_is_reported(self):
        rows = {r['scene']: r for r in self.result['base_profile_quality_comparison']}
        complex_case = rows['mass-effect-7200']
        self.assertEqual(complex_case['adaptive_bytes'], 2072408)
        self.assertEqual(complex_case['adaptive_extra_bytes'], 55296)
        self.assertGreater(complex_case['adaptive_mse'], 0)
        self.assertLess(complex_case['adaptive_mse'], complex_case['fixed_mse'])
        self.assertEqual(complex_case['same_reference_ids'], list(range(33)))
        self.assertLess(complex_case['same_reference_adaptive_mse'], complex_case['same_reference_fixed_mse'])

    def test_gap_savings_include_fallback_and_complete_sidecar(self):
        rows = {r['scene']: r for r in self.result['native_gap_and_complete_pair_recomputed']}
        self.assertEqual(rows['mass-effect-2600']['sidecar_saving_bytes'], 14484)
        self.assertEqual(rows['mass-effect-7200']['sidecar_saving_bytes'], 41682)
        self.assertEqual(rows['mass-effect-2600']['projected_complete_pair_bytes'], 919967)
        self.assertEqual(rows['mass-effect-7200']['projected_complete_pair_bytes'], 1975430)
        self.assertEqual(rows['mass-effect-2600']['max_projected_pair_bytes'], 27693)
        self.assertEqual(rows['mass-effect-7200']['max_projected_pair_bytes'], 48477)

    def test_synthetic_fallback_cases_show_no_false_gain(self):
        self.assertEqual(self.result['synthetic_gap_savings'], {
            'synthetic-static': 0, 'synthetic-small_change': 0, 'synthetic-noise': 0})

    def test_scope_does_not_claim_native_or_physical_30fps(self):
        self.assertIn('projection', self.result['scope']['HD22'])
        self.assertIn('no DMA', self.result['scope']['physical'])


if __name__ == '__main__':
    unittest.main()
