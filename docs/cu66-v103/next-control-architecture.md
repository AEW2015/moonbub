# Next control-architecture experiments after V103

This is a source-inspection plan, not a proven invariant, implemented pipeline,
or timing result. The measured starting point is V102's routed reconstruction
`tile_reg[10]` → `residual_reg[1082]/CE` path and the admission
cell-index/active-cell path seen at synthesis/placement. V103's combinational
mapping candidates retain the existing schedule; their native results must be
read separately before choosing a registered successor. Keep the selected
codec/profile, 720×480 geometry, packet cap and all validation/public counters.

V103's final physical comparisons retain V102: reconstruction-only saves area
but has WNS −14.036 ns, and combined has −17.586 ns, versus V102's −13.976 ns.
Both route with zero errors. The function-only rewrites preserve cycles and
do not establish a routed timing win. These results now prioritize the
registered/precomputed experiments below; they do not prove their gains.

## Admission: state facts and proof obligations

Inspect the [actual V103 admission source](../../fpga/experiments/cu66-v103-admission/cs88_admission_v91i2a.sv).
Its current `cell_index` change preserves the entire unsigned 32-bit input
contract. That full-domain identity is independent of the narrower *reachable
parser-state* invariant a future coordinate counter would need.

| Source event | Existing action | Obligation for cached/registered geometry |
| --- | --- | --- |
| `reset || start || abort_packet` | Overrides the parser case, resets transaction outputs/counters, snapshots epoch/reference/cache inputs; a valid start enters `ACTIVE_CLEAR`. It does **not** assign `tile` or `plane`. | Invalidate pending geometry/active-cell writes before any fresh clear/parse. Do not claim tile is zero immediately after reset. No old transaction may reassert a cell after it has been cleared. |
| Successful `HEADER_CHECK` | After CRC, header, dimensions, sizes, generation/reference and key/mode checks, assigns `plane=0`, `tile=0`, then `KEY_TILE` or `GROUP_BEGIN`. | Establish the coordinate/cell cache and its transaction owner here. Prove all residual-marking paths descend from this qualified entry. |
| `KEY_TILE`, tile below plane limit | Writes the mode, marks a residual only when not hidden, increments tile by one. Hidden tiles also advance. | Update coordinates for **every** tile, not only residuals. Associate a residual mark with the old plane/tile before the increment. |
| `KEY_TILE`, tile equals plane limit | Sets tile zero; advances plane, or leaves plane 2 for `MODE_END`. | Handle the end sentinel separately from a real tile; reset plane-local geometry before the next plane. |
| `GROUP_BEGIN` | Computes `group_end=min(tile+16,tile_count)`, visible count and tag state. | Prove entry tile is inside the plane, arithmetic cannot wrap on reachable states, and end lies in `[tile, tile+16]` and no later than the plane limit. |
| `MODE_BIT`, mixed bit available | Writes one visible tile's residual/copy mode; marks residual only for a one bit, increments tile, enters `GROUP_TILE`. | Preserve the exact sampled bit, old tile/plane, mixed count and bit-consumption order. A fetch/refill must not advance coordinates. |
| `MODE_BIT`, empty-group tag | Only the permitted tag skips directly to `group_end`. | Support a bounded jump, not merely a per-clock increment. Hidden-only skips must not set active cells or add residual blocks. |
| `GROUP_TILE` | End check can reject noncanonical mixed groups. Otherwise hidden/copy tiles advance without residual marking; all-residual groups mark then advance; mixed visible tiles request one bit. | Keep all three advance/no-advance branches and the zero/all-one mixed-group rejection. Hidden tiles do not consume a mixed residual bit. |
| `GROUP_NEXT` | Advances plane and sets tile zero at a plane boundary, otherwise starts the next group. | Preserve the sentinel/plane transition and all last-group truncations. |
| Fetch, header load, bit refill, receipt wait, failed/finished states | Tile is held unless an assignment above executes. `Q_CHECK`/`Q_RUN` and `PLANE_NEXT` later reuse `plane` for chunk processing. | Cache updates must follow actual assignments, not an assumed global tile clock. Disable residual writes outside their original phase, including later plane reuse. |

`residual_tile()` has exactly three call sites: visible `KEY_TILE`, a one-valued
mixed bit in `MODE_BIT`, and the all-residual `GROUP_TILE` branch. Each call sets
`active_cell[11'(cell_index(plane,tile))]` and increments that plane's block
count. A future valid-state proof should establish plane 0–2 and tile below
5,400 for Y or 1,350 for either chroma plane **at these calls**; it must also
establish active-cell index below 1,350 and no call at an end sentinel. The
present source inspection suggests these obligations; it does not prove them
for reset, abort, malformed histories or unconstrained initial state.

Do not remove structural acceptance checks to simplify the path: frame/reference
monotonicity, hidden/group/tag legality, exact mode-stream consumption/padding,
outer/QM CRC, active-cell-required count, qmap run/inherit rules and residual
chunk block counts, bounds, magic and final cursor remain mandatory. Admission
is provisional; its receipt is not whole-frame accepted-state publication.

## Reconstruction: state facts and proof obligations

The [actual reconstruction source](../../fpga/experiments/cu66-v103-reconstruct/cu66_reconstruct_stream_v91k.sv)
sets plane/tile zero on `reset || cancel || start`. During normal operation it
advances tile only on the **accepted 64th output byte** in `EMIT`. At a plane
end it sets tile zero and advances plane, or enters `WAIT_DONE` after plane 2.
Thus a coordinate recurrence must hold while waiting for admission, mode
lookup, residual input, a reference, transform completion and output readiness.
It must count accepted tiles, not coefficient beats, transform clocks or
unaccepted output attempts. The cache should be ready before `MODE_REQ` and
remain aligned through `MODE_WAIT` and all 64 residual inputs.

Keep every `RESIDUAL` guard: frame epoch, plane, tile, fill index, qcell, scale,
per-plane block number, nonzero child epoch/token, and child/token continuity
after the first coefficient. Failed validation must retain error 4 and prevent
the corresponding residual write/count increment. Keep mode/hidden/key checks
(error 1), missing-reference rejection (error 2), reference match/error checks
(error 3), transform owner/error check (error 5), and complete output/drain
requirements. `lookup_cell` is a public combinational output even when its
request is low: caching it must either preserve its all-cycle values or
explicitly identify and validate a changed interface contract.

Reference-response physical ownership survives local reset/cancellation;
`ref_pending` is not a warm-reset flush. New geometry-valid bits must not clear
that owner, steal an old response for a new frame, or bypass the matching
pending epoch/fid/generation/plane/tile tags. Preserve the current priority of
reset/cancel/start, reference responses and FSM actions. In particular,
cancel-only does not clear all diagnostics, and simultaneous start/reset or
start/cancel must retain their existing behavior rather than be normalized.

## Minimal isolated candidates

1. **Precompute expected reconstruction qcell before residual input.** Add a
   frame/plane/tile-owned expected-cell register, initialized alongside the
   source tile assignments and updated on the accepted last output byte.
   First use it only for residual validation, leaving the public lookup
   expression unchanged. Aim for identical ready/valid/error/counter cycles;
   verify that next-tile computation has not simply moved the same long cone
   onto the new register's D input. Compare native placement/routing.
2. **Admission coordinate recurrence.** Track Y column, row parity and row-pair
   base, or a smaller exact offset state. Update for every `+1`, plane reset
   and bounded `tile=group_end` jump; a group jump can cross a row boundary.
   Chroma cell index remains tile. This requires the reachable-state proof
   above; it cannot replace the current full-32-bit function contract merely
   by assuming valid packets. Preserve or explicitly scope inactive-state
   observability and any hierarchical verification accesses.
3. **One-entry tagged active-cell write stage.** Capture the old transaction
   epoch/plane/tile/index and residual intent at each original call. Commit
   only if the owner is still live, and invalidate on reset/start/abort.
   Prove the stage drains before `ACTIVE_SCAN`, so required-cell count, QM
   validation and receipt readiness see every mark. Keep block-counter timing
   unchanged for an exact-cycle variant; otherwise publish a separate latency
   contract and rerun every schedule/occupancy check.
4. **Tagged residual validation/write pipeline, only if still needed.** Capture
   the complete coefficient beat and owner metadata, carry its validation
   result to writeback, hold it through backpressure and cancel obsolete
   entries. A skid/register stage changes ready/error timing unless proven
   otherwise: measure added occupancy, initiation interval, error priority,
   flush/drain cycles and full-frame latency rather than claiming V103's cycle
   equality. Do not accept a later beat that can hide an earlier bad owner.

Each option is a separate variant from the selected measured V103 sources.
Do not combine recurrence, new queueing and parser changes in the first test.

## Test and promotion contract

Add a Python state/coordinate oracle and actual RTL checks at every geometry
advance, hold and residual-mark event. Enumerate all tile/row/plane boundaries,
all 16-tile group starts and final truncations, hidden-region edges, copy/all-
residual/mixed/empty group paths and invalid tag/mixed count cases. Exercise
key and predicted frames, byte fetch starvation, mode/ref/transform/output
stalls, errors on each coefficient field, reset/start/abort/cancel in each
phase, same-cycle competing events, and delayed old reference responses.
For a write stage, specifically interrupt immediately before and after the
last residual mark, during `ACTIVE_CLEAR`, and before `ACTIVE_SCAN`; check
active bits, required cells, per-plane blocks and every public diagnostic.

Require byte-exact coefficient/canonical output, identical rejection reason,
no accepted-state corruption, correct owner drain and bounded queues. For a
representation-only candidate, retain cycle/event equality. For an explicit
latency candidate, check a documented transaction-order/latency relation and
report measured counters without weakening the older checker silently. Then
repeat native source-pinned utilization, critical paths, DRC/methodology and
route status under the unchanged part/clock/visibility; retain parent clock,
boundary/I/O and full-system hardware qualification as open gates.

The [parser review](parser-mapping-review.md) separately ranks: (1) bounded
15-bit prefix/leading-zero factoring; (2) reservoir extraction/keep masks;
(3) serial suffix/control; (4) counter changes only if parser-local evidence
justifies them, retaining public diagnostics; and (5) context-level address
factorization with event/epoch alignment. These are useful independent LUT/
carry studies. Their rank does not establish that they fix the measured
non-parser geometry path, and parser-specific timing gains still need reports.
