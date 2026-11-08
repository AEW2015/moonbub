# V106: fixed-clock decoder timing work

The fixed **100 MHz internal OOC timing target remains unmet**: selected routed setup WNS is **-4.034 ns**.

The selected next-study source is **closure**, with routed WNS **-4.034 ns**, a **+9.090 ns** change from the selected V105 geometry control. This is experimental component source selection from one implementation run per measured variant. It preserves **720×480**, the **49,152-byte CS88 cap**, the codec profile and the tested public cycle schedule. No compression, image-quality or network-bitrate improvement is measured here.

A separate, **unselected post-route diagnostic** reopened the original closure route and ran AggressiveExplore once: WNS changed from -4.034 to -3.777 ns (+0.257 ns), with 44,630 setup endpoints still failing. It is outside the six Default-flow source trials and does not replace the selected source or meet 100 MHz. [Diagnostic details](postroute-probe.md) and the [portable report audit](../../experiments/python-gamebub-v106/postroute/report-audit.json) retain its separate strategy, reports and scope.

**guarded-suffix-idct-cache: tool/build failure**, exit 1, 688.902 s; no placement/routing result was retained. Synthesis WNS -3.581 ns is an estimate only. The attempt remains in the [native audit](../../experiments/python-gamebub-v106/native-audit.json), without routed target qualification.

**local-guards-scratch-area: watchdog timeout**, exit 124, 1800.722 s; no placement/routing result was retained. Synthesis WNS -3.205 ns is an estimate only. The attempt remains in the [native audit](../../experiments/python-gamebub-v106/native-audit.json), without routed target qualification.

## Changes and focused proofs

The selected map retains inherited V105 admission/reconstruction changes. V106 studies exact coordinate helpers and explicitly banked coefficient registers, then uses actual failing paths to add cycle-preserving fixes: parallel modular scratch-layout prefixes, full32 context divide/remainder tables with bounded correction, cached Rice remaining-bit counts, balanced prefix rank, selected-SUFFIX extraction, guarded telemetry and IDCT operand/producer-address caches where selected. No validation, backpressure, owner/cancellation, error priority or clock requirement is removed.

| Experiment | Retained evidence | Details |
| --- | --- | --- |
| Coordinate helpers | 32,768 inputs: all four binary planes × 8,192 tile values; narrow and LUT helpers retain original truncation/invalid-domain behavior. | [Math results](math-results.md) |
| Coefficient storage | 41,431 whole-module edges; both 64-word banks checked each edge; 48 historical boundary cases and 15 directed checks per seed, plus prepared states and same-edge write/failure cases. | [Storage results](locality-results.md) |
| Scratch PLAN | 290,816 exact modular prefix rows, all 131,072 17-bit block values, 9,088 clocked begin cases; 9 accepted-write hazard checks over 311 edges. | [PLAN results](plan-results.md) |
| Context divmod | 4,260,918 actual full32 geometry cases, including 131,072 random full32 cases; 55 real-interface fixtures × 8 configurations, 172 directed checks. | [Context results](context-results.md) |
| Rice caches | 17,431,845 whole-module edges; complete 1,520-vector corpus × 8 configurations, 173,061 golden requests/configuration and 104 directed checks per seed; full32 cache identities and per-clock arithmetic/counter/reservoir oracle. | [Rice results](rice-results.md) |
| Balanced Rice prefix | 18,497,061 whole-module edges; each seed exhausts 524,288 pattern/window cases and 8,320 availability corners, plus the complete generic Rice suite; late window clamp follows a balanced first-one tree. | [PREFIX results](prefix-results.md) |
| Telemetry | 52 counter words × 64 carry positions; 53,248 prepared cases/106,497 prepared edges, plus 7,982,233 historical pipeline edges. | [Telemetry results](telemetry-results.md) |
| Selected SUFFIX | 18,522,021 whole-module edges; 12,480 additional suffix-domain cases/seed plus the full generic corpus. Only unconsumed suffix/decoded private values outside SUFFIX may differ; public/common checks remain unconditional. | [SUFFIX results](suffix-results.md) |
| IDCT operands | 540,368 edges/244,048 multiply edges, 4,303 independent integer-golden tiles, with directed reset/abort coverage across all ten states. | [IDCT results](idct-results.md) |
| Producer cell cache | 262,144 Python transition rows/32,768 helper inputs and exact source recipes. This is model-only component evidence; live cache assertions are checked separately in required paired pipeline lanes. | [Producer cache results](producer-cache-results.md) |
| Live ingress replay cache | 15,988,562 whole-pipeline clock edges, 5,760 prepared full32 boundary/mode/guard cases per seed; all 47 ingress public outputs and independent replay/cache/counter and child Rice reservoir oracles. Inactive private bits/last alone are unqualified and unconsumed. | [Ingress results](ingress-results.md) |
| Scratch word predecode | 223,651 whole-module clocks including 622 historical hazard clocks; all sixteen byte offsets/four banks, independent cache-word/head oracles, corrupt responses and accepted-write hazard suite. | [Scratch results](scratch-results.md) |
| IDCT area repair | 540,368 whole-module clocks/244,048 multiply edges, 4,303 independent integer-golden tiles and all ten abort states. The failed earlier area candidate remains retained separately. | [IDCT area results](idct-area-results.md) |
| Private SUFFIX projection | 296,608 model checks and an exact two-edit low24 projection recipe; model/source-only standalone evidence, with strict paired production RTL qualification required separately. No unused-signal warning is waived. | [Projection model](../../experiments/python-gamebub-v106/suffix24/results.json) |

These focused scopes differ. Exhaustive finite helper domains and exact algebra establish the stated arithmetic identities; prepared-state probes do not establish complete packet reachability. Historical/interface suites and paired integration provide additional behavioral evidence. The selected-SUFFIX specialization allows only its unused private suffix/decoded values to differ outside SUFFIX; all public outputs are checked every edge. The producer-address cache has a model-only standalone proof and live assertions in full paired pipeline lanes. The Rice C++ oracle checks every edge; historical Rice trace checkpoints are sampled every 256 edges plus reset/start, while prepared traces log every edge. The offline Rice checker verifies the recorded checkpoints and exact modular algebra, not omitted transitions. None is a four-state, complete formal or mapped-netlist equivalence proof.

The storage and helper recipes compose to identical bytes in both orders, verified by the [composition proof](../../experiments/python-gamebub-v106/composition.json). The PLAN/context/Rice/PREFIX/telemetry/SUFFIX/IDCT/producer-cache source recipes retain complete production bodies outside their exact edits. Source hashes, retained original bodies, strict compiler commands, finite watchdogs and attempt outcomes are checked by the [independent source/functional audit](../../experiments/python-gamebub-v106/source-audit.json).

## Paired integration

**24 lanes pass 1,344 case/profile runs and 1,632 directed checks** at seeds 106401/106402. The initial six variants and 6 adaptive follow-up/final/locality variants each run fresh and canonical workloads. Baseline/candidate transcripts, events and cycle counters match exactly; canonical bytes match where applicable. Counts include both implementations, seeds, profiles and expected rejects; they are not unique displayed frames or hardware FPS.

Fresh lanes cover admission, coefficients and inverse-transform behavior; canonical lanes also cover reconstruction. The complete per-lane receipts are listed in the [native and functional comparison](vendor-comparison.md).

## Selected source and integration

Apply `source_overrides` from the [selected-source manifest](../../experiments/python-gamebub-v106/selection.json) to the frozen source list, compiling exactly one production file per module. The native decoder closure is 17 files targeting `xc7a100tcsg324-1`. The fresh-only producer override is retained for behavioral reproduction and filtered from the native canonical closure. Keep focused wrappers, prepared-state controls and duplicate module adapters in verification source sets only.

The [comparison and source-map tables](vendor-comparison.md) list every variant, recipe and replacement SHA-256. [Summary JSON](../../experiments/python-gamebub-v106/summary.json), [native audit](../../experiments/python-gamebub-v106/native-audit.json), [actual setup cones](../../experiments/python-gamebub-v106/path-analysis.json) and [methodology findings](../../experiments/python-gamebub-v106/methodology-resolution.json) retain qualification and reproducibility details. The [physical-locality analysis](physical-locality.md) quantifies the retained top-50 fanout list, control-set totals and threshold-specific congestion observations. Audit `PASS_EVIDENCE` verifies retained records; it is not a timing or hardware pass.

## Reproduce

The existing `gamebub-cu66-v69-build` container supplies Verilator 5.020 and GCC with this repository and its external `/build` mount. Runs use assertions, strict warnings, two compilation jobs and finite timeouts. The shared resource gate uses available RAM and memory pressure; swap alone is not a stop condition. Do not overlap more than two heavy jobs.

```sh
python3 scripts/cu66-v106/math.py
python3 scripts/cu66-v106/locality.py
python3 scripts/cu66-v106/plan.py
python3 scripts/cu66-v106/context.py
python3 scripts/cu66-v106/rice.py
python3 scripts/cu66-v106/prefix.py
python3 scripts/cu66-v106/telemetry.py
python3 scripts/cu66-v106/suffix.py
python3 scripts/cu66-v106/idct.py
python3 scripts/cu66-v106/ingress.py
python3 scripts/cu66-v106/scratch.py
python3 scripts/cu66-v106/idct_area.py
python3 scripts/cu66-v106/suffix24.py --verify
python3 scripts/cu66-v106/producer_cache.py --verify
python3 scripts/cu66-v106/idct_area_unit.py --run
python3 scripts/cu66-v106/idct_area_analyze.py
python3 scripts/cu66-v106/compose.py
python3 scripts/cu66-v106/run_matrix.py
python3 scripts/cu66-v106/followup/run_matrix.py
python3 scripts/cu66-v106/final/run_matrix.py
python3 scripts/cu66-v106/locality_final/run_matrix.py
python3 scripts/cu66-v106/audit_sources.py
```

For interrupted follow-up/final/locality matrices, resume without replacing hash-current PASS receipts:

```sh
python3 scripts/cu66-v106/continue_matrix.py --runner followup final
python3 scripts/cu66-v106/locality_final/continue_matrix.py --runner locality_final
```

The resume helper verifies existing PASS source/receipt hashes, waits for a stable resource gate and retries only retained host-gate denials, with bounded retries. Compile, simulation, assertion and transcript-mismatch failures stop for investigation; a retained failed or gated attempt is not a functional PASS.

The initial, follow-up, final and locality runners stay frozen independently. The rejected fifth pipeline trial retains its failed fresh compile and explicitly unrun canonical lane; it is excluded from the 24 required PASS lanes and must not be reproduced as a successful pair. Its native placement failure remains a required retained implementation attempt. The [adaptive campaign policy](../../scripts/cu66-v106/campaign.py) records the measured native set and why native controls were deferred; original declarations of potential trials are not claims that every trial was measured. Reproduce only the actual required implementation-attempt campaign below (failed placement remains a retained failure), using the existing legitimate Artix-enabled Vivado 2026.1 installation and license. Each native job retains two CPUs, two tool threads, an 8 GiB limit, a 1,800-second watchdog, the 10 ns comparison clock and Default directives.

```sh
python3 scripts/cu66-v106/build.py --variant lut --run
python3 scripts/cu66-v106/followup/build.py --variant lut-storage-plan --run
python3 scripts/cu66-v106/followup/build.py --variant closure --run
python3 scripts/cu66-v106/final/build.py --variant closure-prefix-telemetry --run
python3 scripts/cu66-v106/pipeline/build.py --variant guarded-suffix-idct-cache --run
python3 scripts/cu66-v106/locality_final/build.py --variant local-guards-scratch-area --run
python3 scripts/cu66-v106/audit_native.py
python3 scripts/cu66-v106/analyze_paths.py
python3 scripts/cu66-v106/methodology.py --write-external
python3 scripts/cu66-v106/physical_locality.py
python3 scripts/cu66-v106/audit_postroute.py
python3 scripts/cu66-v106/summarize.py
python3 scripts/cu66-v106/render.py
python3 scripts/cu66-v106/render.py --check
python3 scripts/cu66-v106/bundle_manifest.py --verify
```

## Qualification still required

The comparison clock is fixed at **100 MHz**; no relaxed clock, false path, waiver or validation deletion supplies a pass. Setup/hold/pulse-width and legality must be assessed from the actual route, together with the retained methodology/DRC/CDC findings. Even an internal OOC timing pass does not supply missing parent clock-source/boundary, I/O or full-system constraints. Single-route measurements do not establish timing robustness across implementation seeds. The [remaining timing plan](remaining-timing-plan.md) pins the earlier closure cones and concrete next experiments; the actual final routed report must govern their priority.

Hardware remains on another system. Parent/board timing, whole-device external-memory service and arbitration, transport/clock-domain integration, complete custom-path integration, **sustained hardware 30 fps** and **validated complete FPGA decoding below 10 ms** remain open. No achieved-Fmax or hardware test is claimed.
