# Iteration 18: candidate ownership, actual packet admission and decoder traces

Target remains **720×480 coded / 720×405 active game content / 30 scheduled IDs/s**.
This iteration closes the Python integration gap between actual codec construction,
transport admission and decoded-reference publication. It does not qualify a native
ESP32/FPGA system or sustained physical 30 fps. Frozen v17 evidence remains on its
original branch; use the new paired `handoff/gamebub-app-codec-v18-20261103` branches.

## What is implemented

The [candidate study](../experiments/python-game-candidate-commit-study/README.md)
splits AR03 construction from semantic commit. A candidate owns its source-bank
lease. Build and discard cost time; rejection changes neither issued identity nor
published references. The native campaign has 48 candidates, 42 byte/pixel-identical
commits against frozen AR03 controls, six paid transport discards, four paid over-cap
rejections, and 887,040 exact selected RGB565 words with zero mismatch. Thirteen tests
check ownership, reentry, mutation and cleanup. No wire dialect changes here.

The [joint study](../experiments/python-game-joint-admission-study/README.md) runs
actual AR03 bytes through build → causal admission → commit/discard → individual
GF03 fragments → bounded gateway → reassembly → functional decode → AF03 reference
publication. Packet-consumption credits never substitute for decoded-bank ACKs.
Candidate commit waits for paid staged ACK mutation; expiry wins over completion.
Sixteen tests include a reproduced ACK-expiry/candidate deadlock, routing/body identity,
malformed prefix, corruption, loss, queries, replay and delayed feedback.

Its prospective transport is **GF03 v3**, with 1,008-byte payload, 31-byte GF header
and a 16-byte epoch/slot/sequence prefix: maximum UDP datagram 1,055 bytes. PC18
consumed feedback is 29 bytes and QC18 query 28 bytes, each CRC protected. IPv4/UDP
adds 28 bytes to every datagram. Six data credits, one query credit, six mailbox
entries, one worker, two frame reassembly slots, three framebuffer roles and bounded
feedback are explicit. Full GF03 bytes enter the proposed true-FIFO endpoint.
The installed MSV1 JPEG firmware and its existing register interface do not implement
this contract; GF02 vectors below are a separate retained transport fixture.

## Full-resolution gameplay results

Six runs each schedule the same 90 distinct native regression frames at 30 IDs/s.
The source is precompressed Mass Effect footage at 29.88 fps, starting at four seconds.
Capture acquisition is excluded; BOX resize and actual Python build/decode work are
paid. Each profile remeasures that work, so numerical differences between profiles
are not a controlled causal speedup comparison. Two 48-frame synthetic fault cases
bring the campaign to 636 capture events, with 49 source/dependency bindings.

| Profile | Strict / eventual out of 90 | Paid precommit rejections | IDs/s in [500,2500) ms | Maximum presented age ms |
| --- | ---: | ---: | ---: | ---: |
| unbudgeted | 74 / 76 | 0 | 27.5 | 133.3 |
| admit200 | 63 / 65 | 0 | 21.5 | 116.7 |
| admit150_batch8 | 67 / 70 | 15 | 23.0 | 150.0 |
| admit200_link4 | 54 / 58 | 21 | 19.5 | 183.3 |
| lost_credit_query | 59 / 61 | 0 | 20.0 | 133.3 |
| lost_refresh_AF | 75 / 76 | 0 | 29.0 | 133.3 |

All decoded native images preserve all 21,120 selected original RGB565 UI words.
The 150-ms / 8-ms-batch case spends 476.72 ms on the 15 builds it discards, sends no
bytes for them, and has no receiver NACKs. Its maximum in-window presentation gap is 133.33 ms, so bounded admission alone
does not make playback smooth. The 4-Mbps case rejects 21 candidates,
paying 640.40 ms for their builds. Loose admission still permits receiver NACKs;
a deadline estimate is not a receiver-capacity reservation or a latency guarantee.
The retained event trace diagnoses native NACKs as GF03 `busy`: both reassembly
slots are owned when another frame arrives. In the 200-ms case, frame 32’s first feed starts
0.101 ms before frame 30 releases its read-owned slot while frame 31 owns the
other slot. Later chunks may then allocate an incomplete frame until timeout.
Per-feed error timestamps are not retained, so the precise busy-return instant
and subsequent partial-slot occupancy are not proven by this summary.
This makes frame-slot reservation plus cancel/drain semantics the immediate
controller fix; returning a consumed-packet token does not grant a frame slot.
The 200-ms profile rejects zero candidates, so its difference from unbudgeted is
remeasured-service scheduling sensitivity, not admission benefit. The lost-credit
case performs one real query, returns all 1,899 data permits, and ignores delayed
replays. Lost AF03 feedback is built and charged to reverse wire before delivery
is suppressed. All eight cases finish without outstanding candidates, leases,
transactions, ingress frames or packet credits.

**No native gameplay case proves sustained 30 fps.** The best short diagnostic
window is 29 IDs/s in a fault profile; it is not evidence that loss improves rate.
Small synthetic cases report 30 scheduled IDs/s but only eight distinct decoded
hashes in their measured window. They establish fault ordering, not gameplay FPS.
The entire 54.38-second Python campaign runtime is not a playback-rate measurement.

## Actual AR03 vectors and nonuniform decoder demand

The [trace study](../experiments/python-game-ar03-trace-study/README.md) retains
16 complete AR03/AF03 packet decisions, 244 GF02 fixture datagrams, reconstructed
YUV banks, RGB565 outputs and content-addressed objects. Twelve native decisions
reuse six unique acquisitions across GM/exact cohorts; four flat controls exercise
SR. It verifies 97,308 coefficient blocks, 253,440 exact UI words and 53 atomic
negative RX rejections. Eight tests pass. Two byte-refill reservoirs are each bounded
to 64 bits, with observed peak 21 bits; input storage, CRC preflight, output, oracle
and trace storage are outside that bound.

For a native GM refresh key, Y token demand across 60 stripes averages 272.92 bytes
but peaks at 2,470 bytes: **9.05× the uniform assumption**. This measures logical
refill demand from real packets, not external-memory bursts, FPGA cycles or BRAM fit.
Use it to drive the next memory/scanline model rather than uniform per-stripe costs.

## Progression toward an application-specific implementation

1. Add receiver-advertised frame/decode capacity and measured age feedback to the
   candidate admission controller. Reserve capacity before commit; release it only
   on validated completion/expiry. Keep rejected builds and feedback costs paid.
2. Drive a bounded incremental decoder and stripe/SDRAM/scanout model from the
   exported actual AR03 coefficient/refill trace. Include the measured 9.05× burst,
   CRC/publication passes, line-buffer ownership and full-panel deadlines. The
   previous repeated-template memory study is not integrated with this controller.
3. Benchmark bounded native integer kernels using these wire/pixel vectors, then
   measure the ESP32-S3 CRC/copy/DMA/heap, Wi-Fi aggregation/RTT, QSPI arbitration and
   actual endpoint credit latency. Current assumptions are 240 MHz at 60% CPU budget,
   40 MHz quad-write, 8 KiB FIFO and 2 MB/s FIFO drain; none is RF/ISA calibration.
4. Preserve full resolution, exact HUD patches, newest-confirmed prediction and
   bank-local refresh. Evaluate sparse exact residuals only where their whole-chain
   cost beats GM. Compare causal policies on fresh long gameplay with fixed cost
   replay before choosing defaults; do not tune on this reused short regression.
5. Port the contract behind explicit negotiation/reset into Sunshine/ESP32/FPGA
   development branches. Keep the existing JPEG hardware path as the baseline until
   decoder vectors, loss recovery, mapped memory and resource/timing gates pass.

Run `python experiments/verify_prototype_v18.py` for retained hashes, vector replay,
analysis reconciliation and fresh independent audit. It does not regenerate timings.
Study READMEs show the explicit benchmark/test commands. Inventory pins conservatively
include ancestry dependencies, not exclusively executed code. No firmware, FPGA
bitstream, Sunshine native codec or installed service is changed by this handoff.
