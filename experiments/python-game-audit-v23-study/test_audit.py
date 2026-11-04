import unittest

import audit


class V23AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit.build_audit()

    def test_frozen_source_pins_and_retained_replay_counts(self):
        self.assertGreater(self.result['source_pin_count'], 10)
        self.assertEqual(self.result['source_test_counts'], {'joint': 25, 'shared': 16})
        self.assertEqual(self.result['retained_replay'], {
            'decisions': 288,
            'exact_hud_words': 6082560,
            'actual_hd22_span_patches': 456,
            'paired_plain_shared_decisions': 96,
        })

    def test_actual_cp23_sizes_match_previous_hd22_projection_and_cap(self):
        cases = {x['scene']: x for x in self.result['fixed_cp23_rate_and_quality']}
        self.assertEqual(cases['mass-effect-2600']['fixed_complete_bytes'], 919967)
        self.assertEqual(cases['mass-effect-7200']['fixed_complete_bytes'], 1975430)
        self.assertEqual(cases['mass-effect-2600']['fixed_max_complete_bytes'], 27693)
        self.assertEqual(cases['mass-effect-7200']['fixed_max_complete_bytes'], 48477)
        self.assertEqual(self.result['actual_cp23_packet_parses'], 288)
        self.assertEqual(self.result['actual_ja23_acks_parsed'], 288)

    def test_fixed_control_reproduces_complete_display_and_yuv_quality(self):
        cases = {x['scene']: x for x in self.result['fixed_cp23_rate_and_quality']}
        self.assertAlmostEqual(cases['mass-effect-2600']['fixed_projected_rate_forward_Mbps_at30'], 4.980430)
        self.assertAlmostEqual(cases['mass-effect-7200']['fixed_projected_rate_forward_Mbps_at30'], 10.651495)
        self.assertEqual(cases['mass-effect-2600']['exact_hud_words'], 1013760)
        self.assertEqual(cases['mass-effect-7200']['exact_hud_words'], 1013760)

    def test_shared_analysis_reduces_complex_retry_calls_with_byte_parity(self):
        self.assertEqual(self.result['plain_shared_paired_rows'], 96)
        cases = {x['scene']: x for x in self.result['fixed_cp23_rate_and_quality']}
        complex_case = cases['mass-effect-7200']
        self.assertEqual(complex_case['adaptive_plain_analyze_forward'], [59, 177])
        self.assertEqual(complex_case['adaptive_shared_analyze_forward'], [48, 144])

    def test_simple_scene_cpu_regression_is_reported(self):
        simple = self.result['host_cpu_trial']['mass-effect-2600']
        self.assertEqual((simple['plain_ms'], simple['shared_ms']), (1503.45225, 1552.081586))
        self.assertAlmostEqual(simple['change_percent'], 3.2345115051043334)
        self.assertIn('one paired host trial', simple['interpretation'])

    def test_complex_scene_cpu_improvement_and_quality_rate_tradeoff(self):
        complex_cpu = self.result['host_cpu_trial']['mass-effect-7200']
        self.assertEqual((complex_cpu['plain_ms'], complex_cpu['shared_ms']), (1920.602364, 1845.635036))
        self.assertAlmostEqual(complex_cpu['change_percent'], -3.903323738697646)
        complex_trade = next(x for x in self.result['adaptive_rate_quality_tradeoff']
                             if x['scene'] == 'mass-effect-7200')
        self.assertEqual(complex_trade['byte_change'], -14973)
        self.assertAlmostEqual(complex_trade['byte_change_percent'], -0.7224928681996982)
        self.assertAlmostEqual(complex_trade['mean_mse_change'], -0.997281616)
        self.assertAlmostEqual(complex_trade['mean_mse_improvement_percent'], 3.208634762899634)
        self.assertEqual(complex_trade['same_reference_ids'], list(range(48)))
        self.assertEqual((complex_trade['v22_fine_frames'], complex_trade['v23_fine_frames']), (34, 37))
        self.assertLess(complex_trade['mean_mse_change'], 0)

    def test_analysis_guard_traffic_and_retained_host_array_budget(self):
        rows = {x['scene']: x for x in self.result['shared_analysis_memory']}
        self.assertEqual((rows['mass-effect-2600']['source_guard_calls'],
                          rows['mass-effect-2600']['source_guard_bytes']), (96, 99532800))
        self.assertEqual((rows['mass-effect-7200']['source_guard_calls'],
                          rows['mass-effect-7200']['source_guard_bytes']), (107, 110937600))
        self.assertEqual(rows['mass-effect-7200']['retained_analysis_array_bytes_per_context'], 5184000)
        self.assertEqual(rows['mass-effect-7200']['maximum_additional_context_descriptors'], 1)

    def test_claim_boundary_excludes_native_transport_and_physical_rate(self):
        self.assertIn('no native profile enablement', self.result['scope']['physical'])
        self.assertIn('not captured RF traffic', self.result['scope']['wire'])
        self.assertEqual(self.result['independent_fixed_rate_rows'], 96)
        self.assertEqual(self.result['inferred_hd22_span_patch_dispatches'], 456)


if __name__ == '__main__':
    unittest.main()
