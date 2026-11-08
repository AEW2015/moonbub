# V107 native decoder comparison

Fresh variants use Vivado 2026.1 build 6511674, `xc7a100tcsg324-1`, the same **10.000 ns** clock loaded before synthesis and two tool threads. All use Default synthesis/opt/place/route except the explicitly labeled `threshold-runtime` probe, which changes only synthesis to RuntimeOptimized. Its same eighteen RTL/header files and Default placement/routing are hash-bound; different synthesis strategies are not a single-edit RTL-only comparison. The native watchdog is 3,600 seconds versus V106’s 1,800 seconds; runtime is not a matched comparison. No decoder clock relaxation, false path, multicycle exception or invented I/O delay was added.

| Variant | Routed WNS (ns) | Failing setup endpoints | Hold (ns) | Pulse (ns) | Internal 100 MHz |
| --- | ---: | ---: | ---: | ---: | --- |
| V106 selected closure | −4.034 | 44,630 | +0.122 | +3.750 | FAIL |
| quant-aligned | -4.428 | 49,770 | +0.115 | +3.750 | FAIL |
| elastic | -3.447 | 39,420 | +0.042 | +3.750 | FAIL |
| header | SCHEDULING_CANCELLED_NO_TIMING_RESULT | — | — | — | OPEN |
| tables | -3.076 | 21,608 | +0.088 | +3.750 | FAIL |
| payload | -2.735 | 21,836 | +0.098 | +3.750 | FAIL |
| guard | SCHEDULING_CANCELLED_NO_TIMING_RESULT | — | — | — | OPEN |
| meta | -3.146 | 25,263 | +0.073 | +3.750 | FAIL |
| threshold | -3.137 | 29,395 | +0.082 | +3.750 | FAIL |
| threshold-runtime | -2.333 | 21,433 | +0.096 | +3.750 | FAIL |

The selected routed frontier is **threshold-runtime**, WNS **-2.333 ns**. A selected negative slack remains a timing failure. A single completed route does not establish reproducibility across clean builds or strategies.

The earlier V106 sixth-checkpoint continuation completed routing at −4.428 ns. It reused a read-only synthesis checkpoint and is retained separately from fresh synthesis trials. SCALE-only native routing was deferred after targeted routed probes found mode[0] −2.508 ns and scale[0] −2.587 ns; TABLES combines both repairs instead. No deferred run is counted as measured.
The HEADER-only job was deliberately stopped for scheduling at 1,831.615 seconds (exit143) before any synthesis checkpoint/report; its unchanged3,600-second watchdog was not reached. The retained cancellation record distinguishes this from a tool timeout or measured timing failure. The sixth source trial is motivated by an actual read-only TABLES route probe of a constant×43 DSP control path at−2.497 ns, with its original checkpoint hash unchanged.

See [summary JSON](../../experiments/python-gamebub-v107/summary.json), [selected source map](../../experiments/python-gamebub-v107/selection.json), [CSV](../../experiments/python-gamebub-v107/native-comparison.csv), and [independent audit](../../experiments/python-gamebub-v107/audit/baseline-audit.json). The native receipts retain complete source snapshots, exact commands, recipes, hashes, logs and reports. Large checkpoints remain at their documented external paths and are not required for portable report auditing.

## Functional comparison scopes

- Six cycle-exact fresh/canonical lanes: **336 case-profile runs and 408 directed checks**, including both implementations, seeds, profiles and expected rejects. These are not unique displayed frames.
- The complete coefficient tuple register and done fence use a separate latency-aware canonical comparison: **88 case-profile runs and 84 directed checks**, with exact canonical pixels and ordered semantic streams, explicit accepted/delivered/discarded conservation, ownership, error/cancel checks. Public cycle equality against V106 is not claimed.
- HEADER runs **44 new candidate case-profile runs and 42 directed checks**, requiring exact stdout, cycles, events and canonical bytes versus the retained actual elastic control. The control is reused, not reexecuted or recounted.
- TABLES uses the same fresh-candidate-only comparison and control reuse. Component-level RAM proofs are separate from full decoder timing.
- PAYLOAD separately removes resets/control dependence from 1,027 dequant and 1,280 IDCT private payload bits. It requires another 44/42 fresh candidate-only exact comparison and an actual native route; unit mapping is not full decoder timing.
- CDC experiments use separate tops and clocks. Their positive slack never substitutes for decoder timing or parent-board CDC signoff.

## Further qualified control experiments

META captures two pure geometry/domain flags alongside the existing130-bit coefficient payload, with no added public cycles. Its unit and exact full canonical tests pass, but its completed combined route is slower than the selected PAYLOAD route. It remains unselected. The table above retains that negative result. The additional live count-limit path requires another measured control cut.

The four-file header prefix/count-threshold unit passes31,856,723 paired controller edges across both SYNC modes/two seeds. The combined complete pixel decoder additionally passes44 fresh candidate case-profile runs and42 directed checks, requiring exact canonical pixels, events and cycles against the retained actual elastic control. Source-bound native routing is listed above; neither model-only preparation nor the isolated extracted pipeline synthesis margin substitutes for that result. See [count thresholds](count-threshold.md) and [actual extracted mapping](count-threshold-native.md).

The single bounded post-route physical optimization diagnostic crashed in Vivado (exit139) and produced no completed timing result or candidate checkpoint. Its intermediate slack is excluded from selection. Parent checkpoints/sources stayed unchanged; the [failure evidence](postroute-probe.md) is audited separately. No retry or extra strategy sweep was launched.

## Selected closure

Apply the selected manifest’s baseline/source overrides to the frozen V100 source list, then append its additional coefficient-stage source. Compile exactly one implementation of each module. Reproduce both the selected flow_strategy and pinned native recipes alongside the RTL source map. Standalone verification adapters are not production inputs. The native source closure includes the embedded admission helpers; strict Verilator compilation may split the exact same bytes into correctly named helper files. See per-run packaging manifests.

This is component OOC evidence. Board I/O, reset recovery/removal, real CDC integration, transport service, full custom top fit, sustained hardware 30 fps and complete validated decoding below 10 ms remain open. No achieved Fmax is inferred from one WNS result.

## Routed resources

| Variant | LUTs | LUTRAM | FFs | Slices | Control sets | RAMB36 | RAMB18 | DSPs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| quant-aligned | 48174 | 1717 | 37067 | 15425 | 1280 | 32 | 10 | 28 |
| elastic | 47624 | 1715 | 37218 | 15287 | 1201 | 32 | 10 | 28 |
| tables | 36152 | 176 | 34473 | 13642 | 1137 | 32 | 12 | 28 |
| payload | 34990 | 193 | 34399 | 13075 | 1160 | 32 | 12 | 27 |
| meta | 35759 | 189 | 34438 | 13429 | 1222 | 32 | 12 | 25 |
| threshold | 35432 | 280 | 35135 | 13845 | 1168 | 32 | 12 | 41 |
| threshold-runtime | 38186 | 294 | 35480 | 14174 | 1066 | 38 | 17 | 34 |

These are component routed resources, not complete board-fit evidence. Slice occupancy and control-set packing can be much tighter than LUT utilization alone suggests.
