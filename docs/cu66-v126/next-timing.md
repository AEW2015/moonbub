# V127 next timing proposal: mode/owner and readiness return

V126 preserves the qualified functional stream/cycle behavior, and its fresh
125 MHz route **fails global setup timing**. The producer address/ROM split
improves its targeted path, while the complete composition worsens. This note
proposes future trials only; no selected source, proof input, constraint or
execution recipe was changed for this analysis.

The sequence and qualification requirements remain those in the
[V126–V130 plan](../gamebub-v126-v130-timing-streaming-plan.md). That plan's
SHA-256 is `d70d0fc7e8313e58b27945f20c6873bd738fdfb6f443ec3a69f92db2f9acd87b`.

## Frozen V125 comparison

The frozen [V125 next-timing review](../cu66-v125/next-timing.md) binds final
WNS −1.224 ns, TNS −2209.865 ns and 8027 setup failures. Its global producer
cursor→current-cell-cache path is only 0.005 ns worse than the scratch
emit-bank→state family. Global 125 MHz timing therefore fails independently
of the measured V126 local producer improvement.

The V125 matched report
[emit_bank-to-scratch_state.rpt](../../experiments/python-gamebub-v125/request-inspection/candidate-20261110T072031933927Z/emit_bank-to-scratch_state.rpt)
(SHA-256 `0ecf900593630835a991456da201910096f974f75125112ef35bca88a1cbfc2f`)
reports `scratch/emit_bank_reg/C` → `scratch/state_reg[0]_rep/D`:
−1.219 ns slack, 9.166 ns data, 2.777 ns logic and 6.389 ns route, with
13 levels (three CARRY4, nine LUT6, one LUT5). Its initial emit-bank net has
fanout 79 and 1.183 ns net delay. Named intermediate nets include
`child_out_epoch[4]`, `coefficient_valid_INST_0_i_2`, `dense_ready0`, and
`busy_owned_i_14`/`busy_owned_i_7`, followed by state decode and replication.
The report supports a selected-metadata→owner/ready return→local state cone;
it does not by itself identify the arithmetic meaning of every carry cell.

V125's same query reports emit-bank all-endpoint slack −1.219 ns. Other
residuals include group-end→coordinates −0.644 ns, tile→coordinates −0.464 ns,
admission cursor all-endpoints −0.498 ns, and tile→new hidden-predicate D
−0.191 ns. The hidden predicate's outgoing family is +0.182 ns. Those facts
remain baseline observations. The matched V126 results below measure those
families and both new producer stages. Physical placement can change an
unchanged origin's paths.

## Terminal V126 result and matched queries

The terminal [native receipt](../../experiments/python-gamebub-v126/native/20261110T152207460876Z/receipt.json)
hashes to `d7ff370aacaf9de39326704f07478c70b45624280905029bafd78ac82e9029a2`.
It reports WNS **−1.867 ns**, TNS **−4427.979 ns**, 10868 failing setup
endpoints; WHS +0.088 ns and minimum pulse slack +2.750 ns have zero failures.
All 73846 routable nets are routed, with zero routing errors and zero
unconstrained internal endpoints. External I/O remains unqualified: 1101
inputs and 12884 outputs lack delay constraints. The status is component
route finished/signoff open, not a qualified full board parent.

The independent [native audit](../../experiments/python-gamebub-v126/audit/native-independent.json),
SHA-256 `9835508499cdaf017f78526da27c41aee70d40a2c723d0283f0f1a975eaef4c0`,
passes 1412 integrity checks and explicitly has `design_timing_pass=false`.
Its PASS binds evidence; it does not convert negative slack into a pass.
V126 functional qualification retains zero public-cycle change across the
four spatial (decoder and transport), two control/peer and four live-parent streams. That finite
functional result does not qualify physical timing or a gameplay corpus.

The routed checkpoint is 28430879 bytes, SHA-256
`566a7357ffdbfb68aa581367a7d34fe113c30cac48a507ecefb98a4e809d7cbb`.
The [candidate query receipt](../../experiments/python-gamebub-v126/pipeline-inspection/candidate-20261110T154901503581Z/receipt.json)
hashes to `9284ecc6e6774e38542532976c82f8c31ae71a2a13efbb0f07dc04b3d67d01d2`.
The [129-family matched summary](../../experiments/python-gamebub-v126/pipeline-observations.json)
hashes to `01481f0631d4ce7bab53ba10c48f211ba8a5839700f96771bf7820524e54c956`;
its baseline receipt is
`pipeline-inspection/baseline-v125-20261110T131624745862Z/receipt.json`,
SHA-256 `8cbf3cef787b17f7cd56f9bdc0e865c4b790fc517a1565a951efab4d5d051ae9`.
These are read-only observations of existing routed checkpoints.

| Selected worst slack (ns) | V125 | V126 |
| --- | ---: | ---: |
| Producer cursor → original cell cache | −1.224 | +0.246 |
| New prepared address → prepared ROM cell | absent | +0.256 |
| New prepared ROM cell → original cache | absent | +4.802 |
| Producer state → new prepared address | absent | −0.086 |
| Producer plane → original cache | +0.864 | −0.486 |
| Producer state → original cache | −0.323 | −0.698 |
| Producer plane, all endpoints | −0.474 | −1.223 |
| Scratch emit bank → state / all endpoints | −1.219 | −1.813 |
| Admission cursor, all endpoints | −0.498 | −1.020 |
| Admission tile → coordinates | −0.464 | −0.045 |
| Admission group end → coordinates | −0.644 | +0.007 |
| Tile → prepared hidden-predicate D | −0.191 | +0.086 |
| Scratch RAW mode, all endpoints | −0.855 | −1.100 |
| Scratch RAW position, all endpoints | −0.730 | −1.012 |

The state→new-address failure is at address bit1 **CE**, not its arithmetic D
input. Plane's all-endpoint failure reaches admission scale RAM `WEBWE[0]`;
it must not be mislabeled a cache-only problem. New address inventory has all
13 unique bits in 50 physical FFs; new cell has all 11 bits in 11 FFs: 61
physical FFs for 24 logical payload bits. Verification owner FFs are absent.
Producer state declares eight bits while five named bits map; that gap grants
no source narrowing. The complete design grows by 322 LUTs and 110 FFs versus
V125; routed control sets remain 1252. Owner-net KEEP properties are blank,
so source attributes/names do not prove preserved physical lane separation.
Retain reported absent/unreturned paths as gaps, never as positive slack.

Global WNS worsens by 0.643 ns, TNS by 2218.114 ns and failures by 2841
relative to V125. The historical V123 composition (WNS −1.086 ns,
TNS −1709.649 ns) remains a better global comparison, although it also fails.
Keep both controls. Do not automatically promote globally worse V126 merely
because its intended successor split works locally; unchanged origins can
move adversely after mapping/placement/routing without an RTL regression.

## Routed mode/owner path, distinct from placement

The actual global routed path starts at scratch `tile_overlap_mode_reg/C`
and ends at `state_reg[1]_rep__0/D`: −1.867 ns, 9.864 ns data comprising
2.769 ns logic and 7.095 ns route; 13 levels contain two CARRY4, nine LUT6,
one LUT2 and one LUT3. The first mode net has fanout133 and 1.262 ns delay.
It reaches selected `child_out_epoch[14]` (0.831 ns net), coefficient-valid
comparison logic/carry, `child_out_ready` (fanout5), `dense_ready0` (fanout13),
release decode (fanout24), then done/state. The source equations below support
a mode→selected-owner→ready-return interpretation; identifying each carry's
specific epoch/block function still requires mapped fan-in evidence.

The earlier **placed** worst path was command_pending→reconstruction
accepted_start→reset/control→transform readiness→coefficient boundary→scratch
release: −1.625 ns, 9.622 ns data with 7.492 ns *estimated* routing and 13 LUT
levels. Its reset net fanout was1287. It is a distinct placement-stage
observation, not the final routed worst path or an additional measured routed
slack. Both reports remain in the terminal native bundle at
`/home/lori/gamebub-build/cu66-v69/v126-producer-125-20261110T151648420476Z-3888d5/results/`.
The routed report is `route-setup-paths.rpt`; the placement report is
`place-setup-paths.rpt`. Neither makes a local terminal predicate alone a
complete remedy for the upstream readiness/owner return.

## Source-bound dependency and existing edges

The selected scratch is
[packed_scratch_v91g2.sv](../../fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv),
SHA-256 `12ad772136053d040d09770e0e98df6a49889757919993e3725c3ac70bafc5d7`.
The prepared V126 producer is
[cs88_coefficients_v91k.sv](../../fpga/experiments/cu66-v126-producer/cs88_coefficients_v91k.sv),
SHA-256 `5dec7454e6bfae4f7a9d7f64ecfbef8568665ddaa2dc00d4a76de1167a3c7292`.

| Actual source site | Dependency or ownership event |
| --- | --- |
| Scratch 304–311 | `emit_bank` selects ready, full16 block, full32 epoch and payload. |
| Producer 1120–1128, 1148–1149 | V124's two full32/full16 comparison lanes are still present, with the original two-bit KEEP attribute. The selected match drives both ready and valid, including invalid/unready cycles. |
| Child pipeline 201 | Parent ready returns to scratch through running/error/cancel qualification. |
| Scratch 762–765 | Accepted index63 clears the selected bank's ready bit, clears index and flips emit bank. |
| Scratch 1078–1080 | Valid DESC1 initializes bank0 block0/active epoch and begins preparation. |
| Scratch 1111–1114 | AC_CHECK publishes the prepared bank; its metadata already exists. |
| Scratch 1155–1159 | BANK_WAIT allocates the opposite free bank and writes wrapped full16 next block plus active epoch. |
| Scratch 1166–1168 | After the state case, terminal accepted release overrides done/state/busy. |
| Scratch 981, 1065, 1153 | Write/read/prefetch return paths decode stored return-state busy class. |

The routed selected epoch path shows that the existing combinational lane
source does not establish a physically separated owner return. Neither source
KEEP text nor a net name proves that the full mapped comparison cones remain
independent. Repeating that factoring alone is not a new registered cut.

## Bounded cycle-preserving options

The actual mode→selected-tag→owner path supports testing **three independent
full-width owner comparison lanes**: two raw bank lanes plus a scalar lane
using raw `active_epoch` and `output_block`, before selecting one-bit results
with tile mode and emit bank. Current producer 1127–1128 uses already-selected
child epoch/block for its scalar fallback, allowing mode into wide selection
logic. Expose direct raw scalar views through the source hierarchy if this
bounded trial is selected; do not substitute assumed current tags. Prove the
new expression equals the original for every mode, bank selector, full32/full16
value and invalid/unready cycle, including reset and cancel. Use it
consistently for ready/valid/error67, preserve the existing two source KEEP
bits exactly, and add no new synthesis/placement attribute. This Boolean
factor is not guaranteed to remain separated in synthesis; route and query
mode/emit, all three lanes, full tags and ready/state endpoints. It changes
more interface/source scope than a scratch-local predicate and must be
qualified as that specific trial rather than silently folded into V126.

A smaller local tail subtrial is **two registered per-bank terminal
predicates**, prepared with the
existing bank metadata. Proposed names are `prepared_bank_terminal[1:0]`;
these names are proposals, not present selected RTL. At each original metadata
write compute exactly:

```text
prepared_bank_terminal[b] = (uint17(new_bank_block[b]) + uint17(1)
                            == blocks)
```

At DESC1 the new block is zero. At BANK_WAIT it is the original **full16
wrapped** `prepare_block+1`; widen that assigned value before adding one for
the predicate. Computing `uint17(prepare_block)+2` instead loses the original
wrap behavior at 65535. `blocks` remains full17, including 0/1/65535/65536 and
unreachable generic values. Preserve equality rather than substituting ≥.

The final accepted-release test would select this one-bit predicate instead
of selecting a full16 block and then doing widened arithmetic. Keep every
other release/valid/ready gate and its position after the case literal.
Preparation precedes AC_CHECK publication, so no public cycle or bank credit
is added. The ready bank owns the corresponding predicate; clearing ready on
cancel/release and BEGIN_COMMIT makes stale private payload unobservable.
Verification-only keys must bind the sampled full32 epoch, full16 block and
full17 limit and prove maturity before every consume. New payload need not
receive a blanket runtime reset. No combinational recomputation fallback,
new KEEP/DONT_TOUCH, placement directive or timing exception is proposed.

This removes a local arithmetic/select tail; it does **not** remove the live
parent owner comparison or external ready return. The routed carry cells before coefficient-valid cannot all be credited to
this tail. Measure the new predicate's input as well as output and reject an
input-cone regression.

A separate optional subtrial is a registered `return_busy` sibling of every
original `return_state` write: capture the exact target's classification
`target!=IDLE && target!=FINISHED && target!=FAILED` and consume it only at
the original return sites. Include constant targets and `output_plan.next_state`.
No return may occur without its original matching payload/write predecessor.
Preserve the unconditional `busy_owned == state classification` assertion at
scratch 1283–1289. Query return-state→busy/state first; do not bundle this
change merely because it is source-local. It cannot remove an owner/ready
path that bypasses the return decoder.

## A larger registered owner cut requires a complete poststate contract

A registered pair of exact owner-match bits is a distinct alternative to the
observed selected epoch→owner→ready cone. A simple
one-cycle sample is incorrect: expected_block advances on accepted index63,
emit bank flips that same edge, metadata can publish/reallocate, and
current_child_epoch changes on ALLOCATE. Both banks' full32/full16 matches
must reflect **postedge** keys and metadata immediately, including invalid
and unready cycles, because V124's unconditional all-tile-cycle identities
are retained. Bank-ready/child-valid gating is not an owner proof.

Such a trial needs a source-bound writer ledger for scratch DESC1/BANK_WAIT,
parent reset/abort/accepted_start, PREP_PLANE expected-block reset, ALLOCATE
nonce assignment, and DISPATCH expected-block increment. Forward simultaneous
writes with exactly their existing NBA priority. Keep the bank's raw fields,
active child lease, and the parent's expected owner distinct; induce bad-owner
fixtures by coherent parent mismatches, not by corrupting a ready child's own
active-epoch invariant. Duplicate/opposite-bank tags, invalid cycles, full32
high bits and full16 wrap remain legal comparison cases. Initialization and
the first all-cycle comparison must be proved without weakening an old
assertion. This larger cross-module contract is a separate candidate whose cost must be
justified against the measured mode/owner and global readiness-return cones.

## Explicit elastic readiness option

The selected top `cu66-v115-owner/cs88_pipeline_v91k.sv` lines231,239–240 and
251–262 deliver accepted_start from command_pending, form immediate public
revocation/transfer masks and peer cancels, and return boundary_ready to the
producer. Selected `cu66-v116b-domain/cu66_coefficient_elastic.sv` 889–895 has
one registered token but `in_ready=active&&!kill&&!closed&&(!full||out_ready)`.
Its full-slot replacement lookahead propagates transform staged_ready
upstream. Selected transform `cu66-v117-throughput/cu66_inverse_stream_v91j.sv`
979–983 includes reset/start/cancel/fault in kill and input ready. Thus an
existing payload register does not establish registered backward readiness.

If existing-edge preparation/factoring cannot close this cone, a separately
reviewed **`v127-owned-bank-return-v1`** contract should use a finite two-slot
coefficient queue and registered local capacity/credit, with no same-cycle
downstream-ready lookahead on ingress. Retain the complete 130-bit tuple
(frame32, child32, plane2, scale2, block16, tile13, cell11, index6, value16)
and its per-token metadata/domain interpretation. Merely delaying ready with
no storage loses a token when the downstream stops. Full→not-full can insert
a bubble; no zero-public-cycle claim or old global cycle equality is valid
for this alternative.

Require accepted−delivered−canceled=occupancy in[0,2], no duplication or
reordering, exact full keys and first faults, stable stalled tokens and correct
simultaneous push/pop. The end fence must wait behind queued tokens and a
final stalled input offer; output_done cannot bypass either. Define minimum
acceptance-to-delivery latency (one cycle for a registered queue) and bounds
under an explicit service envelope. There is no finite unconditional maximum
under arbitrary downstream stall; a two-token queue can promise at most two
service opportunities after acceptance, not invented wall-clock progress.

Keep immediate public reset/abort/qualified-fault masking and exact error
priority. Distinguish registered local capacity permission from that public
mask; prove that every local start/cancel is covered by public transfer
suppression rather than simply dropping a kill gate. If invalid-cycle ready
behavior or stage interface changes, specify it in this versioned contract.
A reviewed ordered transaction/latency scoreboard replaces only cycle equality;
all old arithmetic/format/ownership/error/cancellation oracles remain.

Cancel logical queue ownership, never physical memory debt. Preserve scratch
outstanding request drain and reconstruction's independent full-key reference
owner (`cu66-v119-owner/cu66_reconstruct_stream_v91k.sv` 192–202): its pending
request survives reset/start/cancel and retires only on matching response.
Include queue occupancy and pending end fence in busy/all_available/joined
done/new-command credit, together with the original reference/scratch/refill
physical debts. No new owner starts while an old accepted request is hidden.
Every added cycle counts against the decode budget. This contract is proposed,
not implemented or qualified here.

## Priority, proof and measurement gates

Retain scratch's literal outer priority at 736–757: matching cancel first;
wrong/unsolicited response error6 retains true debt; DRAIN retirement;
owned prefetch response error5; then owned overlapping-write response error5;
then normal state/release handling. A matching error response without a
prefetch/write owner can reach original case writes, so a blanket
`!response_failure` gate changes behavior. Foreign abort is not cancel.
The final terminal release remains after the case but inside the normal
branch. Same-edge publication and release of different banks retain both
updates. Never deassert busy while DRAIN or real requests remain.

Retain producer reset/abort→accepted_start→overlap queue error→owned child
error→state priority and DISPATCH bad-owner error67 before index63 acceptance.
Full32 child/frame epochs, uint16 expected-block wrap, widened terminal tests,
nonce exhaustion and rejected raw starts stay exact. Current producer-cell
and all inherited scratch/bank/busy/assertion oracles remain active.

Focused proof must execute real metadata writers before new-token consumes,
with separate primer ledgers and no forced new payload/owner fields. Cover
both bank selectors; full16 boundaries and full17 limits; full32 epoch high
bits; all modes; long holds; first publish/first consume; release+publish;
last/nonlast blocks; matching/foreign abort; reset/start overlaps; wrong,
unsolicited, error and matching responses; accepted read/write debt and drain;
and every first-fault overlap. Retain natural actual-controller/parent cycle
pairs. Isolated extracted generic domains are labeled separately from natural
packets. Finite two-state tests and independent algebra are additional evidence,
not formal, four-state or physical reset/CDC proof.

For each future candidate, retain the terminal V126 bindings above and
repeat matched queries for emit-bank→scratch state/busy, both metadata lanes and
parent expected owner→ready/valid/state, ready return→release, terminal D/CE/Q,
return-state D/CE/Q, admission coordinates/hidden-D and V126 producer stages.
Inventory actual FF widths, replicas, control sets and absent paths explicitly.
A new worst path does not prove that the previous family closed. Global
setup/hold/pulse/coverage/routing gates and two fresh same-source passing
builds remain required by the plan. This proposal claims no timing closure,
hardware throughput, 30 distinct displayed fps or complete decode under10ms.
