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

For long host runs, `resource-monitor.py --pid PID --output PATH` records
available RAM and memory PSI plus a secondary `(RAM total - RAM available +
swap used)/(RAM total + swap total)` indicator at 30-second intervals. This
is telemetry only; it does not set a policy, pause, or stop a build. The
recorded ratio uses Linux `MemAvailable` as an estimate and is not resident
working-set utilization. The PID's start time is checked to avoid monitoring a
new process after PID reuse.

The long-run scoreboard checks every decoder pixel against the related C model
and every corresponding back-buffer SDRAM location. It does **not** sample and
compare every RGB pixel actually emitted by the LCD output. The presentation
check observes the core's frame ID and the LCD's swap boundary, plus the modeled
underrun counter. Full scanout pixel checking remains a separate gap.

The strict 1,800-frame criterion checks that all frames finish within one
aggregate 60-second simulated window; it does **not** require each individual
frame to appear within 33.333 ms of its arrival. Per-frame ages are recorded
separately. For example, an audit of the first 209 verified frames found 43
arrival-to-presentation ages above 33.333 ms. This illustrates why throughput
and latency must be reported separately; the prefix is not a final result.
The fixture manifest was independently checked for 1,800 unique hashes, matching
file sizes and SHA-256 values; source content remains synthetic.

## Recorded 1,800-frame strict-window failure

The bounded 1,800-frame Verilator run completed 1,800 distinct generated
JPEGs, but **failed** its strict 60-second source-window assertion. All 1,800
frames were eventually presented in order with no modeled queue/core overflow,
drop or LCD underrun, and all 622,080,000 decoded RGB565 pixels matched the
related fixed-color C model. Only 1,799 frame IDs were presented within the
60-second capture window. The final frame was **2.38483 ms late** relative to
that fixed window. This result is a failure of the specified test, not a pass.

The first-to-last presentation rate was 29.995089 fps over 1,799 intervals;
the strict capture-window count was 1,799/60 = 29.98333 frames/s. Modeled
arrival-to-swap age p50/p95/p99/max was 28.78737/35.70993/36.31573/36.45743 ms
(nearest-rank). Of 1,800 frames, 370 exceeded a nominal 33.33333 ms frame-age
interval. One-second capture-aligned presentation counts were 29 in five
windows, 30 in 51, and 31 in four. Timing is specific to the chosen initial
phase of 30 Hz arrivals relative to the modeled ~65 Hz LCD refresh.

`sixtysec-strict-failure.log` records every frame and final fatal assertion;
`results-1800-failed/verified.jsonl` records JPEG and RTL dump hashes and
C-model verdicts per frame, and `sixtysec-analysis.json` summarizes the result.
All large raw frame dumps were removed **after** exact comparison and hash
recording; the generated JPEGs remain in the local run directory. The C model
shares upstream algorithms with the RTL. RTL-scanout output pixels were not
independently sampled. Results assume synthetic video, immediate complete JPEG
arrival, abstract one-slot external queue, optimistic two-cycle byte-register
bus, functional SDRAM and no real Wi-Fi/QSPI, CPU/network latency, actual
hardware timing or user input. They do not establish live or hardware FPS.

Shifting the sender's phase relative to LCD scanout is a valid separate
sensitivity experiment, but would change both the arrival/decode schedule and
its 60-second window. It cannot relabel this failed run or guarantee real
hardware behavior without a real synchronization mechanism and drift tests.

## Short source-to-display phase sensitivity experiment

A separate test waits an additional configurable number of 100 MHz cycles
between LCD warmup and the first 30 Hz source capture. It does not change the
simulated LCD pixel clock. Three 10-frame runs using the broader marker
candidate, abstract queue and optimistic register upload yielded:

| Startup phase shift | First-to-last fps (9 intervals) | Maximum modeled frame age | Margin before the 10-frame capture-window end |
| ---: | ---: | ---: | ---: |
| 0 ms | 29.284 | 36.067 ms | 0.098 ms |
| 2.5 ms | 29.284 | 36.167 ms | 2.598 ms |
| 7.68338 ms | 30.825 | 35.951 ms | 7.781 ms |

All 30 output frame dumps matched the earlier related-C-model-checked baseline
byte-for-byte. The earlier strict 1,800-frame result still **failed**; these are
only ten-frame phase-sensitivity experiments, not a prediction of a different
60-second run. The 10-frame first-to-last fps varies with the sample boundaries,
and the apparent margin does not imply a stable or low-latency physical system.
Actual sender/display phase control, clock drift, real QSPI, queue capacity,
latency, gameplay and the physical panel remain unmodeled.

From the repo root, reproduce with
`fpga/experiments/throughput30/burst/longrun-study/run-phase-sensitivity.sh`.
It runs the three phases and checks all 30 frames against the related C model.
The separate phase testbench and the per-phase output logs and hashes are in
this directory; no production clock or sender was changed.
