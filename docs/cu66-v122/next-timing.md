# Bounded timing experiments after V122

Select the next experiment from the final routed global and targeted reports.
The source review below identifies candidates; it does not measure improvement
or authorize combining changes until attribution is lost. Preserve V122 as the
exact-cycle functional control and qualified 100 MHz Source B as the remote
board control. Keep the unchanged 8 ns fresh-RTL recipe for comparison.

## Measured RAW-to-scratch ordering cone

The [final route](timing-results.md) makes this the first next target:
RAW-mode → scratch state is −1.949 ns, 18 levels and 9.896 ns data delay.
The mapped RAW source has fanout 102. Source inspection connects the geometry
mux in [ingress](../../fpga/experiments/cu66-v120-range/br88_packet_ingress_sync_v91h.sv#L489),
the pipeline's direct tuple wiring, and sparse ordering/phase/range/error
validation in [scratch](../../fpga/experiments/cu66-v119-scratch/packed_scratch_v91g2.sv#L369)
to the INGEST state decision. Scratch `coef_ready` itself is a simple state/cancel
predicate; registering it alone would change the handshake and miss the measured
validation cone. Netlist hierarchy names do not identify each LUT's exact
Boolean function, so retain the mapped path and source-level interpretation.

A separate zero-cycle trial can precompute a **64-bit raster-rank threshold
mask** on the existing APPEND edge that writes `previous_position` from
`pending_position`. For input raster index `k`, store
`zigzag(k) <= pending_position[5:0]`. At the next valid INGEST, perform the
16-bit block comparison in parallel with the mask lookup. Preserve the full32
ordering predicate:

```text
previous_position[31:22] != 0
  OR coef_block < previous_position[21:6]
  OR (coef_block == previous_position[21:6] AND rank_mask[coef_index])
```

This targets the rank → full-width sparse-position ordering carry chain.
It is a proposed application-specific hardware decomposition, not an implemented
or measured speedup. Bind the mask to the same APPEND owner, epoch, phase and
full32 position; use `pending_position`, not the old previous position, on that
edge. `previous_valid` remains authoritative. Unowned mask payload can remain
unreset only with proof that every consume sees the correct fresh owner.

Before routing, compare the decomposition to the original full32 comparison for
all 64 indices, full16 block boundaries, full32 previous positions, high bits,
equality±1 and rank/block transitions. Exercise all eight phase encodings,
both RAW values and overlapping value/range/zero/epoch/count faults; retain
error2-before3 and every independent input/record-shadow oracle. Cover APPEND
returns through FLUSH_LINE/WRITE_REQ, first events, band/commit invalidation,
reset, matching/foreign abort and all response priority overlaps. In particular,
do not replace the original unowned-response-error fall-through behavior with a
broader cancellation condition. Bad input must never flip the record-view bank
or publish a pending tuple. Compare every public edge, packed byte and physical
memory event to the declared frozen control, with natural cycle delta0.

The prepared admission stages have positive local slack, while the remaining
cursor/state family is −0.250 ns. Keep both V121 and V122 failed source
compositions; name the next trial's exact control before applying a change.
Neither is a qualified 125 MHz handoff. Source B100 remains unchanged.

## Remaining plane-start decision

V122 intentionally leaves `PLANE_BEGIN`'s literal uint32 `cursor+4>residual_end`
guard unchanged. If that path still dominates, prepare its one-bit result on
each actual predecessor edge and consume it at the existing `PLANE_BEGIN` edge.
There are three natural predecessors:

| Predecessor | Operand for preparation | Ownership obligation |
| --- | --- | --- |
| Successful `Q_CHECK` cache reuse | `uint32(residual_start+4)` | Cursor and plane0 are assigned on this edge; old cursor is wrong |
| Successful terminal `Q_RUN` | `uint32(residual_start+4)` | Original terminal/run-count checks authorize plane0 |
| `PLANE_NEXT` | `uint32(cursor+4)` | Cursor was committed by the prior chunk edge; only plane/state change here |

Captures can be unconditional within the predecessor state; rejected captures
are unowned. This keeps the full error-decode success cone out of the payload
D path. Every actual consume still needs independent epoch, end, cursor,
successor-plane and predecessor ownership checks. `PLANE_NEXT` on plane2 goes
to `COMPLETE`; that extra capture must never authorize a fetch.

Keep original Q_CHECK first-fault priority, Q_RUN terminal-before-run-byte
priority, zero-word empty-plane and nonempty chunk cursor updates. Exercise
equality±1, the full32 range and especially `0xfffffffc..0xffffffff` wrap.
The plane-start guard wraps uint32; the existing length bound widens to full64.
They must never share a truncated arithmetic result. Keep every V122 full64
sum assertion and old independent oracle unchanged.

At each capture and consume edge, test all seven reset/start/abort overlaps,
nonreset retries and new epochs. No canceled payload may authorize a later
fetch. Add explicit coherent prepared-domain plane3→0 tests if the generic
two-bit plane wrap contract is claimed. Compare every original public output,
descriptor, fetch event, counter and natural cycle to V122; target delta0.

## Prepared-stage enable cones

The V122 full64 cursor base and uint32 number sum share `WORD_BYTE && index2`.
The partial-word sum uses `FETCH_REQ && index3 && return==CHUNK_LENGTH`; the
final-byte sum uses the corresponding `FETCH_WAIT` qualifier. Source widths
do not establish mapped FF count or physical fanout; use the routed inventory.

If one of these *new* enable cones becomes critical, test enable simplification
separately from the plane-start change. A possible trial captures the two wide
stage payloads on every `FETCH_REQ`/`FETCH_WAIT`, dropping index/return qualifiers
only for those captures. Every real final-byte length sequence still refreshes
the full64 payload on its original edges. Extra captures remain unowned; final
predicate qualification and ownership assertions stay unchanged. Require the
same full functional gates and fresh source-bound native route.

## Other path families and system budget

Inspect RAW mode/coefficients, context-emitted and kill/response paths even if
admission improves. Use local readiness and accepted-transaction ownership,
versioned latency-aware interfaces where needed, and independent cancellation
proofs. Avoid a broad reset/enable rewrite that changes several cones at once.

None of these timing hypotheses shortens the unchanged parent cycle count.
The [memory experiments](memory-next.md) separately address reconstruction,
accepted-write service and validation overlap. A faster component clock,
complete-parent <10 ms and sustained distinct hardware 30 fps need their own
evidence.
