# V72 — qualify masked BL8 writes for CU66

Continue from the frozen v71 baseline at commit `207b16d8f0e04a928810a294787609c6e664db71`. The first action for every v72 evidence run is the read-only baseline audit. Keep v69/v70/v71 bundles, source pins, test records, and the untracked marker-recovery material untouched. Put all new v72 outputs under `fpga/experiments/cu66-v72/`, and documentation under `docs/cu66-v72/`.

V72 is implemented and qualified at the simulation scopes in [hardware-handoff.md](hardware-handoff.md). Exact-device implementation and both target milestones remain open.

## Objective

Replace scalar SDRAM writes with a bounded, accepted-beat-owned BL8 service while preserving exact output, completion ordering, display behavior, and explicit recovery. This is an optimization experiment. It carries no target-fit, routed-timing, physical-throughput, 30-fps, or sub-10-ms claim.

## Implemented write-service contract

- Model each BL8 as eight x16 beats with byte enables and DQM masking. Document lane ordering and the inverse relationship between byte enables and SDRAM DQM levels, then test every byte lane and mixed mask.
- For a canonical tile row, align an eight-pixel row to one eight-beat burst: four useful x16 words occupy the selected upper or lower half; mask all other beats. Define exact address/alignment and half selection. Do not cross row or tile boundaries.
- The portrait strip painter emits eight contiguous x16 words and should use all eight beats with the appropriate mask.
- Scalar HUD operations remain a one-enabled-word fallback and must preserve their current guarded address and semantic behavior.
- Acceptance transfers ownership of the entire burst payload to the memory service. No write completion/ACK may be exposed when a request is merely enqueued. Completion must mean the final enabled write has passed the required recovery/timing point and is visible to subsequent reads under the defined ordering.
- Specify full and partial burst abort behavior. Drain accepted work safely, suppress unaccepted work, and do not report success for incomplete transactions. Reset/recovery must not strand queued beats or produce stale ACKs.
- Invalidate all scalar cache lines and aliases that overlap any enabled byte of the burst. Check read-after-write through every client and alias.
- Do not make producers wait on a coalescer that itself waits for more producer data. Bound buffering and prove backpressure behavior.

## Qualification order

1. Run `scripts/cu66-v72/verify_baseline.py`; retain its PASS output in a new v72 path. Audit and count the exact frozen v69/v70/v71 bundle files and v71 source pins before implementation.
2. Review the burst API: partial-mask byte ordering, half-burst canonical mapping, scalar fallback, tWR/final-beat recovery, ACK visibility, fault/abort drain, reset, and cache aliases. Record decisions in a new API review document before changing RTL.
3. Add memory-level directed checks for each byte mask, upper/lower canonical half, aligned painter burst, scalar HUD write, invalid alignment/range, overlapping cache aliases, concurrent readers, accepted partial abort, late fault, reset during drain, and read-after-write visibility.
4. Exercise two simulators, multiple fixed seeds and both established SDRAM tAC corners. Include bounded fairness, refresh, row/bank conflicts, response stability, and recovery completion. Preserve commands, versions, source hashes, exact input IDs and raw logs.
5. Integrate with the actual v71 packet/base owner, controller, HUD, painter, cache invalidation, and elastic LCD path. Require exact standalone and full-system key/P outputs, all canonical YUV/HUD/RGB words, complete ordered rasters, zero normal-load LCD underruns, and no partial frame acceptance.
6. Compare the identical v71 key/P input and model clocks. The v71 reference is P transaction 260.18963 ms and validated model interval 90.66040 ms. Report both intervals and all queue/service costs; do not infer target CPU decode latency from model time.
7. Re-run the 1,800 distinct chronological-source campaign at fixed 30-fps arrivals and the separate ten-minute physical run only when exact-target implementation, clock/CDC constraints, live transport, CPU/HUD service, and board setup are available. Preserve strict under-10-ms fixed-packet-complete-through-validated-ready timing as a separate on-target gate. No simulation or source-level result closes either gate.

## Comparator and known limits

V71 reconstructed the key/P pair exactly, observed zero underruns across 14,660 complete clean lines, and presented two distinct complete source rasters. Its modeled P transaction was 260.18963 ms and immutable-packet-complete to validated-ready was 90.66040 ms. The comparable v70 strip P transaction was 229.84583 ms and had 11,762 underruns in a differently timed run. These are fixed-input comparison points, not normalized underrun-rate evidence or physical throughput claims. Require V72 to preserve exactness and clean scanout while measuring whether true masked writes improve service.

## Following iteration

Use the measured priorities in [the handoff](hardware-handoff.md#next-work): strip memory inference/banking, reference read service, tile-major storage, guarded HUD batching, and direct-YUV/overlap evaluation. The matched P transaction is now 148.51433 ms with zero modeled underruns; the four-frame tail is 149.87094 ms. Do not treat this improvement as 30 fps or target decoding below 10 ms.
