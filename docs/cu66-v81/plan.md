# V81 tagged wide-fill experiment

Preserve all V80 and earlier evidence. Keep the existing coded/native resolution,
packets, release clocks, canonical/HUD validation and native display checks.
The goals remain sustained 30 distinct source-fps and strict maximum
packet-complete-to-validated latency below 10 ms. Neither is closed by V80.

1. Fork the two-slot reference path to accept four authenticated 128-bit blocks
   per tile, using the actual SDRAM bridge snapshot. Preserve bank leases and
   candidate-write authentication. A drained aborted response is not a commit.
2. Check full-tile payloads, tagged block order, stable held responses, stale or
   wrong identities, abort on acceptance and concurrent writes, including both
   modeled SDRAM timing corners.
3. Instrument first-offered lookup valid, raw logical request acceptance,
   snapshot acceptance, successful block commit and backend write completion.
   Compare their actual dependencies; do not subtract command gaps to predict gain.
4. Require strict lint and component PASS, then compare V81 mode 2 against frozen
   V80 mode 2 and the new mode 3 on identical four-source regular/combat fixtures.
5. Run all 457 sources in four continuous, independently reset histories, with
   no per-source reset, if the candidate is functional. Preserve adverse timing
   and all failed attempts. Repeat actual-system reject/abort/lost-ACK retry.
6. Audit source archives, logs, binary identity, traces and derived metrics,
   publish the reviewable branch and update the external progress note.

A modeled 100 MHz and zero-time native CPU HUD/control do not establish target
clock timing, fit, CDC or ESP32 transport behavior. Longer distinct-source
60/600-second qualifications and physical under-10-ms validation remain open.

## Gate for the next performance experiment

The read-only source review and bounded traces identify a conditional service
floor for the unchanged bridge/controller and observed delta traffic. With
35,040 mandatory physical reads and 35,040 writes, minimum predecessor command
separations of 18/16 memory clocks give at least 1,191,342 clocks (11.91342 ms at
100 MHz) between the first and last mandatory acceptances, even omitting LCD,
row misses, refresh, packet handling and final completion. This applies to the
recorded traffic/service assumptions; it is not a universal codec bound or
formal/physical signoff. See the reviewed edge ledger in the bottleneck study.

A 4/8-slot lookahead or bounded read/write grant-grouping experiment can target
30-fps service and queueing, but it cannot by itself break that conditional
under-10-ms floor while the command counts and serialization remain unchanged.
Before promising that milestone, prototype fewer physical transactions or a
shorter/pipelined bridge/controller service path. Preserve canonical/HUD fences,
write coherency, abort drain and continuous LCD deadlines. Measure the complete
transaction and display path with the original fixture releases; do not infer
a frame speedup from isolated DSP or cache response improvements.
