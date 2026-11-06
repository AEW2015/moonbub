# V91h: explicit synchronous packet-staging RAM ports

Parent: `3e0d0cc527e0b517a7317a4d7ba4f3ff577871f4` (V91g2).

V91h replaces the packet staging array's combinational multi-address reads with
an explicit registered byte-read port. Incoming bytes still use one byte-write
port. Header, descriptor, bitstream replay and RAW accesses now pay a finite
read schedule. The wire format, quantization, packed scratch layout and intended
dense coefficients remain unchanged.

This is a functional memory-port qualification step. It may add service cycles;
it does not establish physical BRAM inference, resource fit or routed timing.
Those target-specific checks remain in V100–V110. The residual-chunk coefficient
endpoint still excludes complete pixel reconstruction and validated publication.

## Static configurations and actual read ownership

The top-level `SYNC_STAGING` parameter selects the implementation at elaboration.
Mode 0 instantiates the frozen asynchronous ingress for the V91g2 control; mode 1
selects the new synchronous ingress. The campaign compiles separate binaries for
the two settings. A synthesized mode-1 path does not retain a runtime-selectable
asynchronous staging reader or a second product staging bank.

The synchronous path has one 8-bit receive write port and one registered 8-bit
read port, with explicit request address, response address/data and epoch tags.
The backing array is not reset. A bounded 46-byte register cache gathers the
42-byte header plus four CRC bytes; it is reused for six-byte descriptors and
their tail-byte checks, replay words of at most four bytes, and RAW pairs.
Header and descriptor values are captured into control registers before this
cache is reused. Small register-cache accesses are distinct from backing-RAM
reads. The 46-byte highwater covers that shared gather cache, not all registers:
there is also a separate four-byte held replay word, two-byte RAW scalar and
one-byte registered RAM response, plus control and header metadata registers.
The conservative scheduler issues one read every two edges; response latency is
still exactly one edge after its request.

CRC is accumulated over accepted input bytes. Metadata cannot be accepted until
the whole packet is received, CRC/header checks pass and every coded context's
descriptor and padding are validated. The scratch allocator therefore cannot
start provisional external writes from a malformed later descriptor.

Context input pauses while a replay word is fetched, but an already-valid
context coefficient remains visible and stable through ready-low, including
RAM request/wait states. A word stays owned until the child decoder accepts it.
RAW fetch starts only after the previous coefficient is accepted; its latched
16-bit value remains stable while held. Partial final words preserve MSB-first
bit ordering, while header fields and RAW pairs remain little endian.

Start/reset/abort invalidates local fetch, word and response ownership. A stale
registered response cannot populate the replacement transaction's buffers.
These local on-chip read responses are distinct from the acknowledged external
packed-store bus: the latter still retains an accepted owner through real ACK
drain before replacement allocation. V91g2's qualified two-bank coded
preparation/emission path is reused unchanged.

The [Python port contract](port-contract.md) provides an independent executable
byte-assembly and ownership model. Its finite checks are not RTL equivalence,
physical memory timing, synthesis or hardware throughput evidence.

## Matched campaigns and results

Each seed compiles both static modes and tests 20 frozen V91e cases against FAST
and SLOW external-memory service: 40 rows per binary, 80 combined. The fixture
has 15 actual packets from five related three-plane sources, four synthetic
cases and an 8,192-block boundary case. This remains a small related source
family, not independent held-out games or native 30-fps hardware captures.

Write overlap, read prefetch and two-bank tile overlap remain selected; mask
clearing remains fixed. Mode 0 must reproduce all nine V91g2 timing/traffic
metrics and the ordered service fingerprint. Mode 1 must reproduce every packed
byte, dense coefficient and rejection behavior, while exposing its actual
staging read costs. RAW is also read through synchronous staging in mode 1, so
its timing can change.

FAST uses a one-edge external-memory response. SLOW uses write16/read18 plus
address/seed-dependent 0–3-edge jitter and deterministic input, request and
consumer stalls. These are synthetic service assumptions. The on-chip staging
port's registered read latency is modeled separately. Scheduling changes can
alter observed consumer-hold and external request-stall counts; analysis retains
those deltas alongside the added cycles.

| Final qualification evidence | Result |
| --- | ---: |
| Seeds / elaborated modes | 910432, 910433 / separate legacy and synchronous binaries |
| Measured configurations per seed | 20 cases × two memory profiles × two static modes = 80 |
| Dense comparisons | 9,003,776 per seed; 18,007,552 total |
| Integrated checks per seed | Legacy 47; synchronous 56, including nine new staging groups |
| Standalone packed-store checks | Nine per seed, unchanged frozen harness |
| Exact legacy control metric values | 40 rows × nine metrics × two seeds = 720 |
| Shared gather-cache highwater | 46 bytes |
| Independent Python model | Nine byte-assembly scenarios and six directed port/hold checks |

| Actual-packet service | V91g2 control | Synchronous staging | Added cycles | Overhead |
| --- | ---: | ---: | ---: | ---: |
| FAST, either seed | 2,885,281 | 2,888,167 | 2,886 | 0.1000% |
| SLOW, seed 910432 | 3,647,754 | 3,651,115 | 3,361 | 0.0921% |
| SLOW, seed 910433 | 3,648,933 | 3,652,091 | 3,158 | 0.0865% |

**This is a port-correctness promotion with a measured cycle cost.** Every
case/profile is slower than the combinational staging control in both seeds;
no cycle-speedup claim is made. The separate synthetic/boundary population adds
0.2154% FAST and 0.159–0.161% SLOW. Consumer-hold deltas for the actual SLOW
packets are +99/+12 edges, and external request-stall deltas +138/−461; those
schedule-dependent changes remain explicit in the analysis.

Each actual population writes 94,747 received bytes and issues/consumes
94,807 registered reads: 690 header/CRC bytes, 420 descriptor/tail bytes and
93,697 replay bytes. Every valid coded packet costs exactly `packet_bytes + 4`
reads, because each of four descriptors has one extra tail-byte access. RAW
costs exactly `packet_bytes` reads. The audit checks these per-packet equations,
all returned bytes and the purpose counts, rather than assuming all reads are
unique. External packed-store traffic stays once per used line and matches the
fixture-derived canonical service signatures. A RAM request is followed by its
registered response one edge later; the conservative engine starts one request
every two edges. The measured pipeline uses 32-bit context input words.

The slowest tested three-plane SLOW coefficient sum is **990,859 cycles**
(seed 910433), versus 990,205 for V91g2. This is still a coefficient-only fence,
not a validated full-frame or millisecond measurement.

[Analysis](../../experiments/python-gamebub-v91h/analysis.json),
[independent audit](../../experiments/python-gamebub-v91h/audit.json),
[port/timing contract](../../experiments/python-gamebub-v91h/telemetry-contract.json)
and [selected RTL receipt](../../fpga/experiments/cu66-v91h/pipeline-results.json)
retain the static compile settings, every case and the source/artifact pins.
Initial rejected snapshots retain the strict module-filename failure, the
local-versus-parent telemetry mismatch, and a directed error stimulus that did
not reach its required pending-read witness. The corrected stimulus sweeps a
single invalid DC code among eight valid prefixes and requires an actual
canceled pending read. Failed receipts stay unchanged; their ignored text
vectors can be reconstructed with `scripts/cu66-v91h/retain_vectors.py --restore`.

## Timing, evidence and remaining scope

Packet, scratch/preparation and emitter histograms each partition the same
running interval and must not be added together. Packet states 12/13 expose
staging request/wait work; shared register-cache occupancy is bounded. Staging
requests, registered responses, received writes and held replay words are
independently checked by the testbench. External-memory service still uses the
fixture-derived canonical signatures and once-per-line traffic assertions.
Exact byte and coefficient goldens remain the functional oracles.

The measured timing fence is BR88 residual-chunk input through dense coefficient
completion. A serialized three-plane source sum is not full-frame validated
decode latency. Achieved clock, calibrated external controller/ESP32 arrival
service, outer frame modes, dequantization/IDCT, references, reconstruction,
HUD/hash checking and atomic publication remain outside this qualification.
**Hardware 30 fps at 720×480 and complete validated FPGA decoding strictly
under 10 ms remain open.**

Next is V91i: outer-frame descriptors, supported modes, quantizers, profile and
chunk placement/admission. Unsupported combinations must reject before reference
or scanout ownership changes. V91j–m then connect the actual pixel consumers and
complete-frame validation fences. Keep the static V91h control, bit/byte goldens
and recovery checks through those changes.

## Reproduce

From this repository with the existing `gamebub-cu66-v69-build` container:

```sh
python3 experiments/python-gamebub-v91h/staging-port-model.py
python3 scripts/cu66-v91h/run_pipeline.py --seed 910432
python3 scripts/cu66-v91h/run_pipeline.py --seed 910433
python3 scripts/cu66-v91h/analyze.py
python3 experiments/python-gamebub-v91h/verify_results.py
```

Receipts retain both static parameter/compiler settings, strict warning/error
and RTL assertion builds, bounded self-checking transcripts, source snapshots,
tool versions, compressed tile traces and source/artifact SHA-256 pins.
