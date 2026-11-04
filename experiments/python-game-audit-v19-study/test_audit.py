import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import audit


class V19AuditScaffoldTests(unittest.TestCase):
    def test_scope_and_portable_pin_resolution(self):
        self.assertEqual(audit.TARGET, {"canvas": [720, 480], "active_image": [720, 405], "fps": 30})
        self.assertEqual(audit.resolve_pin("/old/moonbub-30fps-study/experiments/a.py"), audit.ROOT / "experiments/a.py")
        self.assertEqual(audit.resolve_pin("experiments/a.py"), audit.ROOT / "experiments/a.py")

    def test_not_ready_remains_pending_even_if_artifacts_exist(self):
        with patch.object(audit, "READY_STUDIES", set()):
            result = audit.audit_study("frame_grant", "experiments/not-yet-final")
        self.assertEqual(result["status"], "pending")
        self.assertIn("awaiting explicit final evidence signal", result["errors"])

    def test_final_signal_with_missing_study_data_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(audit, "ROOT", Path(tmp)), patch.object(audit, "READY_STUDIES", {"frame_grant"}):
                result = audit.audit_study("frame_grant", "study")
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("missing" in error for error in result["errors"]))

    def test_changed_source_hash_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = root / "study"
            study.mkdir()
            source = root / "source.py"
            source.write_text("changed content\n")
            expected = hashlib.sha256(b"original content\n").hexdigest()
            (study / "results.json").write_text(json.dumps({"source_sha256": {str(source): expected}}))
            (study / "README.md").write_text("study\n")
            (study / "tests.log").write_text("Ran 1 test\nOK\n")
            (study / "run.log").write_text("retained run\n")
            (study / "verify.log").write_text("PASS\n")
            with patch.object(audit, "ROOT", root), patch.object(audit, "READY_STUDIES", {"frame_grant"}):
                result = audit.audit_study("frame_grant", "study")
        self.assertEqual(result["status"], "invalid")
        self.assertFalse(result["source_pins"][0]["matches"])

    def test_missing_or_failed_test_log_does_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            absent = audit.test_log(Path(tmp) / "absent.log")
            bad_path = Path(tmp) / "bad.log"
            bad_path.write_text("Ran 2 tests\nFAILED (failures=1)\n")
            bad = audit.test_log(bad_path)
        self.assertEqual(absent, {"status": "missing", "passed_count": None})
        self.assertEqual(bad["status"], "invalid")

    def test_both_final_studies_pass_and_hud_omissions_remain_an_unmet_gate(self):
        data = audit.load_audit()
        self.assertEqual(data["status"], "verified")
        self.assertTrue(data["final_signals_received"])
        self.assertEqual(data["results"]["frame_grant"]["status"], "verified")
        stripe = data["results"]["causal_stripe"]
        self.assertEqual(stripe["status"], "verified", stripe["errors"])
        analysis = stripe["analysis"]
        self.assertEqual(analysis["coefficient_blocks"], 97308)
        self.assertEqual(analysis["exact_residual_samples"], 6227712)
        self.assertEqual(analysis["exact_reconstructed_samples"], 6224472)
        self.assertEqual(analysis["selected_ui_words"], 253440)
        self.assertTrue(analysis["actual_coefficient_demand_conserved"])
        self.assertTrue(analysis["conditional_resource_accounting_valid"])
        self.assertTrue(analysis["supplemental_analysis_hash_bound"])
        self.assertTrue(analysis["analysis_replay"]["status"] == "pass")
        self.assertTrue(analysis["verifier_replay"]["status"] == "pass")
        frame = data["results"]["frame_grant"]["analysis"]
        self.assertEqual((frame["case_count"], frame["capture_events"], frame["source_pin_count"]), (12, 790, 58))
        self.assertEqual(frame["native_busy_feed_rejections"], 0)
        self.assertEqual(frame["native_selected_word_mismatches"], 0)
        self.assertTrue(frame["analysis_hash_bound"])
        self.assertEqual(frame["analysis_replay"]["status"], "pass")
        coverage = frame["ui_coverage"]
        self.assertTrue(coverage["selected_words_exact"])
        self.assertEqual(coverage["full_hud_gate"], "unmet")
        self.assertEqual(coverage["partial_decoded_frames"], 44)
        self.assertEqual(coverage["omitted_requested_words"], 253440)
        self.assertIn("not counted as protected", coverage["interpretation"])


if __name__ == "__main__":
    unittest.main()
