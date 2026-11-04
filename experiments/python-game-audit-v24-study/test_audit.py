import unittest

import audit


class V24IndependentAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit.build_audit()

    def test_offline_source_and_sidecar_evidence_covers_both_scenes(self):
        self.assertEqual(self.result['native_cases'], 20)
        self.assertEqual(self.result['native_outputs'], 960)
        self.assertEqual(self.result['retained_rgb565_source_canvases_checked'], 96)
        self.assertEqual(self.result['v23_input_rgb_hash_links_checked'], 96)
        self.assertEqual(self.result['common_yuv420_source_tags_checked'], 96)
        self.assertEqual(self.result['exact_hc22_sidecars_checked'], 96)

    def test_every_native_packet_stream_is_redecoded(self):
        self.assertEqual(self.result['native_packet_blobs_checked'], 20 * 48)
        self.assertEqual(self.result['native_output_ids_redecoded'], 20 * 48)
        self.assertEqual(self.result['key_ids'], [0, 24])

    def test_rgb565_quality_and_exact_hud_are_recomputed(self):
        self.assertEqual(self.result['independently_recomputed_bare_hybrid_quality_rows'], 2 * 20 * 48)
        self.assertEqual(self.result['exact_hybrid_hud_words'], 20 * 48 * 21120)

    def test_custom_baselines_are_replayed_from_frozen_v23_packets(self):
        self.assertEqual(self.result['custom_baseline_rows_replayed'], 4 * 48)

    def test_actual_sampled_operating_points_are_recomputed(self):
        self.assertEqual(self.result['operating_points_recomputed'], 4 * 2 * 2)

    def test_claim_boundaries_and_bounded_artifact_path_guard(self):
        self.assertIn('no Game Bub HEVC/AV1 decoder', self.result['scope']['native'])
        self.assertIn('not prove end-to-end latency', self.result['scope']['timing'])
        self.assertIn('not a BD-rate', self.result['scope']['quality'])
        self.assertIn('hypothetical', self.result['scope']['hybrid'])
        with self.assertRaises(AssertionError):
            audit.raw_blob(dict(path='../outside', raw_bytes=0, raw_sha256='x', stored_sha256='x'))

    def test_owned_lazy_campaign_preserves_streams_and_bounds_copy(self):
        lazy = self.result['lazy_ownership']
        self.assertEqual((lazy['cases'], lazy['decisions'], lazy['paired_identical_rows']), (6, 288, 96))
        self.assertEqual(lazy['copied_snapshot_bytes'], 99532800)
        self.assertEqual(lazy['owned_source_guard_bytes'], 0)

    def test_rs24_campaign_recomputes_losses_and_reboot_stale_rejection(self):
        reset = self.result['recovery_profile_reset']
        self.assertEqual((reset['campaigns'], reset['recovered'], reset['control_messages'],
                          reset['lost_controls_charged']), (10, 9, 100, 13))
        self.assertEqual(reset['reboot_epochs'], [1, 2, 3])
        self.assertTrue(reset['stale_data_rejected'])


if __name__ == '__main__':
    unittest.main()
