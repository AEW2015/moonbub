import unittest

import audit


class V18AuditScaffoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = audit.load_audit()

    def test_all_studies_have_final_signals_and_pass(self):
        self.assertEqual(set(self.data["results"]), {"candidate_commit", "ar03_trace", "joint_admission"})
        self.assertEqual(self.data["status"], "verified")
        self.assertTrue(self.data["final_signals_received"])
        self.assertEqual(self.data["results"]["candidate_commit"]["status"], "verified")
        self.assertEqual(self.data["results"]["ar03_trace"]["status"], "verified")
        self.assertEqual(self.data["results"]["joint_admission"]["status"], "verified")

    def test_candidate_commit_semantics_and_measured_python_work(self):
        a = self.data["results"]["candidate_commit"]["analysis"]
        self.assertEqual((a["native_candidates"], a["commits"], a["discards"], a["cap_rejections"]), (48, 42, 6, 4))
        self.assertTrue(a["all_commits_match_frozen_wire_and_decode"])
        self.assertEqual(a["selected_ui_words"], 887040)
        self.assertTrue(a["discard_state_unchanged_and_leases_released"])
        self.assertTrue(a["paid_cap_rejections_state_unchanged_and_leases_released"])
        self.assertIn("not target CPU cycles", a["measured_python_work"]["scope"])

    def test_trace_actual_packets_objects_and_hash_bound_demand(self):
        a = self.data["results"]["ar03_trace"]["analysis"]
        self.assertEqual(a["status"], "verified", a["errors"])
        self.assertEqual(a["counts"]["frames"], 16)
        self.assertEqual(a["unique_native_acquisitions_are_not_independent_frames"], 6)
        self.assertTrue(a["every_row_retains_packet_feedback_decode_and_reference_objects"])
        self.assertEqual(a["native_rows_with_exact_ui_pixel_count"], 12)
        self.assertTrue(a["all_objects_valid"])
        self.assertEqual(a["atomic_negative_rejections"], 53)
        self.assertEqual(a["stripe_demand"]["plane_traces"], 48)
        self.assertAlmostEqual(a["stripe_demand"]["max_peak_to_uniform_ratio"], 9.050381679389313)
        self.assertFalse(a["physical_memory_or_30fps_claim"])

    def test_joint_admission_wire_credit_publication_and_scope(self):
        result = self.data["results"]["joint_admission"]
        a = result["analysis"]
        self.assertEqual(result["status"], "verified", result["errors"])
        self.assertEqual((a["case_count"], a["capture_count"], a["source_pin_count"]), (8, 636, 49))
        profiles = {x["profile"]: x for x in a["per_case"]}
        self.assertEqual((profiles["admit200"]["committed"], profiles["admit200"]["precommit_rejected"]), (83, 0))
        self.assertEqual((profiles["admit150_batch8"]["committed"], profiles["admit150_batch8"]["precommit_rejected"]), (70, 15))
        self.assertEqual((profiles["admit200_link4"]["committed"], profiles["admit200_link4"]["precommit_rejected"]), (58, 21))
        self.assertTrue(all(x["bounded_and_drained"] and x["credits_distinct_from_decoded_publication"] for x in profiles.values()))
        self.assertTrue(all(x["wrapped_wire_lengths_valid"] for x in profiles.values()))
        self.assertEqual(profiles["lost_credit_query"]["control_datagrams"], 1)
        self.assertTrue(a["supplemental_analysis_hash_bound"])
        self.assertTrue(a["busy_ingress_diagnosis_valid_with_limits"])
        self.assertEqual(a["busy_ingress_diagnosis"]["unbudgeted"]["busy_feed_operations"], 144)
        self.assertIn("not proven", a["busy_ingress_diagnosis"]["unbudgeted"]["scope"])
        self.assertEqual(a["verifier_replay"]["status"], "pass")
        self.assertEqual(a["analysis_replay"]["status"], "pass")
        self.assertTrue(a["python_reference_not_ESP_CPU_or_physical_FPS"])

    def test_target_and_portable_source_pin_resolution(self):
        self.assertEqual(audit.TARGET, {"canvas": [720, 480], "active_image": [720, 405], "fps": 30})
        self.assertEqual(audit.resolve_pin("/old/tree/moonbub-30fps-study/experiments/example.py"), audit.ROOT / "experiments/example.py")
        self.assertEqual(audit.resolve_pin("experiments/example.py"), audit.ROOT / "experiments/example.py")

    def test_missing_or_incomplete_test_logs_do_not_pass(self):
        self.assertEqual(audit.test_log(audit.HERE / "absent-tests.log"), {"status": "missing", "passed_count": None})
        bad = audit.HERE / "bad-tests-fixture.log"
        try:
            bad.write_text("Ran 2 tests\nFAILED (failures=1)\n")
            self.assertEqual(audit.test_log(bad)["status"], "invalid")
        finally:
            bad.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
