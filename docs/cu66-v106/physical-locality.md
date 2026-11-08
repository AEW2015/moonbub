# V106 routed physical locality

This analysis quantifies the actual retained high-fanout, control-set and congestion reports after the final native audit passes. It does not run vendor tools. The machine-readable [evidence ledger](../../experiments/python-gamebub-v106/physical-locality.json) binds the native audit, analyzer, receipts and each retained report hash/byte count.

Only V106 measured routes are compared. Comparable V105 physical-locality reports are absent, so no V105 fanout, control-set or congestion delta is inferred. The high-fanout command requests at most50 nets with timing and load types; its rows are a truncated list rather than a global distribution. Header load types comprise clock-enable, set/reset, data/other and clock loads, each split across Slice, IO and BRAM/DSP/OTHER columns.

| Variant | Retained nets | Largest fanout | Total control sets | Unused register locations in used slices | Nonfinite-slack rows | Congestion report observation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| lut | 50 | 7,275 | 1,140 | 1,114 | 1 | placer_final: none reported above level5; initial_estimated_router: none reported above level5 |
| lut-storage-plan | 50 | 7,277 | 1,203 | 1,089 | 1 | placer_final: none reported above level5; initial_estimated_router: none reported above level5 |
| closure | 50 | 7,270 | 1,207 | 1,121 | 1 | placer_final: none reported above level5; initial_estimated_router: none reported above level5 |
| closure-prefix-telemetry | 50 | 7,135 | 1,209 | 1,149 | 0 | placer_final: none reported above level5; initial_estimated_router: none reported above level5 |
| guarded-suffix-idct-cache | no completed route | — | — | — | — | — |
| local-guards-scratch-area | no completed route | — | — | — | — | — |

## lut

Route WNS is -7.130 ns. The largest retained net is `coefficients/child/scratch/clear`: 7,275 loads, of which 7,256 are reported set/reset loads. The list has 9 nets with fanout≥1,000 and 28 with fanout≥500; these counts refer only to the retained top50. Control sets change by +0 relative to the first measured V106 route (lut); this is a composed implementation comparison, not isolated storage/CSA causality.

| Net (largest ten retained) | Fanout | Driver | Worst reported slack (ns) | Worst reported delay (ns) | CE loads | Set/reset loads | Data/other loads | Clock loads |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `coefficients/child/scratch/clear` | 7,275 | LUT3 | -2.721 | 7.977 | 0 | 7,256 | 19 | 0 |
| `transform/inverse/state[3]_i_1_n_0` | 3,607 | LUT2 | -5.033 | 1.064 | 0 | 3,557 | 50 | 0 |
| `transform/dequant/inverse_launch_INST_0_i_1_n_0` | 2,361 | LUT6 | -4.653 | 1.377 | 0 | 2,351 | 10 | 0 |
| `coefficients/child/scratch/running14_out` | 2,242 | LUT3 | -3.745 | 1.952 | 0 | 2,218 | 24 | 0 |
| `transform/inverse/intermediate[63][23]_i_1_n_0` | 1,536 | LUT6 | -2.854 | 2.116 | 1,536 | 0 | 0 | 0 |
| `transform/inverse/intermediate[63][23]_i_4_n_0` | 1,346 | LUT4 | -3.018 | 8.902 | 0 | 0 | 1,346 | 0 |
| `transform/inverse/state02_out` | 1,316 | LUT5 | -4.653 | 1.783 | 1,313 | 0 | 3 | 0 |
| `transform/dequant/FSM_onehot_math_state_reg[4]` | 1,073 | LUT5 | -1.774 | 3.246 | 1,060 | 0 | 13 | 0 |
| `coefficients/child/scratch/p_41_in` | 1,026 | LUT2 | -5.055 | 4.503 | 0 | 1,019 | 7 | 0 |
| `transform/reset_1` | 901 | LUT3 | -3.889 | 3.773 | 0 | 0 | 901 | 0 |

Across all 50 listed nets, the load-occurrence totals are clock_enable 7,281, set_reset 18,710, data_other 17,807, clock 0. A physical cell can load several nets, so these sums are not unique registers, cells or device-wide loads. Nonfinite-slack rows: `reset` (PORT, fanout664, slack`inf`). In particular an OOC reset/input port with `inf` slack has no finite timing margin reported here; it is not an unconstrained-boundary timing pass.

Congestion observations: * No congestion windows are found above level 5; * No initial estimated congestion windows are found above level 5. This statement is threshold-specific and does not rule out congestion at level5 or below, transient routing congestion, or large net delays.

Pinned reports: [fanout](../../experiments/python-gamebub-v106/native/20261108T005012241750Z/reports/route-high-fanout.rpt) (`bc34ff680e368d98d3aa462a382665138c6076baee892cc9a4a55f9817401a8a`), [control_sets](../../experiments/python-gamebub-v106/native/20261108T005012241750Z/reports/route-control-sets.rpt) (`dac20ec6396ab3523e1d8c6456c37e3194c3723f8f4bb8729bf740c2c9876204`), [congestion](../../experiments/python-gamebub-v106/native/20261108T005012241750Z/reports/route-congestion.rpt) (`e39836a77c3ca0176efc8b29dc3ec1715b9d3c6f31d1c53ddfc806ac2b8e9a94`).

## lut-storage-plan

Route WNS is -6.628 ns. The largest retained net is `coefficients/child/scratch/cancelled`: 7,277 loads, of which 7,256 are reported set/reset loads. The list has 13 nets with fanout≥1,000 and 24 with fanout≥500; these counts refer only to the retained top50. Control sets change by +63 relative to the first measured V106 route (lut); this is a composed implementation comparison, not isolated storage/CSA causality.

| Net (largest ten retained) | Fanout | Driver | Worst reported slack (ns) | Worst reported delay (ns) | CE loads | Set/reset loads | Data/other loads | Clock loads |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `coefficients/child/scratch/cancelled` | 7,277 | LUT3 | -2.833 | 7.071 | 0 | 7,256 | 21 | 0 |
| `transform/inverse/state[3]_i_1_n_0` | 3,606 | LUT2 | -4.078 | 0.976 | 0 | 3,556 | 50 | 0 |
| `transform/dequant/out_dequantized[1279]_i_1_n_0` | 2,351 | LUT2 | -1.280 | 2.648 | 0 | 2,351 | 0 | 0 |
| `coefficients/child/scratch/running14_out` | 2,242 | LUT3 | -2.400 | 1.441 | 0 | 2,218 | 24 | 0 |
| `transform/inverse/intermediate[63][23]_i_1_n_0` | 1,536 | LUT6 | -1.617 | 2.229 | 1,536 | 0 | 0 | 0 |
| `transform/inverse/intermediate[63][23]_i_4_n_0` | 1,346 | LUT4 | -2.279 | 9.841 | 0 | 0 | 1,346 | 0 |
| `transform/inverse/state02_out` | 1,316 | LUT5 | -3.449 | 2.001 | 1,313 | 0 | 3 | 0 |
| `transform/dequant/coefficients[0]` | 1,078 | LUT4 | -1.920 | 2.541 | 1,060 | 0 | 18 | 0 |
| `transform/reset_4` | 1,038 | LUT3 | -2.798 | 4.239 | 0 | 0 | 1,038 | 0 |
| `transform/reset_5` | 1,038 | LUT3 | -1.721 | 3.678 | 0 | 0 | 1,038 | 0 |

Across all 50 listed nets, the load-occurrence totals are clock_enable 7,281, set_reset 18,714, data_other 17,200, clock 0. A physical cell can load several nets, so these sums are not unique registers, cells or device-wide loads. Nonfinite-slack rows: `reset` (PORT, fanout642, slack`inf`). In particular an OOC reset/input port with `inf` slack has no finite timing margin reported here; it is not an unconstrained-boundary timing pass.

Congestion observations: * No congestion windows are found above level 5; * No initial estimated congestion windows are found above level 5. This statement is threshold-specific and does not rule out congestion at level5 or below, transient routing congestion, or large net delays.

Pinned reports: [fanout](../../experiments/python-gamebub-v106/native/20261108T010638248027Z/reports/route-high-fanout.rpt) (`5eb9e72b42a0a69b5ea99c35d0da914badd9bee80975cfc589a482d22a2e88c0`), [control_sets](../../experiments/python-gamebub-v106/native/20261108T010638248027Z/reports/route-control-sets.rpt) (`86d6de8f0f7419df0d8825169bc85861321000cf956a7b2fd50bf8b674ec0752`), [congestion](../../experiments/python-gamebub-v106/native/20261108T010638248027Z/reports/route-congestion.rpt) (`e1522357e347a8f716e4d3022bf4d89c3271d085f88a78e8a09ddbd9d3685b69`).

## closure

Route WNS is -4.034 ns. The largest retained net is `coefficients/child/cancelled`: 7,270 loads, of which 7,256 are reported set/reset loads. The list has 14 nets with fanout≥1,000 and 24 with fanout≥500; these counts refer only to the retained top50. Control sets change by +67 relative to the first measured V106 route (lut); this is a composed implementation comparison, not isolated storage/CSA causality.

| Net (largest ten retained) | Fanout | Driver | Worst reported slack (ns) | Worst reported delay (ns) | CE loads | Set/reset loads | Data/other loads | Clock loads |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `coefficients/child/cancelled` | 7,270 | LUT3 | -2.655 | 1.597 | 0 | 7,256 | 14 | 0 |
| `transform/inverse/state[3]_i_1_n_0` | 3,622 | LUT2 | -3.086 | 2.738 | 0 | 3,557 | 65 | 0 |
| `transform/dequant/out_dequantized[1279]_i_1_n_0` | 2,352 | LUT2 | -0.792 | 3.192 | 0 | 2,352 | 0 | 0 |
| `transform/running14_out` | 2,242 | LUT3 | -2.464 | 3.651 | 0 | 2,218 | 24 | 0 |
| `transform/inverse/intermediate[63][23]_i_1_n_0` | 1,536 | LUT6 | -1.758 | 1.935 | 1,536 | 0 | 0 | 0 |
| `transform/inverse/intermediate[63][23]_i_4_n_0` | 1,346 | LUT4 | -0.157 | 5.419 | 0 | 0 | 1,346 | 0 |
| `transform/inverse/state02_out` | 1,316 | LUT5 | -2.978 | 1.765 | 1,313 | 0 | 3 | 0 |
| `transform/reset_0` | 1,282 | LUT2 | -0.891 | 3.359 | 0 | 1,280 | 2 | 0 |
| `transform/dequant/coefficients[0]` | 1,079 | LUT4 | -0.621 | 2.533 | 1,060 | 0 | 19 | 0 |
| `transform/reset_6` | 1,038 | LUT3 | -2.471 | 3.178 | 0 | 0 | 1,038 | 0 |

Across all 50 listed nets, the load-occurrence totals are clock_enable 7,281, set_reset 18,701, data_other 17,708, clock 0. A physical cell can load several nets, so these sums are not unique registers, cells or device-wide loads. Nonfinite-slack rows: `reset` (PORT, fanout621, slack`inf`). In particular an OOC reset/input port with `inf` slack has no finite timing margin reported here; it is not an unconstrained-boundary timing pass.

Congestion observations: * No congestion windows are found above level 5; * No initial estimated congestion windows are found above level 5. This statement is threshold-specific and does not rule out congestion at level5 or below, transient routing congestion, or large net delays.

Pinned reports: [fanout](../../experiments/python-gamebub-v106/native/20261108T013032873883Z/reports/route-high-fanout.rpt) (`a166416a4ee309a5b988a09254d2fe75bb6fbc82f6367c4af6417584ea06d3ff`), [control_sets](../../experiments/python-gamebub-v106/native/20261108T013032873883Z/reports/route-control-sets.rpt) (`31dff9479884e45627d36f944cd34de2e18bf8c436bda0e1873c2aef1dd5d005`), [congestion](../../experiments/python-gamebub-v106/native/20261108T013032873883Z/reports/route-congestion.rpt) (`e9c8a47ca9a16ebb00f819d8357c619fc08be3830e70f070f405f9b0fe702104`).

## closure-prefix-telemetry

Route WNS is -4.700 ns. The largest retained net is `coefficients/child/scratch/reset_2`: 7,135 loads, of which 7,125 are reported set/reset loads. The list has 14 nets with fanout≥1,000 and 25 with fanout≥500; these counts refer only to the retained top50. Control sets change by +69 relative to the first measured V106 route (lut); this is a composed implementation comparison, not isolated storage/CSA causality.

| Net (largest ten retained) | Fanout | Driver | Worst reported slack (ns) | Worst reported delay (ns) | CE loads | Set/reset loads | Data/other loads | Clock loads |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `coefficients/child/scratch/reset_2` | 7,135 | LUT3 | -1.056 | 6.565 | 0 | 7,125 | 10 | 0 |
| `transform/inverse/inverse_dequant_INST_0_i_1_n_0` | 3,611 | LUT6 | -2.747 | 3.190 | 0 | 3,556 | 55 | 0 |
| `transform/dequant/out_dequantized[1279]_i_1_n_0` | 2,351 | LUT2 | -1.400 | 3.415 | 0 | 2,351 | 0 | 0 |
| `reconstruction/reconstruct/running14_out` | 2,260 | LUT3 | -2.190 | 1.518 | 0 | 2,232 | 28 | 0 |
| `transform/inverse/intermediate[63][23]_i_1_n_0` | 1,536 | LUT6 | -1.493 | 2.535 | 1,536 | 0 | 0 | 0 |
| `transform/inverse/intermediate[63][23]_i_4_n_0` | 1,346 | LUT4 | -0.776 | 6.385 | 0 | 0 | 1,346 | 0 |
| `transform/inverse/state02_out` | 1,316 | LUT5 | -3.602 | 2.453 | 1,313 | 0 | 3 | 0 |
| `reconstruction/reset_0` | 1,282 | LUT2 | -1.524 | 4.322 | 0 | 1,280 | 2 | 0 |
| `transform/dequant/coefficients[0]` | 1,078 | LUT4 | -2.148 | 2.820 | 1,060 | 0 | 18 | 0 |
| `reconstruction/reset_2` | 1,038 | LUT3 | -3.448 | 2.404 | 0 | 0 | 1,038 | 0 |

Across all 50 listed nets, the load-occurrence totals are clock_enable 7,299, set_reset 18,594, data_other 18,153, clock 0. A physical cell can load several nets, so these sums are not unique registers, cells or device-wide loads. Nonfinite-slack rows: none in the retained list. In particular an OOC reset/input port with `inf` slack has no finite timing margin reported here; it is not an unconstrained-boundary timing pass.

Congestion observations: * No congestion windows are found above level 5; * No initial estimated congestion windows are found above level 5. This statement is threshold-specific and does not rule out congestion at level5 or below, transient routing congestion, or large net delays.

Pinned reports: [fanout](../../experiments/python-gamebub-v106/native/20261108T015540764948Z/reports/route-high-fanout.rpt) (`f2e383eb4c486a87e60cdb6986d981f319e8dba4841a9f41eca0565621c83516`), [control_sets](../../experiments/python-gamebub-v106/native/20261108T015540764948Z/reports/route-control-sets.rpt) (`e920074d9a453beef7c71a795f0e5fef6b70fdb6cf91931656c05f078490d570`), [congestion](../../experiments/python-gamebub-v106/native/20261108T015540764948Z/reports/route-congestion.rpt) (`e0be5fd71969018238a5ceec6f7b868fcdb58da2e2cbfb4aa43ac4d89a44210c`).

## Interpretation and reproduction

Large global cancellation/reset/control nets remain a measured locality burden even after tiny coefficient RAMs are removed. Changing storage, modular layout arithmetic or telemetry can also change control sets, FF counts and placement; these composed trials cannot assign every delta to one feature. Unused register locations reported inside slices with registers are a placement/packing metric, not the whole-device free FF count. Threshold-limited congestion estimates do not establish globally congestion-free routing.

```sh
python3 scripts/cu66-v106/audit_native.py
python3 scripts/cu66-v106/physical_locality.py
```

The analyzer requires `native-audit.json` to report `PASS_EVIDENCE`, then independently rechecks report hashes and byte counts against both the audit's bound inputs and the terminal receipt artifacts. `PASS_EVIDENCE` here verifies provenance and parsing, not timing closure. The fixed100MHz target, parent clock/I/O/CDC and methodology signoff, actual external-memory service, sustained hardware30fps and complete under10ms decoding remain separate gates. No achieved Fmax is derived.
