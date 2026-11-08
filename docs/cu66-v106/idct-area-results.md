# V106 IDCT area repair

The first operand-prefetch IDCT passed exact simulation but expanded the full pipeline enough to fail placement. The retained fifth native run reported 66,507 total LUTs and 61,447 combined LUTs against 63,400 available, with 12,350 required slices against 10,647 available. Its synthesized IDCT hierarchy increased from 6,264 to 19,151 LUTs. This is a real rejected implementation; its frozen source and failure evidence are retained.

The new isolated area candidate keeps the same operand-prefetch timing strategy while consolidating selection. One next-k/group/pass/DC decoder selects two unique samples, one source-word read network and one intermediate-word read network. All operands have a single register write site. The new-input bypass selects only the two fixed first coefficients at accepted IDLE. DC forwarding still uses rounded current products on DC_FIRST_ACC; final FIRST_ACC still prefetches previously written intermediate rows 0 and 1.

Source words are fixed wire slices of `source_tile`. Their read index is the exact six-bit concatenation `{next_group,row_bit,next_k}`; the intermediate index is `{next_k,next_group,row_bit}`. These cover the same 0–63 positions as the original index expressions, without variable bit-offset multiplication. No public input width, cycle, state, shortcut or mathematical result changes. Product operands remain signed 24-by-14 bits, producing signed 38-bit products.

## Focused proof

[Focused receipt](../../experiments/python-gamebub-v106/idct-area/results.json) selects attempt `20261108T024135970900Z`, schema `v106-idct-area-clocked-production-comparison-v1`. Strict Verilator 5.020/GCC with assertions, `-Wall`, C++ warnings as errors, j2 and bounded watchdogs passed the complete original/candidate module comparison. No warning waiver or failed focused attempt was needed.

- Both seeds checked all 4,303 independently modeled Q14 output tiles, including the 3,471 historic fixtures, plus 30 all-state reset/abort replays per seed.
- Seed 106401 ran 270,128 clocks; seed 106402 ran 270,240. Together they checked 244,048 multiply edges and all ten FSM states with reset, abort and both guards.
- Public active cycles stay 0 for invalid/zero tiles, 4 for DC-only tiles and 128 for general tiles. Random output backpressure preserves payloads and metadata.
- Live-MUL assertions check every prefetched sample and basis against the original combinational selector. Complete public outputs, state/k/group, original samples/basis and products compare before/after every clock.

[Independent offline audit](../../experiments/python-gamebub-v106/idct-area/trace-audit.json) replays all 540,368 edges, signed products, FSM transitions and active-cycle values, separately recomputes all 4,303 dense integer Q14 goldens, and binds all source, recipe, adapter and trace hashes. This is reachable two-state simulation, not arbitrary-state formal equivalence.

## Frozen inputs

Candidate `fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv` SHA-256: `1ed49416dae06b727544ad1d2f96440f553cd99e5324dc895a0af5edbca5cc32`.

The six unique literal edits start from the original V69 IDCT. Exact recipe SHA-256: `3022274c92cc37c70cbc62e94fc7e9ee54be2039f396e3d539eb3431b69a4ebc`. Headers and all original body text outside these edits remain unchanged. The original failed-area prefetch source remains frozen at `f972987d80a062b4969c71ac6157e8f17ab9e6b18088bafb77c4030eac78990e`.

## Matched unit synthesis

Three sequential isolated unit synthesis screens completed successfully in 437.43 seconds: original, first-prefetch and shared-selector. They used the same Vivado 2026.1 container, xc7a100tcsg324-1 part, OOC/rebuilt/Default synthesis, clock loaded before synthesis at 10 ns, two threads and an 8 GiB limit. Tools and the legitimate existing license were mounted read only, with actual host identity unchanged.

[Unit build receipt](../../experiments/python-gamebub-v106/idct-area/native/20261108T024202129013Z/receipt.json) retains all three source snapshots and hashes, actual tool/version/part output, exact Docker/Tcl commands and settings, resource samples, native reports and checkpoint hashes. [Matched unit comparison](../../experiments/python-gamebub-v106/idct-area/unit-synthesis-comparison.json) independently rechecks those pins and reads the actual utilization/timing reports.

| Standalone production unit | Slice LUTs | FF | DSP | Estimated synthesis worst slack at 10 ns |
| --- | ---: | ---: | ---: | ---: |
| Original | 7,690 | 5,149 | 17 | +0.796 ns |
| First prefetch, rejected area | 16,256 | 5,176 | 19 | −0.700 ns |
| Shared-selector prefetch | **7,772** | **5,129** | **17** | **+2.920 ns** |

The shared selector adds 82 LUTs (1.07%) relative to the matched original unit and removes 8,484 LUTs relative to the first prefetch. It restores the original DSP count. These standalone counts differ from the full pipeline hierarchy because the integration context can optimize differently; area attribution uses the three newly matched units above.

The shared unit's estimated worst setup path is `state_reg[0]/C` → DSP `p_1_out__0__0/A[19]`, with 6.634 ns data delay. The original unit's worst path is `k_reg[1]/C` → DSP `p_1_out__1/A[0]`; the first-prefetch unit's worst path is `out_tile2__0/C` → `out_tile_reg[516]/D`. These are **synthesized, unplaced** reports. Estimated slack is not routed timing or an Fmax measurement.

The new candidate is suitable for the parent's final complete-top fit/timing experiment on the strength of exact simulation and near-original unit area. Complete-top resource fit, post-route timing, real I/O timing, hold/CDC and hardware FPS/validated decoding latency remain separate gates. The fifth failed full build remains rejected and retained; no failure is replaced or overwritten by this unit result.
