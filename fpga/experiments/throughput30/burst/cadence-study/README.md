# Display cadence experiment

This is an isolated, testbench-only experiment, **not a production clock
change or 30 fps proof**. The existing ten-frame JPEG/tile/burst/LCD bench was
instrumented to record when the completed back buffer becomes `pending` and
when its actual LCD frame-boundary swap occurs. Both variants use the same
experimental guarded JPEG decoder, burst SDRAM path, ten distinct 720×480
synthetic JPEGs, one-slot hypothetical external compressed-frame queue,
instantaneous source arrivals at exactly 30 Hz and optimistic register upload.
There is no ESP32, Wi-Fi, QSPI, real RF, production bitstream or board test.

## What explains the nine-interval result

The current test models a 17.029 ns pixel-clock half-period, 541 pixels per
line and 834 lines per refresh. It produces **65.0755 Hz**, or 15.36677 ms per
LCD refresh. Thirty video frames per second cannot be presented at perfectly
uniform 33.333 ms intervals when swaps are restricted to those boundaries:
each image must be held for an integer number of LCD refreshes. In this
10-frame sample seven intervals are 30.73353 ms and two are 46.10030 ms. The
first-to-last rate is 29.28398 fps over nine intervals; the result alone does
not establish a long-run limit of 29.28 fps.

The third frame becomes pending at 10,775,746 memory cycles but swaps at
12,293,425: 15.17679 ms of LCD-boundary waiting. Its source-arrival-to-swap
age is 36.06722 ms. Over these ten frames, pending-to-swap waits span
0.90632–15.17679 ms. The reported presentation timestamps are not measured
input-to-photon latency and do not include frame capture or transport.

## Hypothetical ~60 Hz comparison

A second Verilator run changed **only the testbench** pixel clock half-period
to 18.470 ns (27.0709 MHz pixel clock, approximately 59.9984 Hz refresh).
All ten frames were presented; no modeled drops, queue overflows, or LCD
underruns were seen. Each of the nine observed presentation intervals was
33.33421–33.33422 ms, giving 29.99921 fps in this short window, and the maximum
modeled arrival-to-swap age was 29.80900 ms. The decoded pixel dumps for all
ten frames matched the current-clock dumps byte-for-byte; those baseline dumps
also matched the earlier shared-algorithm C model and XSim trace. Both cadence
variants in this folder are **Verilator-only**; no XSim cross-check was run on
the hypothetical clock.

This is evidence of a cadence/latency tradeoff in an ideal model, **not a
recommendation to change the board clock**. Panel-supported pixel clock and
refresh ranges, porch/sync constraints, MMCM legal settings, whole-design
constraints, physical SDRAM timing, image quality, thermals and hardware
behavior are unverified. A 60 Hz display is not exactly frequency-locked to a
30 Hz source merely by choosing a nominal clock: drift, missed deadlines and
frame loss still need study. Ten frames are insufficient for a sustained claim.

## 1,800-frame scheduling model

`replay.py` uses the measured ten per-frame upload and decode/staging service
times, a constant rational 30 Hz source and ideal periodic LCD swap boundaries,
repeating the ten timings over 1,800 frames. It models a hypothetical one-slot
compressed queue and reports queue-overflow instances, presentation rate and
frame age. For both clocks, the replay reproduces the 10 original observed
swap times within one 100 MHz cycle. Unit tests also check that a deliberately
slow workload produces queue overflow.

At the current modeled clock, this extrapolation reports 29.99509 fps over the
finite first-to-last window, no modeled queue overflows, and 37.554 ms maximum
modeled age. At the hypothetical clock it reports 29.99921 fps, no queue
overflows and 31.383 ms maximum age. **These are analytical estimates, not an
1,800-frame RTL run.** The model assumes that the same service durations repeat
unchanged even as display contention and phase vary, and that the source repeats
these ten simple synthetic images. It models no network, ESP32, memory size,
frame integrity, loss, decoding correctness or actual scanout pixels. It does
not extrapolate the pixel-correctness results. The close finite-window rates
do not prove the specified 30 fps criterion or long-term stability.

## Reproduce

With Verilator 5.x, a C++ compiler, `make`, `timeout`, Python and the pinned
host dependencies, from the repo root run:

```sh
fpga/experiments/throughput30/burst/cadence-study/run-verilator.sh
python3 fpga/experiments/throughput30/burst/cadence-study/test_replay.py
```

The runner creates a new build directory, validates/generates ten JPEG inputs,
runs both clock variants, verifies terminal markers, saves traces and model JSON,
and compares all ten decoded RGB565 dumps between variants. It can take
several minutes. The clock values and inputs are model assumptions. Actual
results: `verilator-65hz.log`, `verilator-60hz-hypothetical.log`,
`replay-65hz-1800.json` and `replay-60hz-1800.json`.
