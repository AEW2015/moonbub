import unittest
import json
from pathlib import Path

from audit import audit_record, compare_common_ids, PACKET_CAP, codec_audit, rate_audit, size_audit

ROOT = Path(__file__).resolve().parents[2]


class AuditTests(unittest.TestCase):
    def test_attempt_limit_counts_candidates(self):
        self.assertTrue(audit_record({"attempts": [{}, {}]})["attempt_limit_ok"])
        self.assertFalse(audit_record({"attempts": [{}, {}, {}]})["attempt_limit_ok"])

    def test_dct_analysis_call_is_distinct_from_plane_transforms(self):
        row = audit_record({"dct_analysis_calls": 1, "plane_dct_calls": 3})
        self.assertTrue(row["one_analysis_call_ok"])
        self.assertEqual(row["plane_dct_calls"], 3)

    def test_charges_all_attempts_and_key_commit(self):
        row = audit_record({"attempts": [{"charged_ms": 3}, {"transform_ms": 2, "entropy_ms": 4}],
                            "key_commit_ms": 5})
        self.assertEqual(row["charged_attempt_ms"], 9)
        self.assertEqual(row["total_charged_ms_including_key_commit"], 14)

    def test_roi_floor_missing_metadata_is_not_proof(self):
        row = audit_record({"roi_floor": 8, "map_stats": {"scale8": 4}})
        self.assertFalse(row["roi_floor_metadata_proven"])
        self.assertEqual(row["roi_floor_evidence_status"], "missing_or_incomplete_evidence")

    def test_cap_checks_whole_packet_independently_of_wire(self):
        self.assertTrue(audit_record({"packet_bytes": PACKET_CAP, "wire_bytes": PACKET_CAP + 10})["whole_packet_cap_ok"])
        self.assertFalse(audit_record({"packet_bytes": PACKET_CAP + 1, "wire_bytes": 20})["whole_packet_cap_ok"])
        self.assertIsNone(audit_record({"wire_bytes": 20})["whole_packet_cap_ok"])

    def test_common_id_quality_requires_exact_emitted_id(self):
        left = {"manifest": {"source_sha256": "s", "selected_pts": [10, 11], "frame_sha256": ["a", "a"]},
                "records": [{"capture_id": 10, "active_rgb565_mse": 1}, {"capture_id": 11, "active_rgb565_mse": 2}]}
        right = {"manifest": {"source_sha256": "s", "selected_pts": [10, 11], "frame_sha256": ["a", "a"]},
                 "records": [{"capture_id": 11, "active_rgb565_mse": 4}, {"capture_id": 12, "active_rgb565_mse": 9}]}
        result = compare_common_ids(left, right)
        self.assertEqual(result["shared_ids"], [11])
        self.assertEqual(result["common_id_mse"][0]["right_minus_left"], 2)
        self.assertTrue(result["same_frame_hashes"])

    def test_stored_v8_counts_and_transform_reuse(self):
        codec = json.loads((ROOT / "experiments/python-game-codec-study/results.json").read_text())
        rate = json.loads((ROOT / "experiments/python-game-rate-study/results.json").read_text())
        ca, ra = codec_audit(codec), rate_audit(rate)
        self.assertEqual(ca["combined_packet_count_recomputed"], 72)
        self.assertTrue(ca["map338_plus_outer50_net342"])
        self.assertTrue(all(check["one_analysis_three_plane_calls_per_frame"]
                            for scene in ca["scenes"] for check in scene["transform_counter_checks"]))
        self.assertEqual(ra["counts"]["policy_decisions"], 120)
        self.assertEqual(ra["counts"]["real_policy_decisions"], 96)
        self.assertEqual(ra["counts"]["stress_policy_decisions"], 24)
        self.assertEqual(ra["counts"]["admitted"], 108)
        self.assertEqual(ra["counts"]["rejected"], 12)
        self.assertTrue(ra["counts"]["all_attempts_at_most_two"])
        self.assertTrue(ra["counts"]["all_rows_one_analysis_three_plane_calls"])

    def test_size_preflight_and_cheap_gate_match_actual_packets(self):
        size = json.loads((ROOT / "experiments/python-game-size-study/results.json").read_text())
        gate = json.loads((ROOT / "experiments/python-game-size-study/gate-results.json").read_text())
        prior = json.loads((ROOT / "experiments/python-game-size-study/prior-check.json").read_text())
        result = size_audit(size, gate, prior, ROOT / "experiments/python-game-codec-study/results.json")
        self.assertTrue(result["paired_row_order_and_source_ids_match"])
        self.assertTrue(result["all_exact_preflight_sizes_match_actual"])
        self.assertTrue(result["all_gate_lower_bounds_le_actual"])
        self.assertTrue(result["all_gate_emitted_sizes_match_actual"])
        self.assertTrue(result["all_selections_match"])
        self.assertTrue(result["all_selected_packet_hashes_match_full_vs_gate"])
        self.assertTrue(result["rgb_equality"]["exact_benchmark_asserts_oracle_rgb_hash_equality"])
        self.assertTrue(result["rgb_equality"]["gate_benchmark_asserts_oracle_rgb_hash_equality"])
        self.assertFalse(result["rgb_equality"]["per_row_rgb_hash_persisted"])
        self.assertTrue(result["prior_packet_check"]["prior_result_hash_matches"])


if __name__ == "__main__":
    unittest.main()
