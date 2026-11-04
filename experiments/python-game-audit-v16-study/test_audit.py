import unittest
import audit
class V16AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=audit.load_audit()

    def test_final_golden_pack_replays_and_pins_all_objects(self):
        data=self.data; golden=data["results"]["golden_vectors"]
        self.assertEqual(golden["status"],"verified")
        analysis=golden["analysis"]
        self.assertEqual((analysis["schema"],analysis["epoch"],analysis["source_pin_count"]),("gamebub-ar02-golden-v1",16,26))
        self.assertEqual((analysis["positive_frames"],analysis["gf02_datagrams"],analysis["negative_vectors"]),(10,12,10))
        self.assertEqual(analysis["selected_ui_words"],768)
        self.assertEqual(analysis["negative_targets"],{"receiver":8,"feedback":2})
        self.assertTrue(analysis["negative_atomicity_expected"])
        self.assertEqual((analysis["unique_object_count"],analysis["object_store_bytes"]),(84,89759))
        self.assertEqual(analysis["replay"]["status"],"pass")
        self.assertTrue(all(p["matches"] for p in golden["source_pins"]))
        self.assertEqual(golden["test_log"]["passed_count"],7)
        self.assertEqual(data["status"],"verified")

    def test_decoder_budget_is_conditional_and_does_not_prove_hardware(self):
        data=self.data; budget=data["results"]["decoder_budget"]
        self.assertEqual(budget["status"],"verified")
        result=budget["analysis"]
        self.assertEqual((result["trace_count"],result["actual_packet_traces"],result["analytical_traces"]),(19,18,1))
        self.assertEqual((result["estimate_count"],result["clock_sweep_points"],result["source_pin_count"]),(57,52,23))
        self.assertEqual(result["capacity_total"],5_042_080)
        self.assertTrue(result["all_line_deadlines_unproven"])
        self.assertTrue(result["assumptions_explicit"])
        self.assertEqual(result["verification_replay"]["status"],"pass")
        self.assertTrue(result["input_media"]["matches"])

    def test_refresh_full_ui_strict_steady_and_reference_evidence(self):
        data=self.data; refresh=data["results"]["refresh_v16"]
        self.assertEqual(refresh["status"],"verified")
        result=refresh["analysis"]
        self.assertEqual((result["case_count"],result["input_frame_count"],result["source_pin_count"]),(6,180,31))
        self.assertTrue(result["input_media"]["matches"])
        self.assertTrue(result["all_cases_same_manifest"])
        self.assertTrue(result["all_ui_21120_exact"])
        self.assertTrue(result["all_model_runs_drained"])
        self.assertEqual(result["verification_replay"]["status"],"pass")
        self.assertEqual(result["analysis_binding"]["status"],"verified")
        self.assertEqual(result["matched_refresh_keys"]["matched_key_ids"],[31,62,93,124,155])
        self.assertEqual(result["matched_refresh_keys"]["regular_key_bytes"],152754)
        self.assertEqual(result["matched_refresh_keys"]["coarse_key_bytes"],128210)
        rates={x["profile"]:(x["strict"],x["eventual"],x["modeled_steady_ids_per_second"]) for x in result["strict_vs_steady"]}
        self.assertEqual(rates,{"gm_initial_only":(174,177,29.8),"gm_refresh30":(158,160,26.6),"gm_refresh30_repeat":(160,162,26.8),"gm_refresh30_coarse":(161,163,27.0),"gm_refresh60_coarse":(168,171,28.8),"gm_refresh90_coarse":(172,174,29.2)})
        self.assertEqual(data["status"],"verified")

    def test_inline_tag_proves_canonical_order_not_decoder_fusion(self):
        data=self.data; inline=data["results"]["inline_tag"]
        self.assertEqual(inline["status"],"verified")
        result=inline["analysis"]
        self.assertEqual((result["case_count"],result["full720x480_cases"],result["source_pin_count"]),(20,8,33))
        self.assertEqual(result["cohort_counts"],{"retained synthetic golden decode":10,"retained native-derived actual AR02 decode; three related source IDs per mode":6,"deterministic synthetic canonical YUV, not encoded gameplay":4})
        self.assertTrue(result["all_canonical_tags_match"])
        self.assertEqual((result["full_resolution_stripe_storage_bytes"],result["canonical_full_frame_sha_bytes"],result["conditional_packed8_publication_reread_bytes"]),(11520,1036804,518400))
        self.assertFalse(result["decoder_fusion_proven"])
        self.assertTrue(result["conditional_budget_only"])
        self.assertEqual(result["verification_replay"]["status"],"pass")
        self.assertEqual(data["status"],"verified")

    def test_gateway_firmware_facts_and_packet_bounds_are_verified(self):
        data=self.data; gateway=data["results"]["esp32_gateway"]
        self.assertEqual(gateway["status"],"verified")
        result=gateway["analysis"]
        self.assertEqual((result["principal_case_count"],result["workload_count"],result["link_burst_cases"],result["source_pin_count"]),(32,4,20,13))
        self.assertEqual(result["workload_frame_counts"],{"gm_initial_only":177,"gm_refresh30":160,"gm_refresh30_coarse":163,"cap_stress_60":60})
        self.assertTrue(result["source_facts_match"])
        self.assertFalse(result["source_facts"]["external_psram_enabled"])
        self.assertFalse(result["source_facts"]["ar02_gf02_implemented"])
        self.assertTrue(result["bounded_mailbox_and_dma"])
        self.assertTrue(result["unmodeled_idle_timeout_explicit"])
        self.assertTrue(result["protocol_and_hardware_claims_false"])
        self.assertEqual(result["corrected_lock_failure_paths"]["status"],"verified")
        self.assertEqual(result["corrected_lock_failure_paths"]["fresh_begin"]["abort_calls"],0)
        self.assertEqual(result["corrected_lock_failure_paths"]["midframe_forward_failure"]["abort100_mailbox_drops"],42)
        self.assertEqual(result["key_scenario_summaries"]["nominal_initial"][:3],(176,177,177))
        self.assertEqual(result["key_scenario_summaries"]["burst8"],(0,0,460))
        self.assertEqual(result["key_scenario_summaries"]["cap_stress"][:4],(38,60,60,12.57984))
        self.assertEqual([x[2] for x in result["ram_scenarios"]],[-13401,52135,117671])
        self.assertEqual(result["verification_replay"]["status"],"pass")
        self.assertEqual(data["status"],"verified")

    def test_missing_inputs_remain_pending(self):
        data=self.data; self.assertEqual(data["audit_version"],16); self.assertEqual(data["target"],audit.TARGET)
        self.assertEqual(data["status"],"verified")
        self.assertTrue(all(data["inputs"][key]["status"]=="verified" for key in audit.STUDIES))
        pending=audit.audit_study("not_finalized","experiments/does-not-exist")
        self.assertEqual(pending["status"],"pending")
        self.assertIn("awaiting final evidence signal",pending["errors"])
    def test_claim_guards_do_not_promote_model_to_hardware(self):
        data=self.data; self.assertFalse(data["claims_guard"]["cyclemodel_proves_hardware"])
        self.assertFalse(data["claims_guard"]["esp32_gateway_model_is_firmware_emulation"])
        self.assertFalse(data["claims_guard"]["gateway_protocol_is_currently_supported"])
        self.assertFalse(data["claims_guard"]["finite_model_proves_live_30fps"]); self.assertFalse(data["claims_guard"]["missing_artifacts_mean_success"])

    def test_completed_source_pins_are_portable_and_match(self):
        data=audit.load_audit()
        for key in ("golden_vectors","decoder_budget","refresh_v16","inline_tag"):
            result=data["results"][key]
            self.assertTrue(result["source_pins"],key)
            self.assertTrue(all(not p["path"].startswith("/") and p["matches"] for p in result["source_pins"]),key)
if __name__=="__main__": unittest.main()
