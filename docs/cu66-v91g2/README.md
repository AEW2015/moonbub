# V91g2: bounded next-tile preparation and delivery overlap

Parent: `f06293ae9f1099841f5de9faa8c6687cff9fb23a` (V91g read prefetch).

This experiment completes V91g's coded next-tile scheduling work with two tile
banks. The DC/AC preparation FSM can build the next tile while an independent
emitter delivers the current tile's 64 scalar coefficients. Runtime-disabled
scheduling remains the V91g read-prefetch control. RAW packets keep that qualified
path in both settings. BR88 wire bytes, quantization, packed layout and intended
coefficients remain unchanged.

This is still a residual-chunk coefficient endpoint. It does not integrate the
pixel transform, reconstruction or complete-frame validation/publication path.
Hardware 30 fps and complete validated FPGA decoding strictly under 10 ms remain
open.

## Two bounded bank owners

Each bank contains 64 signed 16-bit coefficients, a 64-bit validity mask and
block/epoch ownership. Relative to the prior single tile this adds a 128-byte
coefficient bank, an eight-byte mask and control/tag storage. These are logical
RTL storage counts; inferred resources, RAM-port mapping, fit and routed timing
are not yet established.

The producer acquires only a free bank, clears its mask and performs the real
DC/AC cache fetch, range/order checks and sparse merge. It marks a bank ready
only after that preparation finishes. The emitter retains the ready bank through
all 64 accepted output scalars; output stalls cannot release it. Unwritten mask
positions emit zero. The producer cannot lap the consumer or overwrite an
emitting or completed bank waiting behind it.

Preparation completion and the other bank's last-scalar acceptance may share an
edge. Their ready-bit updates target distinct banks. A released bank becomes
available for subsequent producer acquisition, without inventing a zero-time
merge or assuming an extra memory port. A ready next tile can wait under output
backpressure. Final completion requires the last tile's last accepted scalar,
no unfinished preparation and no accepted memory request.

The existing acknowledged memory interface still permits only one physical
request. Actual next-tile preparation subsumes coded-mode lookahead prefetch;
the independent prefetch engine is disabled on that path to prevent competing
cache/port owners. The legacy and RAW paths retain V91g prefetch. Reads may
change order but every used 16-byte line must still be written and read once.

Reset/start/abort invalidates local tile ownership and cancels unaccepted local
work. It cannot erase an accepted physical memory owner; replacement allocation
waits for the real matching response to drain. Wrong-epoch responses fail closed
without retiring the real owner. A matching read-error ACK retires the physical
request, invalidates logical ownership and suppresses concurrent output
acceptance. Late failure stops successful chunk completion; atomic full-frame
publication remains a future consumer contract.

The [independent Python bank contract](bank-contract.md) checks an explicitly
reduced ownership-event domain. It is not RTL equivalence or a cycle-performance
model. The RTL campaign separately compares every dense coefficient and the
entire packed memory image to frozen fixture goldens.

## Qualification and measured results

Each seed tests tile overlap off/on × FAST/SLOW service, with write overlap and
read prefetch selected and mask clearing fixed. The frozen 20 V91e cases include
15 actual packets from three planes of five related source frames, four
synthetic packets and an 8,192-block boundary case. The wider corpus remains
457 related precompressed frames, not independent held-out games or native
30-fps hardware captures.

FAST always accepts requests with a one-edge response delay. SLOW uses
write16/read18 plus address/seed-dependent 0–3-edge jitter and deterministic
input, request and consumer stalls. These are synthetic service assumptions,
not measured SDRAM or ESP32/QSPI limits. Schedule changes can change observed
consumer and request holds; those deltas remain in the analysis.

| Final qualification evidence | Result |
| --- | ---: |
| Seeds / configurations per seed | 910432, 910433 / 80 rows |
| Dense comparisons | 9,003,776 per seed; 18,007,552 total |
| Integrated recovery checks | 47 per seed, including 11 tile-specific checks |
| Standalone write-hazard checks | Nine per seed; eight accepts / eight physical ACKs |
| Exact V91g disabled-control values | 40 rows × nine metrics × two seeds = 720 |
| RAW control | Both tile settings reproduce the two RAW cases at both memory profiles exactly |
| Paired case effects per seed | 34 improved, six unchanged, zero regressed |
| Maximum owned tiles / ready tiles / accepted memory requests | 2 / 2 / 1 |
| Python bounded ownership model | 189,292 states / 503,367 transitions at depth 36 |
| Python seeded scenario | 5,000 actual events, seed 910438; zero terminal restarts |

| Actual-packet service | V91g control | Tile overlap | Cycle reduction |
| --- | ---: | ---: | ---: |
| FAST, either seed | 3,438,248 | 2,885,281 | 16.0828% |
| SLOW, seed 910432 | 4,358,909 | 3,647,754 | 16.3150% |
| SLOW, seed 910433 | 4,359,328 | 3,648,933 | 16.2960% |

Across the 15 actual packets, 26,974 tile preparations, publications and releases
reconcile in every enabled run. In the two SLOW seeds, 711,197/712,019 scalars
are accepted while another tile prepares, and 323,552/323,929 while a real read
is pending. There are 91/86 same-edge publication/release events in those
workloads, in addition to the targeted handoff test. Consumer-hold deltas versus
control are −401/−39 edges and request-stall deltas −158/+207; all are retained
in the per-case analysis. Overlap counts are concurrent observations, not
additive cycle savings. The separate synthetic/boundary population improves
7.9606% FAST and 6.192–6.210% SLOW; RAW remains exactly unchanged.

C3/f50 remains the slowest three-plane SLOW source sum: **990,205 cycles** in
seed 910433, down from 1,219,762. That falls below the old one-million-cycle
reference budget for this coefficient endpoint. **It does not establish a
10-ms decode result:** clock frequency is unqualified, these are serialized
residual chunks, and transforms, other frame modes, reconstruction and validated
publication are still outside the measured path.

[Analysis](../../experiments/python-gamebub-v91g2/analysis.json),
[independent audit](../../experiments/python-gamebub-v91g2/audit.json),
[timing/service contract](../../experiments/python-gamebub-v91g2/telemetry-contract.json)
and [selected RTL receipt](../../fpga/experiments/cu66-v91g2/pipeline-results.json)
pin the cases, commands, tools and artifacts. The first compile rejected an
incorrect helper-function state update; the next attempt exposed a driver that
left a consumed response asserted during a post-edge output check. Both failed
snapshots are retained. The corrected two campaigns preserve all control
metrics; neither the held-output assertion nor warning severity was weakened.
Ignored failed-attempt text vectors can be reconstructed exactly with
`scripts/cu66-v91g2/retain_vectors.py --restore`.

The control must match all nine V91g timing/traffic metrics plus its ordered
service fingerprint. Both RAW settings must match V91g exactly as well.
Independent V88 packet decoding and packed-image reconstruction retain the
functional oracle. Per-line occurrence assertions and fixture-derived canonical
service fingerprints account for reordered reads without hiding duplicate work.
Those fingerprints are diagnostic checksums; they do not replace exact bytes.

## Concurrent telemetry

Packet, preparation-FSM and emitter histograms each independently partition the
same running interval. They must not be added together. The producer's old
`EMIT` state occupancy no longer measures dense delivery when coded overlap is
active. A separate output-valid counter reconciles to accepted coefficients
plus held-output edges in every mode.

Tile acquisition, preparation completion and release counts reconcile to the
coded block count. Ownership and ready-bank highwaters stay at most two.
State 28 (`BANK_WAIT`) measures producer waiting for a free bank; state 29
(`PREP_DONE`) waits while final prepared output is consumed. Preparation/output
and read/output overlap counters count accepted scalars; preparation/output-hold
counts held-output edges. These concurrent observations are not independently
removable delays. Per-tile accepted first/last scalar timestamps show delivery
spans and inter-tile gaps.

## Next milestone

After this checkpoint's exactness, ownership and integrated service gates pass,
V91h replaces combinational packet-staging reads with explicit synchronous RAM
ports and latency. Keep the V91g2 control and every negative/recovery case while
handling headers, unaligned fields, replay and RAW through real port scheduling.
Then V91i–m integrate outer frames, dequantization/IDCT, reconstruction,
references/HUD/hashes and atomic validated publication with finite transport,
memory and display service. V100–V110 retain 7-series technology mapping,
placement, routing and timing on `xc7a100tcsg324-1`.

## Reproduce

From this repository with the existing `gamebub-cu66-v69-build` container:

```sh
python3 experiments/python-gamebub-v91g2/tile-bank-model.py
python3 scripts/cu66-v91g2/run_pipeline.py --seed 910432
python3 scripts/cu66-v91g2/run_pipeline.py --seed 910433
python3 scripts/cu66-v91g2/analyze.py
python3 experiments/python-gamebub-v91g2/verify_results.py
```

Receipts retain source snapshots, strict Verilator assertion/fatal-warning and
C++ warning-as-error builds, bounded self-checking transcripts, tool versions,
JSONL counters, compressed tile traces and source/artifact SHA-256 pins.
