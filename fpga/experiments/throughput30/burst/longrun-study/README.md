# Longer full-resolution RTL experiment

This is an isolated extension of the prior ten-frame test. It uses 60 distinct
synthetic 720×480 q65 JPEGs generated at rational 30 Hz and presents them via
the actual experimental JPEG core, tile transpose, burst SDRAM controller and
LCD RTL. It uses the broader experimental marker candidate under `marker-audit`.
The one-frame compressed-input queue and immediate complete JPEG availability
remain abstract; the core register upload remains one byte per two 100 MHz
cycles. The SDRAM model is functional rather than a vendor timing model. This is
not ESP32, Wi-Fi, QSPI, gameplay, physical SDRAM, Artix-7 timing closure or a
production bitstream, and 60 frames are about two simulated seconds, not the
60 seconds required by the end-to-end success gate.

Each presented frame is checked for one occurrence of each decoder pixel,
correct address bounds, byte-exact SDRAM readback against decoder output, correct
frame ID, no modeled core drops/overflows or LCD underruns, and 43,200 bursts.
The reproduction script then decodes each JPEG with the related fixed-color C
model and requires exact RGB565 comparison. The C model shares algorithms and
RTL-matched color arithmetic; it is not an independently designed decoder.
Presentation FPS, intervals and age are reported for this finite window and
are sensitive to phase between the 30 Hz source and simulated LCD refresh.

Run with Verilator 5.x, make, a C++ compiler, Python/Pillow and GNU timeout:

```sh
BUILD_DIR=/tmp/longrun60 FRAMES=60 TIMEOUT_SECONDS=1800 \
  fpga/experiments/throughput30/burst/longrun-study/run-verilator.sh
python3 fpga/experiments/throughput30/burst/longrun-study/summarize.py \
  /tmp/longrun60/run.log --expected 60
```

The build directory must not already contain fixtures or dumps; binary files
are written only there. The simulation is bounded by both an 8 s simulated
watchdog and a configurable wall timeout. A failed frame or timeout is a
failure/inconclusive outcome, not a 30 fps PASS. The testbench caps `FRAMES` at
180 to keep its 32-bit cycle arithmetic and 8-second watchdog valid. It cannot
be used for the 1,800-frame acceptance gate without widening counters,
revisiting the watchdog and transport model, and scaling runtime and outputs.

## Recorded 60-frame result

Verilator 5.020 completed 60 frames: all 60 frame IDs presented in order,
20,736,000 pixel writes and memory checks, zero model-reported queue/core
overflows, drops or LCD underruns, and all 60 decoded RGB565 frames matched
the related fixed-color C model exactly. First-to-last cadence was 29.99574 fps
over 59 intervals; maximum modeled source-arrival-to-swap age was 36.06722 ms.
The simulation phase took about 406 s wall time; the run covers ~2 s of
synthetic input with the optimistic assumptions above. Logs, summary and
per-frame hashes are alongside this document. A 60-frame finite window is
not the 1,800-frame/60-second target or hardware validation.

## Bounded 1,800-frame / 60-second behavioral run

`tb_jpeg720_sixty_seconds.sv` widens simulation-cycle and schedule values to
64 bits, accepts up to 1,800 frames and sets a 90-second simulated watchdog.
A directed 1,800-step schedule test checks the producer expression beyond 2^32
cycles; a three-frame full RTL run with an artificial cycle origin crosses
2^32 and matches baseline timing after subtracting the origin. The three-frame
test sets `STRICT_WINDOW=0` because its third swap is later than the short
three-frame deadline; a separate negative test confirms `STRICT_WINDOW=1`
rejects that miss. These checks do not prove every long-run behavior.

`generate-jpegs.py` creates only the JPEGs and their manifest (not 1,800
RGB565 reference files). `stream-check.py` reads a completed frame only after
the testbench closes its dump and emits its frame result. It compares every
pixel against the separately executed related C model, records a JPEG hash,
RTL dump hash, frame counters and exact-match result in a flushed/fsynced
JSONL record, then deletes only the two generated and already-verified dump
and oracle files. A directed injected oracle failure stops the check, retains
the unverified dump and emits no summary. A short end-to-end wrapper run of
three frames passed with `STRICT_WINDOW=0`.

A run is started with:

```sh
BUILD_DIR=/tmp/moonbub-60s TIMEOUT_SECONDS=18000 \
  fpga/experiments/throughput30/burst/longrun-study/run-sixty-seconds.sh
```

Default `FRAMES=1800` and `STRICT_WINDOW=1` require all frames to be presented
by the end of the rational 60-second simulated capture window, with no modeled
queue overflow, core drops/overflows or underruns. The 5-hour timeout is wall
clock, not simulated time. It uses a new empty work directory and records
fixture and source hashes; generated images remain in that work directory while
verified large dumps are retired. Expect hours of CPU time. Any failure or
wall timeout is not a success; inspected data may be found in `checked/`.
A successful result would still apply only to this isolated behavioral design,
synthetic video, instantaneous JPEG availability and abstract external queue,
not a real ESP32, Wi-Fi, QSPI, physical memory or board timing.
