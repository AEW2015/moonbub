import unittest
import json
from pathlib import Path

from audit import audit_row, audit_study, audit_hybrid, audit_block, audit_hybrid_link, has_unresolved_work

ROOT = Path(__file__).resolve().parents[2]


class V11AuditTests(unittest.TestCase):
    def test_complete_packet_bytes_drive_cap_check(self):
        row = audit_row({"format": "HG01", "packet_bytes": 49_153, "inner_gm_bytes": 10,
                         "header_bytes": 32, "vector_bytes": 20})
        self.assertFalse(row["cap_ok"])
        self.assertEqual(row["packet_bytes"], 49_153)
        self.assertEqual(row["format_vector_roi_skip_overhead"]["vector_bytes"], 20)

    def test_binding_requires_outer_and_inner_epoch_and_frame_match(self):
        same = audit_row({"outer_epoch": 3, "outer_frame_id": 8,
                          "inner_gm_epoch": 3, "inner_gm_frame_id": 8,
                          "outer_feedback_packet_bytes": 24})
        wrong = audit_row({"outer_epoch": 3, "outer_frame_id": 8,
                           "inner_gm_epoch": 2, "inner_gm_frame_id": 8})
        self.assertTrue(same["outer_inner_binding_matches"])
        self.assertFalse(wrong["outer_inner_binding_matches"])
        self.assertEqual(same["outer_feedback_packet_bytes"], 24)

    def test_reject_atomicity_is_not_inferred_when_missing(self):
        row = audit_row({"status": "rejected"})
        self.assertTrue(row["rejected"])
        self.assertIsNone(row["atomic_reject_evidence"])

    def test_losing_candidate_work_is_counted_as_charged(self):
        row = audit_row({"attempts": [
            {"selected": True, "encode_ms": 1.5, "validate_ms": 0.5},
            {"selected": False, "encode_ms": 3, "validate_ms": 1},
        ]})
        self.assertEqual(row["attempt_charged_service_ms"], 6)
        self.assertEqual(row["loser_attempt_count"], 1)
        self.assertEqual(row["loser_attempt_charged_ms"], 4)

    def test_modes_do_not_double_count_source_frame_pairs(self):
        result = audit_study({"records": [
            {"source_id": "clip", "frame_id": 7, "format": "GM01", "packet_bytes": 100},
            {"source_id": "clip", "frame_id": 7, "format": "HR01", "packet_bytes": 50},
            {"source_id": "clip", "frame_id": 8, "format": "HG01", "packet_bytes": 60},
        ]}, "fixture")
        self.assertEqual(result["row_count"], 3)
        self.assertEqual(result["source_frame_pairs"], 2)
        self.assertEqual(result["distinct_source_ids"], 1)
        self.assertFalse(result["formats_installed_proven"])
        self.assertEqual(result["hardware_timing_rows"], 0)

    def test_actual_hybrid_has_four_decisions_per_source_and_cap_fits(self):
        data=json.loads((ROOT/"experiments/python-game-hybrid-study/results.json").read_text())
        out=audit_hybrid(data)
        self.assertEqual((out["source_records"],out["policy_evaluations"]),(140,560))
        self.assertEqual(out["base_overcap_rejected_sources"],2)
        self.assertEqual(out["base_overcap_rejected_policy_decisions"],8)
        self.assertTrue(out["frame_identity_consistent_across_policies"])
        self.assertTrue(all(v["over_cap"]==0 for v in out["policy_metrics"].values()))

    def test_actual_block_profiles_share_frame_hashes_and_preserve_negative_cases(self):
        data=json.loads((ROOT/"experiments/python-game-block-study/results.json").read_text())
        out=audit_block(data)
        self.assertEqual(out["actual_decode_records"],612)
        self.assertTrue(out["frame_id_input_hashes_match_across_profiles"])
        noise=next(s for s in out["scenes"] if s["name"]=="synthetic-noise-cut")
        self.assertGreater(noise["profile_metrics"]["bm_block4"]["bytes_mean"],noise["profile_metrics"]["gm_zero"]["bytes_mean"])

    def test_actual_link_sums_capture_runs_separately_from_presentations(self):
        data=json.loads((ROOT/"experiments/python-game-hybrid-link-study/results.json").read_text())
        out=audit_hybrid_link(data)
        self.assertEqual((out["case_count"],out["capture_decisions_sum_across_cases"]),(12,720))
        self.assertEqual(out["decoded_format_counts"],{"GM01":231,"HG01":438})
        self.assertEqual(out["prepared_format_counts"],{"GM01":231,"HG01":439})
        self.assertEqual({k:v["cases"] for k,v in out["per_mode"].items()},
                         {"gm_only":4,"adaptive_ui":8})
        self.assertTrue(out["outer_inner_feedback_binding_proven"])
        self.assertEqual(out["packet_event_cap_failures"],0)

    def test_drained_optional_slots_are_not_mistaken_for_active_slots(self):
        data=json.loads((ROOT/"experiments/python-game-hybrid-link-study/results.json").read_text())
        self.assertTrue(all(not has_unresolved_work(c["result"]) for c in data["cases"]))
        self.assertFalse(has_unresolved_work({"unresolved_sender_slots":[None,None],
            "unresolved_ingress_frames":[],"unresolved_credits":[],"pending_ids":[],
            "waiting_at_end":None,"unresolved_cpu":{"parse":0,"feedback_inflight":0}}))

    def test_active_owner_in_sender_slot_remains_unresolved(self):
        self.assertTrue(has_unresolved_work({"unresolved_sender_slots":[None,{"id":7,"owner":"decode"}],
            "unresolved_ingress_frames":[],"unresolved_credits":[],"pending_ids":[],
            "waiting_at_end":None,"unresolved_cpu":{"parse":0}}))

    def test_refresh_probe_is_a_separate_run_not_extra_baseline_frames(self):
        data=json.loads((ROOT/"experiments/python-game-hybrid-link-study/refresh-results.json").read_text())
        out=audit_hybrid_link(data)
        self.assertEqual((out["case_count"],out["capture_decisions_sum_across_cases"]),(2,120))
        self.assertEqual(out["strict_presented_sum_across_case_runs"],117)
        self.assertEqual(out["eventual_presented_sum_across_case_runs"],119)


if __name__ == "__main__":
    unittest.main()
