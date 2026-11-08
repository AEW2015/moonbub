# V107: clock crossings and decoder timing cuts

V107 retains the **720×480 CS88 q16/all-BR88 profile and 49,152-byte packet cap**. It adds exact arithmetic/table rewrites, a complete coefficient tuple register with a done fence, and separately qualified clock/reset crossing experiments. The fixed decoder target remains **10 ns / 100 MHz**. Current measured selection and target status are in the [native comparison](vendor-comparison.md) and [summary](../../experiments/python-gamebub-v107/summary.json); a negative WNS is a failure even when the source is selected as the best tested frontier.

This is a **partial V107 checkpoint**, not complete board integration. The current production `moonshine_top` still instantiates the legacy JPEG core. CU66 transport framing, reference/memory service, publication and display adapters must be implemented and checked before the new decoder can replace it. Sustained hardware 30 fps and complete validated FPGA decoding below 10 ms remain open.

## Implemented and checked

| Change | Evidence and scope |
| --- | --- |
| Fixed-tap Rice reservoir | [17,839,670 actual clock edges](rice.md), historical vectors, boundary/random requests and independent arithmetic/reservoir oracle. |
| Q_RUN byte prefetch | [19,518,735 actual clock edges](quant.md), original full-width guards, error priority and scale-cache collision behavior retained. |
| Signed16 range recode | All 65,536 binary values and 262,144 RTL expression/scale vectors; complete-module integration is qualified separately. |
| Coefficient tuple register | [508,800 unit edges](elastic.md), complete 130-bit identity/value tuple, simultaneous replacement, stalled final offer, done fencing, reset/start/cancel and error flush. |
| Canonical elastic integration | [59,683,424 candidate edges](elastic-pipeline.md), exact pixels and ordered semantic streams across two seeds, explicit push/pop/discard conservation. Cycles may differ from the earlier unstaged decoder. |
| Header sums on existing byte cycles | [22,631,856 actual clock edges](header.md), 35-bit caches with byte forwarding; full canonical comparison additionally requires exact events and cycles versus elastic. |
| Mode/scale BRAM tables | [Table qualification](tables.md), actual mapped UNISIM tests, full admission checks and separate complete-decoder qualification. A physical BRAM write-mode parameter alone is not proof of the observable hold/collision behavior. |
| Dequant private payload reset/enable | [121,728 paired public cycles](payload-reset.md), independent integer/state replay; actual synthesis/query verifies 1,027 grounded reset pins and local registered-state CE. Public data/errors/reset cycles remain exact. |
| IDCT source tile reset/enable | [541,947 paired edges](idct-reset.md), 4,303 independent golden tiles/seed, all original assertions and source-owner checks. Full decoder composition is a separate gate. |
| Token-owned metadata flags | [Static geometry/domain flags](meta-flags.md) capture on the existing coefficient boundary; unit and exact canonical comparison pass. Combined META route is slower than the earlier PAYLOAD comparison. |
| Packet count prefixes | [Four-controller prefix proof](plan-prefix.md), both synchronous/legacy modes, actual forwarded-byte capture and stale-response rejection; the combined THRESHOLD full-pixel/native results are recorded separately. |
| Packet count thresholds | [Eight-edge header pipeline](count-threshold.md) replaces bound packet-count limit multiplication with exact cached ceilings and a live-block comparison. 31,856,723 paired controller edges and the exact full pixel canonical comparison pass. [Extracted synthesis](count-threshold-native.md) separately verifies mapping; full decoder routing remains the clock authority. |
| Clock/reset crossings | [Inventory](cdc.md), [first native probe](cdc-native.md), [synchronous RAM-control repair](cdc-sync.md). These units are not connected to the production CU66 parent. |

The six initial exact fresh/canonical lanes pass **336 case-profile runs and 408 directed checks**. The architectural elastic pair passes **88 case-profile runs and 84 directed checks**. HEADER, TABLES, PAYLOAD, GUARD, META and THRESHOLD each execute another 44 case-profile / 42 directed fresh candidate-only comparisons against the retained actual elastic control; reuse is explicit and the control is not recounted as newly executed. Counts include implementations, seeds/profiles and expected rejects; they are not distinct source frames, real-time throughput or hardware FPS.

No new compression, bitrate, quality, HEVC or AV1 advantage is measured in this phase. The optimization target is the exact existing decode function on 7-series fabric.

## Timing and methodology

Every fresh decoder native build uses the actual Artix-7 part `xc7a100tcsg324-1`, Vivado 2026.1 build 6511674, the same one-clock 10.000 ns OOC constraint, Default implementation directives and two tool threads, except the separately labeled `threshold-runtime` probe, which changes only synthesis to RuntimeOptimized on the same eighteen source/header files. Placement and routing stay Default. Its motivation is bounded synthesis runtime; no QoR improvement is assumed. The fresh-run watchdog increases from V106’s 1,800 seconds to 3,600 seconds. Do not compare their wall time as matched-performance evidence.

The earlier timed-out V106 sixth synthesis checkpoint was resumed read-only through opt/place/route. It completed at −4.428 ns and is retained separately; no new synthesis is attributed to that continuation. Adaptive source trials target observed header arithmetic, table lookup and scratch-to-inverse control paths. The elastic route occupies 15,287/15,850 slices (96.45%), despite 75.12% LUT utilization; control sets and routing locality therefore matter alongside arithmetic depth. SCALE-only full native/canonical work was deferred once targeted routed mode and scale reports showed both independently miss timing; the combined TABLES candidate addresses both.

[Methodology resolution](METHODOLOGY_RESOLUTION_REPORT.md) records unresolved setup, DSP/BRAM mapping advisories and intentionally open board I/O. No decoder false path, multicycle waiver, fabricated input/output delay or relaxed clock was introduced. Positive timing for a small CDC unit does not qualify the decoder or the board.

Native receipts retain source snapshots mounted read-only during execution, exact Tcl/XDC, command logs, resource samples, tool exits, checkpoint hashes and stage reports. Large DCPs and generated binaries stay outside Git; portable evidence audits do not need those external files. The [independent audit](baseline-audit.md) verifies retained evidence and explicitly distinguishes pending, failed, deferred and passed scopes.

## Latency and the next architecture step

The [cycle profiler](latency-next.md) replays the actual canonical traces. Elastic successful cases use 650,593–1,726,035 cycles under the fast memory profile and 1,768,082–2,473,261 cycles under the stalled profile. At a hypothetical qualified 100 MHz these would be 6.506–17.260 ms and 17.681–24.733 ms. Only 2/12 fast-profile successful observations and 0/12 stalled ones are below one million cycles. These fences omit complete production transport/publication integration, and a component OOC route does not validate the complete board clock/integration.

All sampled cases fit a 30-fps cycle budget at hypothetical 100 MHz, but that does not prove sustained hardware 30 fps. The next throughput experiment is a two-entry transformed-result queue so the next tile’s math can overlap the current tile’s 64-sample emission. Its 3,352 logical data bits are a design estimate, not an implemented BRAM allocation or measured speedup.

The [AMD control/reset review](amd-control-guidance.md) adds targeted work on the
measured 7,141-load scratch cancellation and 6,035-load inverse-error cones.
[Source-level candidates](reset-fanout-plan.md) distinguish reset-free payloads,
required ownership/control reset, physical fanout and fragmented control sets.
The [concrete status-use inventory](status-pipeline-inventory.md) distinguishes
actual operational consumers from observation-only output families. Host-only
telemetry may use a coherent tagged snapshot; functional ready/valid,
error/cancel and publication logic retains its required timing contract.

The [read-only routed load attribution](fanout-attribution.md) identifies 7,125
telemetry-data FFs plus three operational FFs on the retained PAYLOAD route’s largest cancellation reset
net. This is the next reset/control target, subject to first-update, timestamp,
feedback and public-zero compatibility. A [small Python model](../../experiments/python-gamebub-v107/telemetry-model/README.md)
checks the validity-masked counter principle and a deliberate stale-feedback
failure; it is not actual RTL or a measured resource/timing improvement. A
versioned host snapshot or minimal production observation wrapper is a future
interface decision, not an existing CSR/AXI interface. Parallel histogram ports
must change before RAM-backed diagnostics can be assumed.

[Next timing cuts](next-timing-cuts.md) distinguish the actual scratch
read-segment routed cone from earlier Rice/coefficient-enable stage estimates.
The capacity-bound prototype is an integer model; the Rice mask argument is
read-only source reasoning. Neither is implemented or timing-qualified. The
[one physical optimization probe](postroute-probe.md) crashed in Vivado and
produced no complete candidate result; its intermediate slack is excluded.

Before hardware handoff:

1. Close the measured decoder setup cones at the unchanged target, repeat the selected clean route, and retain all negative attempts.
2. Implement CU66 protocol/reference/memory/display adapters against real board clocks and bounded service contracts. Keep the related phase-shifted memory clock relationship intact.
3. Use the qualified CDC units only where their service rate fits. The reset-safe pixel FIFO experiment sustains **0.5 words per receiving clock**, insufficient for direct native scanout; retain line buffering/burst credit or redesign this boundary.
4. Run resets, abort/retry, malformed inputs, backpressure and complete publication/golden checks through the assembled parent.
5. Measure 30 distinct published source frames/s on hardware, then complete validated decoding strictly below 10 ms with a correlated measurement boundary.

## Reproduction

The existing `gamebub-cu66-v69-build` container supplies Verilator 5.020/GCC. The native runner uses `acorn-nexys4-ddr:2026.1`, the installed read-only Vivado tool mount and the existing legitimate license mount. Do not print license contents. No board is contacted by these flows.

```sh
python3 scripts/cu66-v107/rice/audit.py
python3 scripts/cu66-v107/quant/audit.py
python3 scripts/cu66-v107/header/audit.py
python3 scripts/cu66-v107/elastic/pipeline_audit.py
python3 fpga/experiments/cu66-v107-cdc-sync/audit.py
python3 fpga/experiments/cu66-v107-cdc-sync/audit_native.py
python3 scripts/cu66-v107/audit.py
python3 scripts/cu66-v107/summarize.py
```

These replay retained evidence without vendor synthesis. Heavy reproduction commands and receipts are in each component document and the source-pinned native builder scripts. Canonical HEADER/TABLES/PAYLOAD/GUARD/META/THRESHOLD commands require their selected focus proof and the retained same-seed elastic control; every current input hash is checked before execution.

To recreate the complete decoder qualification in order (these are heavy jobs; retained source/proof pointers are checked before execution):

```sh
python3 scripts/cu66-v107/run_matrix.py
python3 scripts/cu66-v107/quant_matrix.py
python3 scripts/cu66-v107/elastic_pipeline.py
python3 scripts/cu66-v107/header_pipeline.py
python3 scripts/cu66-v107/tables_pipeline.py
python3 scripts/cu66-v107/payload_pipeline.py
python3 scripts/cu66-v107/guard_pipeline.py
python3 scripts/cu66-v107/meta_pipeline.py
python3 scripts/cu66-v107/threshold_pipeline.py
python3 scripts/cu66-v107/quant_build.py --variant quant-aligned --run --timeout 3600
python3 scripts/cu66-v107/elastic_build.py --variant elastic --run --timeout 3600
python3 scripts/cu66-v107/header_build.py --variant header --run --timeout 3600
python3 scripts/cu66-v107/tables_build.py --variant tables --run --timeout 3600
python3 scripts/cu66-v107/payload_build.py --variant payload --run --timeout 3600
python3 scripts/cu66-v107/meta_build.py --variant meta --run --timeout 3600
python3 scripts/cu66-v107/threshold_build.py --variant threshold --run --timeout 3600
```

Run the focused recipes first when reconstructing the experiment from source;
the retained selected focus proofs supplied here are hash-checked by the full
qualification/native gates. Do not rerun a selected focus concurrently with a
native job that pins its mutable result pointer. Keep earlier qualification
scripts/source bytes frozen; a new implementation uses a new variant and receipt.
The initial exact lanes and the latency-aware elastic bench have different
contracts and must not be substituted for each other.

Use at most **two heavy jobs**. The host gate uses available RAM and full memory pressure: launch with at least 8 GiB available and full PSI average10 below 1; stop an owned run below 4 GiB or sustained full PSI at least 5. Stale swap occupancy alone is not a veto. Native containers and the shared verification container are limited to 8 GiB RAM with no additional swap allowance. The first elastic control compile hit the shared container’s previous 4 GiB cap; that failed attempt is retained. The verified retry uses one compile job and split C++ output. No host swap or unrelated container was changed.
