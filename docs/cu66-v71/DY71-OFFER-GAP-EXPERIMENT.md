# DY71: bounded offer-gap experiment proposal

Proposal only. No RTL, selected manifest, PHY, map, quota, timing or hardware change is selected here. This analysis uses the exact SYNCsafe/math/grouped baseline and observer-only replay02 linked in [reference-block results](DY71-REFERENCE-BLOCK-RESULTS.md). Its source-freeze SHA-256 is `91da4a958f514b4543159c56a2af3a071c109c83e2a490423bf4fdcf74e943b7`; replay02 profiles SHA-256 is `8f0ce604043df68a70857858c9f5abd74a9d8026a73e8f3931137eed9c89fc44`.

## What the existing code establishes

`cu71_cache_dma` accepts one command only in IDLE with the backend idle and no pending reply. It captures one 128-bit response, writes two 64-bit YUV cache rows or eight HUD words, checks the registered cache-write error, drains backend ownership, returns one identity-bound result, then returns to IDLE. The owner advances its page cursor only on that result. Its `!inflight && !dma_busy` command gate prevents offering a successor while the previous payload is being installed.

With a response accepted on edge 0, no abort/error, backend already idle and result ready:

| Event | YUV edge | HUD edge |
|---|---:|---:|
| Response payload captured |0|0|
| Cache writes |1–2|1–8|
| CHECK_CACHE observes final registered write-error |3|9|
| DRAIN sees no pending/backend busy |4|10|
| RESULT consumed; owner advances cursor; DMA returns IDLE |5|11|
| Next command accepted |6|12|
| Next backend request accepted if ready |7|13|

These are code-derived no-stall intervals, not measured distributions or guaranteed backend latency. The registered `wr_error <= wr_valid && bad_write` in `cu71_direct_cache` makes the CHECK edge necessary: publishing success on the final cache-write edge could miss that write's error. A backend response is not sufficient evidence that `lcd_busy` has already cleared.

The grouped bridge starts its LCD grace after a completed physical read. Its 18-clock LCD grace and 4-clock sticky-background grace run while the physical controller can also be busy. A future earlier LCD offer can consume existing LCD grants sooner; it must not change 8:4 physical-command charging, grace constants, local-response accounting or background-client fairness.

## Measured opportunity and its limits

P2 has 99,360 LCD read commands. During the 35.17760 ms completed-IDCT reference block, 7.10840 ms overlaps reserved controller-IDLE cycles: 6.01092 ms LCD-class and 1.09748 ms background-class. Those are intersections, not disjoint additional costs. They neither identify every absent-LCD-offer cause nor establish that all reserved time can disappear. Cache installation, owner cursor turnaround, physical/backend drain, page transitions and the absence of any useful refill can all produce offer gaps.

The previous-write reference-admission block is 16.00631 ms; accepted/inflight reference block is 19.02676 ms. Every admission-blocked clock observes the previous same-generation canonical write occupying the tile adapter. All those writes still need physical service. Simply acknowledging a queued reference earlier would move clocks from admission to inflight without speeding a frame.

## Recommended first isolated control: merge check and drain

Derive a new cache-DMA variant with the same ports and one outstanding command. On CHECK_CACHE, preserve the final registered-error check; if it is clear, `!pending && !lcd_busy` and no matching abort, enter RESULT directly. Otherwise use the existing DRAIN path. Keep normal success, error and abort identities, cache writes and result backpressure unchanged. Leave owner, scheduler, cache, PHY and map byte-identical.

This removes exactly one local clock on each eligible successful command. The sum of that direct saving for P2 cannot exceed 99,360 clocks, or 0.99360 ms at 100 MHz. Its effect on transaction time and physical arbitration is unmeasured and is not that bound added to other overlaps. It is a deliberately small causal control, not a route by itself from 45.52 ms to 33.33 ms.

Instrument the same unchanged baseline and candidate with response-accept→next-LCD-request-offer and →accept histograms, split YUV/HUD and same-page/page-transition; count backend-busy, cache-write, error-check, result/owner and no-useful-front-work reasons. Count controller-IDLE reservation only when another physical client is pending, distinguishing LCD-class and background-class. Charge every edge to exactly one local phase and retain the existing orthogonal overlaps. The same harness should show one-clock local-gap improvement when eligible; any other behavior difference must be explained before broader use.

## Follow-on option: one-command lookahead, two payload records

If the control proves local offer gaps matter, a separate higher-complexity experiment can decouple backend fetch from cache installation. Maintain at most two complete records, each containing generation, frame, cookie, context, source, cache address/kind and response/error state. Keep only one backend read outstanding and one cache write per clock. After response A is captured and the backend is actually idle, issue B while installing A. Do not overwrite A's payload with B's response; with no free record, stop issuing. Responses belong to the single latched outstanding identity, never the current owner cursor.

The owner needs separate issue and retirement cursors; a DMA-only FIFO cannot manufacture the next address because current owner state advances at result retirement. Allocate a unique nonwrapping cookie at issue, retire results in order, and publish page/cache-valid only after every ordered record's final cache write, delayed error check and successful retirement. Preserve address-pipeline validation and page-group hazards.

Front priority applies at issue selection: do not prequeue provisional PREPARE work across a newly eligible front refill. Permit at most an already accepted provisional read to drain. Prefer an owner-supplied successor opportunity rather than an irrevocably admitted provisional descriptor queue. A page-boundary successor must not reuse a cache bank still leased by rendering or mark a page valid before retirement. Failed/aborted records cannot advance a ready/present fence.

On identity-bound provisional abort, suppress writes for canceled records immediately, cancel unissued records, abort/drain the accepted backend operation, and wait for all affected records plus backend ownership to disappear before releasing the context. Accepted FRONT/PENDING commit ownership remains irreversible. An unexpected late response with no matching outstanding record is a fault, never data for a reused slot. Existing fail-closed cookie exhaustion remains mandatory; widening it is a separate verified change.

This can overlap the 2/8 cache-write cycles and owner turnaround with useful backend work, but cannot claim the full 7.10840 ms as savings. It adds state, response storage and ownership cases. Do not combine it with the first control or a memory scheduling change in the initial comparison.

## Comparison: one reference context alongside tile writeback

The current tile adapter has one shared generation/bank/plane/index, 512-bit payload and operation state. It owns a complete four-BL8 tile until its result is acknowledged. One real reference-prefetch context would require independent read metadata and 512-bit storage alongside an immutable previous-write context, plus bounded arbitration on the existing single word-request port. Preserve all four contiguous BL8 commands within the current sticky background group where possible; changing the 8:4 grouped bridge is outside this experiment.

Prefer a narrowly defined next-reference request already produced by the base pipeline over speculative tile-index prediction: hidden tiles, plane transitions and canonical lease identity must remain exact. Deliver reconstructed data only after all four read responses and matching tags, regardless of early queue admission. Keep write-done tied to actual four-burst physical completion. Abort must drain both owned operations before release, and a held read response must not corrupt or block write completion indefinitely.

Such a context could overlap reference service with previous writeback and the next tile's existing entropy/IDCT work. It cannot eliminate writes or add physical bandwidth. Concurrent canonical reads/writes can also reduce locality and increase ACT/PRE, so earlier admission is not the success metric. Compare actual completed frame time, accepted/inflight wait, physical command counts, clean scanout and refresh progress. The current 16.00631 ms admission block, 19.02676 ms inflight block and 3.40296 ms IDCT compute are overlapping workload observations, not a recoverable sum or a promised prefetch gain.

## Minimum component and integration gates

1. Freeze baseline, new variant, harness and exact executable source hashes. First prove the check/drain control independently with all existing DMA identity/cache goldens and all abort positions, including final cache write, CHECK, backend-busy drain, result backpressure, coincident response/abort, stale/unowned response and error on the final cache word. Add explicit no-success-before-delayed-error/drain assertions.
2. For a later lookahead variant, require randomized ready/response/result stalls, fast response B while A installs, two-record-full backpressure, YUV/HUD and page/context transitions, newly eligible front over provisional work, exact cache write ordering, cookie exhaustion, reset and abort at every occupancy/state. Assert occupancy conservation, one physical outstanding read, metadata stability under stalls, no cache-valid/presentation before ordered retirement, and no context reuse before drain. Preserve the SYNCsafe token/bundle and legal quiet-window proofs.
3. Run the same actual qualified pin-model KEY/P/P fixture and full canonical/HUD/pixel oracle. Functional bytes, identities, write/read command totals and presentation ownership must match; timing is the experiment's intended difference, so public cycle lines cannot be required byte-identical to the old baseline. Report stage cycles, IDLE reservation classes, offer gaps, ACT/PRE/refresh, underruns and physical accepted commands. Keep original and candidate evidence separately. No physical playback or sustained-30-fps claim follows from this gate.
4. A reference-context experiment needs its own tile-adapter four-burst read/write/mask/error/abort/backpressure tests before the matched full-system replay. Do not select it merely because an ingress-ready or queue counter improved.

The recommended next action is root selection of the one-clock check/drain control and its paired observer harness. The two-record LCD path and dual-context reference path remain alternatives requiring separate authorization and proof, not concurrent changes to selected sources.
