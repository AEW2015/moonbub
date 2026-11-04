# Finite AR01 reference ownership with GF02 and AF01

This Python model carries actual AR01 bodies through GF02 reassembly, owned
reference decoding and serialized AF01 feedback. The target remains 720×480
coded video, 720×405 active native content and 30 scheduled IDs/s. It uses the
new two-bank AR01 codec, not SR01 residual coding or HG01 exact UI patches.
Its base-only FPS is not directly comparable with v13's UI streaming results.

Bank 0 is the ACKed key; bank 1 is a published reconstructed P. The encoder uses
only a confirmed bank/tag. Promotion first drains all sender transactions and
leases, reserves bank 1, pays reconstruction/hash work, and blocks preparation
until a content-bound ACK or drained expiry. Lost promotion feedback leaves bank
1 unusable; key-bank fallback and later promotion can recover.

## What is paid and owned

Every actual BOX resize, map construction, prepare/rejection, packetization,
GF02 feed batch, decoder begin/complete/abort, AF01 parse/application and expiry
call pays its measured host wall duration. Each stage has an independent
serialized virtual server. This does not measure concurrency on a shared CPU.
Expected-image reconstruction and quality/hash verification are outside clocks
and never select a live reference or promotion.

All GF02 chunks consume their complete IPv4/UDP wire bytes, then enter a real
frame-batched feed call. Unlike the earlier per-chunk model, this model does not
overlap early chunk feeding with the remainder of that frame's wire transfer.
The grouping is explicit and must not be credited as a codec improvement.
Forward/reverse 8 Mb/s, QSPI 160 Mb/s, feedback propagation 10 ms and vblank 60 Hz
are declared assumptions. Actual desktop acquisition and native/RF/SDRAM timing
remain unmeasured.

There are three host transactions, two actual GF02 ingress slots, four feedback
descriptors and three metadata display-buffer roles. A delivered ingress payload
stays pinned through begin, completion or abort. Reference read leases likewise
span the modeled read interval. Sender reclamation waits for queued and active
wire, feed, QSPI, decode and feedback owners. Receiver rejection sends an actual
AF01 NACK; host expiry does not learn the remote rejection before that message
travels back. A wholly dropped single-chunk key fabricates no receiver route or
NACK and instead waits for the sender timeout.

The model first executes an offline mutating call to measure its cost, snapshots
its semantic result, and restores old public state until virtual completion.
This applies to ACK installation and decoder bank publication. Expiry during
ACK work discards future sender publication; an elapsed decode deadline aborts
future receiver publication. Actual work counters are not refunded. Semantic
snapshots use immutable plane arrays and preserve pending rows/read leases.
They are single-threaded modeling scaffolding, not a native concurrent API.

## Retained results

Thirteen cases execute 1,152 capture-policy events, 1,028 preparations and 1,027
successful decodes in 80.63 seconds of host wall time. Native sources are two
60-frame windows and a separate 180-distinct-image held-out window. The sources
are related, precompressed 25/29.88 fps files, scheduled hypothetically at 30 IDs/s.
Case totals are repeated policy runs, not 1,152 distinct captured images.

| Native source / policy | Strict / eventual | Diagnostic IDs/s |
| --- | ---: | ---: |
| Combat, immutable key every 30 | 54 / 55 | 28 |
| Combat, recent-P every 8 plus keys every 30 | 48 / 49 | 25 |
| Combat, recent-P every 16 plus keys every 30 | 52 / 53 | 27 |
| Second, immutable key every 30 | 55 / 57 | 28 |
| Second, recent-P every 8 plus keys every 30 | 48 / 49 | 25 |
| Second, recent-P every 16 plus keys every 30 | 51 / 53 | 26 |
| Held-out 180, immutable key every 30 | 167 / 169 | 28.0 |
| Held-out 180, recent-P every 8 plus keys every 30 | 145 / 146 | 24.2 |
| Held-out 180, immutable initial key | 177 / 179 | 30.0 |
| Held-out 180, recent-P every 16, initial key | 158 / 160 | 26.6 |

Recent references save algorithm bytes, but this conservative all-pending drain
and ACK barrier lose delivery cadence. The held-out recent-8/key-30 run records
1,471 ms waiting on reference drain over six seconds; recent-16/initial records
804 ms. They are exclusive waiting intervals, not additive causal attribution
of missed frames. This motivates a separate bank-specific/overlapped promotion
experiment rather than treating immediate-ACK compression savings as a frame-rate
proof.

The immutable-initial diagnostic 30.0 is a short conditional model operating point.
It still presents only 179/180 IDs eventually and 177 before capture stops. Startup
and final drain must be separated from rolling cadence and interior drops. Initial-
only refresh is not qualified as a production default. All displayed ages obey the
150 ms decode gate plus at most one vblank interval; this is not a strict 150 ms
optical-latency guarantee or hardware 30 fps.

Three full-canvas synthetic fault cases separately exercise an initial key chunk
loss, the first promotion ACK loss, and conflicting ACK/NACK promotion feedback.
The latter leaves the sender bank uncertain even if the receiver decoded it.
Byte/tag checks prevent stale or contradictory feedback from selecting an
unconfirmed reference. Every case drains all pending/ingress/reader ownership.

Eight small actual-packet tests cover immutable and promoted references, lost
promotion fallback, lost/corrupted keys, conflicting feedback and rejected work.
Two regressions inject 100 ms of paid ACK or decoder completion work. They prove
that a timeout/deadline during that interval cannot publish a future reference,
while preserving paid work and physical-reader drain. The unit clock is declared
test machinery, never used in the performance benchmark.

## Memory limits and reproduction

Two retained YUV banks per peer are distinct from pending promotion reconstruction,
source/prediction/coefficient arrays, RGB output, packet copies, queues and display
storage. Logical YUV8 pass counters and Python int16 array byte counts are reported
separately. Peak retained banks can include a private trial publication before
semantic rollback; they are bounded by two and do not prove peak physical memory
or SDRAM service. No target firmware, decoder RTL, CDC or DMA is implemented.

```sh
python -m unittest -v test_model.py
python verify.py                       # read-only retained evidence
python benchmark.py > run.log 2>&1     # regenerate; external media required
```

Use the study virtual environment. Results pin all executed sources and input
media; the parent manifest pins this README and all retained artifacts.
