import unittest
import audit


class IndependentV21Audit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit.build_audit()

    def test_all_native_rows_recomputed_with_cap_and_source_identity(self):
        self.assertEqual(self.result['native_budget_rows_recomputed'], 96)
        self.assertEqual({row['scene'] for row in self.result['native_scenes']},
                         {'mass-effect-2600', 'mass-effect-7200'})
        for scene in self.result['native_scenes']:
            self.assertEqual(scene['frames'], 48)
            self.assertEqual(scene['complete_cap_fits'], 48)
            self.assertLessEqual(scene['maximum_complete_bytes'], audit.FRAME_CAP)

    def test_offline_pair_and_yuv_replay_counts_are_separate(self):
        replay = self.result['component_replay']
        self.assertEqual(replay['CB21_full_display_words'], 3_456_000)
        self.assertEqual(replay['preserved_yuv_samples'], 5_184_000)
        self.assertNotEqual(replay['CB21_full_display_words'], replay['preserved_yuv_samples'])
        self.assertFalse(self.result['joint_base_hud_publication_implemented'])

    def test_cb21_and_ha21_transport_overheads_are_included(self):
        self.assertEqual(self.result['CB21_overhead_bytes'], 57)
        self.assertEqual(self.result['HA21_ack_bytes'], 54)
        self.assertEqual(self.result['ipv4_udp_overhead_per_control'], 28)
        self.assertEqual(audit.transport(1009, True)['hud_ack_reverse_bytes'], 82)
        self.assertEqual(audit.transport(1009, False)['hud_ack_reverse_bytes'], 0)
        # Fewer proposed data fragments can offset HA21 on the aggregate reverse path.
        self.assertNotEqual(self.result['native_scenes'][1]['transport']['proposed_transport']['reverse_ipv4_udp_bytes'],
                            self.result['native_scenes'][1]['transport']['legacy_transport']['reverse_ipv4_udp_bytes'])

    def test_noise_regression_and_no_hardware_fps_claim_are_retained(self):
        self.assertLess(self.result['synthetic_noise_complete_patch_forward_saving_fraction'], 0)
        self.assertFalse(self.result['hardware_rtl_resource_fit_or_physical_30fps_proven'])
        self.assertIn('offline arithmetic', self.result['rate_calculation_scope'])

    def test_source_pins_and_recorded_test_suites(self):
        self.assertEqual(self.result['source_pins_verified'], {'HD21': 6, 'HC21': 53, 'CB21': 170})
        self.assertEqual(self.result['tests_recorded'], {'HD21': 14, 'HC21': 15, 'CB21': 7})


if __name__ == '__main__':
    unittest.main()
