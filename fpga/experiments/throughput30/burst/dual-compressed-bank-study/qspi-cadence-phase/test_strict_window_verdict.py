import json
import unittest
from pathlib import Path

from strict_window_verdict import verdict


class StrictWindowVerdictTests(unittest.TestCase):
    def test_archived_shifted_phase_run_fails(self):
        path = Path(__file__).parent / "results/phase-833333/analysis.json"
        result = verdict(json.loads(path.read_text()))
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("after deadline" in reason for reason in result["reasons"]))

    def test_deadline_is_inclusive(self):
        analysis = {
            "input_frames": 2, "distinct_input_hashes": 2, "admitted": 2,
            "busy_drops": 0, "presented": 2, "window_end_cycle": 100,
            "presented_within_capture_window": 2,
            "per_frame": [{"id": 0, "present": 99}, {"id": 1, "present": 100}],
        }
        self.assertEqual(verdict(analysis)["status"], "PASS")

    def test_busy_drop_and_duplicate_id_fail(self):
        analysis = {
            "input_frames": 2, "distinct_input_hashes": 2, "admitted": 2,
            "busy_drops": 1, "presented": 2, "window_end_cycle": 100,
            "per_frame": [{"id": 0, "present": 90}, {"id": 0, "present": 100}],
        }
        self.assertEqual(verdict(analysis)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
