import unittest

import json
from pathlib import Path

from audit import audit_cache, audit_credit_window, audit_execution, audit_motion, audit_ui_cache, complete_packet, explicit_cost, source_identity, timing_classes

ROOT = Path(__file__).resolve().parents[2]


class V13AuditTests(unittest.TestCase):
    def test_complete_packet_cap_is_unknown_without_complete_size(self):
        self.assertIsNone(complete_packet({"payload_bytes": 100, "frame_cap": 1000})["fits_cap"])
        self.assertFalse(complete_packet({"packet_bytes": 1001, "frame_cap": 1000})["fits_cap"])

    def test_identity_does_not_confuse_rows_or_hashes_with_source_frames(self):
        out = source_identity([
            {"source_id": "clipA", "frame_id": 1, "rgb_sha256": "same", "cohort": "real"},
            {"source_id": "clipA", "frame_id": 1, "rgb_sha256": "same", "cohort": "real"},
            {"source_id": "synthetic", "frame_id": 1, "rgb_sha256": "same", "cohort": "synthetic"},
            {"rgb_sha256": "other"},
        ])
        self.assertEqual(out["rows"], 4)
        self.assertEqual(out["unique_source_frames"], 2)
        self.assertEqual(out["duplicate_source_frame_rows"], 1)
        self.assertEqual(out["rows_missing_source_or_frame_id"], 1)
        self.assertEqual(out["unique_rgb_content_hashes"], 2)

    def test_rejected_attempt_cost_is_still_paid_and_missing_cost_is_unknown(self):
        out = explicit_cost([{"accepted": True, "gate_wall_ms": 2},
                             {"accepted": False, "gate_wall_ms": 7}, {"accepted": False}], ("gate_wall_ms",))
        self.assertEqual(out["explicit_cost_sum_ms"], 9)
        self.assertEqual(out["rejected_explicit_cost_sum_ms"], 7)
        self.assertEqual(out["rows_with_explicit_cost"], 2)

    def test_motion_gate_result_counts_and_logged_regressions(self):
        data = json.loads((ROOT / "experiments/python-game-motion-gate-study/results.json").read_text())
        out = audit_motion(data)
        self.assertEqual((out["decisions_declared"], out["profile_decision_rows"], out["all_profile_candidate_attempts"]), (616, 616, 775))
        self.assertEqual((out["real_gated_rows_without_bm_attempt"], out["synthetic_gated_rows_with_bm_attempt"]), (136, 5))
        self.assertEqual(out["control_packet_match_rows"], 154)
        self.assertTrue(out["regression_tests_present_and_logged_passing"]["all_required_logged_passing"])

    def test_cache_admission_result_exact_bytes_and_rejected_work(self):
        data = json.loads((ROOT / "experiments/python-game-cache-admission-study/results.json").read_text())
        out = audit_cache(data)
        self.assertEqual((out["paired_source_ids_declared"], out["row_count"], out["accepted_rows"], out["rejected_rows"]), (172, 172, 163, 9))
        self.assertEqual(out["cache_hit_attempts"], 49)
        self.assertTrue(out["all_compared_whole_packets_equal"])
        self.assertTrue(out["all_rejected_rows_have_candidate_cost"])
        self.assertTrue(out["cap_before_commit_source_evidence"])
        self.assertTrue(out["regression_tests_present_and_logged_passing"]["all_required_logged_passing"])

    def test_actual_wall_is_separate_from_charged_service(self):
        out = timing_classes({"actual_wall_ms": 34, "charged_service_ms": 22})
        self.assertEqual(out["actual_wall_ms"], 34)
        self.assertEqual(out["charged_service_ms"], 22)
        self.assertTrue(out["actual_wall_and_charged_service_separate"])
        self.assertFalse(out["hardware_timing_proven"])

    def test_execution_keeps_wall_replay_separate_and_rederives_strict_presentations(self):
        data = json.loads((ROOT / "experiments/python-game-execution-study/results.json").read_text())
        out = audit_execution(data)
        self.assertEqual((out["case_count"], out["capture_events_summed_across_runs"]), (16, 1104))
        self.assertEqual(out["strict_timestamp_rederivation_mismatches"], 0)
        self.assertEqual(out["runs_with_unresolved_work_at_end"], 0)
        self.assertTrue(out["actual_wall_observations_available"])
        self.assertTrue(all(v["all_equal"] for v in out["actual_wall_equals_charged_service_observations"].values()))
        self.assertTrue(out["regression_tests_present_and_logged_passing"]["all_required_logged_passing"])
        self.assertFalse(out["hardware_timing_proven"])

    def test_ui_cache_preserves_full_packets_and_counts_changed_background_hits(self):
        data = json.loads((ROOT / "experiments/python-game-ui-cache-study/results.json").read_text())
        out = audit_ui_cache(data)
        self.assertEqual((out["row_count"], out["unique_case_frame_ids"]), (160, 160))
        self.assertEqual(out["cache_hit_attempts"], 292)
        self.assertEqual(out["hits_on_changed_whole_source"], 176)
        self.assertEqual(out["max_entries_observed"], 4)
        self.assertTrue(out["all_cached_packets_match_baseline"])
        self.assertTrue(out["full_validation_ms_recorded_for_cache_hit_attempts"])
        self.assertTrue(out["regression_tests_present_and_logged_passing"]["all_required_logged_passing"])

    def test_credit_window_bounds_and_factory_agreement_use_actual_replay(self):
        data = json.loads((ROOT / "experiments/python-game-credit-window-study/results.json").read_text())
        out = audit_credit_window(data)
        self.assertEqual((out["case_count"], out["capture_events_summed_across_runs"], out["prepared_total"], out["decoded_commit_total"]), (7, 780, 661, 661))
        self.assertEqual(out["strict_timestamp_rederivation_mismatches"], 0)
        self.assertEqual(out["runs_with_unresolved_work_at_end"], 0)
        self.assertTrue(out["all_window_factory_pairs_agree"])
        self.assertTrue(out["all_observed_peaks_fit_configured_pools"])
        self.assertTrue(out["source_pins"]["all_match_and_stable"])
        self.assertTrue(out["regression_tests_present_and_logged_passing"]["all_required_logged_passing"])
        self.assertTrue(out["expiry_wins_regression_has_serialized_ack_then_nack_and_zero_ack_promotion_assertion"])
        self.assertTrue(out["positive_ack_after_reader_drain_control_assertion_present"])
        self.assertTrue(out["unsupported_gate_config_rejection_in_model"])
        self.assertTrue(out["all_main_case_service_tapes_none_actual_wall_mode"])
        self.assertTrue(all(v["all_equal"] for v in out["actual_wall_equals_charged_service_observations"].values()))
        self.assertFalse(out["three_credit_window_is_hardware_default"])


if __name__ == "__main__":
    unittest.main()
