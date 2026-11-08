# V106 methodology resolution report

**Status: actual component evidence measured; methodology/board signoff OPEN.**

Best measured internal-target candidate `closure` routed WNS is -4.034 ns at the unchanged 10 ns (100 MHz) target; the internal setup/hold/pulse/routing target is **OPEN**. WHS +0.122 ns, WPWS +3.750 ns; failing setup/hold/pulse endpoints: 44630/0/0. This is a target-period result, not an achieved-Fmax or board-throughput claim.

Audited native variants in this report: `closure`, `closure-prefix-telemetry`, `guarded-suffix-idct-cache`, `local-guards-scratch-area`, `lut`, `lut-storage-plan`. The names above are derived from actual audited native receipts; deferred candidates must not be presented as additional native measurements.

Constraint source: `component.xdc`, line 4. The command is `create_clock -name component_clk -period 10.000 [get_ports clk]`: clock component_clk, period 10 ns, target input port clk. It is loaded before synthesis. Default implementation directives and two tool threads are retained. No relaxed comparison clock, exception, waiver, I/O delay or parent clock-source location was fabricated to clear findings.

| Variant | Stage | WNS ns | No clock | Unconstrained internal endpoints | Missing input delays | Missing output delays |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| closure | synthesis estimate | -3.461 | 0 | 0 | 1101 | 12885 |
| closure | placed estimate | -3.369 | 0 | 0 | 1101 | 12885 |
| closure | routed | -4.034 | 0 | 0 | 1101 | 12885 |
| closure-prefix-telemetry | synthesis estimate | -3.897 | 0 | 0 | 1101 | 12885 |
| closure-prefix-telemetry | placed estimate | -4.800 | 0 | 0 | 1101 | 12885 |
| closure-prefix-telemetry | routed | -4.700 | 0 | 0 | 1101 | 12885 |
| guarded-suffix-idct-cache | synthesis estimate | -3.581 | 0 | 0 | 1101 | 12885 |
| local-guards-scratch-area | synthesis estimate | -3.205 | 0 | 0 | 1101 | 12885 |
| lut | synthesis estimate | -5.303 | 0 | 0 | 1101 | 12885 |
| lut | placed estimate | -6.246 | 0 | 0 | 1101 | 12885 |
| lut | routed | -7.130 | 0 | 0 | 1101 | 12885 |
| lut-storage-plan | synthesis estimate | -5.113 | 0 | 0 | 1101 | 12885 |
| lut-storage-plan | placed estimate | -4.777 | 0 | 0 | 1101 | 12885 |
| lut-storage-plan | routed | -6.628 | 0 | 0 | 1101 | 12885 |

The endpoint numbers above come from check_timing. Methodology rule counts below are tool-reported summary counts; per-rule enumeration limits have not been qualified. Nonnegative setup slack alone does not establish hold/pulse checks, routing completeness or the external boundary contract.

| Variant | Stage | Report | Rule | Severity | Reported count |
| --- | --- | --- | --- | --- | ---: |
| closure | synth | methodology_reported | SYNTH-5 | Warning | 378 |
| closure | synth | methodology_reported | SYNTH-6 | Warning | 26 |
| closure | synth | methodology_reported | TIMING-16 | Warning | 1000 |
| closure | synth | methodology_reported | TIMING-18 | Warning | 1000 |
| closure | synth | methodology_reported | ULMTCS-1 | Warning | 1 |
| closure | synth | DRC_reported | CFGBVS-1 | Warning | 1 |
| closure | synth | DRC_reported | DPIP-1 | Warning | 49 |
| closure | synth | DRC_reported | DPOP-1 | Warning | 26 |
| closure | synth | DRC_reported | DPOP-2 | Warning | 12 |
| closure | place | methodology_reported | SYNTH-5 | Warning | 378 |
| closure | place | methodology_reported | SYNTH-6 | Warning | 26 |
| closure | place | methodology_reported | TIMING-16 | Warning | 1000 |
| closure | place | methodology_reported | TIMING-18 | Warning | 1000 |
| closure | place | methodology_reported | ULMTCS-1 | Warning | 1 |
| closure | place | DRC_reported | CFGBVS-1 | Warning | 1 |
| closure | place | DRC_reported | DPIP-1 | Warning | 49 |
| closure | place | DRC_reported | DPOP-1 | Warning | 26 |
| closure | place | DRC_reported | DPOP-2 | Warning | 12 |
| closure | route | methodology_reported | SYNTH-5 | Warning | 378 |
| closure | route | methodology_reported | SYNTH-6 | Warning | 26 |
| closure | route | methodology_reported | TIMING-16 | Warning | 1000 |
| closure | route | methodology_reported | TIMING-18 | Warning | 1000 |
| closure | route | methodology_reported | ULMTCS-1 | Warning | 1 |
| closure | route | DRC_reported | CFGBVS-1 | Warning | 1 |
| closure | route | DRC_reported | DPIP-1 | Warning | 49 |
| closure | route | DRC_reported | DPOP-1 | Warning | 26 |
| closure | route | DRC_reported | DPOP-2 | Warning | 12 |
| closure | route | DRC_reported | RTSTAT-10 | Warning | 1 |
| closure-prefix-telemetry | synth | methodology_reported | SYNTH-5 | Warning | 378 |
| closure-prefix-telemetry | synth | methodology_reported | SYNTH-6 | Warning | 26 |
| closure-prefix-telemetry | synth | methodology_reported | TIMING-16 | Warning | 1000 |
| closure-prefix-telemetry | synth | methodology_reported | TIMING-18 | Warning | 1000 |
| closure-prefix-telemetry | synth | methodology_reported | ULMTCS-1 | Warning | 1 |
| closure-prefix-telemetry | synth | DRC_reported | CFGBVS-1 | Warning | 1 |
| closure-prefix-telemetry | synth | DRC_reported | DPIP-1 | Warning | 49 |
| closure-prefix-telemetry | synth | DRC_reported | DPOP-1 | Warning | 26 |
| closure-prefix-telemetry | synth | DRC_reported | DPOP-2 | Warning | 12 |
| closure-prefix-telemetry | place | methodology_reported | SYNTH-5 | Warning | 378 |
| closure-prefix-telemetry | place | methodology_reported | SYNTH-6 | Warning | 26 |
| closure-prefix-telemetry | place | methodology_reported | TIMING-16 | Warning | 1000 |
| closure-prefix-telemetry | place | methodology_reported | TIMING-18 | Warning | 1000 |
| closure-prefix-telemetry | place | methodology_reported | ULMTCS-1 | Warning | 1 |
| closure-prefix-telemetry | place | DRC_reported | CFGBVS-1 | Warning | 1 |
| closure-prefix-telemetry | place | DRC_reported | DPIP-1 | Warning | 49 |
| closure-prefix-telemetry | place | DRC_reported | DPOP-1 | Warning | 26 |
| closure-prefix-telemetry | place | DRC_reported | DPOP-2 | Warning | 12 |
| closure-prefix-telemetry | route | methodology_reported | SYNTH-5 | Warning | 378 |
| closure-prefix-telemetry | route | methodology_reported | SYNTH-6 | Warning | 26 |
| closure-prefix-telemetry | route | methodology_reported | TIMING-16 | Warning | 1000 |
| closure-prefix-telemetry | route | methodology_reported | TIMING-18 | Warning | 1000 |
| closure-prefix-telemetry | route | methodology_reported | ULMTCS-1 | Warning | 1 |
| closure-prefix-telemetry | route | DRC_reported | CFGBVS-1 | Warning | 1 |
| closure-prefix-telemetry | route | DRC_reported | DPIP-1 | Warning | 49 |
| closure-prefix-telemetry | route | DRC_reported | DPOP-1 | Warning | 26 |
| closure-prefix-telemetry | route | DRC_reported | DPOP-2 | Warning | 12 |
| closure-prefix-telemetry | route | DRC_reported | RTSTAT-10 | Warning | 1 |
| guarded-suffix-idct-cache | synth | methodology_reported | SYNTH-5 | Warning | 378 |
| guarded-suffix-idct-cache | synth | methodology_reported | SYNTH-6 | Warning | 26 |
| guarded-suffix-idct-cache | synth | methodology_reported | TIMING-16 | Warning | 1000 |
| guarded-suffix-idct-cache | synth | methodology_reported | TIMING-18 | Warning | 1000 |
| guarded-suffix-idct-cache | synth | methodology_reported | ULMTCS-1 | Warning | 1 |
| guarded-suffix-idct-cache | synth | DRC_reported | CFGBVS-1 | Warning | 1 |
| guarded-suffix-idct-cache | synth | DRC_reported | DPIP-1 | Warning | 17 |
| guarded-suffix-idct-cache | synth | DRC_reported | DPOP-1 | Warning | 30 |
| guarded-suffix-idct-cache | synth | DRC_reported | DPOP-2 | Warning | 13 |
| local-guards-scratch-area | synth | methodology_reported | SYNTH-5 | Warning | 378 |
| local-guards-scratch-area | synth | methodology_reported | SYNTH-6 | Warning | 26 |
| local-guards-scratch-area | synth | methodology_reported | TIMING-16 | Warning | 1000 |
| local-guards-scratch-area | synth | methodology_reported | TIMING-18 | Warning | 1000 |
| local-guards-scratch-area | synth | DRC_reported | CFGBVS-1 | Warning | 1 |
| local-guards-scratch-area | synth | DRC_reported | DPIP-1 | Warning | 17 |
| local-guards-scratch-area | synth | DRC_reported | DPOP-1 | Warning | 28 |
| local-guards-scratch-area | synth | DRC_reported | DPOP-2 | Warning | 11 |
| lut | synth | methodology_reported | RTGT-1 | Advisory | 64 |
| lut | synth | methodology_reported | SYNTH-5 | Warning | 346 |
| lut | synth | methodology_reported | SYNTH-6 | Warning | 16 |
| lut | synth | methodology_reported | TIMING-16 | Warning | 1000 |
| lut | synth | methodology_reported | TIMING-18 | Warning | 1000 |
| lut | synth | DRC_reported | CFGBVS-1 | Warning | 1 |
| lut | synth | DRC_reported | DPIP-1 | Warning | 49 |
| lut | synth | DRC_reported | DPOP-1 | Warning | 26 |
| lut | synth | DRC_reported | DPOP-2 | Warning | 12 |
| lut | place | methodology_reported | RTGT-1 | Advisory | 64 |
| lut | place | methodology_reported | SYNTH-5 | Warning | 346 |
| lut | place | methodology_reported | SYNTH-6 | Warning | 16 |
| lut | place | methodology_reported | TIMING-16 | Warning | 1000 |
| lut | place | methodology_reported | TIMING-18 | Warning | 1000 |
| lut | place | DRC_reported | CFGBVS-1 | Warning | 1 |
| lut | place | DRC_reported | DPIP-1 | Warning | 49 |
| lut | place | DRC_reported | DPOP-1 | Warning | 26 |
| lut | place | DRC_reported | DPOP-2 | Warning | 12 |
| lut | route | methodology_reported | RTGT-1 | Advisory | 64 |
| lut | route | methodology_reported | SYNTH-5 | Warning | 346 |
| lut | route | methodology_reported | SYNTH-6 | Warning | 16 |
| lut | route | methodology_reported | TIMING-16 | Warning | 1000 |
| lut | route | methodology_reported | TIMING-18 | Warning | 1000 |
| lut | route | DRC_reported | CFGBVS-1 | Warning | 1 |
| lut | route | DRC_reported | DPIP-1 | Warning | 49 |
| lut | route | DRC_reported | DPOP-1 | Warning | 26 |
| lut | route | DRC_reported | DPOP-2 | Warning | 12 |
| lut | route | DRC_reported | RTSTAT-10 | Warning | 1 |
| lut-storage-plan | synth | methodology_reported | SYNTH-5 | Warning | 378 |
| lut-storage-plan | synth | methodology_reported | SYNTH-6 | Warning | 16 |
| lut-storage-plan | synth | methodology_reported | TIMING-16 | Warning | 1000 |
| lut-storage-plan | synth | methodology_reported | TIMING-18 | Warning | 1000 |
| lut-storage-plan | synth | DRC_reported | CFGBVS-1 | Warning | 1 |
| lut-storage-plan | synth | DRC_reported | DPIP-1 | Warning | 49 |
| lut-storage-plan | synth | DRC_reported | DPOP-1 | Warning | 26 |
| lut-storage-plan | synth | DRC_reported | DPOP-2 | Warning | 12 |
| lut-storage-plan | place | methodology_reported | SYNTH-5 | Warning | 378 |
| lut-storage-plan | place | methodology_reported | SYNTH-6 | Warning | 16 |
| lut-storage-plan | place | methodology_reported | TIMING-16 | Warning | 1000 |
| lut-storage-plan | place | methodology_reported | TIMING-18 | Warning | 1000 |
| lut-storage-plan | place | DRC_reported | CFGBVS-1 | Warning | 1 |
| lut-storage-plan | place | DRC_reported | DPIP-1 | Warning | 49 |
| lut-storage-plan | place | DRC_reported | DPOP-1 | Warning | 26 |
| lut-storage-plan | place | DRC_reported | DPOP-2 | Warning | 12 |
| lut-storage-plan | route | methodology_reported | SYNTH-5 | Warning | 378 |
| lut-storage-plan | route | methodology_reported | SYNTH-6 | Warning | 16 |
| lut-storage-plan | route | methodology_reported | TIMING-16 | Warning | 1000 |
| lut-storage-plan | route | methodology_reported | TIMING-18 | Warning | 1000 |
| lut-storage-plan | route | DRC_reported | CFGBVS-1 | Warning | 1 |
| lut-storage-plan | route | DRC_reported | DPIP-1 | Warning | 49 |
| lut-storage-plan | route | DRC_reported | DPOP-1 | Warning | 26 |
| lut-storage-plan | route | DRC_reported | DPOP-2 | Warning | 12 |
| lut-storage-plan | route | DRC_reported | RTSTAT-10 | Warning | 1 |

## V106 targeted changes and measured follow-up

- **Coefficient position/validation and storage:** the exact LUT tile-to-cell helpers replace the repeated constant-arithmetic validation evaluation; static bank/word coefficient storage targets the prior distributed-memory write-enable locality. Original invalid-metadata/error priorities and same-edge write ordering remain in the proof contract. Static source shape is not a primitive-mapping or timing verdict; inspect the native inventories, control sets, fanout and worst path for each actual variant.
- **Scratch allocation:** the full32 carry-save PLAN change calculates each aligned allocation prefix independently. Its modulo-2^32 identities preserve overflow, stale-epoch priority, size/count guards and same-cycle owner initialization. The source edit does not authorize narrower addresses, removed validation or an extra allocation cycle.
- **Sparse context position:** exact byte quotient/remainder tables, the combined correction/ZIGZAG table and parallel quotient correction selection target the routed position-to-block/index division cone. The proof covers the full32 position identity and fixed byte tables, including initial all-ones and invalid positions. The small correction bound follows from the table remainders; no unrestricted claim is made for unreachable standalone correction-table addresses.
- **Rice parser remaining bits:** full32 remaining/load-remaining caches target the measured size-to-output control cone. Reset/start initialization and every existing guarded load/PREFIX/SUFFIX update preserve the original modular subtraction identities. This is redundant state with a clocked invariant and unchanged parser cycles, not a stream-size assumption or a removed bound check.
- **Prefix and telemetry follow-up:** balanced first-one rank plus late window clamping replaces the serial scan without changing parser cycles. Static per-word 64-bit telemetry increments retain all public counters, wrap behavior, pre-edge sampling and reset/start/abort priority. Their focused probes and final paired lanes qualify behavior; native results decide whether the actual timing cones improve.
- **Guard-specific suffix, actual IDCT operands and producer cache:** the guarded-suffix-idct-cache trial specializes suffix extraction independently of PREFIX work, prefetches signed IDCT operands within existing MUL/ACC slots, and mirrors every producer plane/tile assignment in a private quant-cell cache. Selected-state substitution, live operand/cache invariants and full paired public behavior are distinct evidence scopes. Read actual mapped DSP registers and routed paths; the producer transition model alone is not whole-controller RTL proof.
- **TIMING-16 / setup and internal target:** the best measured routed result above is read dynamically from the selected native audit. If negative slack or any required setup/hold/pulse/routing check remains, read that actual final worst path and continue measured architectural/locality work. A cone removed from an earlier variant can expose another bottleneck; earlier path names do not identify the final selected limiter.
- **TIMING-18 / parent boundaries and CDC:** missing external input/output delays, parent clocks, interface timing and boundary locations remain system-integration obligations. OOC reports and a positive internal target result do not establish those contracts. Inspect the actual CDC/check_timing scope; paths omitted for absent boundary clock/delay definitions are not validated crossings.
- **SYNTH-6 / RAM pipeline advisory:** native RAM ledgers describe the actual optional primitive registers. The existing registered logical lookups and packet read-first semantics stay in force. An additional RAM output register requires an explicit latency/ownership contract and replay; it is not an attribute-only fix. Verify actual coefficient-storage FF/LUTRAM mapping rather than assuming it from static-word source.
- **RTGT-1 / RAM retargeting advisory:** retain reported opportunities separately from measured primitive mapping. New banking/port/collision changes require behavioral proofs and matched native measurements.
- **DPIP/DPOP / DSP advisories:** report actual AREG/BREG/MREG/PREG settings per primitive and variant. All measured variants retain the original dequantizer. The routed products_reg DSP-input path belongs to cu66_idct8x8 operand selection, not cu66_dequant; V104 dequantizer prefetch is not a direct fix for it. Coordinate tables, carry-save prefix logic and storage changes do not qualify every DSP path or establish a system clock gain.
- **CFGBVS/configuration and OOC route/clock-source findings:** actual parent/board configuration and boundary contracts remain integration obligations. No board configuration value or HD.CLK_SRC/HD.PARTPIN_LOCS was guessed.

The scope is exact same-cycle architectural RTL changes with bounded behavioral evidence and actual component native measurements. No finding was waived, downgraded or hidden by a timing cut. The 100 MHz internal target result is separate from methodology/DRC/CDC/boundary signoff, achieved-Fmax, sustained board 30 fps and complete validated under-10-ms decoding.

Native evidence audit: `experiments/python-gamebub-v106/native-audit.json`, SHA-256 `f5c44d452473a441acf13a66c3e83de5a6259a06a668ebbe7db126142c2a60a5`.
It pins source/constraint/recipe snapshots, retained reports and terminal outcomes. PASS_EVIDENCE authenticates evidence, including failed outcomes; it does not clear the findings above.
