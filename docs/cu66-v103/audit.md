# V103 source and functional evidence audit

**Status: PASS_EVIDENCE.**

This deterministic audit binds source and receipt inputs by SHA-256. It checks the frozen V99 profile and V100 historical source inventory, V102 source baselines, V103 function-only edits and headers, focused function traces, and paired component regressions. It performs no simulation or vendor flow.

## Audit result

| Area | Status |
|---|---|
| baseline_exists_and_is_ancestor | PASS |
| v99_profile_pinned | PASS |
| v100_historical_source_inventory_unchanged | PASS |
| v102_candidate_baselines_unchanged | PASS |
| reconstruct_source_and_manifest_pins | PASS |
| reconstruct_approved_function_only_edit | PASS |
| reconstruct_production_header_unchanged | PASS |
| reconstruct_port_ledger_present | PASS |
| admission_source_and_manifest_pins | PASS |
| admission_approved_function_only_edit | PASS |
| admission_production_header_unchanged | PASS |
| admission_port_ledger_present | PASS |
| focused_reconstruct_receipt_and_artifact_pins | PASS |
| focused_admission_receipt_and_artifact_pins | PASS |
| paired_lane_admission_fresh_receipt | PASS |
| paired_lane_admission_canonical_receipt | PASS |
| paired_lane_reconstruct_canonical_receipt | PASS |
| paired_lane_combined_canonical_receipt | PASS |
| retained_stopped_attempt_is_resource_gate_not_rtl_failure | PASS |

## Paired regression lanes

| Candidate | Mode | Case/profile runs | Directed checks | Result |
|---|---|---:|---:|---|
| Admission | fresh | 24 | 52 | PASS |
| Admission | canonical | 88 | 84 | PASS |
| Reconstruction | canonical | 88 | 84 | PASS |
| Combined | canonical | 88 | 84 | PASS |
| **Total** |  | **288** | **304** |  |

Bound input files: **451**.

The JSON audit contains the detailed check results and exact SHA-256 pins. A `PASS_EVIDENCE` result qualifies only the audited source and component evidence; it does not claim native implementation timing closure, board integration, or hardware frame rate.
