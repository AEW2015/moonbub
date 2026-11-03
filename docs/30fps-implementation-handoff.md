# Game Bub streaming: simulation handoff

Status snapshot: 2026-11-03 11:00 UTC. This is a research branch, not a
hardware release. The required target is 720×480 at 30 **distinct displayed**
frames per second; no complete physical end-to-end 30 fps result has been
measured.

## What has been exercised

- A strict 10-second behavioral QSPI-to-display run presented 300 distinct
  game-derived JPEGs. Inputs were sampled at 29 Hz from a precompressed clip
  and replayed at 30 Hz, about 3.45% faster than source time. Complete frames
  were assumed available at the receiver; there was no ESP32 or network timing.
  See [gameplay results](../fpga/experiments/throughput30/burst/gameplay-study/README.md).
- A separate 1,800-frame register-bus run eventually displayed and checked all
  frames but **failed** its strict 60-second capture window by 2.38483 ms.
  See [failure evidence](../fpga/experiments/throughput30/burst/longrun-study/results-1800-failed/README.md).
  The independent 1,800-frame modeled QSPI run also **failed** the strict
  window by 2.38483 ms after all frames eventually matched the reference; see
  [QSPI failure evidence](../fpga/experiments/throughput30/burst/qspi-longrun/results-1800-strict-failed/README.md).
- A live, stop-and-wait functional bridge ran the unchanged Rust receiver on
  emulated ESP32-S3, delivered accepted bytes to the Verilator FPGA model,
  checked a clean frame and a corrupt-frame abort/recovery sequence. The guest
  is a test harness, not the complete production application; clocks are not
  synchronized. See [live recovery](../fpga/experiments/throughput30/burst/live-multiframe-bridge/README.md).
- An isolated 48 KiB-per-bank dual-ingress candidate received the next frame
  while decoding the previous one. Its experimental QSPI-to-scanout model
  admitted/presented ten synthetic frames at 30 Hz with exact framebuffer and
  modeled LCD pixel checks. The adapter and free-bank status are test-only;
  this is not a 60-second or physical performance result. See [cadence test](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/qspi-cadence10/README.md).
- Narrow JPEG X/Y candidates passed separately scoped compositional stage
  proofs and 90-frame combined behavioral checks. The complete-IDCT inference
  requires the [documented initial-state/reset conditions](../fpga/experiments/throughput30/burst/idct-dsp-study/idct-composition-audit/README.md).
  Standalone generic DSP counts are **not** target implementation results.

## Highest-value next steps

1. Preserve baseline bitstream and logs; implement the dual-bank protocol in an
   isolated FPGA branch with bank generations, accepted/acknowledged abort,
   per-bank CRC/length, CDC ordering and actual QSPI credit/ownership semantics.
   The 48 KiB cap passed the limited local frame-size samples but is not a
   general bound; add safe oversize drop or quality adaptation. Never silently
   truncate a JPEG.
2. Integrate the narrowed JPEG candidates only after reviewing their reset
   conditions. Run complete target-part synthesis, placement, routed timing,
   BRAM utilization and hardware timing checks. The prior routed baseline was
   already at 120.5/135 BRAM tiles and +0.031 ns setup slack; do not infer
   modified-design fit from generic intermediate mapping.
3. Validate display timing against the exact panel and board before changing
   clocks. A hypothetical ~60 Hz model improved frame-age jitter on a ten-second
   sample, but controller documentation alone does not establish physical panel
   support. See [timing sensitivity](../fpga/experiments/throughput30/burst/refresh60-study/README.md).
4. Build a bounded end-to-end 60-second simulation using real guest byte
   handling and a validated synchronized time model, then measure the actual
   ESP32 receive/heap/PSRAM/QSPI path and FPGA counters on hardware. The live
   bridge currently freezes RTL time on IPC and is a functional check only.
5. On the Windows machine, separately measure actual Sunshine/game capture,
   JPEG encode, packet pacing, network loss/jitter and source buffer lifetime.
   Do not extrapolate Linux host microbenchmarks. Correlate capture, reception,
   decoded/presented IDs and physical latency with synchronized clocks or a
   camera-based measurement. See [Sunshine host evidence](https://github.com/AEW2015/Sunshine/blob/study/30fps-sim-20261102/tools/gamebub/measurements/live-30fps-evidence-gap.md).

Do not present the experimental control logic, generic mapping estimates or
simulator-only refresh rate as a hardware-ready image.
