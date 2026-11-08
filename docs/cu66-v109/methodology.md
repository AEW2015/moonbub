# Initial V109 routed methodology: unresolved findings and scope

This supplement interprets the **final routed** initial A/B reports only. A is fault-only (`20261108T112057270069Z`); B is fault plus prefetch and bank decode (`20261108T112912276160Z`). Both use `xc7a100tcsg324-1`, the same single 10 ns component clock and the qualified comparison recipe. Both complete routing but **fail internal 100 MHz setup timing**. No warning is waived, no constraint is changed and no new report is generated here. The frozen per-run `METHODOLOGY_RESOLUTION_REPORT.md` files remain unchanged.

## Exact rule listings and timing results

| Final routed measure | A: fault | B: fault + prefetch + bank |
| --- | ---: | ---: |
| SYNTH-6, Warning | 39 | 39 |
| TIMING-16, Warning | 1,000 listed | 677 listed |
| TIMING-18, Warning | 1,000 listed | 1,000 listed |
| ULMTCS-1, Warning | 1 | 1 |
| Methodology checks found | 2,040 | 1,717 |
| Control sets / available limit | 1,223 / 15,850 | 1,232 / 15,850 |
| Worst setup slack | −1.589 ns | −1.737 ns |
| Total negative setup slack | −8,342.999 ns | −5,988.869 ns |
| Setup-failing endpoints / checked endpoints | 14,204 / 88,186 | 12,615 / 87,886 |
| Worst hold slack; hold-failing endpoints | +0.087 ns; 0 | +0.088 ns; 0 |
| Worst pulse-width slack; pulse-failing endpoints | +3.750 ns; 0 | +3.750 ns; 0 |

These are four rule families, all reported as **Warning**; neither table reports Critical Warning, Error or Info entries. The detail-entry counts match the table counts. The report header says `Max checks: <unlimited>`, but the 1,000-entry rule listings are still **not an endpoint census**. TIMING-16 reports the large-violation subset and A's listing reaches 1,000; TIMING-18 likewise lists 1,000 instances while `check_timing` identifies many more missing I/O delays. The actual 14,204/12,615 setup-failing endpoint counts come from the twelve-column final timing summary. They must not be replaced with the methodology 1,000/677 counts or interpreted as warnings already resolved.

## TIMING-16: internal setup remains unresolved

The clock is the intended 10 ns requirement, and these failing paths are between registers on the same `component_clk`. A's worst reported path is `coefficients/child/packet_decoder/synchronous.ingress/fetch_index_reg[3]` to `fetch_bytes_reg[8][0]/CE`: 11.300 ns data delay, fourteen logic levels, 3.541 ns logic and 7.759 ns routing. B's worst path is `fetch_return_reg[2]` to ingress `error_reg[0]/CE`: 11.448 ns, fifteen levels including seven CARRY4 cells, 3.273 ns logic and 8.175 ns routing. These are actual final routed observations; an earlier synthesis Rice cone does not supersede them.

The first TIMING-16 detail is also not necessarily the worst path: A's first listing is parser `available_reg[6]` to `out_consumed_reg[25]` at −1.000 ns; B's first is `transform/dequant/group_index_reg[0]_rep__1` to `out_dequantized_reg[794]` at −1.000 ns. Use the full routed path and actual source map to select changes, then requalify exact behavior and remeasure the same clock. The qualified FETCH and conditional REQUEST work address measured ingress arithmetic/control paths; their results remain separate trials.

TIMING-16 is **not waivable for this study**. There is no evidence that these same-clock functional paths are false or multicycle. Clock relaxation, exceptions and warning-severity changes would not meet the fixed 100 MHz objective. The positive hold and pulse results do not close setup. Any staged alternative must explicitly preserve or version the public handshake, owner, cancel/drain and cycle contract before claiming a valid optimization.

## TIMING-18: open OOC boundary timing, not internal closure

Both final `check_timing` reports identify **1,101 input ports without input delay** and **12,888 output ports without output delay**. Representative missing input constraints include `abort_packet`, accepted-reference metadata and data; listed outputs include diagnostic counters such as `count_dense[*]`. The component is implemented out of context, with protocol and diagnostic ports rather than a qualified board interface. The retained XDC intentionally supplies only `create_clock -name component_clk -period 10.000 [get_ports clk]`.

These warnings are an explicit **open full-parent/board-boundary qualification scope**. They are not resolved or waived by calling the build OOC. Parent integration must supply the actual clock source and waveform, interface timing relationships, applicable input/output delays or justified internal budgets, and physical board constraints using the real design and device specifications. No guessed delay, clock group, false path or board pin assignment is added to make this report quiet. Internal setup failure remains a separate blocker even while boundary timing is open.

The other `check_timing` categories are zero in both reports: `no_clock`, `constant_clock`, `pulse_width_clock`, `unconstrained_internal_endpoints`, `multiple_clock`, `generated_clocks`, `loops`, `partial_input_delay`, `partial_output_delay` and `latch_loops`. In particular, zero unconstrained **internal endpoints** does not imply constrained top-level I/O or board signoff.

## SYNTH-6: inspect the exact RAM cone before changing latency

Each run lists 39 RAM instances for which no output register was merged into the block. The lists are identical: eight admission `memory_reg_1_*` banks; admission `mode_store/words_reg` and `scale_store/words_reg`; two context-decoder `position_reg_rep` instances; eight synchronous-ingress `memory_reg_1_*` banks; ingress `position_reg_rep`; seven generated `g0_b*` instances; and eleven `producer_cell_cache_reg[*]_i_*` instances. The raw reports retain every full mapped instance name.

This is an unresolved implementation-quality finding, not proof that all 39 RAMs limit the current path. First map a flagged RAM and its output to actual RTL and an actual routed path, inspect the current read enable/address, consumer and response ownership, and determine whether an existing permitted capture edge can absorb a register. A blind `DO_REG`/RAM-output-register change can add a cycle, alter read-during-write forwarding, change reset/hold behavior or misalign tags and acknowledgements. Any proposed change therefore needs its explicit latency/ownership contract, unchanged golden and cancellation checks, canonical qualification and a new measured route. No BRAM property or RTL is changed by this interpretation.

## ULMTCS-1: control locality and payload validity

A uses 1,223 control sets (7.716% of 15,850); B uses 1,232 (7.773%). Both exceed the report's 7.5% recommendation and each produces one Warning. This is a packing/locality pressure signal rather than a timing exception or an independently sufficient cause of the measured worst slack. The report recommends `report_control_sets` for further detail; no new heavy report is run here.

A focused follow-up should associate high-fanout reset/enable drivers with the exact payload/control endpoints and placement neighborhoods, share only equivalent local controls, and preserve immediate externally visible invalidation with explicit validity/ownership. Private payload reset or enable changes are allowed only when every public invalid/debug value, stored observable state, counter and cancel/retry fence remains exact. The existing qualified output-mask and same-edge fault predicates illustrate this discipline; their presence alone does not prove that the remaining 1,223/1,232 sets can be merged or that routing will improve. A stale payload, delayed kill or unqualified prewrite is not an acceptable control-set reduction.

## Retained evidence and immutability

All paths below are under `experiments/python-gamebub-v109/native/`; hashes pin the exact files used for this interpretation.

### A: `20261108T112057270069Z`

- [reports/route-methodology.rpt](../../experiments/python-gamebub-v109/native/20261108T112057270069Z/reports/route-methodology.rpt), SHA-256 `09e0a100414716ce19ce7833e14c039ee2819e9e805190c2d917741728bb2bca`.
- [reports/route-check-timing.rpt](../../experiments/python-gamebub-v109/native/20261108T112057270069Z/reports/route-check-timing.rpt), SHA-256 `37f80de8b0335d79e949458288930defb0343b2b58f1b52df37b76faed6f9f67`.
- [reports/route-timing-summary.rpt](../../experiments/python-gamebub-v109/native/20261108T112057270069Z/reports/route-timing-summary.rpt), SHA-256 `25b4e004f2ac0645326c833f54c8a5ad1abe2f5af841f80f1e3d9b12a200d887`.
- [reports/route-setup-paths.rpt](../../experiments/python-gamebub-v109/native/20261108T112057270069Z/reports/route-setup-paths.rpt), SHA-256 `b5ff4fca46d8a7eff4b1936e122dd6d6295932a7feece54e9306056c0b5c3906`.
- [METHODOLOGY_RESOLUTION_REPORT.md](../../experiments/python-gamebub-v109/native/20261108T112057270069Z/METHODOLOGY_RESOLUTION_REPORT.md), SHA-256 `f5c9698c889f64d1d9badbdc5cebd077b109e5d47a11da700af54a1f52143007`.

### B: `20261108T112912276160Z`

- [reports/route-methodology.rpt](../../experiments/python-gamebub-v109/native/20261108T112912276160Z/reports/route-methodology.rpt), SHA-256 `d3efa3bef059127d6b941c1b4a8f89c0235d8b1b118940b023f9718cd65e5fac`.
- [reports/route-check-timing.rpt](../../experiments/python-gamebub-v109/native/20261108T112912276160Z/reports/route-check-timing.rpt), SHA-256 `4c15b75110d84f12c93c62db041cbd5091ae695ceabf947996214bd766a7c722`.
- [reports/route-timing-summary.rpt](../../experiments/python-gamebub-v109/native/20261108T112912276160Z/reports/route-timing-summary.rpt), SHA-256 `dda1177b2bab7beeae0451aeb0708b2e6331efeabf19e3731a01d7e3e7bad943`.
- [reports/route-setup-paths.rpt](../../experiments/python-gamebub-v109/native/20261108T112912276160Z/reports/route-setup-paths.rpt), SHA-256 `71559aed655c2931af025d429315a2143a85073e154281a4aab4b48609963485`.
- [METHODOLOGY_RESOLUTION_REPORT.md](../../experiments/python-gamebub-v109/native/20261108T112912276160Z/METHODOLOGY_RESOLUTION_REPORT.md), SHA-256 `a51be6beb494302fe040dfc95498a582b22395e4a9a8217abeaac0eba685dac3`.

FETCH and REQUEST methodology counts are intentionally absent until those exact trials have final routed reports. Their source preparation, focused tests, synthesis estimates and parent A/B counts do not establish their final methodology results. This document records interpretation and remaining actions only; zero violations are claimed resolved.
