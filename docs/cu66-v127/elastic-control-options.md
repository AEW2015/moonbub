# Future elastic owner-control cut

This is a source-grounded design option, **not implemented or qualified in V127**. V127 still requires exact Source B/V126 public-cycle equality. Its selected three-lane expression remains frozen. These notes do not predict the pending route result and do not authorize changing its sources or test oracles.

If the cycle-preserving expression is still globally negative, a later version can make a declared latency change at the dense-coefficient boundary. The useful cut is between the scratch emitter and the producer's DISPATCH/publication logic. Registering `child_owner_match` alone is unsafe: the comparison would describe a previous tuple while the current ready/valid handshake can consume a different one.

## Existing ownership and dependencies

| Actual source point | Existing contract | Consequence for a future cut |
| --- | --- | --- |
| `cs88_coefficients_v91k.sv` around 1120–1162 | Three full32-epoch/full16-block comparisons produce `child_owner_match`. It gates both `child_out_ready` and public `out_valid`. | Capture value, index and complete key together. Do not replace owner validation with ready, valid, bank-ready, a shortened tag or a cached comparison of a different tuple. |
| Producer DISPATCH around 1359–1368 | A valid mismatched owner causes error67 even when the downstream is not ready. Block progress occurs on accepted index63. | A new latency contract must explicitly define when an enqueued foreign owner becomes an error. Never publish it. Capture and publication need separate progress accounting. |
| Producer MAP_REQ/MAP_WAIT around 1342–1357 | Mapping fixes `mapped_tile`, `mapped_cell` and `mapped_scale` for the current plane/tile; accepted index63 then advances expected block and returns to mapping. | Do not advance mapped metadata merely because the upstream released its bank. Bind metadata when the corresponding queue head reaches DISPATCH, and keep it stable while public output stalls. |
| Scratch dense output around 308–315 and 763–769 | Tile-bank ownership is released at the emitter's accepted index63; scalar output has its own block/index progression. Two tile banks are not two generic output queue slots. | Once the new queue accepts a tuple, its own storage owns that value independently of the released tile bank. A pointer to a bank that may be overwritten is insufficient. |
| Scratch cancellation/response handling around 739–758 | Cancellation clears logical emission state but preserves accepted external memory debt. A wrong response epoch cannot retire the real outstanding request. | Flush unpublished local coefficients on cancellation; keep accepted memory request ownership and matching-ACK drain unchanged. FIFO-empty does not mean memory-quiescent. |
| Scratch tile retirement around 704–735 | An already-visible local tile write retires physically even across cancellation/reset. | Do not use a new queue reset to suppress that existing retirement obligation. Its assertions stay active. |
| Child `br88_pipeline_v91h.sv` around 124–130, 332–360 | Start/reset/abort suppress output; allocation, packet seal and scratch validation precede valid output; terminal done excludes output/running. | Queue acquisition must honor the validated child output. If it can outlive the child, extend completion fencing and retain the seal/error provenance until it drains. |
| Producer ALLOCATE/WAIT_DONE/start-ready around 1103–1113 and 1326–1371 | New child nonce allocation waits for child quiescence; WAIT_DONE waits for done, not busy, not draining. Start admission is similarly fenced. | New queue occupancy/completion debt must join these fences. Never allow a retry or next plane to reinterpret old queued coefficients. |

All references above are to the exact selected V127 source versions linked below. Line locations describe those bytes, not a future implementation.

## Bounded two-slot proposal

Start with a two-entry, no-fall-through queue **inside the producer**, at the child-output connection. Each entry owns `{outer_frame_epoch[31:0], child_epoch[31:0], block[15:0], index[5:0], coefficient[15:0]}`: 102 payload bits, or 204 for two slots before valid/control storage. This is a logical estimate, not a synthesized resource count. Full frame generation need not be copied blindly: first prove that the existing full outer epoch plus child nonce and flush/quiescence rules uniquely identify every queued owner. Preserve the existing nonce-overflow and frame-epoch rejection rules. Add generation to the entry if that proof exposes an alias.

The queue snapshots the **actual child epoch**, never the normalized public `out_epoch=frame_epoch` as a substitute for child identity. It can bind the outer epoch at acquisition because the producer cannot start another frame while these entries are owned. The proof must establish that invariant on reset, error and retry too.

The upstream `ready` must come only from local registered capacity and a local run/cancel permit. It must not include downstream `out_ready`, the wide owner comparison, mode/bank selection, tile/index terminal arithmetic or the producer's global state decode as a same-cycle return path. Initialize the local permit at child allocation and retire it on cancellation/completion with explicitly specified edge priority. Keep any immediate public reset/abort output mask local; reducing resets on payload storage does not remove cancellation semantics.

A conservative capacity rule is two slots, no bypass and no same-edge replacement when the queue was full. With occupancy one, simultaneous acquisition and publication retain occupancy one and can sustain one tuple each cycle. At full occupancy, a pop frees space for the following cycle. This accepts a recovery bubble after a full stall in exchange for a simple registered readiness boundary. If a registered ready FF is used, derive its next value from the exact post-edge occupancy including all accepted pushes/pops; reserve every advertised slot. Do not merely delay a full flag and accidentally grant a third acceptance.

Preserve a separate acquisition block expectation, advanced only when the child-to-queue handshake accepts index63. The public `expected_block` still advances only on public acceptance. Check a valid offered child's full nonce/block against the acquisition expectation independently of downstream readiness, including when the queue is full. Pipeline this check into a local fault/certificate register rather than feeding it back into upstream ready. A bad offered tuple must trigger a bounded fault even if no queue entry can be accepted; silently waiting for the consumer to free capacity would weaken the present foreign-owner behavior. If a bad tuple is accepted before that registered fault arrives, it remains provisional and must never reach publication. A queue entry must not become eligible for output ahead of its matching validation certificate. This requires checking all same-edge replacement and fault-priority cases, rather than assuming the second slot automatically supplies a sufficient validation delay.

On the downstream side, compare the registered head key against `current_child_epoch` and `expected_block` in the applicable context, then publish only a validated head. First prototype one additional registered validation stage if the head comparison still feeds a long consumer/state cone. Its certificate must be attached to that head's complete key and invalidated on head replacement, new block/context, error and cancellation. Splitting the comparison without these ownership rules would recreate a stale authorization bug.

Validation certificates must be pipelined and bound to each tuple key so ordinary steady-state can sustain one acquisition and one publication per cycle after pipeline fill. Prove the actual initiation interval with the real validation/queue control. Keep the intentional full-queue recovery bubble separate from that result. A head-only scheme that inserts a bubble for every coefficient could worsen the below10ms goal; two slots alone do not establish II=1.

Mapping remains a producer operation. On public acceptance of head index63, advance `expected_block`/tile cursor and issue the next mapping exactly once. The queue may already contain the first tuple(s) of the next block; hold them during MAP_REQ/MAP_WAIT and validate/publish them only after the next mapping context is installed. Do not report a next-block head as a foreign owner while the old block's terminal publication is advancing the context. Restrict acquisition to the allocated child/plane lifetime; crossing a plane or allocating another child requires the queue to be empty and the old child/memory drain complete.

This separates three debts:

1. **Captured dense tuples:** queue entries accepted from scratch but not yet accepted by the public consumer. These can be invalidated by cancellation before publication.
2. **Published tuples:** output handshakes already observed by the consumer. Cancellation cannot pretend they never occurred; downstream frame/commit validity controls their eventual visibility.
3. **Accepted memory requests:** external requests already accepted but not retired by the matching response/ACK. The existing drain owner persists even if both local queue slots are flushed.

The selected RTL currently advances scratch bank/index on `child_out_valid && child_out_ready` and advances producer block context on public `out_valid && out_ready && out_index==63`; these coincide today. The future design must deliberately decouple them and audit every counter or timestamp that currently assumes coincidence. Child done can consequently precede final public consumption. Retain child completion as a pending terminal fact until output debt is zero; extend WAIT_DONE, start-ready and next-plane fences rather than losing a pulse or finishing early. Error priority must be specified for same-edge child failure, malformed queued head, cancellation, public acceptance and memory response. Reusing V127's cycle equality checker would conceal or falsely reject that architectural change.

## Verification before another physical trial

Use a new version, source recipe and explicitly declared latency contract. Keep V127's published proof inputs unchanged. Start with a small cycle-accurate model of queue ownership and then a self-checking RTL wrapper around the real selected child/producer boundary.

Required cases include empty/one/full occupancy; repeated stalls; push/pop together; full-to-pop recovery; index62/63 and block transitions; queued next-block head during mapping; both tile banks and scalar/RAW mode; full32/full16 high-bit differences; foreign or stale frame/child/block; cancellation on each occupancy and on push/pop; immediate retry; nonce exhaustion; valid malformed owner while downstream unready; and child completion while coefficients remain queued. Exercise a matching memory ACK and wrong-epoch response on each cancellation case. The old bank-release and visible-write-retirement assertions remain active.

The new scoreboard compares ordered values, complete keys, positional mapping, errors and accepted request/ACK ownership. It separately checks the permitted latency range and bounded progress for each declared sink-stall profile; it does not excuse arbitrary delay. Record acquisition, validation, publication and terminal fences independently. Include a full queue with a continuously offered foreign tuple and an indefinitely stalled consumer: the bounded fault must still occur, with no invalid publication. Functional failure must remain distinguishable from a watchdog or interrupted process. Re-run the complete spatial decoder, actual V97 transport, peer fault injection and byte/row parent—including HUD/hash/seal/commit oracles—against the declared contract.

The physical acceptance gate is still a fresh 8 ns constrained implementation with all timing families, followed by an identical fresh repeat if positive. Inspect both directions of the new boundary: the old owner/ready/scratch-state path must end at the new local register boundary, and replacement occupancy, permit, validation, cancel and completion paths must also meet timing. Count added FFs/control sets and any bank-fanout regressions. No false paths, multicycle exceptions, new clock assumptions or ready-implies-owner shortcuts qualify it.

The goal remains 720×480, 30 distinct displayed frames/s over ESP32 Wi-Fi, followed by validated hardware decoding below10ms. At an assumed complete-parent125MHz, the retained row last-input→commit profiles are 9.160832ms and12.425576ms. A two-slot cut may help achievable clock frequency and may add latency; it does not by itself remove the stalled profile's303198-cycle excess over a strict10ms budget. Throughput, complete-parent timing, physical SDRAM and real ESP32/network measurements remain separate required evidence.

## Exact source references

- [Selected producer](../../fpga/experiments/cu66-v127-owner/cs88_coefficients_v91k.sv)
- [Selected scratch](../../fpga/experiments/cu66-v127-owner/packed_scratch_v91g2.sv)
- [Selected child pipeline](../../fpga/experiments/cu66-v127-owner/br88_pipeline_v91h.sv)
- [Current V127 contract](verification-plan.md)
- [Current bounded experiment](plan.md)

- `cs88_coefficients_v91k.sv` SHA-256 `a3b3f740ca033c626a7685c39a6774f6d5e13b2f374d492bce9cbe4af6079e04`.
- `packed_scratch_v91g2.sv` SHA-256 `8cd259792d2d7ea0c603117591e5e6033fbded7bacea10d598851f0cc5853ffc`.
- `br88_pipeline_v91h.sv` SHA-256 `0596dce08b8d38651eb303b531e971de604d5ad7f45818a4a2d0d222d0a049cb`.
