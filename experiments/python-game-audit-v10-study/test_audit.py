import unittest

from audit import audit_bundle, audit_rle, audit_selective, audit_service, classify_input, roi_coverage


class V10AuditTests(unittest.TestCase):
    def test_input_class_requires_explicit_provenance(self):
        self.assertEqual(classify_input({"synthetic": True}), "synthetic")
        self.assertEqual(classify_input({"synthetic": False}), "real_source")
        self.assertEqual(classify_input({"name": "camera-frame"}), "provenance_missing")

    def test_selected_roi_coverage_measures_union_and_overlap(self):
        row = {"declared_roi_rects": [[0, 0, 10, 10], [5, 0, 10, 10]],
               "selected_roi_rects": [[0, 0, 10, 10]]}
        result = roi_coverage(row)
        self.assertEqual(result["declared_roi_pixels"], 150)
        self.assertEqual(result["selected_roi_pixels"], 100)
        self.assertEqual(result["selected_pixels_inside_declared_roi"], 100)
        self.assertAlmostEqual(result["selected_roi_coverage_fraction"], 2 / 3)

    def test_selective_audit_checks_cap_and_actual_fallback_identity(self):
        result = audit_selective({"frame_cap_bytes": 100,
                                  "declared_roi_rects": [[0, 0, 10, 10]],
                                  "records": [{"id": 1, "synthetic": False, "packet_bytes": 99,
                                               "selected_roi_rects": [[0, 0, 5, 10]],
                                               "fallback_packet_sha256": "same", "baseline_gm01_sha256": "same"},
                                              {"id": 2, "synthetic": True, "packet_bytes": 101,
                                               "fallback_packet_sha256": "old", "baseline_gm01_sha256": "new"}]})
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["rows"][0]["input_class"], "real_source")
        self.assertEqual(result["rows"][0]["roi_coverage"]["selected_roi_coverage_fraction"], 0.5)
        self.assertTrue(result["rows"][0]["fallback_packet_identity"])
        self.assertFalse(result["rows"][1]["cap_ok"])
        self.assertFalse(result["rows"][1]["fallback_packet_identity"])

    def test_rejected_work_cost_must_be_explicitly_charged(self):
        result = audit_service({"records": [
            {"status": "accepted", "service_components_ms": {"encode": 2, "decode": 3}},
            {"status": "rejected", "service_components_ms": {"encode": 4, "decision": 1}},
            {"status": "rejected"},
        ]})
        self.assertEqual(result["service_total_ms_including_rejects"], 10)
        self.assertEqual(result["rejected_rows_missing_cost_indexes"], [2])
        self.assertFalse(result["all_rejected_work_charged"])

    def test_row_rle_cap_and_timing_backend_are_separate(self):
        result = audit_rle({"records": [
            {"synthetic": False, "packet_bytes": 100, "raw_bytes": 200, "rle_bytes": 100, "backend": "native"},
            {"synthetic": True, "packet_bytes": 50_000, "backend": "python"},
        ]})
        self.assertFalse(result["rows"][1]["cap_ok"])
        self.assertEqual(result["native_timing_rows"], 1)
        self.assertEqual(result["software_timing_rows"], 1)

    def test_stored_selective_service_and_row_results_rederive(self):
        result = audit_bundle()
        self.assertEqual(result["selective"]["row_count"], 60)
        self.assertEqual(result["selective"]["counts"]["real_source_decisions"], 48)
        self.assertEqual(result["selective"]["counts"]["synthetic_decisions"], 12)
        self.assertEqual(result["selective"]["counts"]["deadline_fallbacks"], 18)
        self.assertTrue(all(r["fallback_gm01_identity"] for r in result["selective"]["rows"] if r["format"] == "GM01"))
        self.assertEqual(result["service"]["case_count"], 8)
        self.assertEqual(result["service"]["zero_cpu_case_count"], 2)
        self.assertEqual(result["service"]["charged_cpu_case_count"], 6)
        self.assertEqual(result["service"]["zero_cpu_charged_service_ms"], 0)
        self.assertTrue(result["service"]["all_model_cpu_queues_drained"])
        self.assertEqual(result["row_rle"]["row_count"], 80)
        self.assertTrue(result["row_rle"]["all_four_profile_patch_counts_positive_per_case"])
        self.assertTrue(result["row_rle"]["all_candidate_bytes_choose_minimum"])
        self.assertTrue(result["row_rle"]["all_rederived_means_and_fit_counts_match_stored"])

    def test_standard_codec_quality_byte_pts_and_color_floor_evidence(self):
        result = audit_bundle()
        standard = result["standard_video"]
        self.assertEqual(standard["profile_count"], 18)
        self.assertEqual(standard["total_decoded_records"], 1080)
        self.assertEqual(standard["native_codec_output_records"], 720)
        self.assertTrue(standard["all_profile_manifests_same_per_source"])
        self.assertEqual(standard["manifest_unique_source_rgb_frame_counts"]["mass-effect-combat"], [32])
        self.assertEqual(standard["manifest_unique_source_rgb_frame_counts"]["mass-effect-2600"], [60])
        self.assertTrue(all(r["records_sum_matches_summary"] for r in standard["profiles"]))
        self.assertTrue(all(r["native_coded_bytes_matches_summary"] for r in standard["profiles"] if r["native_coded_bytes_matches_summary"] is not None))
        self.assertTrue(all(r["native_decoder_pts_exact_0_to_59"] for r in standard["profiles"] if r["native_decoder_pts_exact_0_to_59"] is not None))
        self.assertTrue(all(q["stored_quality_matches"] for r in standard["profiles"] for q in r["pooled_quality"].values()))
        self.assertTrue(result["color_floor"]["all_pooled_quality_rederived_matches"])
        self.assertEqual(result["common_color"]["new_native_codec_output_records"], 720)
        self.assertEqual(result["common_color"]["reused_gm_output_records_not_double_counted"], 360)
        self.assertTrue(result["common_color"]["prior_original_results_pin_matches"])
        self.assertTrue(result["common_color"]["frame_manifests_match_original_profiles"])
        self.assertTrue(result["common_color"]["native_pts_and_emitted_pts_exact"])
        self.assertTrue(result["common_color"]["native_packet_plus_extradata_matches_records_and_summaries"])
        self.assertTrue(result["common_color"]["all_pooled_quality_independently_matches"])
        self.assertEqual(result["accounting"]["total_unique_codec_output_rows_across_campaigns"], 1800)
        self.assertEqual(result["accounting"]["separate_color_floor_conversion_rows"], 240)
        self.assertTrue(result["source_pins_match_before_and_after"])
        self.assertTrue(result["external_media_hash_guard_match_before_and_after"])


if __name__ == "__main__":
    unittest.main()
