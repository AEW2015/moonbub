import unittest

import json
from pathlib import Path

from audit import audit_memo, audit_refresh, audit_sparse, candidate_cost, identity_counts, packet_accounting, packet_fit_counts, skip_compatibility, timing_evidence

ROOT = Path(__file__).resolve().parents[2]


class V12AuditTests(unittest.TestCase):
    def test_complete_packet_accounting_includes_header_crc_and_skip_bytes(self):
        row = {"packet_bytes": 120, "payload_bytes": 80, "header_bytes": 24,
               "crc_bytes": 4, "skip_bytes": 12}
        out = packet_accounting(row)
        self.assertEqual(out["component_sum_bytes"], 120)
        self.assertTrue(out["component_sum_matches_packet"])
        self.assertTrue(out["headers_and_crc_recorded"])

    def test_source_frames_are_deduplicated_across_cohorts_and_modes(self):
        out = identity_counts([
            {"source_id":"clip", "frame_id":1, "cohort":"real", "mode":"rate"},
            {"source_id":"clip", "frame_id":1, "cohort":"real", "mode":"motion"},
            {"source_id":"synthetic", "frame_id":1, "cohort":"synthetic"},
        ])
        self.assertEqual(out["rows"], 3)
        self.assertEqual(out["identified_source_frames"], 2)
        self.assertEqual(out["duplicate_source_frame_rows"], 1)
        self.assertEqual(out["cohort_counts"], {"real":2,"synthetic":1})

    def test_losing_candidate_cost_is_included(self):
        out = candidate_cost([{"attempts":[
            {"selected":True,"encode_ms":2,"search_ms":1},
            {"rejected":True,"encode_ms":5,"validate_ms":2},
        ]}])
        self.assertEqual(out["explicit_attempt_service_ms"], 10)
        self.assertEqual(out["loser_explicit_service_ms"], 7)

    def test_skip_is_bit_exact_only_with_explicit_coefficient_and_pixel_equality(self):
        self.assertTrue(skip_compatibility({"source_coefficients":[0,0],"decoded_coefficients":[0,0],
                                           "source_pixels":[8,9],"reconstructed_pixels":[8,9]})["bit_exact_skip_proven"])
        self.assertFalse(skip_compatibility({"zero_coefficients_equal":True})["bit_exact_skip_proven"])

    def test_wall_and_declared_service_timing_remain_separate(self):
        out = timing_evidence({"wall_ms":12,"declared_service_ms":20})
        self.assertEqual(out["measured_wall_ms"],12)
        self.assertEqual(out["declared_service_ms"],20)
        self.assertFalse(out["physical_timing_proven"])

    def test_sparse_actual_rows_are_exact_and_keep_packet_savings_claim_off(self):
        data=json.loads((ROOT/"experiments/python-game-sparse-study/results.json").read_text())
        out=audit_sparse(data)
        self.assertEqual((out["row_count"],out["unique_source_frame_records"]),(120,120))
        self.assertEqual(out["unique_rgb_content_hashes"],92)
        self.assertTrue(out["primary_resolution_720x480_all_cases"])
        self.assertTrue(out["all_baseline_fast_yuv_rgb_and_rgb565_checks_exact"])
        self.assertTrue(out["block_count_partition_consistent"])
        self.assertTrue(out["bypass_count_matches_zero_plus_dc"])
        self.assertFalse(out["packet_byte_savings_claimed"])

    def test_rate_motion_actual_rows_match_only_declared_comparison_evidence(self):
        from audit import audit_rate_motion
        data=json.loads((ROOT/"experiments/python-game-rate-motion-study/results.json").read_text())
        out=audit_rate_motion(data)
        self.assertEqual((out["decision_rows"],out["actual_rate_admitted"]),(462,151))
        self.assertEqual(out["comparison_rows"],154)
        self.assertEqual(out["same_canonical_reference_rows"],154)
        self.assertEqual(out["candidate_packets_match_control_rows"],154)
        self.assertEqual(out["gm_bm_active_mse_diff_rows"],135)
        self.assertEqual(out["complete_packet_vs_inner_plus_header_crc_mismatches"],0)
        self.assertGreater(out["profile_metrics"]["actual_rate"]["losing_candidate_ms"],0)
        self.assertEqual(out["profile_metrics"]["actual_rate"]["actual_decision_rejections"],3)
        self.assertEqual(out["profile_metrics"]["actual_rate"]["over_cap_candidate_attempts"],6)
        self.assertFalse(out["strict_eventual_presentation_counts_available"])

    def test_losing_over_cap_candidate_does_not_count_as_decision_rejection(self):
        counts=packet_fit_counts([{"accepted":True,"attempts":[
            {"fits":False,"selected":False},{"fits":True,"selected":True}]}])
        self.assertEqual(counts,{"actual_decision_rejections":0,"decisions_with_cap_failed_candidates":1,"over_cap_candidate_attempts":1})

    def test_refresh_actual_runs_keep_strict_and_eventual_and_pin_late_ack_regressions(self):
        data=json.loads((ROOT/"experiments/python-game-refresh-study/results.json").read_text())
        out=audit_refresh(data)
        self.assertEqual(out["case_count"],17)
        self.assertEqual(out["capture_events_summed_across_runs"],1020)
        self.assertEqual(out["presentations_rederived_strict_timestamp_mismatches"],0)
        self.assertEqual(out["runs_with_unresolved_work_at_end"],0)
        self.assertEqual(out["pairing_identity_mismatches"],0)
        self.assertEqual(out["unique_source_frames_in_nominal_scale_gm_only"]["real_source"],120)
        self.assertEqual(out["source_frame_decisions_by_cohort"],{"real_source":120,"synthetic":60})
        self.assertTrue(out["late_ack_state_evidence"]["late_ack_tests_recorded_passing"])
        self.assertTrue(out["late_ack_state_evidence"]["asserts_sender_anchor_not_installed"])

    def test_memo_replays_keep_exact_wire_packets_and_separate_sources_from_ids(self):
        data=json.loads((ROOT/"experiments/python-game-memo-study/results.json").read_text())
        out=audit_memo(data)
        self.assertEqual((out["case_count"],out["paired_frame_rows"],out["unique_source_frame_pairs"]),(5,156,156))
        self.assertEqual(out["cohort_frame_rows"],{"real_source":120,"synthetic":36})
        self.assertTrue(out["all_bitstreams_unchanged"])
        self.assertEqual((out["baseline_forward_calls"],out["memo_forward_calls"]),(468,348))
        self.assertFalse(out["packet_byte_savings_claimed"])


if __name__ == "__main__":
    unittest.main()
