# V128 functional qualification

V128 passed fresh RTL simulation and the independent full functional audit. All **4 spatial, 2 peer, and 4 parent stream comparisons** match their frozen controls exactly, including public event cycles. This qualifies functional preservation of the selected timing-oriented RTL changes. Routed 125 MHz timing and sustained hardware streaming remain separate gates.

The selected composition has 18 core source origins: four raw-validation origins and one admission-padding origin changed from V127; 13 are unchanged. The parent suite compiles those 18 origins with six endpoint sources. The original production sources, all original assertion blocks and golden comparisons, and the qualified Source B handoff remain preserved. No hardware was contacted.

## What changed

The raw-validation path computes each complete raw/context tuple's validation before selecting the result, including epoch error classification. The stored scratch format remains independent of that selector. The admission path accumulates the twelve header-padding bytes into one unreset payload flag with current-byte forwarding. Both changes retain the original public scheduling and reject/error priorities.

The [selected composition](../../fpga/experiments/cu66-v128-raw/selected-composition.json) pins all five changed origins and the complete 18-origin closure. Its SHA-256 is `eb0c336ea235a926de03e74c7f34b364b84b611097291d8ff73f40e2bd5fdfed`.

## Fresh actual full-composition runs

| Suite | Seeds and configurations | Retained result |
| --- | --- | --- |
| Spatial canonical | 107601, 107602 | 44 case profiles and 42 directed checks; 2 exact stdout/event/cycle/canonical streams |
| Actual V97 transport → decoder | 107601, 107602 | 24 successful case profiles; 2 exact stdout/event/cycle/canonical streams |
| Peer fault / physical debt / replay | 115501, 115502 | Per seed: 14 canonical retries, 14 prepared-child fault injections, 6 real-parent pending-cancel cases; 2 exact streams |
| Parent byte and row endpoints | 116701/profile 0, 116702/profile 1, for each variant | 4 exact stdout and terminal stream sets, accepted bytes/events/hash cycles, C2/HUD/seal commitments and ownership checks |

The parent runs preserve 560,640 accepted canonical-plus-HUD bytes and 1,025 hash jobs each. Byte mode uses 560,640 write requests/ACKs; row mode uses 70,080. Both retain wrong-ACK draining and retry without reset, independent canonical/HUD goldens, and abstract publication checks.

All new models were compiled with assertions enabled, strict Verilator warnings, and the existing C++ warning/error flags. No seeds, checks, runtime monitors, model-cycle logic, or result oracles were removed. The independent auditor uses the hash-pinned V127 comparison helpers without mutating their namespace. It also rechecks the inherited V127 proof and the original 18-origin Source B handoff hashes.

| Receipt | SHA-256 |
| --- | --- |
| [Spatial](../../experiments/python-gamebub-v128/integrated-study/spatial/attempts/20261110T211442210430Z/receipt.json) | `176a59b9bc1875de20044cc82ba628e6368fed68cd7859babe834c25a348efaa` |
| [Peer](../../experiments/python-gamebub-v128/integrated-study/control-peer/attempts/20261110T213432554639Z/receipt.json) | `4b4c35274550da685d134808ae55d012938935bcf76e6a138865c88f8ba57bb7` |
| [Parent](../../experiments/python-gamebub-v128/integrated-study/live-guard/attempts/20261110T214331755905Z/receipt.json) | `d34981794448ab145469d1dca547269d9a683e1e5592777065263ef77f10bcbb` |
| [Full integration index](../../experiments/python-gamebub-v128/integration/results.json) | `57b48154c3e7beda86cfe347032e505841bcdb2d35e1b9e8e560f9d134848f20` |
| [Independent full audit](../../experiments/python-gamebub-v128/audit/full-independent.json) | `f36c365c68a54699cb6e25183b2f6be5aa2212101f775b2ea94d4e7dab01637c` |

Final statuses are `PASS_V128_RAW_FULL_FUNCTIONAL` and `PASS_INDEPENDENT_V128_FULL_FUNCTIONAL_AUDIT`. All four parent comparisons report `cycle_delta: 0`.

## Focused versus complete-model evidence

The [focused report](focused-results.md) records four raw seeds and two padding seeds, with their precise scope and retained first failures. Raw algebra covers 196,608 independently driven metadata cases and 1,572,864 phase checks per seed with **zero DUT clocks**. It is not a natural-packet reachability proof. The separate real scratch pair covers 74 public begin/memory/ACK/error/cancel contexts per seed without forcing private state.

Padding's two seeds each complete 7,268 headers using the extracted source writer/cache/consumer/error chain. That focused kernel is not the full admission FSM. The fresh spatial, peer, and parent suites above compile and exercise the actual admission FSM and all five changed origins together, providing the separate natural-caller composition evidence.

## Relation to 30 fps and under 10 ms

These changes deliberately preserve cycle counts. The following parent figures measure **last outer input acceptance to commit**, including the modeled endpoint work. Milliseconds are arithmetic conversions assuming a future timing-qualified 125 MHz clock; they are not measured hardware latency.

| Variant / finite service profile | Modeled cycles | Nominal time at 125 MHz |
| --- | ---: | ---: |
| Byte / 0 | 3,704,705 | 29.638 ms |
| Byte / 1 | 9,484,147 | 75.873 ms |
| Row / 0 | 1,145,104 | 9.161 ms |
| Row / 1 | 1,553,197 | 12.426 ms |

Row mode's **start-to-commit** figures are 1,183,316 and 1,601,561 cycles, or nominally 9.467 and 12.812 ms at 125 MHz. Thus the favorable row profile fits a 1,250,000-cycle/10-ms envelope; the delayed service profile exceeds it. Both row examples fit a nominal 33.333-ms frame period, but single-keyframe finite simulation does not prove sustained 30 fps.

Still required: routed timing closure for the selected implementation; the agreed decoder-latency frontier and its worst-case budget; sustained frame sequences with bounded real memory service; and measured ESP32 Wi-Fi/QSPI delivery, physical memory arbitration, buffering, display and input behavior. This functional proof contains no native Sunshine process, ESP32 instruction execution, physical SDRAM, or hardware throughput measurement.

## Retained failures and reviewed verification repairs

All failed attempts remain archived; none was promoted to PASS. Production RTL stayed unchanged throughout these repairs.

- The first raw focused model passed both algebra seeds but its driver read a stale combinational value after clearing abort/reset. The [raw repair](../../experiments/python-gamebub-v128/raw/repair-history/20261110T204235617984Z-drain-settle/repair.json) adds evaluation/checking without a DUT clock; a fresh model reran all four seeds.
- The first padding kernel compile stopped on three strict BLKSEQ warnings in its verification projection. The [padding repair](../../experiments/python-gamebub-v128/padding/repair-history/20261110T204309401260Z-BLKSEQ-projection/repair.json) corrects the temporary/view projection; a fresh model reran both seeds.
- The first full spatial/peer compiles stopped on DECLFILENAME because three modules were packaged under one filename. The [adapter repair](../../experiments/python-gamebub-v128/integration/repair-history/20261110T205652519422Z-lossless-module-packaging/repair.json) selects a separately checked, lossless three-file [compile package](../../fpga/experiments/cu66-v128-padding/compile-packaging.json). The historical production package and source maps remain unchanged, and strict warnings remain enabled.
- Seven full attempts stopped on host memory-pressure gates before compilation/simulation, including pressure immediately after Docker version checks. The [readiness repair archive](../../experiments/python-gamebub-v128/integration/repair-history/20261110T211205924738Z-finite-prelaunch-readiness/repair.json) retains all nine early full failures (seven pressure stops and two compile stops). Its bounded pre-command wait samples at two-second intervals for at most 120 seconds, then retains the original launch assertion. Launch thresholds, execution monitors, resource caps, seeds and oracles are unchanged. Successful final stages ran sequentially.

The [revision-4 full freeze](../../experiments/python-gamebub-v128/audit/full-functional-tooling-freeze-revision4.json) binds the final 86 inputs before these successful full runs. The initial and subsequent freezes, exact archived source bytes/patches, and independent repair reviews remain retained.
