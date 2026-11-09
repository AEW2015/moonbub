# V114 service-cycle results and remaining latency gap

The [primary ledger](../../experiments/python-gamebub-v114/performance.json) and
[optimized ledger](../../experiments/python-gamebub-v114/optimized/performance.json)
read the actual successful RTL transcripts and bind their hashes. Both
compositions reconstruct the frozen 720×480 canonical samples exactly. The
optimized candidate changes address preparation, not the number of decoder
service cycles; its canonical transcripts are identical to the primary ones.

| Memory-service profile | First input byte through component done, cycles | Conditional duration at 125 MHz |
| --- | ---: | ---: |
| Unstalled, 12 case/profile observations | 642,491–1,383,951 | 5.140–11.072 ms |
| Bounded randomized stalls, 12 observations | 1,761,386–2,466,887 | 14.091–19.735 ms |

The two seeds cover six canonical fixtures per profile. The minimum includes a
structural all-COPY case; it is not representative gameplay throughput. Relative
to V113, unstalled first-byte-to-done service counts are unchanged. Whole-case
counts add three command/settling cycles. Random draws follow the same policy
but changed start timing shifts their schedule, so stalled case differences do
not establish a causal optimization speedup.

The fast profile still models finite replies: one-cycle scratch responses and
eight-cycle reference responses. The stressed profile adds 16–19-cycle writes,
18–21-cycle scratch reads, 12–24-cycle reference replies, randomized request/input
stalls and output readiness on roughly one third of draws. These are explicit
bench service assumptions, not measured Game Bub SDRAM, Wi-Fi or ESP32 timings.

These are **cycle measurements**, not validated milliseconds on hardware. The
clock conversions are conditional on routed timing and complete memory service
at that clock. They exclude completed C2/HUD validation, full-parent QSPI/CDC,
Sunshine/ESP32 execution and LCD publication. Even the unstalled worst case
exceeds the strict 1,250,000-cycle / under-10-ms-at-125-MHz goal. A 33.333-ms frame
period budget alone does not prove 30 distinct displayed frames/s over 300 frames.

The SR14 [restart-chunk study](syntax.md) measures possible independently coded
work partitions and header costs. Its hypothetical lane ledger is not an RTL
scheduler, memory-port budget, multi-lane cycle result or full-parent fit proof.
Retire and validate chunks in order, preserve reference/generation ownership, and
measure the actual implementation before claiming a parallel decoding benefit.
