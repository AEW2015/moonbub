# V127 three-lane owner-selection design

This bounded trial preserves V126's public interface and cycles. Preparation
is complete; strict focused execution and fresh physical routing have not run
at this design freeze. It implements the first comparison-factor option in
[V126 next timing](../cu66-v126/next-timing.md), whose final SHA-256 is
`8dfb7ec133a645184cf1fd0e293a8ba7211d7978581e0743b736fb851cfae9de`.
The broader [V126–V130 plan](../gamebub-v126-v130-timing-streaming-plan.md)
stays unchanged. No timing improvement is assumed.

V126's actual global route fails at −1.867 ns WNS/−4427.979 ns TNS/10868
endpoints. The worst path starts at scratch tile_overlap_mode, traverses
selected epoch/owner comparison and the ready return, and ends at scratch
state. Its 9.864 ns data delay includes 7.095 ns routing. The V126 producer
successor split makes cursor→current cache +0.246 ns but its state→new address
CE remains −0.086 ns. V127 is not permission to call that composition globally
closed or automatically preferred to the better historical V123 control.

## Exact three-origin scope

`fpga/experiments/cu66-v127-owner/` contains new versions of these selected
aliases; the other 15 of V126's 18 origins remain byte-identical:

| Alias | Frozen original | V127 delta |
| --- | --- | --- |
| cu66-v91g2/packed_scratch_v91g2.sv | V123 rank, SHA12ad7721… | Direct raw scalar epoch/block outputs only. |
| cu66-v91h/br88_pipeline_v91h.sv | V116b control | Forward those raw views through the existing internal child interface only. |
| cu66-v91k/cs88_coefficients_v91k.sv | V126 successor, SHA5dec7454… | Private raw-view wires and third scalar comparator before mode selection, plus additional verification identities. |

Scratch adds `debug_scalar_epoch[31:0]=active_epoch` and
`debug_scalar_block[15:0]=output_block`. Child forwards them as
`dbg_scalar_epoch` and `dbg_scalar_block`. There is no mode/valid/ready/reset
gate on a raw view. Producer privately connects `raw_scalar_epoch` and
`raw_scalar_block`; its top port list is unchanged. Every original state,
payload, memory interface, writer, reset and physical debt rule is retained.
The edit recipe classifies interface-only, comparator-factor and
verification-only edits separately, so interface changes cannot conceal a
functional mutation.

The existing `tile_owner_match[1:0]` equations and their two source KEEP bits
remain literal. No new synthesis attribute, state register, reset, timing
exception, hierarchy or placement directive is added. The third lane has no
attribute:

```text
bank_match[b] = bank_epoch[b] == current_child_epoch
                AND bank_block[b] == expected_block
scalar_match = raw_scalar_epoch == current_child_epoch
                AND raw_scalar_block == expected_block
owner_match = tile_mode ? bank_match[emit_bank] : scalar_match
```

All epochs remain full32 and blocks full16. The original selected epoch/block
outputs still feed public payload and all original assertions. Ready, valid
and DISPATCH error67 already share owner_match; their equations and branch
order do not change. Unlike the old fallback, the new scalar equality never
uses mode-selected epoch/block fields as inputs. Synthesis may still refactor
this identity; only a fresh route and mapped fan-in/query evidence can decide
whether the physical mode/owner return is shorter.

## Generic equivalence and priority contract

The source already guarantees selected epoch/block equal the chosen bank
fields on tile cycles, including invalid/unready cycles; non-tile cycles select
raw active_epoch/output_block. Choosing the exact scalar comparison after it
is evaluated is a two-state Boolean identity for arbitrary full-width fields.
No bank-ready/child-valid assumption is added. Both independent bank matches
and scalar match remain meaningful even when their lanes are not selected.
All old assertions remain literal; additional all-cycle scalar lane/view
identities certify the new raw connections without suppressing the old
selected-field equality through reset/abort/invalid cycles.

Producer reset/abort, accepted versus blocked raw start, queue fault, owned
child fault, DISPATCH foreign owner, and accepted index63 retain original
priority. uint16 expected-block wrap and the independent widened terminal
comparison are unchanged. V126 successor address/ROM payloads and all
verification owners remain unchanged. Scratch cancellation is matching-owner
cancellation; foreign abort does not revoke a lease. Wrong/unsolicited response,
DRAIN retirement, prefetch error, overlapping write error and final post-case
release ordering remain unchanged. Accepted request debt cannot be cleared by
an interface view or a parent expected-tag mismatch.

## Reversible preparation and packaging

`prepare.py` checks all selected V126 origin hashes before deriving the three
new modules. `edit-recipe.json` records exact forward/reverse substitutions
per source and zero added registers/cycles/attributes. `source-map.json` maps
three aliases to their new source and packaging hashes. Each
`*-packaging.json` is `v127-owner-single-module-packaging-v1`: one complete
lossless module fragment and no split offsets. Preparers do not invoke an old
preparer, write an old source, run compilers or select a result.

`prepare_verification.py` builds nine reversible adapters, four byte-identical
copies, an extended scalar probe and three authored verification inputs.
Original is the V126 producer with module renamed and the two added internal
child outputs bound to private verification wires checked against the actual
scratch scalar registers. Candidate is the V127 producer
with module renamed only. Both use the new interface-only child/scratch;
their old functional bodies are exact. This avoids strict PINMISSING without
warning suppression. Source closure separately certifies those interface-only
deltas. No baseline RTL/oracle is edited.

The scalar probe retains the complete source-extracted V126 successor wrapper
and appends exact V127 bank/scalar/selector comparison fragments plus the
scratch mode expression. Only the extracted comparator's current_child_epoch
name binds to `owner_expected_epoch`, avoiding collision with the retained
stage register. Original fragments, identifier binding and complete wrapper
text are recorded for independent reconstruction. The old full13/plane3
successor scalar checks still execute first and retain their exact counts.

## Focused test and raw-ledger contract

Two fresh strict Verilator models are required, with `--assert -Wall` and
strict C++ warnings, no warning downgrades or skipped original assertions.
The scalar top is `producer_scalar_probe`, compiled with
`verification/tb_owner_scalar.cpp`; CLI is one seed. The whole producer top
is `ready_probe`, compiled with `verification/tb_owner_factor.cpp`; CLI is
`generic|caller seed cases.tsv trace.csv`. Scalar/generic seeds are
127501/127502; actual caller seeds are127601/127602. The qualifier is owned by
the independent verification agent. Expected selector is
`experiments/python-gamebub-v127/owner/results.json`, schema
`v127-owner-selection-three-lane-focused-v1`.

The scalar log first emits unchanged `v126_successor_scalar_verdict`:
98304 cases,1190177 clocks,294912 holds,1120 cancel contexts, exhaustive
32768 full13/all-four-plane cases plus65536 random cases. It then emits
`v127_owner_factor_scalar_verdict`:24576 boundary cases plus65536 full-width
random cases,90112 clocks and270336 evaluations. The matrix covers eight
uint32 epoch boundaries, six uint16 block boundaries, all64 independent
scalar/bank equality patterns, four raw/tile-overlap mode encodings and both
emit selectors. Independent C++ selection of full epoch/block fields is
compared with both original selected-field and new three-lane RTL. Positive
scalar-only and bank-only match counts prevent correlated fixtures from
making the identity vacuous. Extracted generic scalar values are not natural
packet chronology or a formal exhaustive full32 proof.

The generic log first emits all five V126 records unchanged: retained cache,
V119 owner/nonce, V124 wire/clock owner, V126 successor campaign and its
275334-clock monitor. Retained dimensions include2048 prepared counters,
9216 owner cases plus250000 random nonce cases,466944 V124 wire cases,
1152 original clock cases,192 error67 cases,864 cancel cases,16 wraps,
336 holds and224 response contexts. V126's534 contexts,3664 campaign clocks,
1428 actual-writer primers and2236 nonprimer clocks remain separate and exact.
The original per-seed primer trace is retained; no new V127 predicate or
V126 payload/owner is forced.

The appended `v127_owner_factor_verdict` adds393216 boundary wire cases plus
32768 random cases,425984 total. Raw scalar tags and both banks vary
independently across all modes, selectors, ready masks and reset/abort masks.
These are unclocked generic prepared-domain evaluations; arbitrary invalid
raw fields do not claim a reachable child state. The inherited and new
all-cycle observers compare actual original/new values without adding an RTL
clock. The generic observer tracks each instrumented DUT clock level and counts
only low-to-high transitions; repeated evaluations while high are not new
clock edges. This ledger covers instrumented tick_owner edges, not unobserved
legacy Driver.tick activity. Actual caller callbacks supply an explicit
rising-edge flag.

The new sequential terminal-domain campaign adds1152 cases over eight epochs,
six blocks, three parent-owner outcomes and eight reset/abort/start overlaps.
It leaves each ready child's bank/active epoch self-consistent; only original
parent expected tags can be foreign. An unrelated unselected scalar block is
varied while tile mode selects the bank. Expect192 error67,864 cancellations
and16 uint16 terminal wraps. Existing terminal fixtures do not consume the
new V126 successor payload, so no synthetic certificate is created. Their
reset primers are honest fixture edges, not natural packet cycles. The total
additional raw ledger is2308 clocks:1152 test edges and1156 reset primers,
including wire-domain entry/exit resets. The inherited275334 monitor is
printed before these added clocks. The new strict equality retains both
components separately.

Actual caller runs retain every original packet/result row and appended V126
natural stage monitor, then append `v127_owner_factor_caller_verdict` with
measured evaluation/rising-edge/mode/selector coverage. The observer reads
actual raw-view/owner equalities on every evaluation, including held and
invalid cycles, with no extra clocks. Full public/private/cache/scale and
physical memory-debt pairs stay exact. Natural cases and prepared fixtures
are labeled separately. No source-selected error outcome, coefficient value,
format, order, public cycle or cancellation event may change.

All new records declare zero added public cycles, zero skipped pair edges,
zero original checks removed and zero new predicate forces. These are finite
strict two-state regression obligations, not formal/four-state equivalence,
CDC/reset qualification, sustained gameplay, routed timing, 30fps or a complete
validated decode under10ms result. Fresh timing must inspect mode/emit/scalar
lanes/ready and every remaining negative family, preserving adverse tradeoffs.
