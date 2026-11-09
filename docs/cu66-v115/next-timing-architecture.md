# Next timing architecture after V115

This is a source-derived contingency, not implemented RTL or a measured timing improvement. The owner-certificate and final request-bounds candidates are undergoing qualification separately. Re-evaluate this order using their final routed paths before adding stages.

## Evidence and actual cones

The refined 125 MHz routed report is `/home/lori/gamebub-build/cu66-v69/v115-integrated-125-20261109T024836651775Z-7eb017/results/route-setup-paths.rpt`, SHA256 `083e7a0c794e35d21c9af0cffefc6cdeafd1c6b1154a17c5dfc4feed29bbcea6`. It targets `7a100t-csg324`, speed grade -1, period 8 ns.

| Actual start → endpoint | Slack | Data delay | Evidence |
| --- | ---: | ---: | --- |
| `owner_open_reg` → `count_publish_release_same_edge_reg[60]/CE` | −3.067 ns | 10.778 ns | 12 LUT levels; 8.834 ns routing (81.96%); owner fault/mask → coefficient boundary kill/fence → inverse ready → boundary ready → scratch dense ready → tile release → 64-bit counter CE |
| scratch `read_address_reg[3]_rep__1` → `heads_reg_0_3_6_6/SP/WE` | −3.013 ns | 10.396 ns | 10 levels including two CARRY4; 7.988 ns routing (76.84%); selected cache byte/word → sparse position/domain validation → head-write enable |

These are separate from the worst owner-sequence comparison now being cut. The first destination is instrumentation, but the path passes through real data/control decisions. Merely deleting counters would hide one endpoint without proving the ready chain meets timing. The second is an actual distributed-memory write enable, not a multiplier.

## First bounded option: two-entry coefficient boundary

The current `cu66_coefficient_elastic` has one 130-bit payload plus two static-check flags. Its `in_ready=active&&!kill&&!closed&&(!full||out_ready)` directly includes inverse readiness, and `output_done` depends on queue/final-offer state. A two-entry FIFO can remove the **downstream-ready** term from producer readiness: advertise capacity from local registered occupancy only, then enqueue/dequeue independently. Use two complete tuples including both epochs, plane, scale, block, tile, qcell, index, value and the same metadata/domain flags. Do not buffer flags separately from their tuple.

A conservative version uses `in_ready = local_active && !local_closed && occupancy<2` plus the required immediate masks, with no full-plus-pop look-through. A full queue that pops cannot accept another item until the next edge; that one recovery bubble is an explicit contract change. Empty-to-nonempty output may remain registered, so there is no combinational bypass. Capacity is exactly two tokens, not an unbounded queue. Two slots preserve sustained one-token-per-edge operation when occupancy is one; sustained full-state stalls are assessed separately.

**Important limitation:** this FIFO alone does not remove `owner_open → qualified_fault → cancel/kill → ready`. Immediate public revocation must remain combinational. The current top also gates `coefficient_ready` with `transfer_enable`; the producer sees that gate. Do not claim that registering occupancy removes all owner-open paths. A subsequent cut would need an explicitly private, bounded cancellation/grant boundary: registered local capacity grants, immediate top-level public masks, no new grant after revocation, and at most one already-granted private token retired/discarded before local flush. That changes internal acceptance/counter cycles and requires its own contract. It cannot be introduced by silently removing kill gates.

Required proof contract:

- Accepted minus emitted minus explicitly canceled tokens equals occupancy, always in 0..2. A simultaneous enqueue/dequeue must preserve ordering and owner tags, including equal payloads with distinct owners.
- Stable complete head tuple/flags while offered and stalled. No accepted stale tuple following reset, new command, peer fault or external abort. Check every occupancy, simultaneous edge and final-offer state.
- Input-done remains a fence after the final accepted token; preserve the existing case where done arrives with a stalled last offer. Done cannot overtake either slot. No next-owner token crosses the old fence.
- Public valid/ready/request outputs revoke on the original fault/abort edge. Physical memory/reference requests already accepted still drain before credit/retry. No second owner is admitted to “use up” spare FIFO capacity.
- Keep original 78 control checks, four physical drains and the deliberate stale private-tag fault. Add all two-slot cancel/reset occupancy cases and full canonical retries. For declared new latency, compare ordered values/owners/faults with an independent FIFO model; keep the old exact-cycle checker immutable and do not relabel its expected mismatches as a pass.

## Low-risk instrumentation cut to evaluate first

Capture `dbg_tile_publish && dbg_tile_release` into a one-bit local event register and increment the wide count from that register on the next edge. This cuts the real long event cone before 64 counter CEs. Preserve simultaneous publish/release semantics exactly, and capture the event's original cycle for any timestamp. Drain the pending event before a measurement snapshot. Reset behavior must specify whether the preceding interval's event is included or discarded; do not accidentally count an old-owner event in a new owner's counters.

This is an explicit one-edge counter-read contract unless a separately proved forwarding view is provided. Forwarding a 64-bit counter-plus-pending value can recreate a wide output cone, so report both options rather than assuming it is free. Original exact-cycle counter checks remain in the baseline; a new checker must prove `visible_total = retired_total + pending_event` at declared observation fences. This cut may expose the same owner path at another endpoint and is not a timing-closure claim.

## Second bounded option: prepare selected read word before AC extraction

The refined scratch already prepares tag hit on `AC_FETCH`, and forwards a matching `READ_WAIT` response hit into the existing `AC_EXTRACT`. However `read_word`, `read_position` and four bank-local validation predicates still shift/index cache data using registered `read_address[3:0]` in `AC_EXTRACT`. That selected-word/validation chain reaches the `heads` RAM write enable in one edge.

Use one owned prepared read tuple: selected 32-bit word, 19-bit decoded position, band/segment, selected byte offset/line and epoch, plus validation facts that can be computed without a new dependency. Capture a cache-hit tuple on the existing `AC_FETCH` edge using the **same future full address** as the address register; forward a matching response tuple on the existing `READ_WAIT` completion edge. The response path must select from `mem_rsp_data`, not the cache register's old value. Prepare the position from exactly the same bits as `cache_positions`; retain zero extension, signed 13-bit domain checks, band/rank rules, block bound and strict monotonicity against the relevant band's prior head position.

This can preserve extraction cycle count: the existing fetch or response edge feeds the existing extract edge. It must not require a speculative memory response or consume a miss tuple. If computing address plus byte select plus validation on `AC_FETCH` merely moves the critical path, split only the needed offset/selection facts earlier on the existing `AC_CHECK` edge, with warmup/hold proof. Do not register all context globally and create another high-fanout owner signal.

Required proof contract:

- A prepared-valid certificate names exactly the current segment, full line, byte offset and active epoch whenever `AC_EXTRACT` consumes it. Assert selected word/position equal the original cache algebra on consumption, then keep the original validation assertion unchanged as an independent reference.
- Validate read miss, hit, matching error, wrong epoch, late unsolicited response, prefetch completion/replacement and abort/reset on each preparation edge. A bad response cannot certify data; physical outstanding ownership remains until the matching response drains.
- Preserve the exact outer-priority guards and the old late-error behavior. Current scratch deliberately allows certain late writes under matching error cases; do not replace its priority chain with an over-broad `!response_failure` gate.
- AC_CHECK may consume an existing head while another band has a prepared tuple. No mixed band/ordinal and no cached payload surviving into a later owner. Held tuples must remain stable or be explicitly invalidated, never partially updated.
- Compare all raw `heads`, `head_positions`, `head_valid`, cursors, caches and all 128 visible tile words on each original checked edge. Keep all original 72 full, 128 corrupt, four read-owner and 48 boundary checks plus descriptor pending-cancel/retry and forwarded tile-slot cases. Add offset 0..15 coverage (including zero-filled shifts beyond the 128-bit line), all four segment encodings and all three live AC bands; preserve all original bit casts rather than constraining the test to legal aligned offsets only.

## Gate before adoption

Qualify one local change at a time under strict assertions and unchanged warning policy. Then run the actual 18-body spatial/peer/control composition and complete canonical retries, preserve raw failures, and perform native placement/routing for both requested clocks. Count, publication, hash and physical drain results must be reconciled at declared fences. Neither these source-derived cuts nor a 125 MHz component timing pass would establish sustained hardware 30 fps or validated under-10-ms full-frame decoding.
