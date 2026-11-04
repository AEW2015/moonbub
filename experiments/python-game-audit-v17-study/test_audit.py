import unittest

import audit


class V17AuditScaffoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = audit.load_audit()

    def test_three_inputs_verified_after_final_signals(self):
        data = self.data
        self.assertEqual(set(data["results"]), {"paced_gateway", "streaming_memory", "local_refresh"})
        self.assertEqual(data["status"], "verified")
        self.assertTrue(data["final_signal_received"])
        self.assertEqual(data["results"]["paced_gateway"]["status"], "verified")
        self.assertEqual(data["results"]["local_refresh"]["status"], "verified")
        self.assertEqual(data["results"]["streaming_memory"]["status"], "verified")
        self.assertTrue(data["final_signal_received"])
        self.assertEqual(data["status"], "verified")

    def test_paced_gateway_bounds_and_failure_accounting(self):
        result = self.data["results"]["paced_gateway"]
        analysis = result["analysis"]
        self.assertEqual(result["status"], "verified", result["errors"])
        self.assertEqual((analysis["case_count"], analysis["source_pin_count"]), (36, 14))
        self.assertTrue(analysis["bounded_mailbox_zero_overflow"])
        self.assertEqual((analysis["nominal_paced"]["strict"], analysis["nominal_paced"]["eventual"]), (175, 176))
        self.assertEqual(analysis["aggregate8"]["drops"]["latest_replaced"], 35)
        self.assertTrue(analysis["blackhole_retains_six_credits"])
        self.assertEqual(analysis["deterministic_replay"]["status"], "pass")

    def test_local_refresh_quality_cadence_and_protocol_scope(self):
        result = self.data["results"]["local_refresh"]
        analysis = result["analysis"]
        self.assertEqual(result["status"], "verified", result["errors"])
        self.assertEqual((analysis["case_count"], analysis["capture_count"], analysis["source_pin_count"]), (6, 848, 37))
        self.assertTrue(analysis["all_native_ui_words_exact"])
        self.assertEqual((analysis["global"]["strict"], analysis["local"]["strict"], analysis["local"]["eventual"]), (159, 176, 178))
        self.assertEqual(analysis["local"]["distinct_input_and_decoded_window_ids"], 151)
        self.assertEqual(len(analysis["local_bank1_continuity"]), 5)
        self.assertEqual(analysis["analysis_replay"]["status"], "pass")
        self.assertIn("MSV1 JPEG-only", analysis["firmware_protocol_scope"])

    def test_streaming_memory_service_and_epoch_boundaries(self):
        result = self.data["results"]["streaming_memory"]
        analysis = result["analysis"]
        self.assertEqual(result["status"], "verified", result["errors"])
        self.assertEqual((analysis["case_count"], analysis["phase_case_count"], analysis["source_pin_count"]), (8, 4, 28))
        self.assertEqual(analysis["fast_streaming_epoch_boundaries"], {
            "strict_start_count": 29, "strict_clean_finish_count": 29,
            "eventual_clean_count": 30, "start_ids_equal_clean_finish_ids": True,
        })
        self.assertEqual(analysis["main_scenario_summaries"]["fast_streaming_stall_4lines"]["display_line_misses"], 3689)
        self.assertEqual(analysis["main_scenario_summaries"]["fast_streaming_stall_8lines"]["clean_steady_ids_per_second"], 30.0)
        self.assertEqual(analysis["boundary_analysis_replay"]["status"], "pass")

    def test_target_and_portable_source_pin_resolution(self):
        self.assertEqual(audit.TARGET, {"canvas": [720, 480], "active_image": [720, 405], "fps": 30})
        self.assertEqual(
            audit.resolve_pin("/old/tree/moonbub-30fps-study/experiments/example.py"),
            audit.ROOT / "experiments/example.py",
        )
        self.assertEqual(audit.resolve_pin("experiments/example.py"), audit.ROOT / "experiments/example.py")

    def test_incomplete_test_logs_are_not_passes(self):
        self.assertEqual(audit.test_log(audit.HERE / "absent-tests.log"), {"status": "missing", "passed_count": None})


if __name__ == "__main__":
    unittest.main()
