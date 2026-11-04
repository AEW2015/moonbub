import json
import unittest
import audit

class EvidenceAccountingTests(unittest.TestCase):
    def test_payload_only_is_not_complete_wire_packet(self):
        self.assertIsNone(audit.complete_packet_bytes({"payload_bytes": 81}))
        self.assertEqual(audit.complete_packet_bytes({"payload_bytes": 81, "packet_bytes": 94}), 94)

    def test_equal_rgb_does_not_collapse_distinct_source_frames(self):
        rows = [{"source_id": "capture-a", "frame_id": 1, "source_rgb_sha256": "same", "cohort": "real"},
                {"source_id": "capture-b", "frame_id": 1, "source_rgb_sha256": "same", "cohort": "real"}]
        got = audit.identity_counts(rows)
        self.assertEqual(got["unique_source_frames"], 2)
        self.assertEqual(got["unique_rgb_content_hashes"], 1)

    def test_rejected_paid_work_remains_in_cost_total(self):
        got = audit.explicit_cost([{"encode_wall_ms": 3}, {"encode_wall_ms": 7, "accepted": False}], ("encode_wall_ms",))
        self.assertEqual((got["sum_ms"], got["rejected_sum_ms"]), (10, 7))

    def test_missing_ack_binding_keeps_promotion_safety_unknown_or_false(self):
        self.assertIsNone(audit.ack_promotion_evidence([])["promotion_ack_safety"])
        lost = audit.ack_promotion_evidence([{"event": "promote", "tag": 4, "ack_status": "lost", "fallback_bank": 0, "fallback_kind": "key"}])
        self.assertFalse(lost["promotion_ack_safety"])
        self.assertTrue(lost["lost_ack_uncertainty"])
        self.assertEqual(lost["key_bank_fallbacks"], 1)
        bound = audit.ack_promotion_evidence([{"event": "promote", "tag": 4, "ack_status": "accepted"}])
        self.assertTrue(bound["promotion_ack_safety"])

    def test_virtual_timing_is_never_claimed_as_hardware_timing(self):
        got = audit.timing_separation([{"host_wall_ms": 2, "virtual_ms": 10}])
        self.assertEqual(got["host_wall_sum_ms"], 2)
        self.assertEqual(got["virtual_or_declared_sum_ms"], 10)
        self.assertFalse(got["hardware_timing_proven"])

    def test_final_recent_reference_results_recompute_protocol_evidence(self):
        with audit.INPUTS["recent_reference"].open() as f:
            report = audit.audit_recent_reference(json.load(f))
        self.assertEqual((report["declared_native_source_ids"], report["attempted_packets_declared"], report["attempt_rows_recomputed"], report["decoded_packets_declared"]), (300, 924, 924, 916))
        self.assertEqual(report["source_pins"]["pin_count"], 13)
        self.assertTrue(report["source_pins"]["all_match_and_stable"])
        self.assertTrue(report["all_present_external_media_pins_match"])
        self.assertTrue(report["all_prior_reference_frame_tag_bindings_match_acknowledged_state"])
        recent = report["profiles"]["ar_recent8"]
        self.assertEqual((recent["accepted"], recent["rejected"], recent["promotion_completed_rows"]), (308, 4, 36))
        self.assertEqual(recent["promotion_reconstruction_and_tag_work_paid_rows"], 41)
        self.assertEqual(recent["promoted_bank_frame_tag_bindings_valid"], 36)
        self.assertEqual(recent["promoted_bank_frame_tag_bindings_invalid"], 0)
        self.assertTrue(recent["all_accepted_full_packets_within_cap"])
        self.assertTrue(report["source_regression_tests"]["lost_promotion_ack_disables_bank_and_falls_back_to_key"])
        self.assertTrue(report["source_regression_tests"]["physical_reader_leases_block_overwrite"])

    def test_final_finite_ownership_results_recompute_timing_faults_and_bounds(self):
        with audit.INPUTS["finite_reference_ownership"].open() as f:
            report = audit.audit_finite_ownership(json.load(f))
        self.assertEqual((report["case_count_recomputed"], report["capture_events_declared_by_case"], report["prepared_attempts"], report["decoded_commits"]), (13, 1152, 1028, 1027))
        self.assertEqual(report["source_pins"]["pin_count"], 15)
        self.assertTrue(report["source_pins"]["all_match_and_stable"])
        self.assertTrue(report["all_external_media_pins_match"])
        self.assertTrue(report["all_cases_resource_bounded"])
        self.assertTrue(report["all_case_strict_counts_rederived"])
        self.assertTrue(report["all_cases_drained_at_end"])
        self.assertEqual(report["recorded_stage_wall_service_mismatches"], 0)
        self.assertTrue(report["route_nacks_arrived_before_host_ack_expiry"])
        self.assertEqual(report["promotion_ack_loss_case"]["lost_ack_feedback_events"], 1)
        self.assertTrue(report["promotion_ack_loss_case"]["no_nack_fabricated_for_lost_ack"])
        self.assertTrue(report["conflicting_feedback_case"]["accepted_ack_and_nack_for_same_promotion"])
        self.assertFalse(report["conflicting_feedback_case"]["ack_applied_after_conflicting_nack"])
        self.assertTrue(report["regression_tests"]["paid_ack_expiry_cannot_publish"])
        self.assertTrue(report["regression_tests"]["paid_receiver_completion_deadline_aborts_publication"])

    def test_final_overlap_results_recompute_matched_heldout_delivery(self):
        with audit.INPUTS["overlap_reference"].open() as f:
            report = audit.audit_overlap_reference(json.load(f))
        heldout = report["heldout_initial_immutable_vs_overlap"]
        self.assertTrue(heldout["prepared_id_sets_equal"])
        self.assertTrue(heldout["presented_id_sets_equal"])
        self.assertEqual(heldout["prepared_ids_missing_from_both"], [1])
        self.assertEqual(heldout["presented_ids_missing_control"], [1])
        self.assertEqual(heldout["presented_ids_missing_overlap"], [1])
        self.assertEqual((heldout["steady_presented_count_control"], heldout["steady_presented_count_overlap"]), (150, 150))
        self.assertEqual((heldout["steady_unique_native_input_hashes_control"], heldout["steady_unique_native_input_hashes_overlap"]), (150, 150))
        self.assertEqual((heldout["steady_unique_decoded_rgb_hashes_control"], heldout["steady_unique_decoded_rgb_hashes_overlap"]), (150, 150))
        self.assertAlmostEqual(heldout["mean_complete_ar_body_bytes_control"], 18688.59217877095)
        self.assertAlmostEqual(heldout["mean_complete_ar_body_bytes_overlap"], 12216.603351955308)
        self.assertAlmostEqual(heldout["complete_body_size_saving_pct"], 34.63, places=2)
        self.assertEqual(heldout["strict_presentations_control_overlap"], [177, 177])
        self.assertTrue(heldout["input_results_hash_matches_matched_analysis"])
        self.assertTrue(heldout["analysis_source_hash_matches_matched_analysis"])
        self.assertTrue(heldout["analyze_check_log_passes"])
        self.assertEqual(report["base_ownership_audit"]["source_pins"]["pin_count"], 17)
        self.assertTrue(report["base_ownership_audit"]["all_cases_resource_bounded"])
        self.assertTrue(report["pairs_recomputed_match_declared_counts"])
        self.assertTrue(report["all_same_choice_packet_hashes_exact"])

    def test_final_skip_results_recompute_counts_bounds_and_paid_rejects(self):
        with audit.INPUTS["skip_residual"].open() as f:
            report = audit.audit_skip_residual(json.load(f))
        self.assertEqual((report["declared_source_ids"], report["unique_source_frame_keys"], report["decisions_recomputed"]), (154, 154, 770))
        self.assertTrue(report["source_pins"]["all_match_and_stable"])
        self.assertTrue(report["all_present_external_media_pins_match"])
        for name in ("gm", "sr_dense", "sr_exact", "sr_prune2", "sr_prune4"):
            profile = report["profiles"][name]
            self.assertEqual((profile["rows"], profile["admitted"], profile["rejected"]), (154, 151, 3))
            self.assertTrue(profile["all_admitted_packets_within_per_row_cap"])
            self.assertEqual(profile["rejected_rows_with_paid_prepare_ms"], 3)
        self.assertEqual(report["profiles"]["sr_prune2"]["max_observed_pruned_yuv_delta_vs_quantized_gm"], 2)
        self.assertEqual(report["profiles"]["sr_prune4"]["max_observed_pruned_yuv_delta_vs_quantized_gm"], 4)
        self.assertTrue(report["profiles"]["sr_prune4"]["all_checked_prune_blocks_within_row_level_bound"])
        self.assertEqual(report["profiles"]["sr_prune4"]["protected_rgb565_mismatches"], 0)

if __name__ == "__main__": unittest.main()
