# V47 decode-order independent review

Reviewed read-only on 2026-11-07: `C:/moon/publish/firmware/experiments/v47-dy71-hud-order-20261107/native/hud.hpp` against V46. No candidate files edited and no hardware, target build or push performed.

## Decision

No correctness blocker found in the decode-order change. It is a reasonable bounded fragmentation candidate, requiring measured target confirmation. It does not establish that every heap layout succeeds, or that the original physical failure is repaired.

## Immutable reference and canonical output

The only changed function is decode_hud. It first retains four bounded immutable Views into the input and then constructs a four-element candidate vector. The actual decode order is 2,3,0,1; both reference selection and final storage use canonical index i. Thus patch 2 still predicts from accepted patch 2, not the first newly decoded patch. Final envelope hashing visits canonical out[0..3] and retains the original rectangle/tag contract.

Accepted state remains `shared_ptr<const HudCache>` in HudGate. All decode helpers return owned word vectors; the patch prediction pointer is const and remains separate from the new candidate. The new resize(4) default-constructs empty Patch word vectors under the existing Arena Scope. Move assignment transfers allocator-owned data into the matching canonical slot; allocator propagation is already declared true. No accepted patch is moved from or overwritten.

## Malformed input and failure atomicity

Existing checked-packet CRC, profile, identity, prior tag, fixed rectangles, kind ranges and nonzero bounded lengths remain intact. Total component size remains exactly equal to the envelope remainder; four components each at most49152 bytes cannot overflow size_t on the target. Each View is obtained with the existing checked Reader.take and Reader.end now runs before decode. This is equivalent for valid input and rejects trailing/boundary errors before any candidate patch decode.

Each component retains its original full-patch or kind/body binding check, internal CRC, dimensions, reference tag and output-tag checks. The final reconstructed HUD envelope tag is still mandatory. Reordering may change which diagnostic wins when multiple components are malformed, but cannot admit an invalid envelope.

On exception, the local `p`, four-slot `out` and any decoder temporaries unwind through the same tracked allocator; default empty slots release nothing. HudGate creates/publishes its candidate only after decode_hud returns and the tag has passed. A rejected Prepare still advances latest_generation and stores Failed status, exactly as before; it does not roll that generation back. Accepted identity, words and reference tag should remain unchanged. Abort/reset/commit authority is outside the changed function and unchanged.

## Allocation accounting and limits

Fixed output word sizes are7680,7680,15360,11520 bytes. The new order starts the larger outputs first and reserves the Patch container once rather than growing it. This can reduce allocator splits/reallocation overlap without changing the retained output byte count. Arena allocation, physical-reserve checks, failure counters and ownership are untouched.

Observed host logs at `C:/moon/builds/v47-host01/prepare12-test.log` verify253440 golden words and peak88974 bytes, versus V46 peak92544 at `C:/moon/builds/v46-host05/prepare12-test.log` (reduction3570). Both end with live84976 bytes for this sequence. These are native accounting/host results, not target largest-block measurements or a fragmentation proof. Different patch modes or allocator layouts can change temporary allocation demands. The unchanged98304-byte arena cap still governs all allocations.

## Meaningful additional tests before interpreting hardware

1. Preserve independently generated per-word HUD goldens across the full retained sequence. This catches canonical ordering/reference-index regressions without testing the chosen iteration order. Include motion/P frames and several commits, not just KEY.
2. Mutate one component at a time in a P frame, then recompute outer CRCs so validation reaches the intended component: wrong component output tag; wrong reference tag; CRC-valid malformed grammar; length mismatch. For patches0/1 this now fails after larger components were allocated. Require rejection, no candidate publication, exact accepted bytes/tag/identity unchanged and live allocation returning to baseline (allowing the bounded failure string).
3. Force allocator failure at each observed allocation ordinal during a P Prepare, using a host-only allocator/probe harness. For each failure, verify accepted reference preservation, absence of partial candidate, tracked live bytes consistent after unwind, and successful decoding of the same semantic P payload under a newer generation after the injection is removed. Same-generation retry must remain Stale; that is intentional.
4. Run deterministic fragmented-heap models containing multiple suitable/non-suitable holes, testing both V46 and V47 with identical allocation/release schedules and reserve thresholds. Record exact first failed request, free/largest before failure and final coalescing/accounting. Total-live accounting alone cannot demonstrate improved contiguous allocation.
5. Negative envelope cases with valid outer CRC: extra trailing byte, total-length mismatch, zero component, invalid kind/body magic and an incorrect final envelope tag. Require fail-closed behavior and no accepted-state replacement. Do not require identical first-error text if multiple fields are invalid.

Physical success still requires exact V47 image identity, target SRAM/stack review and the existing bounded cached3/cached12 checks; the offline evidence should remain separate from physical performance claims.

## Executed standalone rollback regression

Added only `tests/hud_order.cpp` after root authorization; native/handheld source remains untouched. Actual-native compile with UCRT g++ C++17 -Os -Wall -Wextra -Werror passed. Execution log: `C:/moon/maintenance/v47-order-test/execution.log`.

For P1, independently corrupt component0 then component1 nested CRC, recomputing the outer HU envelope CRC so rejection occurs during component decoding. Both larger outputs had allocated before the failure (checked tracked peak). Both cases returned DecodeRejected with no candidate-ready and no candidate. Accepted KEY0 retained exact generation/id/reference, shared object, envelope tag and independently recomputed 42,240-byte word CRC358486a6. Tracked live bytes returned exactly to baseline42488 after rejection. Same-generation retry was Stale with no additional live bytes; newer-generation valid P1 succeeded, and subsequent abort preserved accepted KEY0. Peak88942.

This regression establishes failure atomicity for late component CRC errors on the actual native implementation; it does not simulate target fragmentation or establish hardware success. Multiple-malformed-component first-error precedence can change under reordered decoding, and is intentionally not asserted identical.
