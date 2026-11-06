# V91f: bounded physical-write overlap

Parent: `96e69d603dd4b8f6fb6aedb72baee8e89d80d5bb` (V91e).

V91f lets coefficient packing continue while an accepted external-memory write
waits for its physical ACK. One immutable 16-byte offered/inflight slot and one
16-byte assembler provide two bounded line owners. The existing scalar pending
record is counted separately; there is no third line queue. Only one physical
request may be accepted at a time. The runtime-disabled path remains the exact
V91e mask-clear control.

The change preserves BR88 wire bytes, quantization, packed scratch layout and
every dense coefficient. It changes scheduling rather than compression or image
quality. The ESP32 remains an opaque bounded forwarder; this experiment changes
neither ESP32 firmware nor Sunshine encoding.

## Ownership and recovery

The slot holds its address, payload and epoch from first offer through matching
physical ACK. Packing fills the other line while memory is pending. When the slot is occupied and another line needs flushing, `FLUSH_LINE`
explicitly backpressures the producer. It can hold a full line or a partial
context tail; its occupancy counter includes both. Matching ACK
and assembler-to-slot transfer may share an edge; the replacement request can
only be accepted on a later edge. Request acceptance never counts as completion.

A seal request is accepted only after all data writes physically drain and no
assembler or offered slot remains. Two descriptor writes then ACK sequentially
before `sealed` is observed and descriptor reads begin. This local seal covers
coefficient ownership; it is not complete-frame validated publication.

Abort/reset withdraws unaccepted local work while retaining the immutable
external transaction and bank hazard until its real matching response drains.
A stale response cannot retire that hazard. Error ACK has priority over enqueue.
Semantic input failure also preserves `busy`/drain ownership, including when a
physical request is accepted on that same edge. The validating integrated packet
parser normally prevents that last low-level combination, so a separate scratch
public-interface test exercises it directly.

The [executable Python ownership contract](ownership-contract.md) explores a
small bounded event space independently of the RTL FSM. It checks ownership,
ACK/error/cancellation, replacement and seal rules. It is an abstract reference,
not formal RTL equivalence or a performance simulator.

## Matched simulation and results

The retained campaign uses seeds 910432 and 910433. Each has 20 frozen V91e cases
in four configurations: overlap off/on × FAST/SLOW memory, with mask clearing
fixed. The 15 actual packets represent three planes of five related source
frames; the other five cases cover synthetic values and maximum block count.
The wider corpus remains 457 related precompressed source frames, not held-out
independent games or a native 30-fps hardware corpus.

FAST always accepts requests and responds after one edge. SLOW uses 16-edge
writes, 18-edge reads, address/seed-dependent 0–3-edge jitter and seeded input,
request and consumer readiness. Ordered request-service hashes exclude epoch
and absolute cycle; they match off/on, as do every packed byte, coefficient and
request count. Cycle-indexed ready patterns are deterministic and matched, but
schedule changes can change the number of observed consumer holds. The analysis
retains those deltas; percentage gains describe these stated service scenarios.

| Final evidence | Result |
| --- | ---: |
| Seeds / configurations per seed | 910432, 910433 / 80 rows (20 cases × four configurations) |
| Dense comparisons | 9,003,776 per seed; 18,007,552 total |
| Integrated directed checks | 28 per seed |
| Separate scratch-interface checks | 9 per run; 311 edges, 8 accepts / 8 physical ACKs |
| V91e exact control metrics | 40 rows × nine metrics × two seeds = 720 matches |
| Maximum measured line owners / accepted requests | 2 / 1 |
| Tested case regressions | 0 in either seed or memory scenario |

| Actual-packet service | Overlap off | Overlap on | Cycle reduction |
| --- | ---: | ---: | ---: |
| FAST, either seed | 3,470,994 | 3,470,951 | 0.00124% (effectively neutral) |
| SLOW, seed 910432 | 4,932,322 | 4,596,935 | 6.7998% |
| SLOW, seed 910433 | 4,932,402 | 4,597,619 | 6.7874% |

The SLOW synthetic/boundary population improves 1.996–2.008%. Seed 910433's
actual packets record 480,721 INGEST/APPEND edges during accepted-write waits,
with only 161 more consumer-hold edges than its control; seed 910432 has 1,173
fewer holds. Request-stall deltas are also retained in the analysis. These
small readiness differences do not change bytes or memory-service fingerprints.
C3/f50 remains the slowest three-plane SLOW source sum, at 1,286,652 cycles
(seed 910433). The transform and validation path still needs integration.

Machine-readable [analysis](../../experiments/python-gamebub-v91f/analysis.json),
[audit](../../experiments/python-gamebub-v91f/audit.json),
[timing/ownership contract](../../experiments/python-gamebub-v91f/telemetry-contract.json)
and [selected RTL receipt](../../fpga/experiments/cu66-v91f/pipeline-results.json)
retain per-case results, seed identities, exact controls and source hashes.


The concurrent assembler hides actual write service: `packing_during_write_pending`
counts pre-edge INGEST/APPEND occupancy while a real accepted write remains
pending. It is an overlapping event counter, not an exclusive stage or a claim
that every such edge saves one total cycle. Packet and scratch histograms each
partition the same service interval; they must not be added together. The old
WRITE_WAIT+READ_WAIT=pending identity applies only with overlap disabled.

Early passing snapshots are retained as superseded review evidence. A later
review found the semantic-failure/drain corner described above; final receipts
must include its repair and direct tests. Source snapshots, compile commands,
strict warning/assertion settings, tools, raw JSONL logs, tile traces and
SHA-256 manifests make the selected runs replayable.

## Limits and next implementation

The endpoint is one BR88 residual chunk through packed scratch to dense scalar
coefficients. Three-plane source sums are serialized chunk service, **not**
full-frame validated decoding. There is no integrated IDCT, reconstruction,
accepted reference/HUD/hash validation or atomic frame publication here. There
is no routed clock, calibrated SDRAM/controller, live ESP32 trace, deployed
firmware or physical throughput result.

Promote this bounded writer into the functional study, keeping overlap-off as a
control. V91g should prefetch bounded read lines and prepare the next tile while
the current tile is delivered; keep finite port/queue ownership explicit before
increasing outstanding requests. V91h then replaces combinational staging reads
with synchronous port scheduling. V91i–m integrate the full frame consumers and
publication fences. V100–V110 remain reserved for 7-series mapping, placement,
routing and timing on `xc7a100tcsg324-1`.

**720×480 sustained hardware 30 fps and complete validated FPGA decoding
strictly under 10 ms both remain open.**

## Reproduce

From this repository, with the existing `gamebub-cu66-v69-build` container:

```sh
python3 experiments/python-gamebub-v91f/write-ownership-model.py
python3 scripts/cu66-v91f/run_pipeline.py --seed 910432
python3 scripts/cu66-v91f/run_pipeline.py --seed 910433
python3 scripts/cu66-v91f/analyze.py
python3 experiments/python-gamebub-v91f/verify_results.py
```

Each runner invocation snapshots and strictly compiles its own source set with
Verilator assertions/fatal warnings and C++ warnings as errors. It runs bounded
self-checking integrated and direct-interface tests. Generated binaries stay in
the build container; retained receipts contain their reproducible commands.
