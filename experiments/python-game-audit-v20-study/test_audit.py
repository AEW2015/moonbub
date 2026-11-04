import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import audit


class V20AuditTests(unittest.TestCase):
    def test_not_ready_stays_pending_even_with_artifact_present(self):
        with patch.object(audit, "READY_STUDIES", set()):
            result = audit.audit_study("hardware_kit", "hardware/gamebub-v20")
        self.assertEqual(result["status"], "pending")
        self.assertIn("awaiting explicit final readiness signal", result["reason"])

    def test_test_log_parser_accepts_only_clean_passes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            good = root / "good.log"
            good.write_text("Ran 3 tests in 0.01s\n\nOK\n")
            bad = root / "bad.log"
            bad.write_text("Ran 3 tests in 0.01s\nFAILED (failures=1)\n")
            self.assertEqual(audit.test_log(good), {"status": "pass", "passed_count": 3})
            self.assertEqual(audit.test_log(bad)["status"], "invalid")
            self.assertEqual(audit.test_log(root / "missing.log")["status"], "missing")

    def test_source_pin_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "input.py").write_text("changed\n")
            expected = hashlib.sha256(b"original\n").hexdigest()
            with patch.object(audit, "ROOT", root):
                pins, errors = audit.source_pins({"source_sha256": {"input.py": expected}})
        self.assertFalse(pins[0]["matches"])
        self.assertIn("source pin mismatch or missing source: input.py", errors)

    def test_final_audit_json_reports_all_three_verified_studies(self):
        data = json.loads(audit.AUDIT_PATH.read_text())
        self.assertEqual(data["status"], "verified")
        self.assertTrue(data["final_signals_received"])
        self.assertEqual(set(data["results"]), set(audit.STUDIES))
        for result in data["results"].values():
            self.assertEqual(result["status"], "verified")
            self.assertFalse(result["errors"])
            self.assertEqual(result["tests"]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
