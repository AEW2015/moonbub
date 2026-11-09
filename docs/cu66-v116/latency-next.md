# V116 row-fast latency: the next bounded throughput cut

Prioritize a V117 co-design of **pipelined II=1 inverse acceptance and two-owner
reconstruction overlap**. Reconstruction overlap alone cannot close the gap:
the selected inverse still accepts at most one coefficient every two edges.
The two limits must be addressed together while retaining registered validation.
No new RTL, compile, simulation or timing run was launched for this analysis.

The completed row-fast run is seed 116701, case actual_001, validation c0_f0,
from LIVE attempt 20261109T053508432181Z. It passed the original keyframe and
wrong-ACK/drain/retry checks. All 560,640 bytes, 70,080 row requests and matching
ACKs, and 1,025 actual hash jobs passed. This analysis uses that completed
profile only. Source and artifact hashes, formulas and event histograms are in
[latency-analysis.json](../../experiments/python-gamebub-v116/latency-analysis.json).
The service is abstract: four 16-bit data edges plus two overhead edges per
eight-byte request, with one physical pending lease.

## Keep the strict final-input fence

The measured interval is **1,416,449 cycles**, from the final accepted outer
byte at 233,671 to validated commit at 1,650,120. Equality with the 1,250,000
cycle budget needs 166,449 cycles saved; strictly below it needs **166,450**.
Presentation is separately observed at 1,650,121. There is no achieved-clock,
physical SDRAM, complete-parent timing or hardware frame-rate claim.

| Exact measured interval | Cycles |
| --- | ---: |
| Final outer byte → first accepted coefficient at 390,682 | 157,011 |
| First → last accepted coefficient at 1,503,893 | 1,113,211 |
| Last coefficient → last canonical hash delivery at 1,504,371 | 478 |
| Last canonical hash delivery → commit | 145,749 |
| Total | 1,416,449 |

The pre-input allocation/clear interval is outside this fence. Its roughly
8,104 start-to-first-input edges cannot be counted as savings against this
post-final-input budget.

## What creates the 157,011-cycle startup

The trace contains 31,518 records: 7,806 each of assemble, dequant and residual,
and 8,100 canonical tile records. It has **no historical admission, child
receive, sparse-parser or seal timestamps**. The following is source-derived
successful-path accounting and a serial lower bound, not a measured state
histogram.

The fixture's outer packet is 30,109 bytes. The first Y chunk is 15,901 bytes,
with sparse counts `[5144,6078,3945,1195]`: 16,362 sparse outputs and 27,580 Rice
symbols, since each AC event requires a run and a level symbol. The child
receives its complete packet before checking its CRC and parsing descriptors.
Scratch output then requires the completed sparse pass and seal; this is the
full first-plane materialization barrier, not just a slow plane selector.
See [child receive and descriptor gating](../../fpga/experiments/cu66-v115-final-ingress/br88_packet_ingress_sync_v91h.sv#L509)
and [sealed dense-output eligibility](../../fpga/experiments/cu66-v115-refined-scratch/packed_scratch_v91g2.sv#L267).

| Source-derived startup account | Edges |
| --- | ---: |
| Structural admission after final outer byte | 11,724 |
| Complete first child packet reception, minimum one edge per byte | 15,901 |
| Rice/context serial skeleton: `4×27580 + 16362` | 126,682 |
| Sum | 154,307 |
| Remaining aggregate startup interval | 2,704 |

The parallel Rice FSM requires separate request, prefix, suffix and response
edges; the context then presents each sparse coefficient on a separate HELD
edge. Those obligatory serial edges dominate startup. Refills may overlap
parser work; do not add a second full refill cost on top of this account.
The small residue includes parent control, descriptors, refill/packing overlap
and seal/drain overhead, and is not assigned artificial timestamps. Source:
[Rice stages](../../fpga/experiments/cu66-v116-rice/br88_rice_elastic.sv#L150),
[context request/result/HELD transitions](../../fpga/experiments/cu66-v113-geometry/br88_context.sv#L4135),
[scratch seal](../../fpga/experiments/cu66-v115-refined-scratch/packed_scratch_v91g2.sv#L766).

The 11,724-edge admission account includes the 8,103 key-tile/sentinel edges,
1,351 active-scan edges and 1,350 qmap fill edges, plus header/qmap/chunk parsing.
Optimizing that structural pass alone cannot recover 166,450 cycles. A future
lazy sparse-table or parallel-band decoder could attack the larger barrier,
but would need its own CRC, malformed-tail, ordering and physical-write proof.

## The 1.113-million-cycle main span has two coupled limits

Every residual tile occupies exactly 64 consecutive accepted-input edges.
Residual and canonical intervals never overlap in this trace. Between the
first residual at 390,830 and the last canonical byte at 1,504,356, the exact
1,113,527-edge partition is:

| Activity | Edges |
| --- | ---: |
| Residual fill, 7,806×64 | 499,584 |
| Canonical emission, 8,100×64 | 518,400 |
| Canonical producer stalls | 32,744 |
| Other mode/math/plane/control gaps | 62,799 |

Canonical interval excess over 64 bytes sums to exactly the independently
reported 32,744 producer stalls. Merely eliminating all those stalls is much
too small. Median residual tile start interval is 132 edges in all planes.
Y has 3,786 intervals at 132 edges; U and V have 1,223 and 1,210 respectively.

Reconstruction accepts residuals only in RESIDUAL, publishes pixels only in
EMIT, and advances its tile/mode frontier after the last emitted byte. Its
single FSM therefore serializes 64 residual fills with 64 canonical outputs.
The existing inverse coefficient banks and two result slots can buffer work,
but cannot change these mutually exclusive reconstruction states. Source:
[ready and valid](../../fpga/experiments/cu66-v110-fault/cu66_reconstruct_stream_v91k.sv#L105),
[fill and emit transitions](../../fpga/experiments/cu66-v110-fault/cu66_reconstruct_stream_v91k.sv#L183).

**That is not a standalone 499,584-cycle savings claim.** The selected inverse
has one accepted tuple slot, A_VALIDATE followed by A_COMMIT, and in_ready only
in A_EMPTY/A_COMMIT. It explicitly supports replacement at II=2. See
[acceptance eligibility](../../fpga/experiments/cu66-v113-inverse/cu66_inverse_stream_v91j.sv#L971)
and the frozen [V113 contract](../cu66-v113/inverse.md).

For 499,584 coefficients, inverse input first-to-last span is at least 999,166
edges. Accounting generously for the initially empty one-slot coefficient
boundary gives a public first-to-last bound of `2N−3 = 999,165`: the final
public token may replace the boundary when inverse token N−1 is accepted.
Even a perfect reconstruction-only change therefore saves at most 114,046
of the measured coefficient-span edges if the surrounding fences are held
fixed. The resulting 1,302,403-cycle interval still misses the strict target
by **52,404 cycles**. II=1 acceptance alone likewise leaves reconstruction's
serialized fill/emission limit: those accepted payload edges alone total
1,017,984. Adding the unchanged startup and final tail already exceeds
1.32 million edges, even before mode/math/stall overhead. This is why the next
cut is a co-design. These are conditional source bounds with surrounding work
retained, not a general prediction for an arbitrary redesigned schedule.

## Minimal V117 contract and measurable savings budget

Keep a registered validation stage. Use true elastic capture/validate/commit
storage with at least two complete owned tuples, so validation of one tuple,
commit of its predecessor and capture of its successor can overlap. Reserve
the bank/index/token frontier in accepted order. Forward coherent registered
reservation metadata; do not flatten validation back into the old V112 payload
write-enable cone. A bank becomes arithmetic-ready only after word 63 commits.

Use two bounded reconstruction tile owners with independent fill and emission
frontiers. One may gather the next 64 residuals while the older canonical tile
is held or emitted. A live canonical output cannot be overwritten by the next
conversion. Payload copies require real registers/ports and costed edges;
the existing arithmetic result slot is not an uncounted extra queue.

There are 7,792 same-plane, physically adjacent residual-tile transitions in
this trace. Hiding at most 64 fill edges at each gives a **498,688-edge raw
overlap upper bound**, conditional on removing the inverse II=2 restriction.
The required 166,450 net saving is 33.38% of that raw opportunity, or 21.32
cycles per residual tile. As an engineering budget, 32 overlap edges per
eligible transition would yield 249,344 edges before newly exposed stalls,
leaving **82,894 edges** for extra queue/SHA/control delay while still meeting
the strict budget. This is a budget for a future measured candidate, not
performance credit. Faster production can move the bottleneck into the row
join or iterative SHA engine.

The minimum proof contract is:

- Keep complete epoch/child/token/plane/block/tile/qcell/scale/index/value
  ownership. Separate accepted, validated and committed counts. Younger tuples
  cannot commit or publish after an earlier invalid tuple revokes ownership.
- Preserve index, metadata, domain, token-wrap/partial-EOF and arithmetic fault
  priority, first-fault hold, and immediate reset/start/cancel/fault masks.
- Bound reconstruction owners at two; never reuse a bank while fill,
  conversion, reference debt, ready output or a stalled final byte owns it.
  Hidden/copy/residual modes retain full-grid order and residual ordinals.
- Keep the accepted reference bank immutable under its fid/generation lease.
  A pending reference keeps its full response tuple and survives warm reset or
  cancellation until the exact matching response drains. Existing accepted
  scratch/reference/candidate physical debt must also drain.
- Assert final done only after EOF, accepted-slot validation/commit, arithmetic,
  both result/reconstruction owners, the final byte and reference debt drain.
  Publication still waits for all actual candidate ACKs and C2/HUD/root/seal.
- Retain original independent math, malformed/owner/boundary, canonical/HUD,
  qcache and retry oracles. Declare the changed schedule separately while
  preserving the old checker. Require fresh focused, component, peer and LIVE
  proofs and a newly authorized native timing result. V116 proves none of this
  proposed architecture.

## Why tail-only Merkle work is secondary

The final canonical hash byte precedes root completion by 101,792 edges:
82 to the final real leaf, four empty leaves at 133 edges each, then 511
internal nodes at exactly 198 edges each. Root then precedes the last HUD hash
byte by 43,557 edges; HUD digest takes 135 more, seal 264, and commit one.
These sum to the measured 145,749-edge tail. Actual job tags are NODE=2/node1
for root, HUD=3 and SEAL=4; no HUD-write-before-root constraint is assumed.

Even hiding the entire root tail leaves another 64,658 cycles to save. Hiding
the entire post-canonical tail leaves 20,701. Incremental Merkle remains useful,
but the shared SHA engine cannot process a node concurrently with a leaf.
A bounded scheduler/buffer or separately costed engine is required; job
reordering can otherwise reappear as producer backpressure. Preserve every
domain prefix, node index, digest and final seal. It is not a substitute for
the measured coefficient/reconstruction throughput cut.
