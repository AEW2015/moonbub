# V125 complete functional results

All four stages pass with fresh candidate RTL execution. The [source-bound index](../../experiments/python-gamebub-v125/integration/results.json) has status `PASS_V125_TILE_FULL_FUNCTIONAL`; the [independent audit](../../experiments/python-gamebub-v125/audit/full-independent-v2.json) has status `PASS_INDEPENDENT_V125_FULL_FUNCTIONAL_AUDIT`. All 18 source/include origins and their exact order are bound to frozen V124, with only the admission alias replaced. Ten raw stdout/event/canonical/hash stream sets equal V124 directly. Public-cycle delta is **zero**.

Only `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv` changes, to [the V125 admission source](../../fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv). Three scalar predicate payload bits capture original full32 hidden/equality decisions on existing predecessor edges. Group equality captures at the completed-tag edge after the original GROUP_BEGIN min expression registers its end. Verification-only full-key owners do not belong to the production datapath. No original assertion or require body is removed, no public cycle is added, and no synthesis attribute is added. The unchanged V124 producer retains exactly its existing two source KEEP bits; this is not a claim that routed KEEP properties are TRUE or that physical cones are isolated. V123 scratch, V121 queue, all other origins, parameters and interfaces remain unchanged.

| Evidence | SHA256 |
| --- | --- |
| Admission source | `2f65ff770775404071e383890c75549ccb08ec9998993c86f1662cfed65d71eb` |
| Lossless three-fragment packaging | `96c4683277db3d2ddf8bc710af2808b09949b9e9ba6979d9c3f43eb7be154144` |
| Production recipe | `d811713b4b467acc7aa66faa640477285443a6689ad6641a9e6b549091fa3dbd` |
| Verification recipe | `fd5acdb803a59614d6de433a8856c4924aafac6f4f63981f48ce2ed94fbd841d` |
| V124 comparison index | `9514c117b7a3769babb3cb4bc9b1c6b4bf355212203c710695696b7b63fcf33f` |
| Selected V125 index | `a06d14b48b89e672aa74c7675d21365cbf64e831f9327f4678e7ec7aee15e987` |
| Independent full functional audit | `61c343b82cc12604e989380ffe415820e09ad0dfd5cfd71b7ebb91c7e5cf6a75` |
| Independent focused audit | `89e9b3b66e220bde38cf0fdf2e8bc4eaf83685c1c140a17bf632797c8cd542b9` |

## Selected receipts

Selectors and actual receipt paths are both pinned in the index. Every attempt is retained.

| Stage | Selected receipt | SHA256 |
| --- | --- | --- |
| focused | [20261110T060144640227Z](../../experiments/python-gamebub-v125/tile/attempts/20261110T060144640227Z/receipt.json) | `4ec296015f29a2f20a202a132077abef6d95207b91e43fe0a39355a0ad89cd69` |
| parent | [20261110T063334084983Z](../../experiments/python-gamebub-v125/integrated-study/live-guard/attempts/20261110T063334084983Z/receipt.json) | `764c3e3492975112f73ecfa4b9165c412237cf25173d0ff064895192a06910bf` |
| peer | [20261110T061418813782Z](../../experiments/python-gamebub-v125/integrated-study/control-peer/attempts/20261110T061418813782Z/receipt.json) | `bcf4d559883e96a5a70c3496858b53ab020df2ad63e7cc60de8701682057e47a` |
| spatial | [20261110T061418579688Z](../../experiments/python-gamebub-v125/integrated-study/spatial/attempts/20261110T061418579688Z/receipt.json) | `675ac887d1b180796be2282eb72aa0853f3c64b15685b099efc24aca9db6f649` |

| Stage | Source hash entries | Artifact hash entries |
| --- | ---: | ---: |
| focused | 68 | 100 |
| spatial | 97 | 99 |
| peer | 102 | 96 |
| parent | 108 | 121 |

Hash-map sizes count evidence entries rather than distinct tests or gameplay frames. Four full integration runners, the focused runner and both auditors have reversible derivations. Every Verilator build retains `--assert -Wall` with no warning downgrade. Executable builds and the actual transport adapter retain strict C++17/-O2/-Wall/-Wextra/-Werror; the frozen v97_forward library-only exception is explicit. Earlier owner/rank/bounds/queue receipts and their original semantic/source/artifact checks remain pinned and independently checked; they do not replace the new candidate runs.

## Preserved auditor correction

The frozen first auditor (`04cb427113091fc2eba1b06c71fe0564658a1eb6e8eac0de22ff2cbb5f5d5e6f`) stopped at an incorrect comparison between the parent’s complete 24-file order and the decoder’s 18-file order. The [retained failure](../../experiments/python-gamebub-v125/audit/full-independent-initial-failure.json) includes actual/baseline/expected lists and the old comparison. Root approved a [new v2 auditor](../../scripts/cu66-v125/audit_functional_v2.py), source SHA `d32422e163a841f3114d891bca65054f70b82b4412d3ec4a294eca0c7456552d`, with a [single reversible hunk](../../experiments/python-gamebub-v125/audit/full-independent-v2-derivation.json), SHA `a5c8be27f2307c84baa3b528879ed3495f67612ca5d084063cd4b8bb64afb3f6`. It checks the exact core18 prefix and each complete mapped V124 stage order, including all six unchanged parent wrappers. No frozen auditor, source, receipt, fixture, assertion or oracle changed; passing RTL was not rerun. The selected independent full result is explicitly `full-independent-v2.json`.

## Focused scalar, source pair and actual controller

Scalar and generic seeds are 125501/125502; actual controller seeds are 125601/125602. Each scalar run executes 8309 tile values × four planes × seven group-end choices = 232652 boundary cases plus 65536 random full32 cases, or 298188 total. Each executes 596376 holds, 2087316 cancellation checks covering every nonzero reset/start/abort combination per case, eight extracted terminal-call transitions including plane-three wrapping behavior, and 5665589 actual clocks. High-bit, plane-three, hidden/terminal/group-true and unsigned32-plus16-wrap counts are positive in both seeds. This is lossless production scalar/task/call extraction, not arbitrary original-controller coordinate reachability. The original GROUP_BEGIN unsigned32-min expression is byte-identical; its registered end and later current-versus-old-end capture are checked separately in real source-pair transitions.

Each prepared source-pair campaign executes 411 contexts, 852 semantic clocks plus 411 real predecessor primers = 1263 physical clocks, 189 cancellation contexts, 19 follow-up consumes, three malformed contexts and two speculative mode writes that survive the later original error8. All 33 original states retain all seven cancellation overlaps. All nine predecessor categories are observed. Writers 0–6 have first-consume coverage; plane-clear writer7 is honestly counted as overwritten before consume, while GROUP_BEGIN category8 only invalidates ownership. No new predicate or owner is forced. Prepared-domain clocks are explicitly separate from natural packet cycles.

The complete V122 bounds→header-match→owner→legacy chain remains: 540 owned mode-bound cases, 25344 boundary cases/294 cancellations, 67664 full35 header cases including 65536 random and 4096 owned consumes, 36 natural packets plus 36 retries, 135328 header idle holds, 16384 random full32 bounds cases and 56 bounds cancellations per seed. Quant/header/scale preparation retains 348673/738933/40585 edges. All independent coordinate/quant/scale/mode replays pass.

| Generic seed | Old mode semantic cases | Original mode clocks | Added real mode primers | Actual mode clocks | Total primers incl. campaign | Natural monitored clocks | Prepared monitored clocks | Total monitored clocks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 125501 | 158228 | 158230 | 40879 | 199109 | 41290 | 13637393 | 200370 | 13837763 |
| 125502 | 158228 | 158230 | 40891 | 199121 | 41302 | 13635637 | 200382 | 13836019 |

Raw primer traces contain every sequential real MODE_BIT writer8→GROUP_TILE10 edge. The old 158230-clock component is preserved explicitly; the new raw mode total includes all measured primer edges. The source-pair monitor holds/consumes/writer/overwrite/cancellation arrays and complete scalar truth-domain counts are retained in the selected focused receipt and independent focused audit.

Actual controller seeds each execute 11 frozen vectors, two profiles, 22 case rows, 12 directed checks, 4058368 dense comparisons, 913984 directed dense comparisons and 63412 tile rows. Whole public/private/raw-scale pairs, exact coefficient/mapped tuples, request/ACK accounting, accepted-write draining and clean retries retain every original oracle.

## Complete decoder, actual transport and peer

Decoder seeds 107601/107602 execute 44 case profiles and 42 directed checks in total. Each retains 11 vectors/two configurations, 4,058,368 dense, assembly, dequant and residual comparisons, 1,436,969 directed dense comparisons and 63,412 tile rows. Canonical comparisons are 7,084,797/7,084,793 respectively; clock edges are 23,199,700/23,191,806. All original elastic held/fence/error/drain checks remain and stdout, accepted events, cycles and canonical artifacts equal V124 exactly.

The elastic checks remain explicit:

| Decoder seed | Fence checks | Held checks | Accepted/delivered/discarded |
| --- | ---: | ---: | --- |
| 107601 | 2,219,406 | 10,315,235 | 5,495,337 / 5,495,335 / 2 |
| 107602 | 2,214,517 | 10,312,399 | 5,495,337 / 5,495,335 / 2 |

Actual V97 transport seeds 107601/107602 each pass 12 successful profiles, two abort/reset retries and 16 public accepted/registered-delivered/poisoned command tuples. Each retains 16 wrong completion-token and 16 wrong DMA-token cases, 17,246 held-ACK cycles, 16 source stalls, 147,558 sink stalls, at most two descriptors and 2,048 FIFO/reserved bytes. Clock edges are 19,195,936/19,198,071. The actual V97 model and strict host adapter execute; neither a software transport substitution nor source-name-only qualification is used. All raw streams equal V124.

Peer seeds 115501/115502 each retain eight directed checks/eight child canonical retries, 14 prepared child fault injections, two accepted-write/four accepted-read/two queued-replay cases, and six real-parent pending-cancel cases (three abort and three reset), with six parent retries and 14 total canonical retries. Parent stage mask is `0x7`; eight local cancel edges, three parent private-cancel edges and 11 total local cancel edges are retained. Clock edges are 15,562,880/15,563,413. Existing physical-owner/held/error/drain assertions and the original injection contract remain; all stdout/event/canonical bytes and cycles equal V124.

The ten independent exact stream sets are four complete decoder/transport sets, two peer sets and four parent sets. The expanded six-row V113 canonical-golden hash remains `6d4e956a413d23d3945d30419c19dcb065423bfe486ea37506361cb0d9c73097`; complete-component canonical-actual TSV raw hash remains `a9f796047cc725a19e14dfae7bed75a57735e4c6d12def28ade7b98e99f8a861`.

## Guarded parent and unchanged modeled latency

Both byte and row variants pass fast/stalled seeds 116701/116702. All six terminal dictionaries and every raw stdout/event/actual/hash stream equal V124, including their cycles. Every profile retains 518,400 canonical bytes, 42,240 HUD bytes, 560,640 delivered/ACKed/hash bytes, 1,025 hash jobs, two directed checks, one observed wrong-token ACK with owned-write draining, and clean retry without reset. Byte requests/ACKs are 560,640 each; row requests/ACKs are 70,080 each, representing eight bytes per row request. The abstract service has a 16-bit bus and one pending physical-service request. Hash-kind counts remain `[508,4,511,1,1]` and maximum ownership remains one slot for byte/three for row.

Parent guard checks equal total clock edges: byte fast/stalled 3,938,310/9,737,801 and row fast/stalled 1,378,719/1,807,173. Every profile observes 33,384 raw local reads and matching responses, zero final pending reads, a one-edge parent-fault gap and at most one private residual handshake. Original cancel checks remain; internal work and physical responses are not masked to satisfy them.

The independent C2 root remains `d918803829f69e61f9743eb94cfad209c74b203099c995aaa5c24984e3b555b9`, HUD SHA `3aedb933fbc4fbbe7ca2a2fa6a0ad44582f3d1745b108945da0d2e10b0f2175f` and seal `a6a785a850784b3c4a7b145563412df6ff7bfcbb45128cf00daf9f29423f9ee1`. Actual C2/hash/seal validation uses the retained software HUD decode and abstract finite service; it is not a physical SDRAM or full-RTL HUD-decoder result.

Accepted-last-input-to-validated-commit counts are unchanged:

| Abstract service | Fast cycles | Stalled cycles | Delta versus V124 |
| --- | ---: | ---: | ---: |
| Byte | 3,704,705 | 9,484,147 | 0 |
| Row | 1,145,104 | 1,553,197 | 0 |

At an assumed complete-parent 125 MHz, the row counts project to 9.160832/12.425576 ms. Strictly below 10 ms still requires 303,198 fewer stalled cycles. This source change saves no public cycles. The measurement begins at accepted last input, not capture, first input, network arrival or start; it does not establish end-to-end display latency. A complete-parent 125 MHz clock is not physically qualified by these simulations. Routed component timing is a separate gate.

## Resource scope and limits

All selected V125 stages pass on their first attempts; no V125 resource stop or retry is hidden. Each controlled job retains 2 CPUs, 8 GiB RAM and 8 GiB RAM-plus-swap, compiler job1, unchanged launch/live memory, combined-use, PSI and finite host/tool watchdogs. Peer and spatial launched together after focused independent PASS with no known outside heavy process, 25596121088 available bytes, full PSI0 and combined use0.302478976. Spatial seeds stayed serial. Parent launched as one serial byte/row job with one observed external Vivado (actual PID749975), 23801913344 available bytes, full PSI0 and combined use0.350507698. The focused launch also observed one external Vivado. These are dispatch observations; unmanaged jobs can appear later and the study cannot enforce a host-wide reservation. No unrelated job was stopped or modified. Historical V124 stopped attempts and their resource transcripts remain unchanged as retained evidence; they are not V125 attempts.

These finite repeated golden/profile fixtures do not establish sustained distinct gameplay frames. Actual ESP32 CPU/Wi-Fi/QSPI, physical memory service/calibration, complete-board timing/CDC, hardware30fps and validated hardware decode below10ms remain separate. Native routed timing is a separate gate. Qualified Source B100 remains the hardware-integration control; these results do not promote V125 to a clock-qualified production endpoint. Separate endpoint/JPEG/model work is excluded from these functional source/proof globs.
