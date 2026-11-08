# V107 component latency: next milestone after clock timing

Clock timing remains the primary gate. The following are recorded **component simulation cycles at a hypothetical100 MHz**, not a qualified operating frequency, measured hardware FPS or accepted-frame publication latency. The elastic boundary passes its two-seed canonical functional campaign, but these traces independently show that nonzero successful fast cases still miss the strict10 ms cycle budget.

## Pinned read-only analysis and bench boundary

[profile_latency.py](../../scripts/cu66-v107/profile_latency.py) streams all four retained gzip event traces and records compressed/raw hashes, row counts, source hashes and the canonical receipt hash in [results.json](../../experiments/python-gamebub-v107/latency/results.json). It preserves the source campaign counts and uses integer histograms rather than retaining all events. All four traces contain378,996 events each; each has50,462 complete transforms from successful case/profiles. The streaming join holds at most one assembled-but-not-emitted transform owner; this is an event-join observation, not a claim that the two coefficient banks have only one owner. No RTL, vendor jobs, compiles or new tests were run.

The pinned canonical [receipt](../../experiments/python-gamebub-v107/elastic-pipeline/attempts/20261108T040408755478Z-733a6edf/results.json) SHA-256 is `3e279727a44a81dd5a612059ad0581921c9f74dada7935aaef211f8b7287dc9f`. Both seeds107601/107602 and control/elastic traces are included. Only successful case/profiles enter these distributions; expected-error cases and unrecorded directed recoveries are excluded.

The [bench start](../../fpga/experiments/cu66-v107-elastic/verification/bench.cpp#L353) sets begin_cycle immediately before the accepted frame-start tick. The case's `cycles=cycle-begin_cycle` is printed after [completion/error checks and ownership settle](../../fpga/experiments/cu66-v107-elastic/verification/bench.cpp#L387). It includes packet-byte offers, admission, scratch request/ACK service, inverse transforms, reconstruction, modeled reference service, canonical output acceptance and any settle ticks. Optional1350-byte qcache preload occurs before begin_cycle and is reported separately. Host transport, HUD/C2 work, accepted-frame publication and hardware execution are outside this boundary. The original `full_frame_publication:false` field remains preserved. This must not be called full end-to-end publication/decode timing.

Profile0 accepts packet bytes/output whenever available and models finite scratch/reference service. Profile1 adds the original input/output/request stalls and longer finite service. These are two explicit bench environments, not a production service guarantee.

## Successful case distributions

Each row has12 observations: six successful caseids × two seeds. Repeated cases/seeds remain declared observations, not independent workload sampling. Median averages the middle two values; p95 is nearest rank `ceil(0.95*N)`, which is the maximum for N=12. Cycle comparisons are strict: `<1,000,000` and `<3,333,000`. The latter is the requested approximate30 fps budget at hypothetical100 MHz; no hardware30 fps qualification follows.

| Variant | Profile | Min cycles | Median | p95 | Max | Strict<1M | Strict<3.333M |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Quant-aligned control | Fast | 650,593 | 1,196,834 | 1,726,027 | 1,726,027 | 2/12 | 12/12 |
| Quant-aligned control | Stalled | 1,769,386 | 2,095,155 | 2,473,667 | 2,473,667 | 0/12 | 12/12 |
| Elastic candidate | Fast | 650,593 | 1,196,953 | 1,726,035 | 1,726,035 | 2/12 | 12/12 |
| Elastic candidate | Stalled | 1,768,082 | 2,093,345 | 2,473,261 | 2,473,261 | 0/12 | 12/12 |

At the hypothetical frequency, elastic fast min/median/p95/max are6.506/11.970/17.260/17.260 ms; stalled are17.681/20.933/24.733/24.733 ms. Only the two all-copy fast repeats are under1M cycles. Every successful nonzero fast case remains above1M; all24 successful elastic case/profile observations remain below3.333M. The same outcome holds for control. Cycle deltas from adding the elastic boundary are small: fast−6..+129 and stalled−3,278..+3,178. The latency milestone needs work beyond the timing cut.

## What the actual transform timestamps show

The event `assemble` is the accepted dequantizer launch; `dequant` is the accepted DQ→IDCT handoff; `residual` records first and last accepted samples of a64-sample inverse tile. Joins check token/plane/block/tile/cell/scale/frame/child identity and complete64-sample records. Each variant/profile distribution contains50,462 complete tiles across both seeds; between-tile metrics contain50,452 pairs because ten nonempty successful frame runs each have no predecessor for their first tile. All-copy runs have no transform events.

| Elastic measured interval | Profile | Min | Median | p95 | Max |
| --- | --- | ---: | ---: | ---: | ---: |
| Assemble→DQ/IDCT handshake | Fast | 1 | 9 | 9 | 9 |
| Assemble→DQ/IDCT handshake | Stalled | 1 | 9 | 9 | 9 |
| DQ/IDCT handoff→first accepted residual | Fast | 2 | 130 | 221 | 36,464 |
| DQ/IDCT handoff→first accepted residual | Stalled | 2 | 202 | 646 | 104,518 |
|64-sample accepted-output span, inclusive | Fast | 64 | 64 | 64 | 64 |
|64-sample accepted-output span, inclusive | Stalled | 64 | 64 | 64 | 64 |
| Gap: prior last residual→next first residual, exclusive | Fast | 68 | 140 | 231 | 37,422 |
| Gap: prior last residual→next first residual, exclusive | Stalled | 130 | 212 | 656 | 104,995 |
| Prior last residual→next assemble launch | Fast | 2 | 2 | 2 | 24,620 |
| Prior last residual→next assemble launch | Stalled | 2 | 2 | 2 | 24,605 |
| Assemble→last accepted residual, inclusive | Fast | 67 | 203 | 294 | 36,537 |
| Assemble→last accepted residual, inclusive | Stalled | 67 | 274 | 719 | 104,591 |

Control has the same fast medians/p95s and the same64-cycle output spans. Its stalled median/p95 DQ→first interval is202/647 cycles, between-tile gap211/658 and assemble→last274/720; elastic differences are small. Full control distributions and all maxima are retained in the JSON.

These are **handshake intervals with waits/backpressure**, not pure kernel measurements. Assemble→handoff includes dequantization and readiness wait. Handoff→first residual includes IDCT work plus controller and consumer wait; the traces do not expose a separate IDCT-result-ready timestamp. Every tile emits its64 accepted residual samples consecutively once the burst starts, even under the stalled profile: observed waiting is between bursts, not inside these bursts. Large gaps can include unavailable input tiles, reconstruction/reference service or output wait. Do not infer AC/DC classes solely from interval length, and do not sum overlapping interval categories as total case cycles.

## One concrete next architecture to evaluate

Evaluate a **two-entry whole-tile result queue between IDCT and residual emission**, after the fixed-clock experiment is measured. The current [inverse output gating](../../fpga/experiments/cu66-v107-value-check/cu66_inverse_stream_v91j.sv#L942) ties out_valid to M_EMIT and acknowledges IDCT only with accepted sample63. The [M_EMIT transition](../../fpga/experiments/cu66-v107-value-check/cu66_inverse_stream_v91j.sv#L1042) frees the active coefficient bank, flips math_bank and returns M_IDLE only on that final acceptance. The [IDCT itself](../../fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv#L138) accepts input only in IDLE and [holds OUTPUT_TILE until out_ready](../../fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv#L245). Thus the next tile cannot start while the prior tile's64-sample result is being serialized. Measured median/p95 restart is exactly two cycles after the last residual acceptance, consistent with this control structure.

A future queue would capture the complete1536-bit signed24×64 IDCT result plus its immutable output owner, acknowledge IDCT at capture, and allow the next coefficient bank to launch while a separate emitter drains the queued tile. Snapshot the full140-bit owner tuple (token32, frame_epoch32, child_epoch32, plane2, scale2, block16, tile13, cell11) before freeing/reusing the coefficient bank. Two result entries require3072 payload bits plus280 metadata bits:3352 bits/419 bytes, plus valid/head/tail/emit-index control. This is a raw storage budget only; a wide parallel capture and selector may map to many FFs/muxes, so actual area, control fanout and timing must be measured. No RAM inference or gain is promised.

The fast traces serialize3,229,568 residual-emission cycles across the12 successful runs. A result queue offers an opportunity to overlap some of that serialization, and possibly some inter-burst consumer wait, with next-tile math. That count is not a predicted saving: input availability, DQ/IDCT latency, result capacity, reconstruction readiness and other pipeline work still limit overlap. The current evidence does not establish that this change alone can meet strict1M cycles.

Before implementation, define separate math-result and emitter ownership; queue-full backpressure; stable held payload/metadata; token/epoch ordering; reset/start/cancel flush; mismatch/error priority; and done only after input, math and result queue drain. Keep output/completed-tile counters on actual residual acceptance. Then require independent arithmetic goldens and latency-aware whole-pipeline token/flush/canonical-byte checks, followed by actual fixed10 ns timing/resource comparison. This is a concrete future experiment, not implemented or validated performance improvement. Generic hardware30 fps, complete decode below10 ms and full C2/HUD publication remain open.
