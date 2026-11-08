import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import summarize

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixtures" / "v48-network-result-validated.json"
DOC = json.loads(FIXTURE.read_text(encoding="utf-8"))
INPUT_SHA = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()

class SummaryTests(unittest.TestCase):
    def test_real_v48_receipt_derives_tail_intervals_same_session(self):
        result = summarize.summarize_doc(copy.deepcopy(DOC), FIXTURE, INPUT_SHA)
        self.assertEqual(result["identity"]["execution_scope"], "physical")
        self.assertFalse(result["cross_session_join"])
        self.assertEqual([f["ordinal"] for f in result["frames"]], [9, 10, 11])
        rows = {f["ordinal"]: {x["name"]: x for x in f["intervals"]} for f in result["frames"]}
        self.assertEqual(rows[9]["native_wall_us"]["value"], 212382)
        self.assertEqual(rows[10]["native_wall_us"]["value"], 196723)
        self.assertEqual(rows[11]["native_wall_us"]["value"], 124060)
        self.assertEqual(rows[9]["hu_extract_wall_us"]["value"], 501053)
        self.assertIn("not CPU-exclusive", result["timing_semantics"]["native_wall"])
        self.assertIn("No per-stage QSPI", result["timing_semantics"]["qspi"])

    def test_missing_timestamp_is_unknown(self):
        doc = copy.deepcopy(DOC)
        doc["raw_rows"]["8"] = "native ordinal=9 start=288654165 cpu_us=212382"
        result = summarize.summarize_doc(doc, FIXTURE, INPUT_SHA)
        native = result["frames"][0]["intervals"][3]
        self.assertEqual(native["status"], "unknown")
        self.assertEqual(native["reason"], "missing_invalid_or_negative_timestamp")

    def test_missing_native_stage_is_unknown(self):
        doc = copy.deepcopy(DOC)
        doc["raw_rows"]["8"] = "unrecognized native details"
        result = summarize.summarize_doc(doc, FIXTURE, INPUT_SHA)
        native = result["frames"][0]["intervals"][3]
        self.assertEqual(native["status"], "unknown")
        self.assertEqual(native["reason"], "missing_stage")

    def test_missing_hu_and_frame_stages_are_unknown_without_exception(self):
        doc = copy.deepcopy(DOC)
        doc["raw_rows"]["4"] = "unrecognized frame details"
        doc["raw_rows"]["7"] = "unrecognized extraction details"
        result = summarize.summarize_doc(doc, FIXTURE, INPUT_SHA)
        row = result["frames"][0]
        self.assertIsNone(row["frame_id"])
        intervals = {item["name"]: item for item in row["intervals"]}
        self.assertEqual(intervals["hu_extract_wall_us"]["status"], "unknown")
        self.assertEqual(row["hu_scalar_commands"], None)

    def test_truncated_export_rejected(self):
        doc = copy.deepcopy(DOC)
        del doc["raw_rows"]["42"]
        with self.assertRaisesRegex(summarize.InputError, "truncated_or_noncontiguous|raw_rows_do_not_match"):
            summarize.summarize_doc(doc, FIXTURE, INPUT_SHA)

    def test_negative_interval_is_unknown(self):
        doc = copy.deepcopy(DOC)
        doc["raw_rows"]["8"] = "native ordinal=9 start=288654165 done=288654164 cpu_us=1"
        result = summarize.summarize_doc(doc, FIXTURE, INPUT_SHA)
        native = result["frames"][0]["intervals"][3]
        self.assertEqual(native["status"], "unknown")
        self.assertEqual(native["reason"], "negative_interval")

    def test_duplicate_ordinal_stage_rejected(self):
        doc = copy.deepcopy(DOC)
        doc["raw_rows"]["42"] = "native ordinal=11 start=1 done=2 cpu_us=1"
        with self.assertRaisesRegex(summarize.InputError, "duplicate_ordinal_stage:11:native"):
            summarize.summarize_doc(doc, FIXTURE, INPUT_SHA)

    def test_model_tag_never_labeled_physical(self):
        doc = copy.deepcopy(DOC)
        doc["evidence_kind"] = "model"
        result = summarize.summarize_doc(doc, FIXTURE, INPUT_SHA)
        self.assertEqual(result["identity"]["execution_scope"], "model")

    def test_unrecognized_evidence_scope_rejected(self):
        doc = copy.deepcopy(DOC)
        doc["evidence_kind"] = "probably_physical"
        with self.assertRaisesRegex(summarize.InputError, "unrecognized_evidence_scope"):
            summarize.summarize_doc(doc, FIXTURE, INPUT_SHA)

    def test_invalid_identity_hash_rejected(self):
        doc = copy.deepcopy(DOC)
        doc["ELF"] = "1234"
        with self.assertRaisesRegex(summarize.InputError, "source_and_session_identity_required"):
            summarize.summarize_doc(doc, FIXTURE, INPUT_SHA)

    def test_missing_validated_export_receipt_rejected(self):
        doc = copy.deepcopy(DOC)
        doc["USB"]["both_independently_validated"] = False
        with self.assertRaisesRegex(summarize.InputError, "validated_physical_receipt_required"):
            summarize.summarize_doc(doc, FIXTURE, INPUT_SHA)

    def test_modified_input_fails_source_hash_binding(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "result.json"
            altered = copy.deepcopy(DOC)
            altered["raw_rows"]["8"] = altered["raw_rows"]["8"].replace("212382", "212383")
            p.write_text(json.dumps(altered), encoding="utf-8")
            with self.assertRaisesRegex(summarize.InputError, "input_sha256_does_not_match"):
                summarize.summarize(p, INPUT_SHA)

if __name__ == "__main__":
    unittest.main()
