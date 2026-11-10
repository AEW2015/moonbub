# Owned elastic validation after V128

This is an unfrozen design exploration for a later version if V128's routed result still misses 125 MHz. It does not change V128 RTL, qualify timing, or supersede its exact-cycle verification contract. The next implemented candidate must follow the actual routed worst path; the alternatives here are bounded ways to add a real register boundary rather than repeatedly rearrange the same combinational cone.

## Actual boundary and constraints

The current [pipeline](../../fpga/experiments/cu66-v128-raw/br88_pipeline_v91h.sv) directly connects packet decoder `out_valid/out_ready` to scratch `coef_valid/coef_ready`. The [synchronous ingress](../../fpga/experiments/cu66-v128-raw/br88_packet_ingress_sync_v91h.sv) exposes both direct tuples and selects the public coefficient with its own `raw_mode`. Scratch's separately stored `raw_mode` describes the allocated format. These two mode values must never be conflated.

Each coefficient tuple is exactly 72 bits: epoch32, block16, index6, signed value16, and band2. Current scratch [validation](../../fpga/experiments/cu66-v128-raw/packed_scratch_v91g2.sv) computes two eight-phase decision lanes and selects Boolean results with `coef_select_raw`. It then selects the current `phase`. Full epoch and block comparisons, signed limits, count limits, raster/DC/AC rules, and the implemented rank-mask expression are part of the contract.

The current scratch grants `coef_ready` only in `INGEST` and outside cancellation. A valid good coefficient moves to `APPEND`; `APPEND` updates `written`, `previous_position`, `previous_valid`, `rank_threshold_mask`, and the assembler before returning to `INGEST` or waiting on a full line. It therefore does not currently accept one coefficient every clock. A validation unit with initiation interval one cannot by itself make the whole scratch path II=1.

The V127 mapped evidence identified ingress mode selection before full epoch validation on the scratch error/state path. V128 removes that mux-before-comparison structure without adding cycles. If registers are needed next, they must actually interrupt the measured cone, including the control destination, rather than only register a status mirror.

## First candidate: selected tuple register with ordered retirement

Insert a private elastic coefficient channel between ingress and scratch. The first bounded implementation keeps scratch validation in its existing `INGEST` retirement context and registers the selected tuple before it reaches that context.

The token contains the full selected 72-bit tuple, the actual ingress selector, and a live allocation owner. The owner includes the full active epoch plus an allocation/cancellation generation that changes even on a replacement start using the same epoch. Epoch equality alone is not a sufficient kill tag. A small generation tag requires a proof that it cannot wrap while an old token is live; otherwise use a sufficiently wide tag and a bounded-lifetime assertion. The `valid` bit owns all token payload; reset the small ownership/control state, not every payload bit.

V128's two direct combinational views remain observable for their existing diagnostics. A buffered token must never be reconstructed later from those live views. The value, selector, owner and any registered predicate must travel together. This candidate can remove ingress mode-to-validation coupling, but it leaves the tuple-register-to-full-validation-to-scratch-control path. Route it before claiming that it solves a remaining carry-chain bottleneck.

A one-entry elastic slot can use `up_ready = !slot_valid || retire` when that ready path meets timing. To cut ready fanout as well, use a two-entry skid queue with locally registered occupancy/credit and no combinational downstream-ready path back to ingress. Define `enqueue = upstream_valid && upstream_ready` and `retire = head_valid && scratch_ready && owner_live && !kill`; head payload stays stable until retirement or an explicit owner kill. Simultaneous enqueue/retire must preserve FIFO order and one token per accepted handshake. Never assert ready for capacity that a simultaneous cancel or error can invalidate ambiguously.

This changes the internal coefficient acceptance edge. It must declare that change. It may also change byte-ready stalls and packet completion latency even though packet bytes and decoded coefficients remain identical.

## Second candidate: register complete validation decisions

If the new worst path remains full comparison through scratch control, split validation itself into owned stages:

1. Capture the full tuple and owner at a defined eligible issue edge. Snapshot every mutable operand needed by validation: full phase, allocated format, block limit, selected count, `written`, previous-position/valid and rank mask, or an equivalent committed-order state. Keep a separate exact selected epoch-mismatch result for error 2 versus error 3.
2. Compute and register bounded partial decisions. For example, full32 epoch inequality can be four byte-inequality flags with a later OR; the full16 block/range checks and sparse high/block/rank checks can have independent registered results. Preserve the original strict/inclusive comparisons and signed widths. Any magnitude decomposition needs an exhaustive boundary proof; truncating high bits is not permitted.
3. At ordered retirement, combine the registered decisions and either enter the original append action or raise the selected error. The tuple used to construct `pending_record` and `pending_position` must be the same token whose predicates were registered.

Do not register a predicate against stale scratch state. In the conservative first implementation, only one token may issue validation against a committed scratch context until its predecessor reaches `APPEND` or fails. Buffered later tokens may wait without validation. This adds declared latency while avoiding a speculative dependency network.

A later II=1 validation front end would need a shadow ordered state updated by every issued good token, rollback/flush on the first bad token, and barriers for phase changes, line flushes and band end. The shadow rank mask must match the actual writer after each committed append. That is a separate feature, not an incidental addition to this timing fix. Keep the existing scratch service limit visible in throughput reporting even if the validation arithmetic itself sustains II=1.

## Control tokens and barriers

A coefficient-only queue is safe only if control events cannot overtake it. The simplest initial protocol holds band-end readiness and scratch seal delivery until all older coefficients have retired. A unified ordered token queue for coefficients and band-end events is a possible later implementation, but seal still requires the original line/debt fences.

| Existing interface/event | Required rule after adding elasticity |
| --- | --- |
| Metadata `meta_valid/meta_ready` | Establish one live allocation before accepting its coefficient tokens; queue must not expose old-owner tokens to a new allocation. |
| Coefficient | Accept into available queue capacity; retire in order only in a valid scratch ingest context. An invalid coefficient is an ordered error event, not silently dropped data. |
| Band end | Cannot overtake an earlier buffered/validating coefficient. Preserve coefficient-over-band priority when both are offered. Validate full epoch, band and committed count at retirement. |
| Packet `done` | Ingress may finish after enqueueing its last coefficient. Gate scratch seal with queue/validation empty as well as the existing allocation/seal-sent conditions. |
| Seal | Preserve `WAIT_SEAL`, full epoch, empty assembly/write-slot and outstanding-request rules. A token queue must not make an early `seal_ready` shortcut. |
| Replacement `start` | Kill old speculative tokens, preserve new-owner start priority, and do not allow old error cancellation to defeat ingress start. |
| Abort/reset | Invalidate speculative tokens and suppress their later writes/errors. Drain accepted physical requests using their captured request owner; do not erase debt. |

The actual child currently uses `packet_abort = abort_packet || (!start && running && store_error!=0)` and `store_abort = start || abort_packet || (running && packet_error!=0)`. Its error arbitration gives packet errors precedence over store errors when both are observed on the same child edge. A new queue must preserve this explicit arbitration or define and verify a replacement ordered-error contract. Adding latency can turn formerly simultaneous faults into different-cycle observations; that difference requires an intentional rule and tests, not an assumption that the old `if/else` automatically preserves causal priority.

## Cancellation, error and physical ACK debt

Scratch cancellation is `reset || (abort_valid && abort_epoch==owned_abort_epoch)`. `owned_abort_epoch` uses the queued allocation while begin preparation is live and the active allocation otherwise. A new token owner must agree with that allocation lifetime, including begin preparation and immediate retries.

Keep the current outer-priority behavior explicit: cancellation first; then unexpected/wrong-epoch memory response error 6; then drain handling; then owned prefetch/write response errors; then normal ingest/append actions. In `INGEST`, epoch mismatch remains error 2 before any format error 3. Do not OR all error classes into a generic failure bit. Retain coefficient-over-band-end precedence and the existing full band-end error 2 versus 4 distinction.

A queued or validating coefficient has no physical memory debt until an actual `mem_req_valid && mem_req_ready` write handshake occurs. It may be discarded by an authorized owner kill. Once a physical request is accepted, its `request_epoch`/address/data and outstanding credit must remain until the matching ACK. Cancellation cannot treat queue-empty as memory-drained. A mismatched response must not retire the true request, and a same-edge accepted request plus coefficient fault must still enter `DRAIN` when required. Clearing speculative token validity must not clear `outstanding` or invent a matching ACK.

Retries must cover the same epoch as well as changed epochs. Reusing only `epoch` as a pipeline owner is unsafe when replacement/start events use equal values. The existing allocator may reject nonmonotonic allocations; token killing still must work without relying on that rejection to prevent stale speculative side effects.

## Verification contract for a latency-changing branch

Keep V128 sources, exact-cycle receipts, old assertions, and tests immutable. Create a new candidate namespace and a manifest declaring the selected interface changes and added cycles. Exact old-cycle comparison remains a valid regression for V128; it should not permanently prohibit a pipeline with a separately reviewed latency contract.

Use two clearly separated oracles:

- **Semantic stream equivalence:** compare ordered accepted packet bytes, decoded coefficient tuples, band-end events, physical request address/data/epoch/type, matched ACK retirement, reconstructed dense outputs, errors and frame/publication hashes. Permit declared idle-cycle differences. Compare only transactions whose handshakes actually occurred; never delete a mismatching accepted event to align traces.
- **Timing and ownership correctness:** independently check every ready/valid hold, queue occupancy, accept-minus-retire-minus-kill conservation, owner lifetime, first-error ordering, seal barrier, bounded progress under a documented fair memory service, and exact physical-debt accounting. A latency-aware scoreboard must not hide duplicate/missing events or deadlock behind arbitrary timeouts.

Compare runs with handshake-aware drivers, using the same ordered payload and service scenario rather than blindly presenting an identical cycle schedule to different ready signals. Keep accepted external source transactions identical in no-cancel cases. For cancellation tests, label each accepted event by allocation and the explicit cancellation cut; compare committed events and permitted discarded speculative suffixes. When accepted counts differ because the new queue exposes additional capacity before cancel, report that difference and prove all extra accepted tokens were killed without side effects. Do not call those traces exact accepted-handshake equivalence.

Minimum added tests are: empty/full/simultaneous enqueue-retire; long output stalls; selected RAW/context crossed with stored format; full32 high epoch aliases; full16 block aliases; all eight phase encodings; arbitrary private rank masks for implemented-expression equivalence and separate coherent-owner mathematical checks; back-to-back valid tokens; every partial pipeline occupancy at reset/abort/start; same-epoch restart; band-end plus final coefficient; done/seal while tokens remain; malformed first/middle/last coefficient; simultaneous packet/store/memory faults; accepted write plus cancellation/error; wrong ACK followed by real ACK; matching ACK and new write acceptance on the same edge; and full-line flush/retry with no duplicate record.

Assertions must be moved only where their observation edge genuinely changes, with a documented old-to-new edge mapping and unchanged logical predicate. Preserve combinational invalid/unready views where they remain part of an interface. New registered views are owned by token-valid; do not claim arbitrary stale payload identity between differently clocked designs. No production `force`, new comparison-result backdoor, warning suppression, weakened range checks, or canceled ACK obligations are acceptable proof shortcuts.

## Measurement and selection gates

First prove a standalone elastic/token model and the actual candidate RTL under randomized stalls and cancellation. Then run the full source-bound decoder/transport/peer/parent path with latency-aware scoreboards and the existing frame/event hash oracles. Report accepted and committed throughput separately, validation II separately from scratch service II, queue high-water/credit stalls, physical-debt drain time, and min/median/p95/max latency.

Only then synthesize and route the exact candidate for the actual Series-7 part at 8 ns with the same reviewed clock/memory recipe. Inspect new worst paths, including ready, owner kill, status fanout and partial-validation-to-control paths. Registering data while leaving a high-fanout combinational global kill or ready chain can merely move the violation.

At 125 MHz, 10 ms is 1,250,000 clocks and a 30 fps frame interval is about 4,166,667 clocks. At 100 MHz those budgets are 1,000,000 and about 3,333,333 clocks. These arithmetic budgets are not achieved decode times. Added pipeline cycles must be counted across every coefficient, stall and flush, and reported alongside Wi-Fi/ESP32/QSPI transport and memory service assumptions. Sustained hardware 30 fps and validated under-10-ms hardware decoding remain separate open acceptance tests.

Select between the simple tuple cut and registered complete validation only after V128's actual route report identifies the remaining cone. Implement one bounded architecture first, preserve an immutable old comparison baseline, and use a new latency contract when the architecture genuinely changes public timing.
