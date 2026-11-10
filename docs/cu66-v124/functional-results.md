# V124 complete functional results

All four stages pass with fresh candidate RTL execution. The [source-bound index](../../experiments/python-gamebub-v124/integration/results.json) has status `PASS_V124_OWNER_FULL_FUNCTIONAL`; the [independent audit](../../experiments/python-gamebub-v124/audit/full-independent.json) has status `PASS_INDEPENDENT_V124_FULL_FUNCTIONAL_AUDIT`. The source contract checks all 18 source/include origins and their order. The independent audit verifies selected source/artifact closure, the producer-only change, retained assertions/oracles and ten raw stdout/event/canonical/hash stream sets directly against frozen V123. Public-cycle delta is **zero**.

Only alias `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv` changes, to [the V124 producer](../../fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv). The two combinational owner-result bits have the approved KEEP attribute. The independent audit verifies that exact scope: one `keep = "true"` declaration on `logic [1:0] tile_owner_match`, no removed synthesis attributes and no other added directive. No new register or public cycle is introduced. V123 scratch rank, its packaging, V122 admission bounds and split packaging, V121 queue, the other origins, parameters and public interfaces remain unchanged.

| Evidence | SHA256 |
| --- | --- |
| Producer source | `963b46c3449d3a31e5ae85763f0681c6e68156c8d8c2c4c330d834ed2554fb53` |
| Single-module packaging | `85e2ffc9b3e0cb2de6526ff32434a584f025cdd059dab2f97f38c7ee3baf9e74` |
| Producer edit recipe | `ea3a47f12e476a1c52c374a9d678f36c314080e4e75e4bb1732c75c344ff50d0` |
| V123 comparison index | `0a665162168f4aaa9bff29546263d57b61abbef50bb65fefc2606de919f15d00` |
| Selected V124 index | `9514c117b7a3769babb3cb4bc9b1c6b4bf355212203c710695696b7b63fcf33f` |
| Independent functional audit | `34f81e238b0457c193bb3c2e180d9ba3899724b3e64f54eb721ec0683f714bb5` |

## Selected receipts

The index pins both selectors and their resolved receipts. These are the selected receipt pins; every attempt directory is retained.

| Stage | Selected receipt, UTC attempt | SHA256 |
| --- | --- | --- |
| focused | [20261110T040103948600Z](../../experiments/python-gamebub-v124/owner/attempts/20261110T040103948600Z/receipt.json) | `0a807acc5de0e3d44ed09b22848d58badbfbd8467cacb6aef3aebe5ef1f33e01` |
| spatial | [20261110T041257339298Z](../../experiments/python-gamebub-v124/integrated-study/spatial/attempts/20261110T041257339298Z/receipt.json) | `babedf199182efa369ac31ca6959002d0e4c41cc81e9e856f9dd84c891b53228` |
| peer | [20261110T041257454468Z](../../experiments/python-gamebub-v124/integrated-study/control-peer/attempts/20261110T041257454468Z/receipt.json) | `a3aceccbec2fca85d135bc0b049388f6a7413e7a73b7dba9000f2edbf171cb54` |
| parent | [20261110T043423394427Z](../../experiments/python-gamebub-v124/integrated-study/live-guard/attempts/20261110T043423394427Z/receipt.json) | `9585b02e8e7c710a4a35732d39b4f57af9c5d3a842f14d00dbdf0ed8c1cd8a7b` |

| Selected stage | Source hash entries | Artifact hash entries |
| --- | ---: | ---: |
| focused | 37 | 47 |
| spatial | 88 | 91 |
| peer | 93 | 88 |
| parent | 97 | 111 |

These counts describe hash maps, not distinct tests or gameplay frames. The independent audit also preserves the earlier V123 rank and V122 bounds semantic checks and their source/artifact pins. All four integration runners and both independent auditors have recorded forward/reverse derivations. Every Verilator compile uses `--assert -Wall`, without warning downgrades. Executable builds and the separate transport adapter retain strict C++17/-O2/-Wall/-Wextra/-Werror flags. The frozen generated v97_forward library-only exception remains explicit. No older execution substitutes for V124 candidate execution.

## Focused producer and actual caller

Generic seeds 124101/124102 each pass the complete inherited cache/nonce checks and three retained raw terminal dictionaries. Per seed, the inherited ready checks retain 2,048 prepared counter cases, 14,892 cache beats, 13 preloads, 12,838 scale commits and 19 start attempts. Public comparisons are 60,515/60,377 and clock edges 16,564/16,518 respectively. The inherited owner oracle retains 9,216 cases plus 250,000 randomized cases; 2,176 accepted cases, 6,966 reason64 cases and 74 reason66 cases remain exact.

Each generic seed also passes all new owner-lane dimensions:

| Owner-lane coverage | Per seed |
| --- | ---: |
| Wire cases | 466,944 |
| Randomized full-width cases | 65,536 |
| State cases | 8,192 |
| Mode/bank-ready/guard masks | `0xF` each |
| Emit-bank mask | `0x3` |
| Invalid-context ready-true cases | 9,856 |
| Unready-context ready-true cases | 1,792 |
| Clocked cases | 1,152 |
| Error67 cases | 192 |
| Cancel cases | 864 |
| Wrap cases | 16 |
| Held edges | 336 |
| Response contexts | 224 |
| Added public cycles/error-cycle delta/skipped pair edges/removed checks | 0 each |

These prepared-domain cases are explicitly not natural packet reachability claims. Complete full32 epoch/full16 block tuples, invalid/unready cycles and the non-tile fallback are retained; matching only a valid-bank subset is insufficient. Source/wrapper/fixture recipes reconstruct in both directions, all original assertion blocks remain, and inherited need/require/require_owner expressions are retained.

Actual controller seeds 124201/124202 each execute 11 frozen vectors, two profiles, 22 case rows and 12 directed checks. Each retains 4,058,368 dense comparisons, 913,984 directed dense comparisons and 63,412 tile rows. Every case passes the original whole public/private/raw-scale pair comparisons, exact coefficients/mapped tuple fields, request/ACK accounting and final no-pending-drain checks.

## Complete decoder, actual transport and peer

Decoder seeds 107601/107602 execute 44 case profiles and 42 directed checks in total. Each retains 11 vectors/two configurations, 4,058,368 dense, assembly, dequant and residual comparisons, 1,436,969 directed dense comparisons and 63,412 tile rows. Canonical comparisons are 7,084,797/7,084,793 respectively; clock edges are 23,199,700/23,191,806. All original elastic held/fence/error/drain checks remain and stdout, accepted events, cycles and canonical artifacts equal V123 exactly.

The elastic checks remain explicit:

| Decoder seed | Fence checks | Held checks | Accepted/delivered/discarded |
| --- | ---: | ---: | --- |
| 107601 | 2,219,406 | 10,315,235 | 5,495,337 / 5,495,335 / 2 |
| 107602 | 2,214,517 | 10,312,399 | 5,495,337 / 5,495,335 / 2 |

Actual V97 transport seeds 107601/107602 each pass 12 successful profiles, two abort/reset retries and 16 public accepted/registered-delivered/poisoned command tuples. Each retains 16 wrong completion-token and 16 wrong DMA-token cases, 17,246 held-ACK cycles, 16 source stalls, 147,558 sink stalls, at most two descriptors and 2,048 FIFO/reserved bytes. Clock edges are 19,195,936/19,198,071. The actual V97 model and strict host adapter execute; neither a software transport substitution nor source-name-only qualification is used. All raw streams equal V123.

Peer seeds 115501/115502 each retain eight directed checks/eight child canonical retries, 14 prepared child fault injections, two accepted-write/four accepted-read/two queued-replay cases, and six real-parent pending-cancel cases (three abort and three reset), with six parent retries and 14 total canonical retries. Parent stage mask is `0x7`; eight local cancel edges, three parent private-cancel edges and 11 total local cancel edges are retained. Clock edges are 15,562,880/15,563,413. Existing physical-owner/held/error/drain assertions and the original injection contract remain; all stdout/event/canonical bytes and cycles equal V123.

The ten independent exact stream sets are four complete decoder/transport sets, two peer sets and four parent sets. The expanded six-row V113 canonical-golden hash remains `6d4e956a413d23d3945d30419c19dcb065423bfe486ea37506361cb0d9c73097`; complete-component canonical-actual TSV raw hash remains `a9f796047cc725a19e14dfae7bed75a57735e4c6d12def28ade7b98e99f8a861`.

## Guarded parent and unchanged modeled latency

Both byte and row variants pass fast/stalled seeds 116701/116702. All six terminal dictionaries and every raw stdout/event/actual/hash stream equal V123, including their cycles. Every profile retains 518,400 canonical bytes, 42,240 HUD bytes, 560,640 delivered/ACKed/hash bytes, 1,025 hash jobs, two directed checks, one observed wrong-token ACK with owned-write draining, and clean retry without reset. Byte requests/ACKs are 560,640 each; row requests/ACKs are 70,080 each, representing eight bytes per row request. The abstract service has a 16-bit bus and one pending physical-service request. Hash-kind counts remain `[508,4,511,1,1]` and maximum ownership remains one slot for byte/three for row.

Parent guard checks equal total clock edges: byte fast/stalled 3,938,310/9,737,801 and row fast/stalled 1,378,719/1,807,173. Every profile observes 33,384 raw local reads and matching responses, zero final pending reads, a one-edge parent-fault gap and at most one private residual handshake. Original cancel checks remain; internal work and physical responses are not masked to satisfy them.

The independent C2 root remains `d918803829f69e61f9743eb94cfad209c74b203099c995aaa5c24984e3b555b9`, HUD SHA `3aedb933fbc4fbbe7ca2a2fa6a0ad44582f3d1745b108945da0d2e10b0f2175f` and seal `a6a785a850784b3c4a7b145563412df6ff7bfcbb45128cf00daf9f29423f9ee1`. Actual C2/hash/seal validation uses the retained software HUD decode and abstract finite service; it is not a physical SDRAM or full-RTL HUD-decoder result.

Accepted-last-input-to-validated-commit counts are unchanged:

| Abstract service | Fast cycles | Stalled cycles | Delta versus V123 |
| --- | ---: | ---: | ---: |
| Byte | 3,704,705 | 9,484,147 | 0 |
| Row | 1,145,104 | 1,553,197 | 0 |

At an assumed complete-parent 125 MHz, the row counts project to 9.160832/12.425576 ms. Strictly below 10 ms still requires 303,198 fewer stalled cycles. This source change saves no public cycles. The measurement begins at accepted last input, not capture, first input, network arrival or start; it does not establish end-to-end display latency. A complete-parent 125 MHz clock is not physically qualified by these simulations. Routed component timing is a separate gate.

## Retained resource stop and fresh retry

The [first parent attempt](../../experiments/python-gamebub-v124/integrated-study/live-guard/attempts/20261110T043102723610Z/receipt.json) stopped during byte compilation, before any RTL simulation. Its SHA256 is `d9e8ad3fdea2d39d3c53672d2146180233ae2a37e24270159e286eda3d37dd51`; complete attempt duration is 41.809079522 seconds. The live full-memory PSI gate observed avg10 5.09 in consecutive samples at 36.351531499/37.807914820 seconds. At the stop, available memory was 16,203,354,112 bytes and combined RAM-plus-swap use was 0.548335097. This was a resource-watchdog stop, not an RTL verdict.

The failed receipt retains 97 source and 90 artifact hash entries. The [resource samples](../../experiments/python-gamebub-v124/integrated-study/live-guard/attempts/20261110T043102723610Z/byte-compile.log.resources.jsonl), [compiler transcript](../../experiments/python-gamebub-v124/integrated-study/live-guard/attempts/20261110T043102723610Z/byte-compile.log) and [stop transcript](../../experiments/python-gamebub-v124/integrated-study/live-guard/attempts/20261110T043102723610Z/byte-compile.log.stop.log) are retained. Unrelated external Vivado work was observed during the pressure period; causality was not established. No unrelated job was stopped or modified.

After those initial external Vivados exited and launch gates recovered, Root authorized one fresh unchanged-source parent retry, alongside an external Python audit. It launched with 25,533,964,288 available bytes, full PSI 0 and combined use 0.298526692. That selected attempt passed. The same 2-CPU/8-GiB RAM/8-GiB RAM-plus-swap limits, strict flags and live watchdogs remained; no source, fixture, assertion or gate was changed. Later external Vivados could appear after the reservation, so the reservation was not an enforceable host-wide concurrency limit. Only the single already-granted Gamebub parent job continued. Source/artifact maps were rehashed, and all 97 retained source copies in both failed and selected parent attempts additionally matched their source pins.

These are finite repeated golden/profile fixtures, not sustained distinct gameplay frames. Actual ESP32 CPU/Wi-Fi/QSPI, physical memory timing/service, complete-board timing/CDC, hardware 30 fps and validated hardware decode below 10 ms remain separate. The separate JPEG endpoint/probe work is not part of this component qualification or its source/proof globs. Qualified Source B100 remains the hardware-integration control; these functional results do not promote V124 to a clock-qualified or production endpoint.
