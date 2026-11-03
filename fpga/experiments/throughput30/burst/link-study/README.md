# Finite-rate payload link experiment

The prior ten-frame test delivered a complete compressed JPEG instantaneously
at each 30 Hz capture. This modified testbench instead serializes its exact JPEG
byte count through a hypothetical constant-rate, lossless payload link before
placing it into the same abstract one-frame external queue. Each frame is
captured on the original 30 Hz schedule; capture-to-presentation age includes
serialization, queue wait, the optimistic FPGA register upload, JPEG decode and
LCD-boundary wait. It uses the experimental SOF guard, tile orderer and burst
controller, with functional SDRAM and real LCD RTL. For this model, a capture
arriving before the prior JPEG completes on the serial link, or an arrival to
an occupied queue, fails explicitly. The model neither implements a sender
queue nor simulates losses; it assumes the link starts exactly at capture.

At a hypothetical constant 8,000,000 **payload bits/s**, all ten frames
presented in the Verilator experiment, without modeled drops, external queue
overflow or LCD underruns. First and last presentation were 7,683,395 and
36,880,249 100 MHz cycles, respectively: 9 intervals over 291.96854 ms, or
30.825 fps **over this short window**. Maximum modeled capture-to-presentation
age was 6,160,114 cycles (61.60114 ms). All ten decoder output dumps are
byte-identical to the previously C-model-checked guarded run; hashes are in
`link8-hashes.json`. These are synthetic fixtures, not gameplay.

The rate is an **assumption**, not measured Wi-Fi/QSPI throughput. There is no
packet/header/FEC/audio overhead, CPU CRC time, packet loss, jitter, real
ESP32 receiver, QSPI serialization or timing calibration. The register bus
is also optimistic at one byte per two 100 MHz cycles. No hard bound or
sustained 30 fps is established. A short-window 30.825 fps depends on display
phase and sampling; use much longer runs and measured service traces. This is
functional behavioral RTL, not implemented production hardware or timing
closure. Encoder capture timing and network frame-completion timing are
simplified to a single serialized payload per frame.

To reproduce, install Verilator 5.x, make, C++, GNU timeout and Python/Pillow:

```sh
RATE_BPS=8000000 ./fpga/experiments/throughput30/burst/link-study/run-verilator.sh
```

The script generates ten deterministic fixtures in a new build directory,
compiles the RTL, bounds the simulation, requires a terminal PASS marker, and
compares each frame against the related C decoder. Set `BUILD_DIR` to an empty
path to retain artifacts. The unrelated JPEG parser marker fixes and queue are
research only; do not deploy the simulated design as a result of this test.

As a negative control, a 4,000,000 payload bits/s run fails explicitly at the
second capture because the first 26,159-byte JPEG is still being serialized.
That is expected for this model with no sender queue. These frame sizes average
above 4 Mb/s at 30 Hz, so adding a queue cannot make that fixed-rate link keep
up indefinitely; the actual quality/rate choice and device throughput remain
to be measured. `link4-expected-failure.log` preserves the diagnostic. The
experiment intentionally exits nonzero for this condition.

In the `FRAME_RESULT` rows, `queue_wait_cycles` is inherited from the earlier
testbench: here it means **capture-to-core-service time**, including payload
serialization and any queue wait. It must not be interpreted as queue-only
latency. `LINK_RESULT` records serialization completion separately.
