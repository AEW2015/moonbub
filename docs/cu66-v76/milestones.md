# Milestones and measurement boundaries

The goals remain sustained **30 distinct game-source frames per second** through
ESP32 → FPGA → display, followed by a **strict observed maximum below 10 ms for
validated FPGA decoding**, with no resolution reduction used to pass either gate.
They are separate measurements; a fast transform kernel, a repeated panel refresh
or a passing source-file audit establishes neither.

## Timestamp contract

For each generation/source ID record:

1. **Ingress complete:** the complete immutable compressed frame is available
   to the FPGA receiver. Real packet staging, retransmission and transport still
   belong in whole-system throughput and input-to-photon measurements.
2. **Admission:** the FPGA accepts that generation. Retain queue time from
   ingress complete; do not restart a failed latency timer on a retry.
3. **Validated ready:** the complete canonical image, required hashes/validation,
   actual memory drains and required HUD transfer fence are complete. The
   primary decode interval is ingress-complete → validated-ready; admission →
   validated-ready is an additional internal diagnostic. Include real memory
   stalls and any queue/validation delay in the primary interval.
4. **Composition ready / processor commit acknowledgment:** preserve both
   events and their identities. Neither is automatically a panel presentation.
5. **Qualified front switch and complete correct raster:** record both, using
   the actual display acknowledgment and full-raster source identity. A correct
   black border is not the first game-image pixel.

The V76 phase test's ingress timestamp is a modeled immutable-packet release,
with admission one declared tick later. Native CPU HUD decoding/hashing/control
execution and live ESP32 Wi-Fi/QSPI are not charged to that model. Real hardware
needs synchronized timestamp capture and a stated timer resolution; software
wall time or an assumed 100-MHz conversion is not routed-Fmax evidence.

## Throughput gate

Count distinct, ordered, correct source IDs delivered under the configured
30-fps input schedule. Keep missing, repeated, rejected, queued and late source
IDs, mixed-generation output, black/mismatching lines and underruns explicit.
Panel refreshes of an unchanged front do not increase source-frame throughput.
A native refresh rate that is not an integer multiple of 30 may produce normal
vblank quantization; state presentation jitter separately from the sustained
source rate and declare a deadline policy before the qualification campaign.

For the current single-candidate transaction path, 33.333… ms is its serial
service budget. A transaction exceeding it fails that implementation's 30-fps
service test. Future pipelines with genuine overlap need independent initiation
interval, queue-depth, latency and output-throughput checks; a blanket
33.333-ms end-to-end latency requirement is not a general definition of 30 fps.

Qualification progresses through:

- The retained **457-frame histories** for changed-path functional coverage.
- **1,800 distinct sources at 30 fps = 60 seconds**, the predefined modeled
  fixed-arrival campaign. This is not the ten-minute physical test.
- **18,000 distinct sources at 30 fps = 600 seconds**, after declared warm-up,
  for the ten-minute physical goal with live transport, processor service,
  actual display and target timing/CDC qualification. Declare start/end-window
  accounting and permitted jitter before measuring; retain all failures.

The V76 four-phase, two-source replay is diagnostic evidence rather than one of
those sustained campaigns.

## Decode-latency gate

Retain the 30-fps gate while requiring every measured ingress-complete →
validated-ready interval to be **strictly less than 10,000,000 ns**. Report
sample count, minimum, maximum, tail distribution, source/type, load/phase and
failure/recovery conditions. An observed maximum bounds only the tested campaign;
it is not a formal worst-case execution-time proof.

Exercise active scanout, reference traffic, refresh, bank/row conflicts, HUD
transfers, source/arrival phases, cache misses, response stalls and applicable
recovery paths. Isolated kernel, average, bootstrap or best-phase timings cannot
substitute for the validated-frame result. A recovery that invalidates a frame
must be reported as a failed source/deadline outcome, not silently removed from
latency statistics.

## Direct-YUV component gate

An eight-physical-row strip has **147.403024 µs** in the declared native timing.
A measured controller-service miss is a performance failure even when every
returned word is correct. Conversely, service-only success does not prove exact
bilinear/HUD pixels, hardware cache behavior, safe generation leases, scanout
ownership, pixel-clock delivery or sustained 30-fps decoding. Those require
subsequent RTL integration and target measurement.
