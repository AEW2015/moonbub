# Plan: demonstrate Game Bub 30 fps with Verilator and Renode

## Goal and what constitutes evidence

Target **720×480 JPEG at 30 unique displayed frames per second** on the Game
Bub's 800×480 display, with the 16:9 video letterboxed if applicable. Start
with the JPEG path already being integrated; compare MPEG-2 or a custom codec
only after there is an executable decoder and an equivalent presentation test.
Neither simulated LCD refreshes nor accepted/network-received frames count as
newly displayed video frames.

A simulation result is scoped to its model, input trace and assumptions. For
the nominal no-loss workload, after an explicitly reported warm-up, require at
least 1,800 distinct, ordered and complete frame IDs presented in 60 seconds of
**simulated time**, with no missing IDs, transport/FIFO overflows, torn frames,
SDRAM protocol errors or LCD underruns. Drive at least 1,800 consecutive frames
at a known 30 Hz input cadence; the test must not reuse a short static frame
while reporting it as a new frame. Check every displayed frame against a decoded
reference or an explicitly defined pixel tolerance. Record the interval from
input to actual scanout and report p50/p95/p99 and maximum, plus presented FPS,
queue high-water marks, bandwidth and any drops. Results for losses, stalls or
scene changes are separate recovery experiments; never hide dropped frames in
an average. Sixty simulated seconds can take much longer than a minute to run.

This is a proposed acceptance baseline, not an already demonstrated result.
If a chosen LCD refresh rate means an exact 30 Hz swap cadence is impossible,
report actual modeled refresh, distinct frame timestamps and 10-second windows;
do not substitute a video-refresh counter for frame IDs. Set a latency target
using user requirements and hardware data rather than inventing one here.

## Progress update — 2026-11-02/03

The evidence below records the initial baseline; later work is tracked in
[the study progress](30fps-progress-2026-11-02.md). The following results are
behavioral simulations unless explicitly stated otherwise:

- The experimental burst path and its functional SDRAM model now run under
  both Verilator and XSim. Short full-resolution tests have passed with exact
  comparison against a related C decoder; this is not an independent codec or
  physical timing proof. See [burst README](../fpga/experiments/throughput30/burst/README.md).
- The experimental QSPI/CDC-to-LCD model passed a ten-frame test, and a
  separate packet-trace study passed clean and lossy ten-frame workloads.
  Its whole-frame network staging and FIFO credits are hypothetical; neither
  is a production ESP32/FPGA integration. See [network study](../fpga/experiments/throughput30/burst/network-rtl-study/README.md).
- Two 1,800-frame runs are **in progress**, one with optimistic register-bus
  upload and one through modeled QSPI. Neither is a completed 60-second pass.
  Partial results also show that display cadence does not establish a 33.3 ms
  per-frame latency deadline. See [latency study](../fpga/experiments/throughput30/burst/latency-study/README.md).
- Directed abort tests exposed partial-staging and simultaneous abort/vblank
  issues; isolated candidates pass selected Verilator tests and XSim checks.
  Production recovery, command acknowledgment and buffer ownership remain open.
  See [abort study](../fpga/experiments/throughput30/burst/abort-study/README.md).
- No ESP32-S3 firmware has been booted in Renode. As an alternative, an
  isolated Espressif ESP32-S3 emulator harness runs the unchanged Rust
  receiver and passes virtual UDP data over a synthetic live IPC bridge to
  Verilator. Clean frames and a pre-commit corruption/abort recovery scenario
  passed. The modified harness is not the complete production app, and the
  simulators have no shared clock, so this is functional integration rather
  than 30 fps or hardware proof. See [the live bridge](../fpga/experiments/throughput30/burst/live-multiframe-bridge/README.md).

## Current evidence and constraints

- XSim ran actual memory/LCD RTL and a functional SDRAM model for a single
  720×480 frame: current writes took 88.76 ms with scanout and the isolated
  transpose candidate 53.10 ms. Neither meets the 33.33 ms/frame budget in that
  workload. The transpose groups writes but does not create SDRAM bursts.
- Verilator 5.020 passed the transpose test, including the 345,600-pixel trace.
  The memory/LCD test timed out after 300 seconds without PASS. Diagnose this
  before relying on its throughput; the previous XSim result remains separate.
- No Renode Game Bub ESP32-S3 firmware boot or Renode–Verilator bridge has been
  demonstrated. Model availability and exact capabilities must be verified,
  not inferred from the existence of a generic Xtensa platform.
- Existing hardware observations and test scripts are valuable for calibration,
  but hardware resides on a different system. Simulation is not an RF, power,
  signal-integrity, timing-closure or measured input-to-photon guarantee.

## Phase 0 — Pin inputs and define the reference

1. Pin the Moonbub RTL, firmware and Sunshine host revisions; record tool
   versions, submodules, exact build flags and hashes of all input streams. Use
   separate worktrees and avoid disturbing the active hardware branches.
2. Prepare direct gameplay captures where available: quiet HUD, fast motion,
   scene change, particles, dark areas and detailed text. Keep rights and input
   provenance; include a deterministic synthetic stress sequence. State frame
   count, unique source frames, 720×480 conversion and 30 Hz timestamps.
3. Encode a reproducible sequence using the **actual supported** JPEG syntax,
   including sampling and Huffman restrictions. Produce an independent
   software-decoded RGB565 reference for each image and exact frame IDs; do not
   assume a generic FFmpeg MJPEG stream is receiver-compatible. Verify a short
   fixture against the existing decoder before scaling the workload.
4. Specify model assumptions and a machine-readable result schema: simulated
   and wall time, sender/receiver revisions, queue limits, link service,
   frame IDs, completeness, decode status, presentation timestamps, pixels,
   overflow/underrun/error counters and latency clock domains.

**Gate:** a second machine regenerates fixtures and verifies their hashes;
the short fixture can be decoded by the reference and target RTL.

## Phase 1 — Make Verilator trustworthy for the existing memory test

1. Add flushed milestones and bounded watchdogs for reset, SDRAM initialization,
   trace ingest, warm-up, write completion and readback. Report both wall and
   simulated progress so slow execution can be distinguished from deadlock.
2. Resolve or justify each Verilator width, timing and model warning; check
   event scheduling, initial state, tri-state/2-state differences, clock-domain
   crossings, and SDRAM-model assumptions. Never suppress an error solely to
   make the test pass.
3. Run a small deterministic fixture in both Verilator and XSim. Compare exact
   transaction sequence, cycle counts, memory contents, LCD requests and
   underruns; investigate any differences before scaling to the full trace.
4. Rerun the full 345,600-pixel existing and transpose workloads. Preserve
   per-frame checks, simulated time, stdout/stderr, version and exit status.
   A timeout is inconclusive, not PASS or a 30 fps result.

**Gate:** both simulators agree on correct pixels, bounded completion and the
explanation for any cycle differences; baseline performance is reproducible.

## Phase 2 — Prototype a genuinely faster FPGA path

1. Implement burst-capable SDRAM writes in a separate branch, starting with the
   existing decoder's block order and optional ping-pong tile buffers. Check
   actual SDRAM part/mode register, write burst semantics, timing, bank/row and
   address boundaries, byte lanes, refresh and line-fetch priority.
2. Add self-checking tests for backpressure, simultaneous scanout, refresh,
   reset/abort, partial tiles, buffer ownership, CDC and burst boundaries. Poison
   back buffers and compare every pixel. Inject starvation and verify bounded
   recovery without displaying incomplete frames.
3. Replay the same full frame and quantify busy/idle cycles, accepted writes,
   refresh stalls, arbiter grants and scanout underruns. Measure rather than
   assuming the required >1.59× improvement over the current transpose result.
4. Use the actual Artix-7 toolchain/device to check constraints, utilization,
   post-route timing and memory-device timing; review the small existing timing
   margin. Functional Verilator/XSim success alone is not a fit or timing pass.

**Gate:** the new implementation completes full-frame writes during concurrent
scanout inside 33.33 ms with zero detected errors, exact pixels, and documented
margin; this is still a component gate, not full-pipeline 30 fps proof.

## Phase 3 — Full FPGA video pipeline in Verilator

1. Connect the real SPI/QSPI ingress/register path, compressed-frame storage,
   JPEG parser/decoder, framebuffer manager, burst memory and LCD RTL. Drive
   the same transactions/handshakes as the firmware interface; retain actual
   clocks, reset and CDC behavior. Keep a vendor SDRAM timing-model or separate
   timing checks as a cross-check, subject to model availability/licensing.
2. Replay timestamped JPEG frames through a bounded source model. Exercise
   incomplete frames, malformed/oversize inputs, queue full, overflow, reset,
   frame replacement and CRC handling. The scoreboard must observe the actual
   scanout swap, associate it with the correct ID and compare the output pixels.
3. First pass 10 consecutive frames, then a 10-second 300-frame window, then the
   nominal 60-second acceptance workload. Simulate realistic variable JPEG
   frame sizes and pacing. Include another test with host/ingress stalls and a
   separate modeled packet-loss campaign to measure recovery and freshness.
4. Track frame ID at received, decoded, pending and actual presented stages.
   Check existing registers at `0x02c`, `0x030`, `0x034`, `0x044` and `0x050`
   against monitor-observed events; verify semantics in the pinned RTL before
   depending on them. Verify display swaps do not expose partially written data.

**Gate:** the simulated FPGA pipeline meets the 60-second nominal criterion
with source backpressure and no error counters, and the scoreboard proves new
frames and correct pixels. Report its allowed input service assumptions.

## Phase 4 — Renode firmware and bridge feasibility

1. Inventory current Renode releases and supported Xtensa/ESP32-S3 CPU,
   interrupt, timer, memory, peripheral and ROM/boot models. Pin the selected
   version. Write a capability matrix with tests, not just board-list entries.
2. Run a minimal ESP32-S3 ELF, then the actual pinned Game Bub receiver
   firmware. Verify boot, timers, buffer management and scheduling before
   claiming CPU/firmware coverage. Document unsupported Wi-Fi, SPI, DMA and
   interrupt features and how each will be modeled or stubbed.
3. Build a bounded, timestamped ingress model that replays recorded Wi-Fi/UDP
   traffic and loss; expose model configuration, queues and timing. A traffic
   feeder is not an ESP32 radio model or measured Wi-Fi capacity.
4. Connect the Renode-side interface to the Verilated FPGA model using Renode's
   supported co-simulation bridge or a documented adapter for the real QSPI
   interface. Check transaction ordering, credit/backpressure, clocks, reset,
   time synchronization and error propagation with known short transactions.
   Verify actual firmware exercises the path; a synthetic driver is a separate,
   lower-confidence integration test.
5. **If Renode cannot execute the target firmware or its necessary peripherals,**
   stop the full-system Renode claim. Continue Phase 3 with a clearly labeled
   synthetic transaction driver and evaluate an ESP32-S3-capable emulator or
   real hardware as an alternative. Do not substitute a different processor
   and call it an ESP32 result.

**Gate:** the real firmware boots and exchanges checked transactions with the
actual Verilated FPGA path, or the missing capabilities are reported as blockers.

## Phase 5 — Co-simulation, codec comparison and hardware correlation

1. Run the Phase 3 workload through the real firmware and bridged FPGA, with
   a calibrated ingress model and explicit CPU, bus and QSPI clock assumptions.
   Pass the same 60-second displayed-frame gate and capture latency/counters.
   Identify whether CPU work is cycle accurate; use virtual time only to the
   degree supported by the model.
2. Sweep input frame-size bursts, service rates, jitter, stalls and queue sizes;
   compare results under fixed total wire budgets including packet overhead.
   For inter-frame codecs also test reference loss and recovery; do not compare
   a software-only MPEG-2 result with an RTL JPEG result as equal proof.
3. On the remote hardware, measure actual concurrent Wi-Fi and QSPI goodput,
   buffer and overflow counters, FPGA decoded and presented IDs, LCD underruns,
   and host capture/encode and transport delays. Correlate simulated service
   profiles with these traces. Report hardware as a separate result.
4. For an eventual hardware demonstration, sustain at least 1,800 unique frames
   actually presented in 60 seconds with explicit drop and error counts, plus
   visual-quality review and a separately measured input-to-photon latency.
   Test audio/input simultaneously when those paths exist; report their status.

**Final result:** report one of (a) component-only validation, (b) simulated
30 fps under named assumptions, or (c) corroborated hardware 30 fps. Supply
commits, commands, model limitations, raw counters, logs and reproduction files.
A failed or blocked gate remains visible; it is not a partial 30 fps pass.
