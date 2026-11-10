# V126 complete functional results

All four stages pass with fresh candidate RTL execution. The [source-bound index](../../experiments/python-gamebub-v126/integration/results.json) is `PASS_V126_PRODUCER_FULL_FUNCTIONAL`; the [independent full audit](../../experiments/python-gamebub-v126/audit/full-independent.json), executed by the explicitly derived v3 auditor, is `PASS_INDEPENDENT_V126_FULL_FUNCTIONAL_AUDIT`. Ten raw stream sets equal frozen V125 directly: four decoder/actual-transport sets, two peer sets and four byte/row parent sets. Public-cycle delta is **zero**. Functional PASS does not establish routed timing closure.

Only the producer alias `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv` changes to [the V126 producer](../../fpga/experiments/cu66-v126-producer/cs88_coefficients_v91k.sv). All other 17 selected source/include origins and their order equal V125. The decoder and peer retain the exact 18-source order; the parent retains its exact 24-source order, including six unchanged wrappers. Two payload registers declare 13 successor-address bits and 11 successor-cell bits. They capture on existing PREP/MAP_REQ/advance edges; same-edge public consumption and original error priority remain. These 24 logical bits are not a prediction of 24 physical mapped flip-flops. New address/cell ownership keys are verification-only.

V125 admission predicates and their lossless three-fragment packaging, V123 scratch, V121 queue, all original assertions, interfaces and parameters remain unchanged. No new synthesis attribute is added. The producer retains exactly its two existing combinational source KEEP bits; this is not a claim that routed KEEP properties are TRUE or that physical timing cones are isolated.

| Evidence | SHA256 |
| --- | --- |
| Producer source | `5dec7454e6bfae4f7a9d7f64ecfbef8568665ddaa2dc00d4a76de1167a3c7292` |
| Single-module lossless packaging | `96d41ba538d6f2ac56f0301820824b173ddeba05ce585401474129342df3320a` |
| Production derivation | `ff67493404afe0563833793b24c8d84bffd2d43fb3e2cba434991d7fc1941235` |
| Selected verification recipe | `419617eca2263965c6c81403ba4fa77fae750b8cbb6b328c0be4b23a2be6d598` |
| V125 comparison index | `a06d14b48b89e672aa74c7675d21365cbf64e831f9327f4678e7ec7aee15e987` |
| Selected V126 index | `7d534c343732bc50786bff874c9b6d536bceaa6298fc5e7f002d98b5216e732f` |
| Independent full functional audit | `82e612b68473985381a283f7c084514eea9f219758e9dcf204f8cee7d484ff07` |
| Independent focused audit | `c4137c64b15b84dbce24f70ce6c6bac774e8ebbddde371fbce7dc5ca86eb083b` |
| Executed v3 auditor | `c7efaad7328ad5bc5754ba332420e6006bf76652da660e7d01ae55777f655d42` |

## Selected receipts and exact comparisons

The index pins selectors and actual selected receipt paths separately. Hash-map sizes count evidence entries, not distinct tests or gameplay frames.

| Stage | Actual selected receipt | SHA256 | Sources / artifacts |
| --- | --- | --- | ---: |
| focused | [20261110T142915604891Z](../../experiments/python-gamebub-v126/producer/attempts/20261110T142915604891Z/receipt.json) | `b3a18c18b617bdd5085b86f90f15bae8208f4eafdb85752b830158ff43abe133` | 45 / 69 |
| spatial | [20261110T144445374480Z](../../experiments/python-gamebub-v126/integrated-study/spatial/attempts/20261110T144445374480Z/receipt.json) | `53c40c4703f0f15281b3a1829f7874f1aad210c556c846a9d1a5772c8c94e1b0` | 104 / 105 |
| peer | [20261110T144445693279Z](../../experiments/python-gamebub-v126/integrated-study/control-peer/attempts/20261110T144445693279Z/receipt.json) | `4ee6eefb27e3c2e0b979f83d8f44166469e3d9ff2b50727fde348b35eb26e596` | 109 / 102 |
| parent | [20261110T150311884448Z](../../experiments/python-gamebub-v126/integrated-study/live-guard/attempts/20261110T150311884448Z/receipt.json) | `37bd6c7d608c4f401292ddc731ca50f9efb880d79c2f76ed74e087d3165dbd48` | 115 / 127 |

All retained V125 tile, V124 owner, V123 rank, V122 bounds and V121 queue source/artifact/semantic checks are independently audited alongside the new producer proof. They do not substitute for fresh V126 candidate runs. Complete stdout, accepted event, canonical and parent actual/hash payloads are compared after decompression, including their cycle fields. Original canonical goldens, physical-debt checks, HUD/C2/seal checks and error ordering remain. The complete parent order is compared to the mapped V125 parent order, preserving the corrected 18-versus-24 source distinction.

## New producer and retained focused coverage

Scalar/generic seeds are 126501/126502; actual-controller seeds are 126601/126602. Each scalar seed checks all 8,192 tile values across four planes (32,768 exhaustive cases), plus 65,536 random cases: 98,304 total, 1,190,177 physical clocks, 294,912 hold edges and 1,120 cancellations covering four planes, eight boundary tiles, five phases and all seven nonzero reset/start/abort combinations. Successor-address wrap, plus-two wrap, plane-three behavior, 11-bit Y-cell truncation and canceled speculative ROM-value changes all have positive coverage. The wrapper extracts exact production function/task/ROM/call fragments, with an independent integer oracle. Arbitrary full13 geometry uses declared old-field scalar fixtures; it does not claim that the original controller reaches those states.

Each whole-source prepared campaign checks 534 contexts, 3,664 clocks = 1,428 actual predecessor primers + 2,236 other clocks, 24 earliest-response cases, 555 coherent skip advances, 21 held-child edges, 96 nonterminal advances, 288 reset/abort cases, 48 original bad-owner error67 cases, 72 stage overlaps, nine unowned malformed-bound cases, three empty-plane cases and three actual accepted-start cases. The odd Y walk reaches tile185/cell47, then consumes the distinct tile186/cell48. New payloads and ownership keys are never forced. Child physical debt is not erased; accepted-start fixtures assert that no physical request is outstanding before clearing their declared logical prepared lease. Original physical-response retirement and actual-caller ACK/drain oracles are retained.

Each primer trace has exactly 1,428 edges, split 510 PREP3→ALLOCATE4, 486 MAP_REQ9→MAP_WAIT10 and 432 MAP_WAIT10→DISPATCH11 edges across planes0–2. They are real writer clocks inside explicit prepared contexts, separate from natural packet cycles. The instrumented generic monitor counts exactly 275,334 edges = 271,670 inherited tick_owner edges + 3,664 campaign edges. Its event totals, complete owner keys, current-cache checks, captures, consumes, held values, earliest responses, blocked starts and revocation priorities retain strict checks. The original legacy cache Driver reports its own separate `edges` counter.

Each generic seed also retains 2,048 prepared cache-counter cases; more than 10,000 cache beats and 50,000 public comparisons; 9,216 V119 owner cases plus 250,000 random full32 nonce cases; and the complete V124 lane suite: 466,944 wire cases, 65,536 random fullwidth cases, 8,192 state cases, 1,152 clock cases, 192 error67 cases, 864 cancellations, 16 wrap cases, 336 held edges and 224 response contexts. Invalid/unready-ready contexts remain checked, and all mode/bank-ready/guard masks are15 with emitter mask3. Original-check-removal and added-cycle/error-cycle/skipped-edge counters remain zero.

Each actual-controller seed retains 11 frozen vectors, two profiles, 22 case rows, 12 directed checks, 4,058,368 dense comparisons, 913,984 directed dense comparisons and 63,412 tile rows. Both stages are observed through the unchanged full producer/child source pair, including earliest lookup responses, held outputs and accepted-start invalidation. Public/private/raw-scale comparisons, exact coefficients and mapped tuples, accepted requests/ACKs, physical draining and clean retries retain every original oracle.

The separate inherited V125 tile proof remains source-bound to admission SHA `2f65ff770775404071e383890c75549ccb08ec9998993c86f1662cfed65d71eb`. Its full32 scalar/terminal-call proof, 411-context actual-source campaign, measured mode primers and every older bounds/header/coordinate/quant/scale/mode replay remain independently checked. No new producer fixture replaces these admission proofs.

## Retained failures, diagnostics and independent-auditor corrections

The selected focused proof is the fourth official fresh attempt. Earlier official attempts remain immutable: [attempt1](../../experiments/python-gamebub-v126/producer/attempts/20261110T135405341398Z/receipt.json) failed before Docker because the runner omitted its inherited memory helper; [attempt2](../../experiments/python-gamebub-v126/producer/attempts/20261110T135558247917Z/receipt.json) passed scalar compilation but strict C++ compilation rejected misleading indentation; [attempt3](../../experiments/python-gamebub-v126/producer/attempts/20261110T140125927269Z/receipt.json) passed both scalar seeds and inherited generic checks, then an original reference assertion rejected the new fixture’s incoherent child-bank poisoning. The repaired fixture changes only parent expected owner fields, preserving the child lease and the original error67-before-consume check. Production source stayed `5dec7454…` throughout. Exact before/after sources, recipes, logs and receipts are retained under [producer repair history](../../experiments/python-gamebub-v126/producer/repair-history/).

Two separate private-build diagnostic runs retain qualification=false: one exposed the one-edge observer-accounting mistake after all 534 campaign contexts passed, and the count-printing probe measured275334. A later diagnostic passed all five generic rows with original/model-cache integrity intact. These incremental copies never published qualification selectors. The final official selected attempt rebuilt both models freshly and reran all six prescribed scalar/generic/caller runs. The [independent arithmetic record](../../experiments/python-gamebub-v126/audit/full-independent-counter-repair-attempts/20261110T142603894228Z/repair.json) derives 268434 owner-main edges +2 wire-domain resets +3234 clocked-domain edges =271670; strict total equality remains275334. The [revision5 freeze](../../experiments/python-gamebub-v126/audit/full-independent-tooling-freeze-revision5.json) preserves all earlier freezes and repairs.

The first focused independent audit stopped on a reporting-only lookup of `clock_edges` in the unchanged baseline dictionary, whose actual key is `edges`. The [preserved failure](../../experiments/python-gamebub-v126/audit/full-independent-focused-attempts/20261110T144247594799Z/failure.json) records code SHA4aea6150…; the [new v2 derivation](../../experiments/python-gamebub-v126/audit/full-independent-v2-derivation.json) changes only that reporting lookup. Its independent focused audit passes. The first full v2 audit then rejected a misplaced new producer inventory count4 inside the unchanged inherited tile count5 function. The [preserved full failure](../../experiments/python-gamebub-v126/audit/full-independent-full-attempts/20261110T151358425960Z/failure.json) and [exact v3 movement](../../experiments/python-gamebub-v126/audit/full-independent-v3-derivation.json) retain both frozen auditors. V3 moves the count4 check into the producer function; the original tile function again matches V125 byte-for-byte, the strict producer count4 check remains, and the total need() call count is unchanged. Root approved both corrections. Passing RTL, fixtures, runners, selected receipts and proof-pinned inputs were not changed or rerun for either auditor correction. The [v3 supplemental freeze](../../experiments/python-gamebub-v126/audit/full-independent-tooling-freeze-v3-supplement.json) binds the executed auditor.

## Complete decoder, actual transport and peer

Decoder seeds 107601/107602 execute 44 case profiles and 42 directed checks in total. Each retains 11 vectors/two configurations, 4,058,368 dense, assembly, dequant and residual comparisons, 1,436,969 directed dense comparisons and 63,412 tile rows. Canonical comparisons are 7,084,797/7,084,793 respectively; clock edges are 23,199,700/23,191,806. All original elastic held/fence/error/drain checks remain and stdout, accepted events, cycles and canonical artifacts equal V125 exactly.

The elastic checks remain explicit:

| Decoder seed | Fence checks | Held checks | Accepted/delivered/discarded |
| --- | ---: | ---: | --- |
| 107601 | 2,219,406 | 10,315,235 | 5,495,337 / 5,495,335 / 2 |
| 107602 | 2,214,517 | 10,312,399 | 5,495,337 / 5,495,335 / 2 |

Actual V97 transport seeds 107601/107602 each pass 12 successful profiles, two abort/reset retries and 16 public accepted/registered-delivered/poisoned command tuples. Each retains 16 wrong completion-token and 16 wrong DMA-token cases, 17,246 held-ACK cycles, 16 source stalls, 147,558 sink stalls, at most two descriptors and 2,048 FIFO/reserved bytes. Clock edges are 19,195,936/19,198,071. The actual V97 model and strict host adapter execute; neither a software transport substitution nor source-name-only qualification is used. All raw streams equal V125.

Peer seeds 115501/115502 each retain eight directed checks/eight child canonical retries, 14 prepared child fault injections, two accepted-write/four accepted-read/two queued-replay cases, and six real-parent pending-cancel cases (three abort and three reset), with six parent retries and 14 total canonical retries. Parent stage mask is `0x7`; eight local cancel edges, three parent private-cancel edges and 11 total local cancel edges are retained. Clock edges are 15,562,880/15,563,413. Existing physical-owner/held/error/drain assertions and the original injection contract remain; all stdout/event/canonical bytes and cycles equal V125.

The ten independent exact stream sets are four complete decoder/transport sets, two peer sets and four parent sets. The expanded six-row V113 canonical-golden hash remains `6d4e956a413d23d3945d30419c19dcb065423bfe486ea37506361cb0d9c73097`; complete-component canonical-actual TSV raw hash remains `a9f796047cc725a19e14dfae7bed75a57735e4c6d12def28ade7b98e99f8a861`.

## Guarded parent and unchanged modeled latency

Both byte and row variants pass fast/stalled seeds 116701/116702. All six terminal dictionaries and every raw stdout/event/actual/hash stream equal V125, including their cycles. Every profile retains 518,400 canonical bytes, 42,240 HUD bytes, 560,640 delivered/ACKed/hash bytes, 1,025 hash jobs, two directed checks, one observed wrong-token ACK with owned-write draining, and clean retry without reset. Byte requests/ACKs are 560,640 each; row requests/ACKs are 70,080 each, representing eight bytes per row request. The abstract service has a 16-bit bus and one pending physical-service request. Hash-kind counts remain `[508,4,511,1,1]` and maximum ownership remains one slot for byte/three for row.

Parent guard checks equal total clock edges: byte fast/stalled 3,938,310/9,737,801 and row fast/stalled 1,378,719/1,807,173. Every profile observes 33,384 raw local reads and matching responses, zero final pending reads, a one-edge parent-fault gap and at most one private residual handshake. Original cancel checks remain; internal work and physical responses are not masked to satisfy them.

The independent C2 root remains `d918803829f69e61f9743eb94cfad209c74b203099c995aaa5c24984e3b555b9`, HUD SHA `3aedb933fbc4fbbe7ca2a2fa6a0ad44582f3d1745b108945da0d2e10b0f2175f` and seal `a6a785a850784b3c4a7b145563412df6ff7bfcbb45128cf00daf9f29423f9ee1`. Actual C2/hash/seal validation uses the retained software HUD decode and abstract finite service; it is not a physical SDRAM or full-RTL HUD-decoder result.

Accepted-last-input-to-validated-commit counts are unchanged:

| Abstract service | Ordinary cycles | Stalled cycles | Ordinary / stalled projection at125MHz | Delta versus V125 |
| --- | ---: | ---: | --- | ---: |
| Byte | 3,704,705 | 9,484,147 | 29.637640 /75.873176 ms | 0 |
| Row | 1,145,104 | 1,553,197 | 9.160832 /12.425576 ms | 0 |

At an assumed complete-parent 125 MHz, the row counts project to 9.160832/12.425576 ms. Strictly below 10 ms still requires 303,198 fewer stalled cycles. This source change saves no public cycles. The measurement begins at accepted last input, not capture, first input, network arrival or start; it does not establish end-to-end display latency. A complete-parent 125 MHz clock is not physically qualified by these simulations. Routed component timing is a separate gate.

## Resource scope and limits

Peer, spatial and parent each pass their first V126 full-stage attempts; no full-stage resource stop or retry occurred. Each controlled heavy job uses two CPUs, compiler job1, **8GiB RAM and 8GiB total RAM+swap**. That total does not provide another8GiB of swap. Strict standalone Verilator5.020 retains --assert/-Wall, executable builds retain C++17/-O2/-Wall/-Wextra/-Werror, and the actual V97 library-only build plus strict separate g++ adapter exception is preserved. Launch/live available-memory, combined-use, PSI and finite host/tool watchdogs remain unchanged.

Peer and spatial launched together only after focused independent PASS, with25,471,496,192 available bytes, full PSIavg10=0 and combined use0.3010866417; no external Vivado or known heavy process was observed. Spatial decoder and transport seeds stayed serial. Parent launched after both terminal PASS, as one serial byte/row job, with25,314,758,656 available bytes, full PSIavg10=0 and combined use0.3055160970; no external Vivado or V126 heavy container was observed immediately before dispatch. These observations do not enforce a reservation against unrelated later work. No unrelated job was stopped or modified.

These finite repeated golden/profile fixtures do not establish sustained distinct gameplay frames. The modeled row projection does not qualify a complete-parent125MHz clock. Native routed component timing, complete-board timing/CDC, physical SDRAM/calibration, ESP32 CPU, Wi-Fi/QSPI, full-RTL HUD decode, hardware30fps and validated hardware decode below10ms remain separate gates. The endpoint starts at the accepted last outer input and ends at validated commit, rather than capture/network/first-input/display. Qualified SourceB100 remains the hardware-integration control; no V126 production-clock promotion follows from functional PASS. Separate endpoint/JPEG/model work is excluded from the functional source/proof globs.
