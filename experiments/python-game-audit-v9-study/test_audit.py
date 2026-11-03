import unittest
import json
from pathlib import Path

from audit import (ROOT, audit_feedback, audit_hud, audit_transport,
                   audit_hud_studies, audit_feedback_results, audit_pipeline, run_v9_audit,
                   capture_outcomes)


class AuditV9Tests(unittest.TestCase):
    def test_capture_outcomes_keep_stages_and_deduplicate_ids(self):
        result = capture_outcomes({
            "distinct_presented_ids": [1, 2, 2],
            "eventually_presented_ids": [1, 2, 3],
            "diagnostic_ids": [1, 2, 3, 4],
            "measurement_seconds": 2,
        })
        self.assertEqual(result["distinct_strict"]["unique_count"], 2)
        self.assertEqual(result["eventual"]["unique_count"], 3)
        self.assertEqual(result["diagnostic"]["unique_count"], 4)
        self.assertTrue(result["displayed_fps_proven"])

    def test_aggregate_service_cost_counts_rejects_and_binding(self):
        result = audit_feedback({"records": [
            {"status": "accepted", "service_ms": 4, "sent_epoch": 2, "applied_epoch": 2,
             "sent_frame_id": 10, "applied_frame_id": 10},
            {"status": "rejected", "service_ms": 3, "sent_epoch": 2, "applied_epoch": 2,
             "sent_frame_id": 11, "applied_frame_id": 11},
        ]})
        self.assertEqual(result["reject_count"], 1)
        self.assertTrue(result["service_cost_includes_rejects"])
        self.assertEqual(result["service_cost_sum_ms"], 7)
        self.assertTrue(result["feedback_binding_proven"])

    def test_transport_needs_headers_payload_peak_and_drain(self):
        result = audit_transport({"records": [{"forward_wire_bytes": 100, "feedback_wire_bytes": 12}],
                                  "headers_bytes": 8, "total_wire_bytes": 120,
                                  "two_slot_payload_peak_bytes": 4096,
                                  "physical_read_drain": False})
        self.assertEqual(result["calculated_wire_bytes"], 120)
        self.assertTrue(result["wire_accounting_matches"])
        self.assertEqual(result["two_slot_payload_peak_bytes"], 4096)
        self.assertFalse(result["physical_drain_proven"])

    def test_hud_patch_claims_require_parsed_pixel_and_color_metadata(self):
        result = audit_hud({"modes": [
            {"name": "normal", "whole_frame_bytes": 500, "predictor_unchanged": True,
             "patches": [{"width": 4, "height": 3, "rgb565_colors": [0, 65535], "bytes": 8}]},
            {"name": "pressure", "whole_frame_bytes": 900, "predictor_unchanged": True,
             "patches": [{"bytes": 20}]},
        ]})
        self.assertTrue(result["modes"][0]["all_roi_color_claims_supported"])
        self.assertFalse(result["modes"][1]["all_roi_color_claims_supported"])
        self.assertTrue(result["modes"][0]["predictor_unchanged_proven"])
        self.assertTrue(result["whole_frame_cap_is_not_roi_pixel_proof"])

    def test_missing_claim_fields_stay_missing(self):
        self.assertEqual(capture_outcomes({})["distinct_strict"]["evidence"], "missing")
        self.assertEqual(audit_feedback({})["feedback_binding_evidence"], "missing")
        self.assertIn("headers", audit_transport({})["gaps"])

    def test_stored_pipeline_and_feedback_evidence_is_rederived(self):
        base = ROOT / "experiments"
        pipeline = json.loads((base / "python-game-pipeline-study/results.json").read_text())
        feedback = json.loads((base / "python-game-feedback-study/results.json").read_text())
        regression = json.loads((base / "python-game-feedback-study/regression.json").read_text())
        pa = audit_pipeline(pipeline)
        fa = audit_feedback_results(feedback, regression)
        self.assertEqual(pa["case_count"], 12)
        self.assertEqual(sum(c["service_reject_n"] for c in pa["cases"]), 8)
        self.assertTrue(all(c["drain_clear"] for c in pa["cases"]))
        self.assertTrue(all(c["feedback_epoch_frame_binding"]["binding_proven"] for c in pa["cases"]))
        self.assertTrue(all(c["capture_count"] == 60 for c in pa["cases"][:10]))
        self.assertTrue(all(c["diagnostic_presentation_count"] == round(c["diagnostic_presentation_fps_rederived"])
                            for c in pa["cases"][:10]))
        self.assertEqual(pa["cases"][0]["diagnostic_presentation_count"], 29)
        self.assertEqual(pa["cases"][0]["diagnostic_window_ms"], [500, 1500.0])
        self.assertEqual(pa["cases"][0]["diagnostic_presentation_fps_rederived"], 29.0)
        self.assertEqual(fa["forward_protocol_header_bytes_per_chunk"], 31)
        self.assertEqual(fa["forward_ipv4_udp_overhead_per_chunk"], 28)
        self.assertEqual(fa["feedback_protocol_bytes_per_feedback"], 24)
        self.assertEqual(fa["reverse_ipv4_udp_overhead_per_feedback"], 28)
        self.assertTrue(fa["all_resources_drained"])
        self.assertFalse(regression["v8_gf01"]["delivered_pin_retained_after_conflict"])
        self.assertTrue(regression["v9_gf02"]["delivered_pin_retained_after_conflict"])

    def test_stored_hud_scope_and_source_guards(self):
        base = ROOT / "experiments/python-game-hud-study"
        data = json.loads((base / "results.json").read_text())
        flat = json.loads((base / "flat-results.json").read_text())
        result = audit_hud_studies(data, flat)
        self.assertEqual(result["main_patch_records"], 36)
        self.assertEqual(result["main_roi_exact_word_records"], 36)
        self.assertEqual(result["main_patch_cap_failures"], 36)
        self.assertEqual(len(result["flat_patch_cases"]), 2)
        self.assertTrue(result["predictor_claim_supported_by_independent_state_check"])
        complete = run_v9_audit()
        self.assertTrue(complete["source_pins_match_before_and_after"])
        self.assertTrue(complete["external_media_hash_guard_match_before_and_after"])


if __name__ == "__main__":
    unittest.main()
