# Ten-frame synthetic 30 Hz QSPI and dual-bank display study

The functional Verilator bench schedules ten distinct pinned synthetic 720×480
JPEGs at integer-cycle times `epoch + floor(id * 10,000,000 / 3)` using a
100 MHz model clock. Separate producer and consumer execute concurrently. The
producer reads a test-only, CDC-ordered bank-free status at each scheduled
arrival; if neither bank is free at the status read, it records that frame as a
busy drop. It does not hold a separate waiting frame. A late producer aborts the
run rather than silently sliding the schedule. The status is sampled shortly
after arrival, during a QSPI transaction, and is not a production register. It
reflects the controller's current FREE bank states. There is one sender, so no
other producer can steal the observed bank before begin.

An experimental QSPI endpoint, conservative 63-slot CDC credit FIFO and
test-only MMIO adapter carry metadata and payload; every write is credit
bounded, data counts are fenced, and CRC-checked commit is fenced before a frame
is considered admitted. The adapter supports only the stated test protocol and
does not implement production firmware or general failure recovery. The
consumer launches each admitted frame as soon as a bank and the single decoder
are available; presentation occurs on the next modeled display boundary, with
no additional artificial scan-completion delay. Each decoded frame is checked
pixel-for-pixel against the related C model and against functional SDRAM before
and after its presentation. The LCD scoreboard checks every completed active
canvas scan against an immutable per-frame array and catches frame changes,
ordering errors and incorrect pixels. The test drains admitted work after the
last arrival; `check.py` verifies IDs, scheduled times, input/drop partition,
unique presentation ordering, counts and each frame's C-model result.

The run uses synthetic byte ingress, no ESP32 or Wi-Fi, and functional models
of CDC and SDRAM. The selected fixtures are ten adjacent synthetic images, not
captured gameplay or a representative distribution. A ten-frame pass cannot
establish sustained 30 fps, physical timing, FPGA fit, signal margins, network
performance or production readiness. Simulated LCD canvas checks do not cover
physical sync/electrical behavior. All timing values are model cycles, with
milliseconds shown only by arithmetic conversion at the assumed 100 MHz.

Set `BUILD_DIR` to an empty scratch directory and `FIXTURE_DIR` to the pinned
`/home/lori/gamebub-tools/network-rtl-repro-v1/fixtures` directory, then run
`run.sh` with Verilator 5.x, make, C++ compiler, Python 3, coreutils and GNU
timeout. `sources.sha256` and `fixtures.sha256` are checked before compilation.
Fixture generator: `experiments/fixture30/generate.py`. The source bench uses a
48 KiB cap for each of two banks. Details of its test-only bus map and credit
fencing are in `../qspi-scanout-integration/README.md`.

The clean hash-checked run admitted and presented IDs 0–9 in order, with zero
busy drops, FIFO overflows, or post-warmup modeled LCD underruns; all ten
framebuffer/C-model comparisons and 21 complete canvas scans passed. Its
arrival-to-presentation range was 2,566,800–3,866,702 model cycles, or
25.668–38.667 ms at the assumed 100 MHz. Event logs and small comparison
results are in `results/`; the full clean run is
`/home/lori/gamebub-tools/bank-qspi-cadence10-v4/`.
