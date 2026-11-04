import unittest
import audit


class V15AuditTests(unittest.TestCase):
    def test_ui_result_verified_and_exact_display_selection(self):
        data = audit.load_audit()
        ui = data["results"]["unified_ui"]
        self.assertEqual(ui["status"], "verified")
        self.assertEqual(ui["paired_ids"], 160)
        self.assertEqual(ui["patch_attempts_per_variant"], 640)
        self.assertEqual(ui["cache_hits"], 292)
        self.assertEqual(ui["hits_on_changed_whole_source"], 176)
        self.assertEqual(ui["study_regression_test_log"]["passed_count"], 8)
        self.assertTrue(ui["selected_original_rgb565_exact"])
        self.assertTrue(ui["unselected_base_rgb565_exact"])
        self.assertTrue(ui["cached_and_uncached_selector_output_equal"])
        self.assertTrue(ui["cached_and_uncached_display_hash_equal"])
        self.assertEqual(ui["errors"], [])

    def test_codec_full_packet_caps_paid_rejections_and_quality(self):
        data = audit.load_audit()
        codec = data["results"]["unified_codec"]
        self.assertEqual(codec["status"], "verified")
        self.assertEqual(codec["decision_rows"], 1020)
        self.assertEqual(codec["admitted"], 1002)
        self.assertEqual(codec["rejected_with_paid_cap_work"], 18)
        self.assertEqual(codec["accepted_full_packet_over_cap"], 0)
        self.assertEqual(codec["packet_vs_recorded_complete_bytes_mismatch"], 0)
        self.assertEqual(codec["inner_plus_envelope_size_mismatches"], 0)
        self.assertEqual(codec["cap_rejections_not_over_cap"], 0)
        self.assertEqual(codec["actual_analyze_call_counts"], {1: 1020})
        self.assertEqual(codec["actual_forward_call_counts"], {3: 1020})
        self.assertTrue(codec["same_frame_ids_and_input_hashes_across_profiles"])
        self.assertEqual(codec["exact_same_reference_delta_violations"], 0)
        self.assertEqual(codec["prune4_over_bound_violations"], 0)
        self.assertEqual(codec["protected_gm_rgb565_mismatch_rows"], 0)
        self.assertEqual(codec["selected_original_rgb565_mismatch_rows"], 0)
        self.assertEqual(codec["matched_exact_reference"]["status"], "verified")
        self.assertEqual(codec["study_regression_test_log"]["passed_count"], 10)

    def test_stream_crc_tags_ownership_fallback_and_drains(self):
        data = audit.load_audit()
        stream = data["results"]["unified_stream"]
        self.assertEqual(stream["status"], "verified")
        self.assertEqual((stream["case_count"], stream["capture_events"], stream["prepared"], stream["decoded"]), (14, 1248, 1154, 1152))
        self.assertEqual(stream["complete_packet_cap_and_crc_reference_binding_errors"], {
            "cap_or_size": 0, "inner_envelope_ui_sum": 0, "outer_route_crc": 0, "stored_reference_tag_or_read_pin": 0})
        self.assertEqual(stream["max_resource_peaks"], {"sender": 3, "ingress": 2, "framebuffers": 3, "feedback": 2})
        self.assertTrue(stream["physical_drains_all_cases"])
        self.assertTrue(stream["lost_promotion_ack_safe_fallback"])
        self.assertTrue(stream["conflicting_feedback_expires"])
        self.assertEqual(stream["selected_ui_mismatch_rows"], 0)
        self.assertEqual(stream["study_regression_test_log"]["passed_count"], 11)
        self.assertTrue(stream["verify_log_pass"])

    def test_cadence_gate_final_is_verified_and_exact_policy_is_negative(self):
        data = audit.load_audit()
        gate = data["results"]["cadence_gate"]
        self.assertEqual(gate["status"], "verified")
        self.assertTrue(gate["validation_disjoint"])
        self.assertEqual((gate["prior_max_pts"], gate["new_min_pts"], gate["new_max_pts"]), (119600, 120000, 144000))
        self.assertEqual((gate["gate_evaluations"], gate["gate_eligible"]), (174, 0))
        self.assertAlmostEqual(gate["gate_service_ms_per_evaluation"], 0.1070772586)
        self.assertEqual(gate["matched_control_comparison"]["actual_control_sr_wins_skipped"], 79)
        self.assertEqual(gate["matched_control_comparison"]["matched_control_inner_bytes_saved"], 19400)
        self.assertEqual(gate["study_regression_test_log"]["passed_count"], 15)
        self.assertTrue(gate["verify_log_pass"])
        self.assertTrue(gate["analysis_verify_log_pass"])
        self.assertEqual(data["status"], "verified")

    def test_paths_are_portable_and_all_finalized_inputs_verified(self):
        data = audit.load_audit()
        for result in data["results"].values():
            self.assertTrue(all(not p["path"].startswith("/") for p in result["source_pins"]))
            self.assertTrue(all(not p.startswith("/") for p in result["external_media_hashes"]))
        self.assertEqual(data["status"], "verified")
        self.assertEqual(data["inputs"]["cadence_gate"]["status"], "verified")
        self.assertEqual(data["checks"]["cadence_gate_matches_fps_priority_exact_policy"], "verified")


if __name__ == "__main__":
    unittest.main()
