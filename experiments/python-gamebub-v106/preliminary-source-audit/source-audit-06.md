# V106 source and functional audit

**Status: `PENDING`.** This offline auditor checks pinned files and retained evidence; it does not run compilers, simulations, or vendor flows.

## Contract

- Baseline `eececf35da97c9b14230d464ecde7576cb7840db` and frozen 720×480 profile with a 49,152-byte cap are checked against Git baseline contents.
- The selected V105 geometry admission/reconstruction sources are pinned and used as this study’s inherited starting point.
- Six exact math recipes and the two-edit inverse storage recipe are reconstructed from baseline source bytes.
- Math plus storage recipes are independently applied in both orders and compared with the emitted LUT-storage source.
- Focused math and storage receipts require strict tool flags, pinned artifacts and independent trace replay sidecars.
- The adaptive native policy records measured −5.303 ns synthesis, −7.130 ns routed worst path, twelve Rice paths at −6.531 ns, closure at −4.034 ns, and prefix/telemetry routing at −4.700 ns (synthesis −3.897 ns). Six full-flow attempts are tracked, including the rejected fifth candidate; seven controls are explicitly deferred. The replacement targets Rice suffix, IDCT operand, ingress replay and scratch-position logic.
- The plan scratch-layout edit has its own exact source recipe, clocked production comparison and independent modular trace audit.
- The context byte-divmod edit has its own exact source recipe, recorded exhaustive valid-position and deterministic full-width edge/random checks, and independent trace audit.
- The Rice cache edit has its own exact recipe, whole-module clocked equivalence receipt and independent checkpoint/algebra audit.
- The prefix/telemetry variant layers the balanced prefix window over the tested Rice cache and applies the telemetry counter recipe. The guarded-suffix-IDCT-cache map then adds suffix specialization, actual IDCT operand prefetch and producer-coordinate cache edits.
- The guarded-suffix focused probe scopes its private comparison to SUFFIX and checks all public/common private signals on every clock; its historical offline checkpoints are sampled, while the C++ oracle checks every edge.
- The producer lookup-cache sources have exact recipes over the frozen LUT siblings and an independently replayed finite transition model. This is model and source evidence only; the selected integrated pipeline lanes must exercise both live cache assertions.
- The IDCT operand-prefetch edit is reconstructed over baseline RTL and its separate integer model vectors are hash-checked. Integrated component lanes establish the clocked production comparison.
- The focused IDCT probe compares public cycles and outputs with a complete per-edge product/state oracle; its sidecar independently recomputes all 4,303 integer output goldens.
- The area-prefetch IDCT also has a separately pinned three-way unit-synthesis comparison at 10 ns; the shared source maps 7,772 slice LUTs, 5,129 registers and 17 DSPs with +2.920 ns estimated unit slack. This is unit synthesis evidence only, not whole-top area fit or routed timing.
- The final scratch predecode edit is a nine-step recipe over the measured PLAN candidate, with exhaustive upper-position and finite edge/random source model evidence, plus a clocked production probe. Its new parent-response capture timing depends on real input delays and remains open.
- The synchronous ingress replay cache is reconstructed from baseline source and checked by a universal modulo-32 model plus actual two-seed whole-pipeline clocked probes. Inactive private `ctx_bits`/`ctx_last` outside `CONTEXT_RUN` remain outside its claim.
- The earlier guarded-suffix-IDCT-cache candidate is excluded from required functional lanes after strict production lint failed on unused `suffix_extracted[63:24]`; its canonical attempt remains UNRUN. The exact failed receipt and lint log are verified and preserved. The replacement uses the private 24-bit suffix projection, area-qualified IDCT, ingress cache, and scratch cache.
- The paired matrix checks six initial and six follow-up/closure variants in fresh and canonical modes at seeds 106401 and 106402.
- Missing evidence remains PENDING. `PASS_EVIDENCE` is an evidence audit result, not a timing or hardware signoff.

## Results

- `PASS` `baseline_exists_and_is_ancestor`
- `PASS` `retained_v106_baseline_audit_and_open_qualification_limits`
- `PASS` `frozen_720x480_profile_and_49152_byte_cap`
- `PASS` `frozen_baseline_rtl_inventory`
- `PASS` `inherited_v105_geometry_selection_sources`
- `PASS` `retained_v105_source_and_native_audits`
- `PASS` `math_recipe_index_frozen`
- `PASS` `six_exact_math_recipes_recover_over_baseline_sources`
- `PASS` `focused_math_receipt_and_independent_trace_audit`
- `PASS` `locality_two_edit_recipe_exact_recovery`
- `PASS` `math_storage_recipes_commute_both_orders`
- `PASS` `emitted_lut_storage_source_matches_both_orders`
- `PASS` `plan_two_edit_recipe_exact_recovery_over_baseline`
- `PASS` `context_two_edit_recipe_exact_recovery_over_baseline`
- `PASS` `rice_eight_edit_recipe_exact_recovery_over_baseline`
- `PASS` `prefix_two_edit_recipe_exact_recovery_over_rice_candidate`
- `PASS` `suffix_three_edit_recipe_exact_recovery_over_prefix_candidate`
- `PASS` `telemetry_three_edit_recipe_exact_recovery_over_baseline`
- `PASS` `producer_cache_cs88_coefficients_v91k.sv_exact_recipe_over_lut_source`
- `PASS` `producer_cache_cs88_pipeline_v91i2b.sv_exact_recipe_over_lut_source`
- `PASS` `producer_cache_model_trace_and_scope`
- `PASS` `idct_recipe_exact_recovery_over_baseline`
- `PASS` `idct_independent_integer_model_and_vector_pins`
- `PASS` `scratch_nine_edit_recipe_exact_recovery_over_plan_candidate`
- `PASS` `scratch_position_predecode_independent_model`
- `PASS` `idct_area_recipe_exact_recovery_over_baseline`
- `PASS` `idct_area_independent_integer_model_and_vector_pins`
- `PASS` `suffix24_two_edit_recipe_exact_recovery_over_suffix`
- `PASS` `suffix24_exact_projection_model_and_open_RTL_obligation`
- `PASS` `ingress_seven_edit_recipe_exact_recovery_over_baseline`
- `PASS` `ingress_full32_modular_invariant_model`
- `PASS` `idct_area_matched_unit_synthesis_evidence_and_limits`
- `PASS` `adaptive_native_campaign_policy_and_deferred_variants`
- `PASS` `adaptive_campaign_rejected_functional_receipt_pin`
- `PASS` `adaptive_redirection_evidence`
- `PASS` `adaptive_redirection_route_evidence`
- `PASS` `adaptive_redirection_closure_route_evidence`
- `PASS` `adaptive_redirection_prefix_telemetry_route_evidence`
- `PASS` `adaptive_redirection_prefix_telemetry_synth_evidence`
- `PASS` `adaptive_campaign_rejected_pipeline_receipt`
- `PASS` `adaptive_campaign_rejected_pipeline_log`
- `PASS` `adaptive_campaign_area_preflight_comparison`
- `PASS` `focused_plan_receipt_and_independent_trace_audit`
- `PASS` `focused_context_receipt_and_independent_trace_audit`
- `PASS` `focused_rice_receipt_and_independent_evidence_audit`
- `PASS` `prefix_pretool_resource_gate_denial_retained_without_execution`
- `PASS` `focused_prefix_receipt_and_independent_evidence_audit`
- `PASS` `focused_suffix_receipt_and_independent_trace_audit`
- `PASS` `focused_idct_receipt_and_independent_trace_audit`
- `PASS` `focused_idct_area_receipt_and_independent_trace_audit`
- `PASS` `focused_scratch_receipt_and_independent_trace_audit`
- `PASS` `focused_ingress_receipt_and_independent_trace_audit`
- `PASS` `focused_telemetry_receipt_and_independent_trace_audit`
- `PASS` `focused_locality_receipt_and_independent_trace_audit`
- `PASS` `lane_narrow_fresh_paired_exact_receipt`
- `PASS` `lane_narrow_canonical_paired_exact_receipt`
- `PASS` `lane_lut_fresh_paired_exact_receipt`
- `PASS` `lane_lut_canonical_paired_exact_receipt`
- `PASS` `lane_storage_fresh_paired_exact_receipt`
- `PASS` `lane_storage_canonical_paired_exact_receipt`
- `PASS` `lane_lut-storage_fresh_paired_exact_receipt`
- `PASS` `lane_lut-storage_canonical_paired_exact_receipt`
- `PASS` `lane_lut-storage-memory_fresh_paired_exact_receipt`
- `PASS` `lane_lut-storage-memory_canonical_paired_exact_receipt`
- `PASS` `lane_memory_fresh_paired_exact_receipt`
- `PASS` `lane_memory_canonical_paired_exact_receipt`
- `PASS` `lane_lut-plan_fresh_paired_exact_receipt`
- `PASS` `lane_lut-plan_canonical_paired_exact_receipt`
- `PASS` `lane_lut-storage-plan_fresh_paired_exact_receipt`
- `PASS` `lane_lut-storage-plan_canonical_paired_exact_receipt`
- `PASS` `lane_lut-storage-plan-context_fresh_paired_exact_receipt`
- `PASS` `lane_lut-storage-plan-context_canonical_paired_exact_receipt`
- `PASS` `lane_closure_fresh_paired_exact_receipt`
- `PASS` `lane_closure_canonical_paired_exact_receipt`
- `PASS` `lane_closure-prefix-telemetry_fresh_paired_exact_receipt`
- `PASS` `lane_closure-prefix-telemetry_canonical_paired_exact_receipt`
- `PASS` `lane_local-guards-scratch-area_fresh_paired_exact_receipt`
- `PENDING` `lane_local-guards-scratch-area_canonical_paired_exact_receipt`
- `PASS` `rejected_pipeline_fifth_fresh_strict_lint_failure_retained`
- `PASS` `pipeline_import_preflight_failure_preserved`

## Pending evidence

- lane_local-guards-scratch-area_canonical_paired_exact_receipt

The focused math lane exhaustively checks the listed combinational input space. The context arithmetic lane covers all recorded valid positions, every byte lookup constant, and deterministic full-width edge/random inputs; it does not exhaust all 2^32 positions. The focused storage probe compares actual clocked behavior, prepared internal states, and retained historical boundary/interface tests; prepared states do not establish complete packet reachability. The Rice offline auditor replays complete prepared-phase checkpoints and sampled historical-phase checkpoints; the focused C++ run separately compares all public and private oracle fields each clock. The prefix-window suite exercises every rank/window pattern and crafted available-window edges, plus retained historical traffic. The telemetry offline audit replays every prepared edge and sampled historical checkpoints; the C++ comparator checks the full model each historical edge. This evidence does not establish full formal state-space equivalence, routed timing closure, parent-clock or I/O signoff, hardware 30 fps, board service, or under-10-ms decode qualification. See `experiments/python-gamebub-v106/source-audit.json` for paths, hashes and receipt details.
