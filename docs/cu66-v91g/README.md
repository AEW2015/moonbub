# V91g: bounded needed-line read prefetch

Parent: `34fdfea410b2b355fa5a88e514ff4193c420d03d` (V91f).

This checkpoint overlaps needed memory reads with delivery of the current tile's
dense coefficients. It retains the V91f write-overlap path, mask clearing and
one accepted physical memory request. The runtime-disabled read-prefetch path
is compared with the exact V91f overlap-enabled control. BR88 bytes, quantizers,
packed layout and intended dense coefficients remain unchanged.

This completes the bounded read-prefetch part of V91g. **Full next-tile merge
concurrent with current-tile delivery remains to be implemented and qualified.**
The implementation is a coefficient endpoint, not a complete pixel decoder or a
hardware streaming result.

## Scheduling and storage ownership

During coded `EMIT`, the current tile is already latched independently of the
four segment caches. A candidate is the next block's DC line or the AC cursor's
next unread record line, when that line differs from its segment's cached line.
A held AC head is stored separately. An old cache line is replaceable only after
all its records have been extracted. Bounds exclude unused segment tails and
prefetching beyond the final coded block. RAW output similarly uses an already
latched scalar while the next required line can be fetched.

Prefetch reuses the existing cache data registers; it adds no payload cache.
It does add selection, offer and ownership control and instrumentation. Physical
resource fit, RAM-port mapping and routed timing remain unqualified.

One immutable request snapshot holds segment, byte address and epoch from offer
through acceptance and physical response. A matching successful ACK installs
cache bytes; acceptance alone cannot make them valid. Output ready-low leaves
the current dense tuple unchanged even while a response fills the cache. At a
scalar/tile boundary, an offered or accepted prefetch drains before demand reads
or next-tile preparation continue. Final completion cannot leave a physical
transaction pending.

Reset/abort drops unaccepted local work and retains an accepted external owner
until its real matching response drains; replacement allocation waits. A stale
response cannot retire that owner. Matching error ACK retires the physical
request but fails the logical transaction without filling the cache. Read
prefetch starts only after packet/coefficient seal and descriptor checks, and
never publishes a complete frame. Direct-interface tests exercise read-specific
cancellation, backpressure, response errors and output-hold cases in addition to
the retained write-owner checks.

The [Python ownership model](prefetch-contract.md) is an independent executable
abstraction of the cache/offer/ACK/output-hold rules. Its bounded exploration is
not formal RTL equivalence, synthesis or a cycle-performance prediction.

## Matched controls and traffic accounting

The retained V91e fixtures contain 20 cases: 15 actual packets from three planes
of five related source frames, four synthetic packets and one maximum-block
boundary case. They remain a small subset of a 457-frame related walkthrough
family, not independent held-out games or native 30-fps hardware captures.

Each seed tests read prefetch off/on × FAST/SLOW memory, with write overlap on
and serial clearing off. FAST always accepts and responds after one edge. SLOW
uses write16/read18 plus address/seed-dependent 0–3-edge jitter and deterministic
input, request and consumer stalls. Scheduling changes can alter observed stall
counts under cycle-indexed readiness; the analysis retains those deltas.

Reads can change order. Each successful case must still touch every used
16-byte line exactly once for writing and once for reading, and compare every
packed byte and dense coefficient against independent fixture goldens. The
ordered write-only signature and a commutative full-service signature are
independently derived from the packed fixture, request direction/address,
assumed response delay and write payload. They are diagnostic fingerprints;
exact byte checks and per-line occurrence assertions remain the functional
oracles. The old ordered full-service signature must match V91f when prefetch is
disabled, but need not match between reordered off/on reads.

| Final qualification evidence | Result |
| --- | ---: |
| Seeds / measured configurations | 910432 and 910433 / 80 rows per seed |
| Dense comparisons | 9,003,776 per seed; 18,007,552 total |
| Integrated directed checks | 36 per seed, including eight new prefetch checks |
| Standalone write-hazard checks | Nine per seed; eight accepts and eight physical ACKs |
| Exact V91f control metrics | 40 rows × nine fields × two seeds = 720 matches |
| Paired cases per seed | 36 improved, four unchanged, zero regressed |
| Maximum cache lines / prefetch offers / accepted bus requests | 4 / 1 / 1 |
| Python bounded ownership exploration | 436 states / 764 transitions, depth 11 |
| Python seeded scenario | 2,888 checked events + 112 terminal restarts in 3,000 steps |

| Actual-packet service | V91f control | Prefetch enabled | Cycle reduction |
| --- | ---: | ---: | ---: |
| FAST, either seed | 3,470,951 | 3,438,248 | 0.9422% |
| SLOW, seed 910432 | 4,596,935 | 4,358,909 | 5.1779% |
| SLOW, seed 910433 | 4,597,619 | 4,359,328 | 5.1829% |

Each actual-packet population prefetches, physically acknowledges and first-uses
10,901 needed lines. In SLOW, 159,756/159,457 dense scalars are accepted while a
prefetch is pending; only nine/one edges wait in the boundary drain state. These
are overlapping observations, not additive savings. Consumer-hold deltas are
+23/−143 edges versus control, with request-stall deltas +14/−114. The separate
synthetic/boundary population improves 0.4968% FAST and 2.724–2.730% SLOW.

C3/f50 remains the slowest three-plane SLOW source sum: 1,219,762 cycles in
seed 910433, versus 1,286,652 in V91f. This is serialized coefficient service,
not full-frame latency. The transforms and validated publication path are still
missing from this timing fence.

[Analysis](../../experiments/python-gamebub-v91g/analysis.json),
[independent audit](../../experiments/python-gamebub-v91g/audit.json),
[timing/service contract](../../experiments/python-gamebub-v91g/telemetry-contract.json)
and [selected RTL receipt](../../fpga/experiments/cu66-v91g/pipeline-results.json)
retain every case, seed, source pin and tool command. The first RTL campaign
passed its testbench but a Python post-analysis variable-shadowing error rejected
the overall receipt; the corrected helper was rerun in two complete campaigns.
That failed receipt and its sources remain. Its transient text vectors can be
recreated byte-for-byte with `scripts/cu66-v91g/retain_vectors.py --restore`.


## Telemetry and limits

Packet and scratch histograms independently partition the same running interval.
Do not add them together. Physical memory-pending edges are counted independently
of scratch state; a read can now be pending during dense output. State 27 is
`PREFETCH_DRAIN`, and IDs 28–31 remain reserved. Prefetch offers, accepted reads,
successful ACKs and first uses must reconcile for every valid case. A first-use
marker clears when the prefetched line is first extracted. Accepted dense
scalars coincident with pending prefetch are counted separately from drain-state
occupancy; neither is a promise that each event saves one total cycle.

The timing fence remains BR88 residual-chunk input to dense coefficient
completion. Serialized three-plane sums are not full-frame validated decode
latency. Dequantization/IDCT, reconstruction, accepted references, HUD/hash checks
and atomic publication are not integrated here. No achieved clock, calibrated
memory-controller service, measured ESP32/QSPI arrivals or hardware deployment
is claimed.

Next finish V91g's bounded next-tile merge overlap, preserving held-output and
memory-port ownership. V91h then makes staging RAM ports synchronous. V91i–m
integrate complete frame consumers/publication; V100–V110 retain the 7-series
mapping, placement, routing and timing work on `xc7a100tcsg324-1`.
**Sustained hardware 30 fps at 720×480 and complete validated FPGA decoding
strictly under 10 ms remain open.**

## Remaining V91g implementation contract

1. Separate the preparation block index from the output block/index. Use two
   bounded 64×16-bit tile banks, each with its own 64-bit validity mask and
   epoch/block ownership. Relative to the current single tile this adds one
   128-byte coefficient bank plus an eight-byte mask and control; physical
   inference and fit still need measurement.
2. Keep the emitted bank immutable until all 64 scalars are accepted. Prepare
   only the next block in the other bank, using the same DC/AC cursor checks and
   finite acknowledged memory interface. Do not add physical outstanding
   requests or assume a second RAM port without an explicit contract.
3. Exchange bank ownership only when preparation is complete and the consumer
   releases the old bank. A completed next bank waits under backpressure; the
   producer cannot lap or overwrite the emitted bank. Keep RAW on its qualified
   path initially unless its separate bounded scheduling change is measured.
4. Preserve cancellation and drain semantics across both FSMs. An accepted
   external transaction blocks replacement even after local banks are
   invalidated; late errors cannot become successful chunk completion.
5. Retain this prefetch implementation as the exact runtime-disabled control.
   Add full-output holds, preparation completing on the last-output edge,
   delayed read/error/stale responses, reset/start races, empty AC bands and
   maximum-block cases. Compare every dense coefficient and all physical
   traffic against the frozen fixture-derived controls.
6. Measure integrated cycles, bank occupancy, preparation/delivery overlap,
   inter-tile gaps and consumer-hold deltas under FAST/SLOW and adversarial
   service. Close V91g only after the added bank ownership and measured service
   gains pass independent audit; then proceed to V91h synchronous staging ports.

## Reproduce

From the repository with the existing `gamebub-cu66-v69-build` container:

```sh
python3 experiments/python-gamebub-v91g/prefetch-ownership-model.py
python3 scripts/cu66-v91g/run_pipeline.py --seed 910432
python3 scripts/cu66-v91g/run_pipeline.py --seed 910433
python3 scripts/cu66-v91g/analyze.py
python3 experiments/python-gamebub-v91g/verify_results.py
```

Each campaign retains source snapshots, strict Verilator/assertion and C++
warning-as-error compile commands, tool versions, direct-interface verdicts,
JSONL case metrics, compressed tile traces and SHA-256 pins. Failed attempts
remain identifiable alongside selected passing receipts. Generated binaries stay
in the build container.
