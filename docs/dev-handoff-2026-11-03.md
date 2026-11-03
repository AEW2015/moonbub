# MoonBub developer handoff — 2026-11-03

For proposed custom codec work, read the [codec audit and revised plan](codec-development-audit-plan.md)
before selecting a new decoder. It preserves JPEG as the baseline and defines
software comparison, reference-state and memory-service gates.

The [external-memory audit](external-memory-audit-plan.md) qualifies SRAM and
second-SDRAM-chip use as separate work packages. It corrects the proposed
60 fps bandwidth budget and distinguishes raw advertised capacity from this
streaming top's implemented interfaces.

## Baseline and evidence boundary

New software-only evidence is in the
[Python codec study](../experiments/python-codec-study/README.md) and
[memory-service study](../experiments/python-memory-study/README.md). They
include bounded parsers/reference-state tests and comparisons with exact
receiver-profile JPEG on short, precompressed Mass Effect samples. JPEG remains
the control; these additions do not change device firmware or the bitstream.
Use the result manifests rather than inferring hardware FPS from offline
frame counts or hypothetical vblank eligibility.

The work is on the [Moonbub study branch](https://github.com/AEW2015/moonbub/tree/study/30fps-sim-20261102) and the [Sunshine study branch](https://github.com/AEW2015/Sunshine/tree/study/30fps-sim-20261102). These branches contain experimental code and evidence; none of the new RTL should be treated as a production bitstream. Existing separately qualified device artifacts must be identified and preserved before testing.

The memory architecture uses FPGA BRAM for a 256 KiB compressed-JPEG buffer and two 480-word LCD line banks. A 720×480 RGB565 framebuffer is 691,200 bytes and resides in external SDRAM. The board's SDRAM identity, population, timing and physical operation are unverified; the simulation memory is functional, not a vendor timing model. See [FPGA architecture](../fpga/README.md), [SDRAM controller](../fpga/rtl/moonshine_sdram.sv), [memory integration](../fpga/rtl/moonshine_memory.sv), and [LCD scanout](../fpga/rtl/moonshine_lcd.sv). BRAM use or fit is not evidence of external-memory throughput.

Two alternatives are available for investigation: [two 48 KiB BRAM banks](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/xc7-map-study/README.md), with an explicit JPEG size cap, or [two 256 KiB SDRAM staging slots](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/sdram-storage-model/README.md), which would preserve the existing size limit but contend with scanout and pixel writes. Neither is implemented or qualified for production. The available Vivado installation lacks the target Artix part, so the BRAM inference estimates are not target placement or timing results.

The experimental [SDRAM-fed reader](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/sdram-jpeg-reader-study/README.md) and [burst writer](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/sdram-jpeg-writer-study/README.md) pass bounded unit tests. A [two-frame integration](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/sdram-jpeg-full-study/README.md) passed with a testbench byte source feeding the writer, modeled SDRAM, reader, real JPEG decoder and LCD RTL. Its validity guard is testbench logic, not a production CRC; real ingress, CDC, ownership and physical drain recovery remain to be implemented.

The [stage-timing study](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/sdram-jpeg-timing-study/README.md) records one modeled fixture's internal timing. Its testbench injects bytes faster than the nominal QSPI payload ceiling; it cannot be used as a hardware or capture-to-photon latency result.

The strongest full-frame results are isolated behavioral simulations. The burst candidate completed one synthetic decoded frame with concurrent modeled LCD fetch in 21.65697 ms, and a single JPEG-to-frame-swap integration completed a synthetic 720×480 fixture in 25.37677 ms with no new modeled underruns. Neither is a sustained stream or measured display rate. The isolated synthetic four-client arbiter passed 24 periodic display-line deadlines (worst 1,025 cycles / 1,843-cycle limit) while its three background clients completed their small fixed workloads. It has strict display priority, can starve background clients, assumes always-ready read sinks, and lacks response backpressure, CDC, transaction identity, abort and write-drain acknowledgement. These experiments are useful starting evidence, not integrated or hardware validation. See [burst experiment results and limits](../fpga/experiments/throughput30/burst/README.md) and [arbiter study](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/sdram-arbiter-study/README.md).

The [300-frame cadence study](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/qspi-cadence-jitter/README.md) uses deterministic synthetic JPEG arrivals and a functional SDRAM/LCD model. All three completed ten-second cases—zero jitter, ±2 ms jitter, and ±2 ms with hypothetical ~60 Hz scanout—presented 300 distinct frames with no modeled busy drops or underruns and passed related C-model pixel checks. The ±2 ms baseline had p95/max frame age 39.410/41.825 ms; the hypothetical 60 Hz case had 30.051/30.064 ms for one starting phase. With a shifted capture phase, the [same hypothetical 60 Hz test](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/qspi-cadence-phase/README.md) **failed** the strict window: 299/300 frames appeared in time, and the final frame was 5.064 ms late despite all frames eventually matching. A separate [1,800-frame single-bank QSPI run](../fpga/experiments/throughput30/burst/qspi-longrun/results-1800-strict-failed/README.md) **failed** its strict 60-second window by 2.38483 ms despite all frames eventually matching the reference. These models assume complete frames arrive at scheduled instants and do not represent network, ESP32 execution or physical presentation.

Cross-machine access to the physical board and its serial/programming resources is currently unavailable. No board-level test, panel measurement, physical SDRAM qualification, or target-fit claim is available. The separate routed baseline reports in [timing review](timing-review.md) apply to their stated implementation and provisional assumptions; they do not qualify this branch or board.

## Work packages and acceptance evidence

For independent agents, use separate worktrees or branches and preserve the
study evidence. Suggested task prompts:

> **FPGA/hardware agent:** Starting from the Moonbub study branch, evaluate the
> BRAM and SDRAM options below, select an integration candidate using measured
> resource/timing evidence, and integrate the actual display, decoder and
> bounded ingress paths. First reproduce the relevant simulations; then run
> target implementation and hardware tests only on your accessible device.
> Report bitstream/source hashes, model limits, timing, memory use, frame IDs,
> underruns and failure/recovery results. Do not assume this study is a
> hardware-qualified 30 fps image.

> **Firmware/host agent:** Starting from the linked Moonbub and Sunshine study
> branches, implement and test bounded transaction identity, ACK/NACK,
> reset/drain and size/quality behavior at the real firmware/host interfaces.
> Preserve the installed Sunshine service and existing working baseline. Use
> your accessible hardware for throughput and recovery measurements; report
> host capture, receiver ingress and actual presentation separately. Do not
> treat an ingress ACK or simulator time as a displayed-frame measurement.

### FPGA: turn the burst candidate into an integrated memory path

- Start from the isolated [full-frame burst candidate](../fpga/experiments/throughput30/burst/README.md), preserving the current single-pixel path as a reference. Integrate the real decoder/transpose, a bounded queue, the LCD line-fetch path and a memory arbiter. Add explicit backpressure, response ownership, abort/reset recovery, refresh handling and atomic frame publication.
- Strengthen the [four-client arbitration prototype](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/sdram-arbiter-study/README.md): replace the unbounded-starvation risk with a justified display service bound and fairness policy; add range checking, non-always-ready sinks, queue limits and transaction identity. Include real frame-sized JPEG staging and decoded writes in the same workload.
- Acceptance: multi-frame tests across phase, row/bank changes and refresh; exact pixel and frame-ID conservation; no stale or partial publication, unexplained drops, protocol faults or underruns; measured full-frame service within the agreed budget under concurrent scanout. Report model assumptions. Then synthesize/place/route the actual target and validate physical SDRAM and panel on the identified board. Simulation success does not substitute for those gates.

Primary RTL: [`moonshine_sdram.sv`](../fpga/rtl/moonshine_sdram.sv), [`moonshine_memory.sv`](../fpga/rtl/moonshine_memory.sv), [`moonshine_core.sv`](../fpga/rtl/moonshine_core.sv), [`moonshine_lcd.sv`](../fpga/rtl/moonshine_lcd.sv). Keep experiments under `fpga/experiments/throughput30/` until reviewed.

### FPGA/verification: finish the cadence campaign

- Extend the archived 300-frame comparisons across capture phases, service and arrival variation, and longer intervals. Preserve exact invocation, inputs, source hashes and logs; check every accepted/dropped ID, framebuffer, LCD output, scan count, underrun and capture-window count. Analyze arrival variation against nominal capture time and state precisely what the model does and does not represent.
- Acceptance: reproducible successful run artifacts and tested analysis for each configuration; report incomplete runs as pending. This evidence remains behavioral simulation and cannot establish hardware FPS.

### Firmware: bounded ingress and recovery

- Exercise session replacement, disconnect, contention, incomplete/corrupt/oversize frames, FIFO credit exhaustion and recovery using the exact production Rust protocol module. On hardware, correlate host session/frame IDs with ingress, QSPI accepted/lost words, decode, publication and presentation; keep these boundaries distinct.
- Use the [tagged gateway prototype](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/tagged-gateway-rtl/README.md) and [NACK-aware guest experiment](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/live-guest-nack/README.md) as design evidence, not as existing production semantics. Define transaction generations, bounded replay, CDC credits, physical write-drain ACK and reset reconciliation before connecting them to firmware.
- Acceptance: exact firmware build/hash and logs; malformed or partial input never becomes visible; losses are counted; a subsequent valid frame recovers without reset. Measure concurrent Wi-Fi/QSPI only on the physical device.

Primary files: [`protocol.rs`](../firmware/handheld/src/streaming/protocol.rs), [`streaming/mod.rs`](../firmware/handheld/src/streaming/mod.rs), and [`firmware/evidence/`](../firmware/evidence/).

### Host: capture, JPEG policy and pacing

- Measure capture, canvas conversion, encode, packet send and queue age independently. Record IDs, monotonic timestamps, quality, byte size and drop reason. Bound stale-frame backlog and verify the exact receiver JPEG profile and byte cap. Run both a fixed hashed local clip and live capture on the target host.
- The study sender's optional `--frame-telemetry` emits normalized host capture and send-completion records for the [offline correlator](../telemetry-study/README.md). Capture timing includes source acquisition and canvas preparation. Session ID and capture sequence are host metadata, not current MSV1 fields; receiver instrumentation must coordinate the session and map wire IDs, including wrap. These records do not establish ingress or presentation.
- The isolated [48 KiB q90/q80 study](../experiments/jpeg-cap-quality-study/README.md) evaluated 1,493 frames from one low-resolution 25 fps sample: q90 exceeded the cap on 503 frames; a same-frame q80 retry selected q90 for 990 and q80 for 503, with zero drops. The second 360-frame clip had no q90 overflows and required no retry. The measured PSNR is against an upscaled, already-compressed source; it is not perceptual acceptance. Timings are offline encoder timings, not gameplay or target measurements. See [first clip summary](../experiments/jpeg-cap-quality-study/SUMMARY.md) and [second clip summary](../experiments/jpeg-cap-quality-study/mass-effect-29_88/SUMMARY.md).
- Acceptance: repeatable per-stage latency distributions, explicit size/overflow and retry counts, queue age and drop counts, then physical host-to-receiver correlation. Keep the retry optional until image-quality limits are agreed and receiver behavior is measured.

Primary experimental sender and capture work is in [Sunshine tools/gamebub](https://github.com/AEW2015/Sunshine/tree/study/30fps-sim-20261102/tools/gamebub). Its `--max-jpeg-bytes` and one-retry quality setting are optional study features, not installed Sunshine behavior. The native capture/scaling experiment is not yet a working Windows capture integration.

### End-to-end: demonstrate presentation cadence on the board

- After access is coordinated, identify board, FPGA, SDRAM and panel; record firmware/bitstream hashes. Validate a known pattern and JPEG fixtures first, then stream representative gameplay. Correlate capture, encode/send, firmware ingress, FPGA decode/publication and physical presentation using session-scoped IDs. Keep host and receiver clocks separate; cross-clock latency requires a same-session offset and uncertainty including drift over the full measurement interval.
- Before the run, agree rate window, acceptable age percentiles, quality/byte cap, and loss/underrun limits. Acceptance is a sustained physical presentation measurement over the agreed interval (recommend at least 10 minutes), with distinct presented IDs, interval/age distributions, repeats/drops and fault counters. Sender completion, ingress, one fixture or a simulated service rate do not count as presented FPS.

## Claims to preserve

No current result establishes 30 physical displayed fps, target fit, physical SDRAM performance or gameplay image acceptance. The 21.65697 ms burst service and 25.37677 ms JPEG integration are single-frame functional-model results; the arbiter test is a small synthetic schedule. Three synthetic 300-frame cases passed their ten-second windows, but the shifted-phase case failed its window; the separate single-bank 1,800-frame run failed its strict 60-second window. Cross-machine board/serial access is unavailable. Keep each of these limits attached when reusing results.
