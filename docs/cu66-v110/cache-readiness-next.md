# Next cache-readiness predicate: small exact source candidate, not implemented

A same-edge `cache_count_nonzero` predicate is a narrow, causally relevant candidate **if the final routed report retains the current cache-count/readiness family**. The selected producer currently has no `cache_load_active` or equivalent registered zero predicate. Its eleven-bit `cache_count` directly supplies `busy` and `start_ready`; it also remains the RAM write index and first-byte/tag counter. A new predicate would replace only the readiness/busy zero reduction, retaining the original counter and cache-write/tag/error behavior. No RTL, proof, model, source copy, simulation or native run was created by this investigation.

## Actual source and placed evidence

The selected producer is [V109 fault producer](../../fpga/experiments/cu66-v109-fault/cs88_coefficients_v91k.sv), SHA-256 `5f18c913b6f2702e8f1036ba70b3ba7328d7cdbdfbc8810972c577bee167e86b`. Relevant current expressions at lines 1044–1049 are:

```
frame_running = state != IDLE && state != FINISHED && state != FAILED
busy          = frame_running || child_busy || cache_count != 0
start_ready   = !frame_running && !child_busy && !child_draining &&
                cache_count == 0 && !reset && !abort_packet
accepted_start = start && start_ready
cache_ready   = !frame_running && !child_busy && !child_draining &&
                !reset && !abort_packet && !start
```

COMBINED `results/place-setup-paths.rpt`, SHA-256 `61e6766e39f760b61ab06f2611a08a6024197ae92d4464a9065c520c87addec4`, is **placed estimated timing, not final route**. Its first path launches at `coefficients/cache_count_reg[4]/Q` and ends at ingress `buffer_bytes_reg[0]/CE`: slack −1.624 ns, 11.335 ns data delay, fifteen LUT levels, 8.884 ns estimated routing (78.377%). The first two cells after the count register are LUT6s; the path then passes readiness/accepted-start, cancellation/reset distribution, refill queue and ingress/context acceptance control.

That reported path still launches at a real count bit and traverses combinational decoding; this launch dependency has not already become an independently registered one-bit readiness predicate. Optimized names such as `frame_epoch`, `cache_complete` and `full` are aliases, not a unique source equation for each LUT. A future mapped predicate report must establish whether synthesis preserves or merges the new redundant register. Removing the eleven-bit reduction does not remove the remaining global control levels or predict recovered slack.

## Complete count-write and priority audit

There are exactly **three textual `cache_count <=` writes**, all in the cache sequential block, lines 1143–1162. There is no later override from the producer state process.

| Existing branch, in priority order | Count next value | Required predicate next value |
| --- | --- | --- |
| `reset || abort_packet` | zero | false |
| `accepted_start` | hold; only `cache_complete` is cleared | hold |
| `cache_valid && cache_ready`, with `cache_last || cache_count==1349` | zero | false |
| Same accepted beat, otherwise | eleven-bit assignment of `cache_count+1` | `(11'(cache_count+1) != 0)` |
| Every other edge | hold | hold |

This construction is paired with the actual counter writes; sampling `cache_count!=0` into a new register on every edge would be one cycle late. On the increment edge the predicate must use the **truncated next counter**, not unconditionally one. The original unsigned eleven-bit assignment wraps 2047 to zero; `(cache_count != 11'd2047)` is an equivalent increment-branch predicate. Legal post-reset loads remain in 0..1349 because count 1349 terminates independently of `cache_last`, so legal loads never take the wrap. Preserve the full-width prepared-state behavior anyway.

`accepted_start` legally implies count zero, but its original implicit hold should remain an implicit hold, including prepared-state priority tests. Cache accepted-start and cache-beat paths are mutually exclusive through `cache_ready`'s `!start`. Preserve the original branch ordering rather than assigning a speculative next flag from concurrent input signals.

The cache block has four `cache_complete` assignments and four `cache_error` assignments; neither is a substitute for count ownership. On the first accepted byte, tags latch and completion/error clear; later same-edge data/last checks override that error clear. `cache_data==3` sets error 3 and suppresses the RAM write, **but still advances or terminates count**. An early `cache_last`, missing last at count 1349, or malformed final data resets count even if completion remains false and error stays nonzero. The final completion assignment tests the old error, exactly as before. Cache error itself never resets count; reset/abort or an accepted terminal beat does. `cache_last` without an accepted beat has no effect.

Concrete edges that a proof must retain:

- Start asserted during a partial preload blocks both start acceptance and `cache_ready`; it does not secretly finish or abort the preload. `blocked_starts` retains its original increment edge.
- A held final cache beat and simultaneous asserted start cannot complete the load on that edge while count is nonzero; the beat is not accepted. Completion on a prior accepted edge can permit a start on the following edge.
- At count zero, accepted start suppresses a simultaneous first cache beat. Accepted start consumes the one-shot completion tag without changing count.
- Abort/reset wins over all cache signals and clears count, tags, error and completion together. An outstanding child drain still independently blocks readiness after cache count becomes zero.
- Malformed first/interior/terminal beats, early last, count 1349 without last, repeated loads and a count-2047 prepared wrap must produce the original count, tags, completion, error and RAM-write sequence.

A future candidate needs a per-cycle invariant `cache_count_nonzero == (cache_count != 0)` through every reset/abort/start/hold/failure edge. Substitute that bit in `busy` and `start_ready` only after proving it; no public cycle, invalid value, counter or output is intentionally changed.

## Why a wider local-quiescence flag is a separate edit

`frame_running` is combinational state decoding; it is not explicitly stored. The main producer process contains **31 textual state assignments**: one IDLE, ten FAILED, one FINISHED, and nineteen assignments to active states, including the compile-time refill-state choice. A co-registered running bit can be exact only if every assignment receives the predicate for its actual next state and implicit holds remain holds. The accepted-start ADMIT assignment has a same-edge invalid/nonmonotonic-epoch FAILED override; the later override must also win in the predicate. All queue/child/admission/nonce/replay/tag failures and the final NEXT_PLANE-to-FINISHED transition must remain paired.

A combined `producer_local_quiescent = !frame_running && !cache_count_nonzero` additionally needs both next values across the two original sequential processes. Computing it from old state/count in a third process is late. It is a larger proof/edit than the three-write cache predicate and is not necessary for the specific count-zero launch. The external `child_busy` and `child_draining` parts must remain live unless their exact next-state ownership interfaces are separately available; registering their current values would change accepted-start behavior. The producer FSM may already receive efficient synthesis encoding, so do not infer a separate running-bit gain from the source declaration.

## Smallest useful qualification

The V107 metadata focused units cover the elastic coefficient boundary and inverse, **not a standalone complete-producer miter**. `scripts/cu66-v107/meta_pipeline.py` uses the complete pipeline bench at `fpga/experiments/cu66-v107-elastic/verification/bench.cpp`; the current V110 canonical harness retains its independent fixture/event/pixel checks, including partial-cache abort, one-shot preload, reference identity and retry cases. Do not claim the metadata unit alone qualifies a producer edit.

If final routing justifies this cut, first create a new namespace and reversible three-write recipe. Exhaust the eleven-bit count domain and cache control/error/last/reset/start priority, retaining the 2047 wrap and malformed-beat cases above. A focused actual full-producer old/new pair with the current actual child bodies can compare every public field, invalid value, counter and cache RAM write/tag while independently predicting count/ready/start acceptance; source-extracted cache logic alone is a supplemental model. Add direct flag/count equality without weakening existing assertions or goldens. Then run the complete unchanged canonical comparison for the exact selected composition before any separately audited, policy-counted native trial. No implementation or heavy slot is requested by this document.
