# V91i2a: CS88 dispatch and BR88 coefficient placement

This checkpoint connects the restricted CS88 outer-frame path to the frozen
[V91h BR88 coefficient pipeline](../cu66-v91h/README.md). It retains the native
720×480 geometry and the existing bytes and quantization. Each emitted dense
coefficient carries its frame epoch, plane, residual-block ordinal, native tile,
coefficient index, quantizer cell and quantizer code.

This is the all-BR88 part of V91i2. A frame containing any AB38 residual chunk
rejects before the first child decoder starts. Empty residual planes are skipped.
COPY and CONST positions are used to locate residual coefficients; their pixel
consumers are not implemented here. `done` means the scheduled residual jobs
finished, including a zero-job frame; it is not validated frame publication.

## Ownership and storage

The new admission fork retains provisional mode and scale tables and exposes
registered packet-byte and table reads. Dispatch serially copies each admitted
BR88 span into the unchanged child frontend, then maps its chunk-local dense
blocks to the ordered residual positions. Both packet banks remain explicit:
49,152 bytes each, or **98,304 bytes (96 KiB)** total packet staging, before mode,
scale, cache and control storage. This is a functional architecture budget,
not a mapped resource count or evidence of target memory fit.

QM6 uses a complete externally supplied 1,350-value quantizer snapshot with
matching accepted-reference identity. A frame consumes that snapshot; the
provisional scale array cannot silently authorize a later accepted reference.
No accepted-reference or quantizer-cache commit exists at this endpoint.

Frame epochs and child-job epochs are separate. Each chunk receives a fresh
child epoch, while all of a frame's output tuples retain its frame epoch.
Cancellation invalidates local outputs, and an already accepted external
scratch request retains its owner until acknowledgment. Replacement cannot
overwrite packet/cache state or allocate a new child while the previous child
is busy or draining. The [contract](contract.md) defines exact interfaces,
error priority, byte/tuple ownership, timing fences and memory-service models.

## Reproduction

The two final seeds pass the complete case/profile matrix:

| Seed | Vectors | FAST/SLOW rows | Exact qualification coefficient/tuple checks | Tile records | Directed checks |
|---|---:|---:|---:|---:|---:|
| 911201 | 11 | 22 | 4,058,368 | 63,412 | 10 |
| 911202 | 11 | 22 | 4,058,368 | 63,412 | 10 |

The primary native evidence is four related frames, c0/f0, c0/f1, c0/f3 and
c3/f50, with three exact V91e BR88 coefficient goldens apiece. The extra rows
cover two native AB38/mixed rejections, an empty-residual frame, synthetic
quantizer snapshots and a corrupted third-plane chunk. These variations and
repeated memory profiles/seeds are not additional independent gameplay content.
The late CRC case preserves checked provisional Y/Cb output, emits no Cr
coefficients and never signals completion. The directed suite checks abort
and warm reset with an accepted write pending, blocked replacement, held
mapped output, retry after failure without reset, partial-cache cancellation,
one-shot preload ownership and invalid frame epochs. Each seed additionally
checks 913,984 directed coefficients outside the qualification tile traces.

The [independent audit](../../experiments/python-gamebub-v91i2/audit.json)
and [summary](../../experiments/python-gamebub-v91i2/summary.json) pin the
source, vectors and selected attempts. The largest measured native-frame
start-to-coefficient-completion count is **1,140,868 cycles**; the largest
packet-complete-to-coefficient-completion count is **1,068,582 cycles**.
QM6 rows separately charge 1,350 preload cycles; that preload is outside the
frame-start fence. These are new integrated coefficient fences, not a matched
speedup comparison with older chunk-only counters, an achieved clock, or a
complete validated decoding result.

The Python model selects retained native CS88 packets and cross-checks their
exact BR88 span bytes against the frozen V91e signed-coefficient goldens.
The independent auditor parses modes and quantizers separately and uses the
frozen V88 entropy reader as an alternate coefficient oracle. Synthetic cases
are labeled separately from native frame evidence.

```sh
python3 experiments/python-gamebub-v91i2/model.py
python3 scripts/cu66-v91i2/run_pipeline.py --seed 911201
python3 scripts/cu66-v91i2/run_pipeline.py --seed 911202
python3 experiments/python-gamebub-v91i2/verify_results.py
python3 scripts/cu66-v91i2/summarize.py
```

The runner uses the existing `gamebub-cu66-v69-build` container with Verilator
5.020 and GCC 13.3.0, strict assertions/warnings, and two compiler jobs. Every
attempt retains source/vector snapshots, commands, exit status, tool versions,
logs and observed tile traces, including failures. FAST/SLOW service profiles
are finite behavioral external-memory models, not measured SDRAM timing.

The retained draft lint failures were a reserved identifier and unused widths,
fixed without warning waivers. One seed-911202 build linked successfully and
then failed in Verilator 5.020 shutdown, matching its documented
[thread-pool race](https://github.com/verilator/verilator/issues/4931).
An unchanged-source, unchanged-flags retry passed. The
[5.024 release notes](https://github.com/verilator/verilator-announce/issues/69)
record a fix; this checkpoint retains 5.020 and the failed attempt rather than
changing tools or treating its nonzero exit as a pass. An earlier successful
run is retained but superseded by the final fail-closed child-output gate.

## Remaining gates

First use this frozen baseline to measure a bounded registered-read refill
FIFO against the current request/wait/send loop. Preserve both endpoint
ownership and the exact byte stream under child backpressure. Also price the
8,101-cycle provisional-mode initialization and test any alternative validity
scheme rather than assuming uninitialized entries are safe. Run each change
against identical source bytes and service assumptions; preserve a disabled
control and all old failures. The current 32-bit child-nonce exhaustion guard
is implemented but its terminal boundary is not exhausted in this RTL suite.

AB38 decoding or a negotiated sender fallback is required for mixed frames.
The full V91i transaction owner must integrate with dequantization/IDCT,
reconstruction, accepted-reference pixels, COPY/CONST generation, HUD, content
roots/seals and atomic publication. Those consumers must treat this endpoint's
coefficients and completion as provisional.

No hardware 30-fps, complete validated decode under 10 ms, physical placement,
routing, memory fit, achieved clock or ESP32 throughput result follows from
this simulation. V100–V110 retain the planned 7-series physical qualification.
