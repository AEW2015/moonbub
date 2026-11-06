# DY71 unchanged replay: measured blocking results

**Update:** [replay02 subdivision](DY71-REFERENCE-BLOCK-RESULTS.md) locates16.00631ms in reference admission blocked by previous canonical writeback, with19.02676ms accepted/inflight. Original results below are preserved.

The observation-only replay **exactly matches** the selected SYNCsafe/math/grouped baseline: all public stage cycles, canonical/HUD checks, frame counts, presentation times and counters are unchanged. DUT hashes are unchanged; Verilator used two build jobs. No Vivado, hardware or behavior change was used.

**P2 is blocked on reference availability, not IDCT arithmetic.** Of41.62844ms BASE_RUN,35.17760ms (84.50%) has a completed IDCT waiting specifically for the P reference; IDCT arithmetic itself occupies3.40296ms.

| P2 exclusive BASE bin | ms |
|---|---:|
| Completed-IDCT waiting for reference |35.17760|
| IDCT computation/pipeline |3.40296|
| Entropy/scatter wait |1.41905|
| Canonical write-fork memory branch blocked |0.61069|
| Dequant output wait |0.41990|
| Final hash wait |0.03105|
| Remaining configuration/handshakes and11both-fork blocked clocks |0.56719|
| **Conserved BASE total** |**41.62844**|

P2 HUD completion precedes canonical completion by16.55631ms (internal `hud_at=8022457`, `base_at=9678088`); both canonical-complete HUD/drain tail bins are zero. SHA executes518464round clocks (5.18464ms), largely overlapped: row/hash-only write-fork blocking is zero, final hash wait0.03105ms. Entropy is busy41.57021ms but output-stalled31.92039ms; its busy counter must not be called compute time. P2 actually has fewer entropy decisions and less IDCT computation than P1.

Reference and write latencies are **overlapping**, not additive critical-path bins:

| Per frame | KEY | P1 | P2 |
|---|---:|---:|---:|
| Completed-IDCT reference block, ms |0|20.16398|35.17760|
| IDCT compute, ms |3.92568|4.04088|3.40296|
| Reference accepted?response summed latency, ms |0|13.06181|19.68210|
| Canonical write accepted?drained summed latency, ms |7.79871|13.41529|20.41388|

P2 has7806reference responses and8100canonical writes. Since its35.17760ms reference-blocked interval exceeds **all** accepted-reference pending time19.68210ms, at least15.49550ms of that block occurs outside accepted-reference pending. The exact admission/inflight/delivery split was not instrumented. The selected tile adapter serializes reads and writes in one active transaction; prior-write occupancy is therefore a source-supported hypothesis for admission delay, not a measured numerical attribution.

All8.01729ms P2 reservation idle occurs during BASE_RUN;7.10840ms overlaps the reference-blocked bin. It is part of that interval, not an additional cost or promised saving. The next smallest diagnostic is a wrapper-only split of that one dominant bin by `ref_req_valid/ref_req_ready`, reference-pending, tile-adapter state/writing, and previous canonical-write pending, retaining physical command/order and quota. No PHY/map/quota or codec change is selected by this report.

## Evidence and limits

Evidence directory: `fpga/experiments/cu66-v71/direct-system/profiling-v001/evidence/replay01`.

- `profiles.json` contains every exclusive bin, overlap, latency and timestamp; `analysis.json` independently checks conservation.
- BASE bins sum to observed BASE clocks; all public-state clocks plus one startup clock sum to each transaction. Reserved class/phase/bin counts conserve; each overlap is bounded by its observation interval.
- Reference/write latency sums equal observed pending clocks. IDCT input?consumed-output latency equals actual compute plus output-valid holding clocks. SHA round observations equal the leaf counter; IDCT/write completions equal8100tiles. No unknown BASE state was accepted.
- `result.json` asserts exact baseline log comparison; `source-freeze.json` binds untouched DUTs and observer-only sources. Baseline remains `syncsafe-math-v002/evidence/new-fence-three01` (source-freeze SHA542a612074618feb3e3d2463f4688e6318281f11e3d8ff1f2876f13575d51ad3).

P2 still takes45.52368ms and its presentation interval is46.10029ms. These are three simulated chronological frames, not steady-state30fps, physical playback, or ESP32/FreeRTOS/QSPI timing. HUD semantic CPU work remains outside HDL time. Overlap counters and source-level hypotheses must not be presented as counterfactual speedups.

| New evidence | SHA-256 |
|---|---|
| `profiles.json` | `0da495bab9fca61ad6809fb7de2c9d04f41378cbf8e90b9047988458ec2234d7` |
| `analysis.json` | `89508dd1ab80d6ead065c2f3235bec465084ec5e8acdff410436d94988cb650b` |
| `frames.log` | `672bea58f41508826300a76b571989121fdc518c7b2275733716db112c43c843` |
| `source-freeze.json` | `dad71bcba8dad9b9399925a36a8a5b282e7cb09846e7841c6ccdff801f4b5266` |
| `tb.cpp` | `6b01d904493bfe4dee1c20a2f6c4a83052a6feed4dbeb2704212ea94e5a0b942` |
| `cu71_direct_system_sim.sv` | `d1e0842895b946cab3fc7edd33937abb92704ca18ddcdbbfda53913a9cf69a45` |
