# Future inverse private coefficient-write enable

This is a read-only source assessment of the frozen V117 inverse
`67ec3d9d87678a141286dae8815f83380bea133754062179c3cc5793b42f87f4`.
No RTL, bench, runner or policy was changed, and no simulation or native run was
launched. A future candidate requires an actual routed cause, a new source-bound
proof and its own authorized measurement. No timing gain is assigned here.

The source supports a **conditional qualified-interface safety hypothesis**:
a private physical write can depend on the registered validated tuple alone,
while logical commit, bank publication and arithmetic launch retain their
current immediate cancellation masks. The extra killed-edge write changes raw
private/debug values and therefore needs an explicit contract and independent
physical-store verification.

## Current source facts

The [logical commit](../../fpga/experiments/cu66-v117-throughput/cu66_inverse_stream_v91j.sv#L997)
is `running && !kill && commit_valid`; `kill` includes reset, start, cancel and
sticky fault. The [coefficient storage](../../fpga/experiments/cu66-v117-throughput/cu66_inverse_stream_v91j.sv#L1015)
is two banks of 64 individually enabled 16-bit words: **2,048 payload FF bits**.
Only one word is selected on an ordinary edge. The common logical commit feeds
128 bank/word enable decoders; this is different from a single 2,048-load enable
net and its actual mapped fanout still needs measurement.

The full accepted tuple passes registered validation before
[`commit_valid` and its operands are transferred](../../fpga/experiments/cu66-v117-throughput/cu66_inverse_stream_v91j.sv#L1072).
An invalid captured tuple invokes `fail`, whose later assignments clear both
stage-valid bits on that same edge. Thus a protocol-reached `commit_valid=1`
record describes an earlier tuple that survived index, metadata, domain and
first-word token-exhaustion checks. It is distinct from the current captured
record, which can still be invalid.

The [logical commit frontier](../../fpga/experiments/cu66-v117-throughput/cu66_inverse_stream_v91j.sv#L1101)
allocates bank metadata only for word 0 and marks READY only after word 63.
The arithmetic controller selects only READY banks and holds a selected bank
ACTIVE until a matching valid IDCT result is copied into its reserved result
slot. The [release edge](../../fpga/experiments/cu66-v117-throughput/cu66_inverse_stream_v91j.sv#L1130)
frees that coefficient bank only after the complete result copy. Output holds
use separate 1,536-bit result payload stores.

The existing [same-edge assertions](../../fpga/experiments/cu66-v117-throughput/cu66_inverse_stream_v91j.sv#L1150)
check logical commit ownership, reserved arithmetic/result owners and done
fences. Their `!kill` guards and logical `coefficient_commit` predicate mean
that they do not prove an added physical write on a killed edge. The added
V117 accepted/committed occupancy assertion is likewise a logical-stage
conservation check.

## Bounded proposed split

The following is unimplemented pseudocode for a future source candidate:

```systemverilog
assign storage_write = commit_valid;
// coefficient_commit remains the existing running && !kill && commit_valid.
// Only the coefficient payload FF condition changes:
if (storage_write && accepted_bank == b && expected_index == w)
    value <= accepted_value;
```

The registered bank, expected word index and validated value remain the write
operands. Current live input fields, the younger captured tuple, combinational
validation, downstream readiness and unregistered error predicates must not
replace them. Every metadata/count/frontier/READY/math/result/public-output
update retains its existing logical predicate and priority.

This split permits one old, validated private word to be written on a reset,
start or cancel edge. The main control branch still revokes logical owners and
clears both stages. A private word 63 write cannot make the bank READY, allocate
a result slot, launch DSP work, increment `count_tiles`, or retain valid output.
A new frame must replace all 64 words under its own owner before READY.

Current behavior also allows an older validated private word to commit on the
edge that a younger tuple faults: the payload write and commit count precede
logical owner revocation. A future split must preserve that behavior and
input-versus-arithmetic fault priority. Adding `input_fault==0` or a late
arithmetic-error guard to storage would change that existing ordering.

## Preconditions to prove, including killed edges

Each is a required assertion or independent-model obligation, not a fact
established for a new candidate by this document.

| Condition before a physical write | Required consequence |
| --- | --- |
| Initialized, protocol-reached `commit_valid` | The record survived the prior validation edge; accepted index equals expected index; static flags are clear and the applicable first-word token-exhaustion predicate is clear. |
| Any `storage_write`, even while kill is high | Accepted bank and expected index name the current committed fill frontier before the edge. |
| Expected index 0 | The destination coefficient bank is FREE and freshly reserved for this tuple. |
| Expected index 1–63 | The destination bank is FILL under the same complete epoch/child/token/plane/scale/block/tile/qcell owner. |
| READY or ACTIVE coefficient bank | No physical write targets it. |
| Arithmetic phase is non-IDLE | The pending physical write targets the other bank; the complete DSP-owned bank remains stable. |
| Normal active edge without kill | Physical write equals existing logical coefficient commit; no new queue or acceptance cycle appears. |
| Physical write plus kill | No logical commit/publication/launch is created; stages and logical banks revoke at the original edge. |
| Following a killed last-word write | There is no READY bank or old valid result attributable to that private write. |
| New frame/repeated owner IDs | Every word is replaced under the new owner before its bank is eligible for arithmetic. |

The active-bank check uses the **pre-edge math-bank index**. Reset assigns a new
math-bank index, so comparing only the post-reset selected debug bank could
accidentally inspect the wrong bank. READY banks waiting for an available result
slot also require protection; an ACTIVE-only check is insufficient.

These conditions cover legal initialized transactions. Deliberately prepared
private-state tests must establish the same coherent stage, frontier and bank
ownership. An inconsistent backdoor state is not a basis for relaxing the
write guard or weakening an assertion.

## Existing oracles and the extra physical-write ledger

The selected [inverse bench](../../fpga/experiments/cu66-v117-throughput/tb_inverse.cpp#L32)
clears pending logical commits when reset/start/cancel/error kills an owner,
otherwise schedules acceptance at E+2. It checks `count_commits` against that
ledger and checks complete coefficient/dequant/residual goldens at real launch
and output handshakes. Those checks can remain unchanged because logical
commit/count/launch timing remains unchanged.

A killed private storage write would intentionally be absent from
`count_commits`. The counter would keep its existing logical meaning; it could
no longer be described as a count of every physical payload FF write. A new
observer must report private killed writes separately. The existing selected
bench's cancellation tests check no old valid output, busy owner or done after
kill; they do not snapshot every inactive coefficient word on that edge.

The historical [V110 locality bench](../../fpga/experiments/cu66-v110-fault/verification/tb_inverse.cpp)
contains a stricter independent whole-store oracle, including all 128 inactive
words and guarded cycles. Its guarded no-write policy would distinguish the
new physical behavior. Preserve that historical checker and result as the old
contract; do not silently skip killed edges or relabel raw-store differences as
full private-state equivalence.

A suitable future paired proof uses two independent expected physical stores:

1. Retain the existing baseline and its no-killed-write ledger unchanged.
2. Model candidate capture, registered validation, failure flush and E+2 physical
   write from accepted records, including an already validated record written on
   a kill edge. Do not derive the expected write merely by reading the candidate
   `storage_write` signal.
3. Compare **all 128 words** against each expected store every sampled edge,
   including inactive/held/killed words. Keep a separate exact logical ledger
   and the existing control/counter/fault/held-valid comparisons.
4. At every real arithmetic launch, compare the complete source tile and owner
   with the original independent golden. Retain exact dequant/residual values
   and held outputs through every retry.

Unqualified `dbg_coefficients` is continuously wired to the selected physical
bank, so its values can change in a killed/unowned interval. This is a declared
raw-debug-view difference, not a qualified video-data or ownership difference.
An all-port raw-cycle equivalence claim would therefore be inappropriate.

## Required targeted cases before adoption

- Both banks, all 64 target words, and reset/start/cancel on the E+2 physical
  write edge. Check the single selected word against its registered old tuple,
  all other words against their ledgers, and all logical masks unchanged.
- Cancel at first-word commit, last-word capture, last-word validation and
  last-word commit. A physical word 63 update must leave no READY tile, token
  advance, math launch or old valid publication after revocation.
- Hold an older result while another DSP job is ACTIVE and the other bank has
  a pending validated write. On kill, snapshot and compare the **entire old
  DSP-owned bank**, reserved result slot and held result. Repeat across DQ and
  IDCT phases, including a coherent prepared stalled-producer case if a prolonged
  stall cannot be reached from this module's public ports. Label prepared-state
  evidence separately from complete public transactions.
- Keep both result slots full and coefficient banks backpressured; prove a
  private pending write never targets a READY/ACTIVE bank or creates a third
  owner. Preserve all existing finite-capacity and ordered-drain checks.
- Exercise a younger malformed tuple coincident with an older commit, and a
  late arithmetic error coincident with an older write. Retain current write
  ordering, fault priority, first-fault hold and owner revocation.
- Retry without power reset using repeated epoch/tile identifiers but different
  coefficients, including partial EOF at 1, 7 and 63 words. Prove old private
  words cannot contribute to a later full tile or complete a partial frame.
- Preserve all selected boundary math cases, real-interface cancellation and
  E+2 checks. Add new cases and assertions rather than suppressing existing
  warnings, assertions, comparison clocks or watchdog failures.

## Selection and measurement gate

The current I67ec and R5b sources remain frozen. This option should be selected
only if a new actual routed path or mapped control-origin report shows that the
coefficient storage's cancellation fan-in is a relevant limiting cone. A future
native report must inspect actual CE/R/S startpoints for the decoded bank/word
writes; the RTL expression alone does not establish mapped locality. Source
fanout reduction alone supplies no frequency, latency or frame-rate credit.
A new candidate still needs focused, complete body/transport/peer/LIVE and its
own routed evidence before a hardware handoff claim.
