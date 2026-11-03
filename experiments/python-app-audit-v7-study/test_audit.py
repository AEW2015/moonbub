import unittest
from audit import (audit_roi_result, causality_audit, packet_rate, pooled_mse,
                   source_sequence_guard)


class AppAuditTests(unittest.TestCase):
    def test_rate_counts_real_packet_lengths_and_map_overhead_at_30fps(self):
        got = packet_rate([{"packet_bytes": 100, "roi_map_bytes": 4},
                           {"packet_bytes": 200, "roi_map_bytes": 8}])
        self.assertEqual(got["packet_bytes_total"], 300)
        self.assertEqual(got["roi_map_bytes_total"], 12)
        self.assertEqual(got["wire_kbit_s_at_fps"], 37.44)

    def test_rate_rejects_missing_or_invalid_length(self):
        with self.assertRaises(ValueError):
            packet_rate([{"packet_bytes": 5}, {"packet_bytes": -1}])

    def test_pooled_mse_weights_by_pixel_area(self):
        got = pooled_mse([
            {"roi_squared_error_sum": 100, "roi_pixels": 10,
             "background_squared_error_sum": 0, "background_pixels": 90},
            {"roi_squared_error_sum": 0, "roi_pixels": 90,
             "background_squared_error_sum": 100, "background_pixels": 10},
        ])
        self.assertEqual(got["roi"]["mse"], 1)
        self.assertEqual(got["background"]["mse"], 1)

    def test_source_guard_requires_source_and_per_frame_identity(self):
        a = {"source_id": "clipA", "source_sha256": "abc", "selected_ids": [1, 2],
             "selected_frame_sha256": ["x", "y"]}
        b = dict(a, selected_frame_sha256=["x", "z"])
        self.assertFalse(source_sequence_guard(a, b)["comparable"])
        self.assertIn("selected_frame_sha256", source_sequence_guard(a, b)["mismatched_fields"])

    def test_causality_needs_explicit_clean_declaration_and_flags_oracle(self):
        missing = causality_audit({})
        self.assertFalse(missing["clean_declared_metadata"])
        self.assertEqual(len(missing["missing_required_fields"]), 3)
        clean = causality_audit({"oracle_used": False, "future_frames_used": False,
                                 "lookahead_frames": 0})
        self.assertTrue(clean["clean_declared_metadata"])
        flagged = causality_audit({"oracle_used": True, "future_frames_used": False,
                                   "lookahead_frames": 0})
        self.assertTrue(flagged["suspicious_fields"])
        self.assertFalse(flagged["clean_declared_metadata"])


    def test_roi_audit_checks_map_geometry_area_pooling_and_missing_causality(self):
        area = 720 * 480
        bg_mse = (2 * area - 256) / (area - 256)
        profile = {"bytes": 500, "info": {"width": 720, "height": 480,
                    "scale_map_bytes": 338, "outer_header_crc_bytes": 34},
                   "metrics": {"active": {"mse": 2, "pixels": area},
                               "roi": {"mse": 1, "pixels": 256},
                               "background": {"mse": bg_mse, "pixels": area-256}}}
        data = {"syntax": {"map_bytes_720x480": 338, "outer_header_crc_bytes": 34},
                "scenes": [{"name": "s", "source_index": 0, "input_sha256": "f",
                    "declared_rectangles": [[0, 0, 16, 16]], "manifest": {
                      "source": "clip", "source_sha256": "src", "frame_sha256": ["f"],
                      "selected_pts": [0], "target_width": 720, "target_height": 480,
                      "active_rects": [[0, 0, 720, 480]]},
                    "profiles": {"uniform16": profile,
                                 "budget_roi8mix": dict(profile, bytes=490)}}]}
        got = audit_roi_result(data)
        self.assertTrue(got["all_packet_maps_and_areas_reconcile"])
        self.assertEqual(got["packet_rates"]["uniform16"]["wire_kbit_s_at_30fps"], 120.0)
        self.assertFalse(got["causality_proven_by_manifest"])
        self.assertEqual(got["profile_cap_counts"]["budget_roi8mix"]["over_48k"], 0)


if __name__ == "__main__":
    unittest.main()
