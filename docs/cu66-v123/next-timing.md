# V123 next timing proposal: bank owner qualification

This is a read-only source/report analysis and a proposed bounded next trial.
No production source, frozen focused input, constraint or implementation recipe
was changed, and no build or Vivado job was launched for this note.

The emitted routed reports for
`/home/lori/gamebub-build/cu66-v69/v123-rank-125-20261110T024405001928Z-98bc8c/results/`
show setup WNS **-1.086 ns**, TNS **-1709.649 ns**, and **6,724 failing
endpoints** at the existing 8 ns component clock. The setup report identifies
the new global worst path as scratch `emit_bank_reg/C` to
`busy_owned_reg/D`: 9.034 ns data delay, comprising 2.380 ns logic and
6.654 ns routing, through 11 levels: three CARRY4, six LUT6, one LUT3 and one
LUT2. The first emit-bank net has fanout 84 and 1.448 ns routing delay.
The next listed path reaches a scratch state register through the same owner
and ready return, with -1.011 ns slack.

These observations were read from `route-setup-paths.rpt` and
`route-timing-summary.rpt` while the native job was completing its remaining
reports. The parent must bind the terminal native receipt and report hashes.
Timing still fails. A different global worst path does not establish that the
entire previous RAW/rank family closed. The completed read-only queries report
RAW-mode all-endpoint slack −0.891 ns and rank-mask all-endpoint slack +0.159 ns;
RAW remains negative. See [the terminal results](timing-results.md) for receipt
and checkpoint hash bindings. No expected slack improvement is asserted for
this next proposal.

Both the current scratch source and the routed snapshot hash to
`12ad772136053d040d09770e0e98df6a49889757919993e3725c3ac70bafc5d7`.
The relevant source chain is:

| Site | Actual dependency |
| --- | --- |
| V123 scratch lines 304–311 | Tile-mode dense valid selects `bank_ready[emit_bank]`; block and epoch select `bank_block[emit_bank]` and `bank_epoch[emit_bank]`. |
| Selected V119 coefficients lines 1065–1066 | `child_out_ready` and output valid compare the selected full32 child epoch and uint16 block with `current_child_epoch` and `expected_block`, under DISPATCH/reset/abort gating. |
| Selected V116b child pipeline line 201 | Parent `child_out_ready`, running, error and cancellation qualify scratch `dense_ready`. |
| V123 scratch lines 260, 762–766, 1166–1168 | A 64th accepted tile coefficient releases its bank; the last-bank predicate then overrides the normal case result with done/FINISHED/busy=false. |

The physical report names `child_out_epoch[11]`, `child_out_ready3`,
`dense_ready0`, `dbg_tile_release` and the final busy decode along this path.
Thus emit-bank affects busy through a cross-module **owner comparison → ready
return → terminal release** cone. It is not merely a local busy-state decode.
The reported carry cells occur before `child_out_ready`; identifying which
epoch/block comparison implements each physical cell requires a fan-in query.
They must not all be attributed to the final bank-block-plus-one predicate.

The proposed first trial changes only owner qualification in the coefficients
wrapper. Its existing child outputs already expose both bank epochs, both bank
blocks, tile mode and emit-bank selection. Compute two independent full-width
match bits before selecting one:

```text
match[b] = (bank_epoch[b] == current_child_epoch)
           AND (bank_block[b] == expected_block), for b = 0, 1

owner_match = tile_mode ? match[emit_bank]
                         : original_scalar_epoch_and_block_match
```

Use the same exact `owner_match` for the two ready/valid equations and the
DISPATCH bad-owner error-67 condition at coefficients line 1238. Keep all
remaining gates and branch order literal. This factors the emit-bank selector
after two spatial comparisons, instead of selecting 32/16-bit fields before
their comparison. It adds no register, owner, credit, public cycle or payload
latency. Synthesis can refactor Boolean logic; the retained mapped cone and a
fresh route, including all-endpoint reports, must establish its actual effect.
Two parallel comparisons can also cost additional logic/routing resources.

The key two-state identity is exact for arbitrary unsigned32 epochs,
unsigned16 blocks and either bank selector:

```text
((s ? E1 : E0) == E) AND ((s ? B1 : B0) == B)
  == (s ? ((E1 == E) AND (B1 == B))
        : ((E0 == E) AND (B0 == B)))
```

Do not qualify a lane by bank-ready, child-valid, a presumed current epoch or
a presumed expected block. The original ready expression is evaluated even
when child-valid is false or the selected bank is unready. All such generic
values and bad-owner outcomes must remain identical. Non-tile RAW and sparse
output paths retain their original scalar owner equation. The existing bank
views must first be asserted to equal the selected child output fields for
every tile-mode cycle, including invalid cycles; this is not an assumption
that their payload always belongs to the current owner.

The coefficients wrapper's reset/abort and accepted-start handling remain
unchanged. Its refill-error branch precedes child-error handling, and both
precede the state case. Within DISPATCH, a valid bad owner produces error 67
before the last-coefficient acceptance branch. `expected_block` still advances
on precisely the original accepted index-63 edge, preserving uint16 wrap and
the separate widened terminal comparison with `selected_blocks`. A
combinational spatial comparison uses that live expected owner; it requires no
prediction or new-cycle ownership contract.

The scratch priorities must remain exactly as in source lines 736–757:

1. `cancel = reset || (abort_valid && abort_epoch == owned_abort_epoch)` wins.
   The selected abort owner is the queued epoch during begin preparation and
   the active epoch otherwise. Foreign abort is not cancellation.
2. Cancellation retains real outstanding debt in DRAIN unless a matching
   response retires it; a wrong response cannot release that debt.
3. Without cancellation, unsolicited or wrong-epoch response produces error 6
   and DRAIN/FAILED according to real outstanding ownership.
4. Existing DRAIN retirement precedes prefetch/write response-error branches.
5. An owned prefetch response error, then an owned overlapping-write response
   error, produces error 5 with the original retirement effects.
6. Only the remaining normal branch can perform case writes and tile release.
   A matching response error without prefetch/write ownership can still reach
   those case writes. It must not be replaced by a blanket response-failure
   exclusion.

Within that normal branch, the final tile finish at lines 1166–1168 remains
**after the case**, retaining its final same-edge state/done/busy override.
Moving it outside the normal branch could override cancellation/errors;
moving it before the case could lose its intended last-write priority.
Same-edge release/publish of different banks and opposite-bank ownership remain
unchanged. The FLUSH_LINE, WRITE_WAIT, READ_WAIT and PREFETCH_DRAIN return paths
retain the exact busy classification
`return_state != IDLE && return_state != FINISHED && return_state != FAILED`.
Busy cannot be deasserted merely because emission stalls or production finishes
while an owned bank or physical response remains.

A bounded verification plan must retain every current assertion/oracle and add:

- An independent equality between the spatial match and the original full32/
  uint16 selected-field expression, covering both banks, all mode/selector
  encodings and invalid/unready/child-invalid cycles. Include opposite-bank
  poison, duplicate tags, mismatches, equality-adjacent/high-bit epochs and
  full16 block boundaries; do not narrow tags or assume bank epochs agree.
- Exact ready/valid/error-67 comparisons through reset, abort, accepted/rejected
  starts, child/refill errors, DISPATCH/MAP/WAIT transitions and arbitrary
  downstream stalls. Bad-owner input must never retire or publish an output.
- Same-edge index-63 acceptance, emit-bank flip, expected-block increment/wrap,
  last-child WAIT_DONE transition, final scratch FINISHED override and busy
  deassertion. Preserve all metadata, payload, counters and event cycles.
- Every scratch cancellation/response overlap above, including current/foreign
  abort, matching error without a prefetch/write owner, wrong/unsolicited
  responses, pending read/write drain and matching final physical retirement.
- The existing unconditional same-edge
  `busy_owned == (state != IDLE && state != FINISHED && state != FAILED)`
  assertion, stable held-bank/payload assertions, and the final-tile absence of
  outstanding/prefetch/preparation debt. Do not suppress assertions for the
  cancellation or retirement edges.
- Strict generic and real-caller pairs against selected V123, then unchanged
  full-parent functional qualification and the fixed native route. Declare and
  verify zero added public/error cycles and zero skipped pair edges. The
  expected timing effect remains a hypothesis until measured.

These obligations concern finite two-state generic semantics unless a separate
formal or four-state proof is performed. This note establishes no new RTL
qualification, timing closure, CDC result, throughput or hardware result.
