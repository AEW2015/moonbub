# CU71 arithmetic timing candidates

These are new candidates derived from the preserved CFG-remainder pipeline. No previous entropy, codec wire format, FPGA clock or board timing constraint is changed. Native synthesis diagnostics are not routed timing or hardware playback evidence.

`cu71_ab38_decoder_arithpipe.sv` snapshots the accepted stream, probability address/value, interval span, low and code. Four appended states register product, clamped partition, boundary and application. The existing error-0x21 interval/context guard executes before the snapshot. Abort/reset retain priority over all state actions, including probability writes.

For a valid interval, span is 2..65536. An unsigned 17-by-8-bit product fits 25 bits; shifting by eight preserves the original floor operation. The original clamp yields a partition in 1..65535. Since partition is less than span, `low+partition-1` lies within the original 16-bit interval. Probability adaptation uses the captured probability and the original rounding rule. This adds latency; it does not establish decoder throughput improvement.

`_v2` snapshots band/block range calculations. The full 17-by-6-bit product and one-width increment fit 23 bits. Signed pending-index comparisons remain 32 bits. Only after the range guard establishes `0 <= index-base < width <= 43` does the coefficient calculation use the low six bits. Error priority and zigzag placement are retained.

`_v3` precomputes exact 5*N, 15*N and 43*N event limits after successful header validation, before any stream parameter or event check. These private scratch bounds need no reset: they are consumed only after that successful header state. No new states are introduced by v3.

`_v4` snapshots stream parameters and separates parameter rounding, encoded-byte count and validation. The original 32-bit wrap behavior of `bits+7` and `8*(length-6)` is explicitly retained, including malformed-input behavior. Parameter errors keep priority 0x08, 0x09, 0x0a. Original debug state IDs 0..42 remain unchanged; new states are appended.

Every preparation script records parent/candidate hashes. Each regression directory freezes selected RTL, native harness, fixture indexes and all referenced fixture/oracle files. Coefficients and invalid rejection results are checked independently against those existing fixtures. Added abort probes reach every appended state, assert abort, check the entire probability RAM and decision counter remain unchanged, hold abort, verify quiescence, then retry a valid fixture. These are native Verilator tests, not electrical, ESP32, or physical playback proof.

The OOC runner uses xc7a100tcsg324-1, a 10 ns clock and the parent's unchanged 1 ns maximum input/output register budget. No false-path/multicycle relaxation or clock reduction is used. Inspect each frozen `executed.tcl`, source hash, setup paths and timing summary; tool exit success alone is not timing success. Unplaced hold estimates are not a routed hold result.

| Candidate | Native synthesized setup WNS | Worst measured cone |
|---|---:|---|
| Parent CFG pipeline | -9.019 ns | Context/probability read through arithmetic multiply, clamp and apply |
| Arithmetic v1 | -3.341 ns | Band block+1 multiply and comparison |
| Arithmetic v2 | -2.244 ns | Stream-selected event count bound multiply/comparison |
| Arithmetic v3 | -1.952 ns | Stream bit-count read through rounded parameter length and validation |
| Arithmetic v4 | +0.544 ns | DC-column select through signed DC accumulation/range check |

V4 synthesized utilization is 3096 LUTs (296 LUTRAM), 2781 FFs, one RAMB18 and four DSP blocks. Its setup diagnostic has zero failing endpoints, but the unplaced hold estimate is -0.537 ns; the report therefore does not claim an overall timing pass. Full-system source selection, fit, routed setup/hold timing and later controlled hardware tests remain integration gates. `arith-qualification.json`, when present, is produced only after the complete v4 regression and all source/hash checks finish.

`evidence/arith-malformed03` additionally compares freshly rebuilt frozen CFG-baseline RTL with v4 on 116 CRC-resealed real packets: all four streams, unsigned bit-count overflow boundaries, simultaneous invalid Rice parameters, and independently invalid Rice parameters. Exact observed errors agree: 112 error-0x08 cases, one error-0x09 case and three error-0x0a cases. This is directed coverage, not an exhaustive malformed-input proof. Attempts 01/02 preserve harness launch/CRLF fixture-format failures and are not RTL failure evidence.

`evidence/arith-cfg-v4-02` executes the inherited configuration sweep against the exact v4 model, rather than relying only on inheritance: all 2,073,600 supported block-count/width pairs (49,499 valid, 2,024,101 rejected) and all 17 configuration-validation abort positions pass. The driver changes metadata after acceptance to check retained-input behavior. Attempt 01 preserves the missing public-model DPI include-path compiler failure; it did not execute RTL.

The selected v4 full campaign completed all 1,371 actual coefficient oracles with no rejection. Decisions (43,436,569), renormalizations (35,844,140) and external reads (9,125,548) exactly match the parent CFG campaign. Total native simulated cycles increase from 435,692,006 to 651,151,908 (about 49.45%); randomized output stalls are nearly equal. Positive leaf setup therefore fixes a combinational timing problem but does not demonstrate increased decoder throughput. Full-system profiling and any later context overlap or stage-latency optimization require separate verification.
