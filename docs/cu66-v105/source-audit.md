# V105 source and functional audit

**Status: `PASS_EVIDENCE`.** This offline audit does not compile or simulate RTL and does not run vendor flows.

## Verified contract

- Baseline `afc073e36f813cbcedaec9b21b61cda239453a5b` is checked as an existing ancestor of HEAD.
- V99 q16 profile and V100 historical RTL inventory are pinned to their baseline Git contents.
- Both admission and memory candidates must be reconstructed byte-for-byte from exact edit recipes over the selected V102 memory source.
- The auditor independently applies admission then memory edits and memory then admission edits; both orders must produce identical source bytes and match the emitted integration source.
- Candidate headers/ports, verification adapters, selected V104 geometry/DSP source pins, focused receipts, and all eight required pipeline lanes are checked.
- The required matrix is admission fresh/canonical, memory fresh/canonical, geometry canonical, combined canonical, and locality fresh/canonical at seeds 105401 and 105402. Missing evidence remains PENDING.

## Results

The eight paired lanes total 512 case-profile runs and 576 directed checks. Each same-seed transcript and event stream is compared byte-for-byte; canonical lanes also compare canonical artifacts. This establishes the listed component-level behavioral evidence only.

- `PASS` `baseline_exists_and_is_ancestor`
- `PASS` `v99_profile_frozen`
- `PASS` `historical_v100_source_inventory_unchanged`
- `PASS` `selected_v102_baseline_source_pins`
- `PASS` `retained_v104_source_and_native_evidence`
- `PASS` `admission_recipe_exact_recovery_and_baseline`
- `PASS` `admission_public_header_and_port_ledger_unchanged`
- `PASS` `admission_verification_adapters_exact`
- `PASS` `memory_recipe_exact_recovery_and_baseline`
- `PASS` `memory_public_header_unchanged`
- `PASS` `admission_memory_both_order_composition`
- `PASS` `composition_emitted_source_matches_both_orders`
- `PASS` `v104_geometry_candidate_pins_and_public_header`
- `PASS` `v104_dsp_candidate_pins_and_public_header`
- `PASS` `focused_admission_receipt_and_independent_trace_audit`
- `PASS` `focused_memory_receipt_and_independent_trace_audit`
- `PASS` `lane_admission_fresh_paired_exact_receipt`
- `PASS` `lane_admission_canonical_paired_exact_receipt`
- `PASS` `lane_memory_fresh_paired_exact_receipt`
- `PASS` `lane_memory_canonical_paired_exact_receipt`
- `PASS` `lane_geometry_canonical_paired_exact_receipt`
- `PASS` `lane_combined_canonical_paired_exact_receipt`
- `PASS` `lane_locality_fresh_paired_exact_receipt`
- `PASS` `lane_locality_canonical_paired_exact_receipt`

PASS_EVIDENCE does not mean full formal state-space equivalence, board-service proof, routed timing closure, parent-clock/I/O signoff, hardware 30 fps qualification, or under-10-ms decode qualification. The focused memory probe uses explicitly prepared internal states and does not establish packet-admission protocol reachability. The coordinate trace is a clocked reachable-state check with a bounded oracle, not a complete formal proof. Detailed hashes and receipt metadata are in `experiments/python-gamebub-v105/source-audit.json`.
