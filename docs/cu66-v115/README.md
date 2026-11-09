# V115: registered preparation and timing qualification

Branch: `study/gamebub-v115-timing-cuts-20261108`.
Base: `6098d48e5c4b57576fddeec1ae6facbc25165a11`.

The initial, refined and final custom-decoder compositions pass fresh functional
qualification. The final selection uses six aliases in the same 18-origin
component. Routed timing is measured separately at actual 100 and 125 MHz. The full
V115 operational-parent roadmap exit remains open.

See the generated [selected-evidence status](status.md) for all compositions.
The [refined implementation](refined.md) follows the initial routed failures
with early header-length preparation and a local scratch write slot. The
[final composition](final.md) adds an owned cancellation authorization bit and
splits request-address arithmetic from bounds checking on existing edges.
It has six aliases relative to V114 and passes its own focused, canonical,
transport and peer qualification.

## Final measured outcome

Functional qualification passes; **neither routed clock target meets setup**.

| Final OOC component target | Routed WNS | Failing setup endpoints | Hold / pulse / routing errors |
| --- | ---: | ---: | --- |
| 100 MHz / 10 ns | −0.263 ns | 3 | 0 / 0 / 0 |
| 125 MHz / 8 ns | −2.974 ns | 24,606 | 0 / 0 / 0 |

The six initial routes across three source compositions are complete and all
fail setup. No negative run qualifies for the one allowed positive fresh
repeat. [Independent native audit](native-final.md) and
[mapped-register checks](mapped-registers.md) retain the actual reports and
confirm the intended cuts survived mapping. The variant is **not timing
qualified** and the complete operational parent remains open.

The [actual final routed next steps](final-routed-next.md) supersede the earlier
synthesis/placement hypotheses: target Rice symbol-request/output-zeroing
control at 125 MHz and plane-dependent admission bounds at 100 MHz. The
separate overlapping write/ACK/hash change is still needed for latency.

## What changed

The selected V114 prepared-prefetch 125-MHz control failed setup at −2.696 ns.
Its worst reported path included a wide input-domain/control cone reaching an
IDCT DSP input; other repeated paths involved descriptor selection, parser
remaining bits, scratch admission and cache-read comparisons. The initial V115 candidate changes
exactly five bodies in that 18-origin composition:

- [Dequant and IDCT](inverse.md): local grouped validity/zero predicates and
  registered preparation before arithmetic. Ordinary helper service adds one
  edge per helper while preserving signed arithmetic and accepted-value order.
- [Ingress and parser](ingress.md): owned band descriptor selection, cached
  replay predicates and prepared parser windows. One private selection edge
  per compressed band separates descriptor selection from consumption.
- [Packed scratch](scratch.md): captured descriptor, three private preparation
  edges and earlier read-tag/address predicates. Reserved-owner aborts and
  private committed anti-replay history have distinct semantics.

The initial/refined candidates retain the V114 command-delivery top. The
final candidate substitutes its cancellation certificate while keeping the
original E/E+1 command API. The V113 inverse wrapper remains unchanged. There is no codec/wire-format change or quality reduction. The
candidate remains the application-specific CS88/BR88 path; the separate JPEG
probe is a comparison/integration experiment.

## Executed functional evidence

The selected [final decoder/transport proof](../../experiments/python-gamebub-v115/final/spatial/results.json)
passes 44 canonical case profiles, 42 directed checks, 24 actual V97 transport
profiles and four abort/reset retries across two seeds. Decoder and transport
models compile fresh; all original functional oracles remain enabled. Output
matches the frozen V113 canonical bytes. Public cycles intentionally differ
under the declared preparation contracts.

Focused inverse, ingress/parser and scratch campaigns retain their earlier
value/ordering/held-output/drain checks and add tests for new preparation
phases. The [actual-composition peer campaign](control-peer.md) covers eight
existing fault/retry cases plus six real-parent pending-preparation abort/reset
cases per seed, with 14 complete canonical retries per seed. The
[final peer selection](../../experiments/python-gamebub-v115/final/control-peer/results.json)
repeats those checks using the actual final 18-source composition. The supplemental
scratch metadata probe tests invalid geometry, error priority and same-tag
retry without permitting physical work. Failed source-review drafts and
failed test/compiler attempts are retained separately from selected PASS. The
[independent final functional audit](final-functional-terminal.md) verifies
76 complete canonical rows (39,398,400 Y/Cb/Cr byte samples), selected sources,
snapshots and retained artifacts, with no mismatches.

## Performance and remaining gates

The [actual-cycle ledger](performance.md) covers 24 successful component rows
and 24 normal transport rows. Fast component first-byte-to-done ranges from
642,491 to 1,385,090 cycles. At an **assumed** 125 MHz that is 5.140–11.081 ms;
stalled component service reaches 19.707 ms. Eight of twelve fast rows fit the
conditional strict under-10-ms budget, and no stalled row does. Added
preparation costs a median 11 fast-case cycles versus V114, with a maximum
per-case increase of 5,530 cycles. Achieved clock, full validation/publication
latency and sustained frame rate require their own evidence. The joined
[C2/HUD/seal partition](live-parent.md) currently measures strict last-required-
byte to validated commit at 3,062,014 cycles fast and 5,732,576 stalled:
**24.496 / 45.861 ms at an assumed 125 MHz**. Those exceed 10 ms. The larger
parent has no achieved-clock qualification.

The [final source qualification](final.md) preserves all 48 successful measured
component/transport fence cycles from the initial V115 selection. All three
[ACK/C2/HUD/seal partitions](live-parent.md) pass the same bounded keyframe
and negative ACK/drain checks. These partitions use abstract memory/publication;
they do not qualify the physical memory/display parent.

The [native method](native-method.md) fixes source hashes, actual 8/10-ns clocks
before fresh synthesis, tools, routing method, resources and a bounded global
source-composition budget. No timing exceptions, guessed I/O delays or strategy
sweep are introduced. See the machine-readable
[current results](../../experiments/python-gamebub-v115/results.json) for
completed native measurements and any remaining failures.

The [harness inventory](harness-readiness.md) identifies reusable real Sunshine
serialization, Rust parsing and existing QSPI/JPEG/memory/display tests. The
[new JPEG wire probe](jpeg-wire.md) has a separate source-bound result and
explicit adapter, oracle and memory-model limitations. It is not the complete
custom-codec harness.

The original [V111–V115 roadmap](../gamebub-v111-v115-simulation-spatial-plan.md)
still requires actual custom endpoints, the operational parent and its
validation-to-physical-memory/display integration, target firmware/time
calibration, 300 distinct frames,
60/600-second campaigns and full-parent timing/CDC/I/O qualification. Hardware
30 fps and validated full decoding below 10 ms remain open. No hardware,
installed Sunshine instance or relay is contacted by this iteration.

Use the [reproduction guide](reproduce.md) for bounded commands, tool pins,
resource gates and the distinction between fresh, inherited and exploratory
evidence.

The [validated latency budget](validated-budget-next.md) identifies another
required architecture change: the current byte-write/ACK join has a floor of
2,242,560 cycles for this frame, already 17.94 ms at an assumed 125 MHz. Faster
IDCT alone cannot meet complete validated decoding below 10 ms. A bounded
overlapping row-write join must preserve actual ACK ownership, expanded-byte
hash order and the C2/HUD/seal fences.

The [next iteration brief](next-iteration.md) separates residual timing closure
from the overlapping write/ACK/hash work. The [observability review](observability-next.md)
proposes a production CSR/snapshot/ILA interface while retaining useful counters.
It does not assume that removing debug ports fixes RAM inference or timing.

The [queued-epoch diagnosis](queued-epoch-next.md) is a synthesis-only hypothesis
until confirmed by the final routed cone. It retains generic foreign-abort-tag
rejection and proposes no source change in this iteration.
