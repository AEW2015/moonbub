# V91g2 bounded tile preparation overlap

V91g2 completes the next-tile preparation portion of the V91g functional study.
The runtime `tile_overlap` choice is captured at integrated start and passed as
`begin_tile_overlap` at scratch allocation. The measured configuration fixes
write overlap on, read prefetch on and validity-mask clearing on, then compares
tile overlap disabled/enabled under the retained FAST/SLOW service scenarios.
Disabled mode must reproduce V91g prefetch-enabled timing and traffic exactly.
RAW uses the qualified V91g scalar/prefetch path in both modes.

For coded chunks, the writer, acknowledged packed scratch layout, descriptor
validation, four segment caches, DC/AC heads, coefficient checks and one physical
outstanding request remain. The tile array becomes two bounded 64×16-bit banks,
each with its own 64-bit validity mask and epoch/block tag. This adds one
128-byte coefficient bank and one eight-byte mask relative to the single-bank
path, plus the two owner tags and selection/control state. Instrumentation also
has a hardware cost. No BRAM/LUTRAM inference, target resource fit or clock is
claimed here.

The existing preparation FSM owns `prep_bank` and `prepare_block`, clears its
mask, fetches/validates actual DC/AC records over the finite memory interface,
and merges them into that free bank. Completion marks the bank ready. The
independent emitter owns `emit_bank`, its stored block/epoch tag and scalar
index. A ready bank is immutable through all 64 accepted outputs, including
consumer holds. The ready bit stays asserted while the bank is emitting.

State 28 (`BANK_WAIT`) starts only the next sequential block in the other bank
when that bank was already free before the edge. A bank released on this edge
is eligible on a later edge; no write races the old last-scalar acceptance.
Both ready banks stall the producer, so it cannot lap or overwrite a held
emitter. A preparation completion and the other bank's last scalar acceptance
may share an edge because they update different ready bits. Newly prepared
output becomes visible after that edge. State 29 (`PREP_DONE`) waits after the
final preparation. Chunk done requires the final bank's sixty-fourth acceptance
and no accepted memory request. State IDs 0–27 retain the prior meanings; 30/31
are reserved.

Actual next-tile preparation subsumes coded EMIT-window read prefetch, so that
old lookahead engine is disabled only for coded tile-overlap mode. It remains
unchanged for the runtime-disabled control and RAW. The preparation reader owns
the sole physical port; output reads the other local tile bank. No extra
outstanding request, memory port, hidden transform, or zero-time merge is used.

Abort/reset/start invalidates both local tile owners while retaining any
accepted external memory owner until its matching response drains. New bank
allocation waits. A wrong-epoch response fails logical ownership closed but
cannot retire the true physical owner. A matching error ACK retires the physical
request and fails the chunk without output advancement on that error edge.
The emitter's updates occur inside the normal sequential branch after global
cancel/response-error priorities. In coded overlap, dense validity suppresses
all response failures, including demand-read failures while another tile emits.

Assertions pin every ready bank's 64 coefficients, mask and owner tags until
release, restrict preparation to an unready bank, check active output epoch and
block bounds, and exclude a pending memory transaction on final completion.
The external C++ driver records each accepting edge and then deasserts a
consumed response-valid/error signal before reevaluating settled public pins.
This prevents the retired ACK from appearing combinationally as a second,
unsolicited response after `outstanding` clears. It adds no clock edge and
changes no accepted-edge counter. The retained scoreboard independently compares every accepted scalar and the
whole packed image, checks immutable held output/request tuples, and checks
all used lines are read and written exactly once. Read order can change, so
canonical full-service and ordered write-only fingerprints remain derived from
the independent packed fixture rather than requiring identical ordered reads.

Telemetry still samples pre-edge states. Packet and preparation/scratch state
histograms each partition the same active interval. The new independent emitter
histogram has states 0 (coded emitter idle), 1 (coded valid/ready), 2 (coded valid
held) and 3 (legacy/RAW path). It also partitions that interval. Do not add these
concurrent histograms. `output_valid_edges` is independently observed in every
mode and equals accepted dense values plus consumer holds. The old EMIT/RAW FSM
occupancy identity applies only to the runtime-disabled or RAW path.

`tile_overlap_counters` records preparation starts, publishes, releases, accepted
output while preparing, held output while preparing, accepted output with a
physical read pending, state-28 wait edges, its both-ready subset, state-29 wait
edges, same-edge publish/release and all-mode output-valid edges. Successful
coded overlap requires starts = publishes = releases = block count. Highwaters
include at most two owned tile banks (including the preparing bank) and two
ready banks. RAW/disabled tile counters are zero except all-mode output-valid
edges; legacy prefetch counters retain their former meaning.

The integrated suite retains 36 earlier checks and adds eleven coded-tile
checks using a small valid sixteen-zero-block packet: both-ready held output
for 257 edges with no producer lapping, next-tile read ACK during held output,
accepted-read cancellation, matching error ACK, stale response and real drain,
held reset with matching ACK, replacement allocation blocked by an old read,
ordered bank handoff, exact same-edge publication/release, unaccepted offered
read under request stalls, and final held scalar for 257 edges. Existing
standalone nine-case scratch write-hazard checks remain. This direct packet is
a verification fixture, not additional measured gameplay coverage. The retained
20 measured vectors and their exact goldens remain frozen.

The runner snapshots sources and tools, uses fatal Verilator warnings and RTL
assertions, C++ warnings as errors, and bounded self-checking tests. See the
root V91g2 documentation and selected receipts for measured outcomes. This ends
at dense coefficient completion: no integrated dequantization/IDCT, reference,
reconstruction, HUD/hash/atomic frame publication, achieved clock, calibrated
physical controller, live ESP32 service or hardware 30-fps result is implied.
