# Bounded timing architecture hypotheses after V117

These are future V118 design/prototype ideas, not changes to frozen V117 C, a new native launch or a promised clock. They are grounded in the completed [C125/C100 mapping review](final-c-mapping.md):125MHz fails−1.679ns on scratch tile-event/control;100MHz fails−0.317ns on inverse result-head metadata into reconstruction payload CE.

## 1. Register an owned residual acceptance/validation/commit path

**Measured cause:** C100 result_head→selected metadata/validation/fault→residual-word CE,10.028ns, with72.6% routing. The current inverse selects the entire output owner from `result_meta[result_head]`; reconstruction validates frame/child/token/plane/block/tile/qcell/scale/index in the same accepted edge that enables a24-bit word.

Prototype a complete accepted tuple plus expected-owner snapshot, a registered validation result and a local payload commit stage. Keep an initiation interval of one when capacity is available; separate accepted position/token from committed fill position. Word63 may make the math bank ready only after it validates and commits. A fault in an older tuple must cancel every younger acceptance and prevent later token/canonical publication. External reset/cancel and public masks remain immediate; accepted physical reference response leases survive until their exact matching ACK.

This adds real owners and may change declared error/commit timing. Verify that schedule explicitly with an independent accepted-event/commit ledger and the unchanged arithmetic, canonical, whole-owner, first-fault and physical-debt oracles. Do not claim old-cycle equivalence by omitting clocks or invalidating old assertions. Measure added drain/startup clocks and sustained throughput rather than assuming the pipeline is free.

## 2. Stabilize the inverse's completed-head presentation record

**Measured source:** result_head fanout153 and1.947ns first routing segment in the C100 path. A completed result's owner is stable while it is offered, yet currently comes through the head-bank mux at every sample.

Compare a whole result presentation record, loaded from the completed slot before valid is offered, with the direct head-mux baseline. Bind every owner field, full residual payload owner and emit index. Release the slot only after all64 handshakes. A setup bubble is permissible only as a declared measured schedule change with held-output stability and final drain accounted; a new head cannot replace a stalled old head. Keep physically separate completed slots and accepted-versus-visible frontiers. Determine whether a presentation register alone or the acceptance pipeline above gives the better routed result; do not combine unmeasured changes and attribute all improvement to one feature.

## 3. Prepare scratch head/tile events and replay extents under their real owners

**Measured125MHz cause:** read_band→cursor/head mux and equality/carry→tile-event→bank_ready/busy/state feedback. Consider an owned head/position/block-match record matured on existing fetch/extract edges. Carry band, epoch, cursor, block, bank and valid together; invalidate by the real owner transition. Register compact validated event predicates before the broad state/status consumer, preserving the original error precedence and ensuring no younger tile publishes after an older invalid head.

A separate retained path, selected_offset→admission/replay/error status−1.509ns, motivates preparing immutable per-chunk extents or retaining the actual accepted request address/epoch for its response comparison. Do not recompute an old response's owner from a mutable current cursor. Preserve full32-bit bounds, overflow/wrap rejection, wrong-epoch/address rejection and the original finite packet domain. Existing control clocks may provide preparation opportunities, but zero added latency must be proved rather than assumed.

## 4. Treat remaining wide physical controls as routing problems

C's bank enables map directly to FFs, yet C125 bank0's512-load CE wire costs8.231ns and still fails. Merely adding another syntactically identical FF can be merged and does not prove locality. If this remains material after the earlier cuts, compare actual lane/bank ownership or bounded multi-edge physical copies whose valid/completion protocol has meaning. A tile becomes READY only when every required lane has committed; canceled inactive storage must never overwrite an older READY head. Preserve or explicitly model the original physical kill-COPY behavior. Do not use false paths, reduced coverage or hidden payload resets as substitutes for an architecture proof.

## Concrete bounded option:16 bytes per beat over four copy edges

C125 bank0's direct FDRE enable still has an8.231ns routed net and−0.976ns slack. Compare a real **16-byte ×4-edge** canonical copy with the current64-byte/512-bit atomic copy. Each selected lane would enable128 payload bits rather than512. This is a source-architecture hypothesis, not a measured fanout/timing improvement; actual mapping and routing must establish the resulting controls.

Retain the sole existing engine result while all four beats copy into the inactive destination owner. Hold its full512-bit result and ID stable; release the engine only after the fourth committed beat. Mark that destination READY only after all four lanes and owner metadata are complete. The older READY head remains immutable and can continue ordered emission. A canceled partial copy must revoke its inactive logical owner and never publish; no stale partial lane may survive as valid data in a later token/frame. Any beat physically sampled on a cancellation edge must be accounted for explicitly by the new private-storage contract.

Use the existing engine result and destination storage; do not silently add an extra tile buffer. Record any real new owner/beat/index state and its storage cost. Avoid KEEP, forced fanout attributes or replicated FF syntax as substitutes for physical ownership. The new copy takes four real edges: it cannot be compared as if it still completed in one. Preserve the old atomic-copy baseline tests, then use an independent whole512-bit, four-beat ledger and cancellation/reset/error tests at every beat boundary for the new declared schedule, including older held heads, fault priority and final drain.

### Source-level cycle budget, not a latency bound

For the current fast parent fixture, a preliminary scheduling projection is:

| Proposed change | Assumed raw added edges |
|---|---:|
| Four-edge copy instead of one for8,100 canonical tiles |3×8,100 =24,300 |
| Two owned residual validation/commit stages, about7,806 residual tiles |2×7,806 =15,612 |
| Combined raw projection |39,912 |

The current fast row parent measurement is1,126,533 cycles. A10ms budget at a hypothetical validated125MHz is1,250,000 cycles, leaving123,467 raw cycles. Subtracting the39,912 projection leaves83,555 raw cycles. **This is neither a measured result nor a formal worst-case bound.** It assumes the stated fixture geometry and stage costs and ignores newly introduced backpressure, queue/engine coupling, replay/reference stalls, pipeline fill/drain interactions and changes to the parent critical path. Recompute it for other mode mixtures and service profiles. Current C125 does not meet timing, so even the frequency used for this arithmetic is conditional.

The intended tradeoff is explicit: spend bounded real pipeline/copy edges to seek a shorter combinational path and a potentially useful validated clock. Added stages help only if complete source-bound parent simulations retain the required throughput/latency under the actual service models and fresh native runs close timing. Preserve complete accepted-versus-committed tuple and beat ownership ledgers, first-fault ordering, response debt and final byte/hash/publication fences. No improvement in30fps or under10ms is established by this projection.

## Qualification gate for any future candidate

Keep frozen C as the independent baseline. Run complete focused math/geometry/stall/malformed/EOF/token-wrap/reset/cancel/fault/reference/drain/retry tests and source-bound whole-component/LIVE comparisons, adding independent ledgers for every new stage. Maintain exact byte/ACK/hash/C2/HUD commitments; declare any changed schedule and measure real accepted-edge latency, sustained FPS and resource use. Only after source qualification should a separately authorized future fixed-method native budget measure synthesis, placement and actual routing. Require nonnegative setup/hold/pulse checks, correct constraints, zero routing errors and an independent fresh positive repeat before calling that component clock validated. Full-parent routing and hardware measurement are further gates; simulated cycle arithmetic alone cannot close the30fps/under10ms hardware milestones.
