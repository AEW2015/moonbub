# Hypothetical ~60 Hz LCD clock: ten-frame QSPI comparison

This separate experiment reruns the hash-pinned `../qspi-cadence10` synthetic
30 Hz workload using an otherwise identical testbench, except that the LCD
pixel-clock half-period changes from 17.029 ns to 18.470 ns. The modeled raster
remains 541×834 pixels; these clocks correspond mathematically to approximately
65.076 Hz and 59.998 Hz respectively. The wrapper verifies that the testbench
sources differ only by that one substitution, and pins the source, fixtures,
and original baseline log and pixel dumps.

Input arrivals are fixed at `epoch + floor(id * 10,000,000/3)` at an assumed
100 MHz. Busy admission is determined from the test-only ordered bank-free
status; the producer does not queue busy frames, and the consumer presents on
the next modeled display boundary without an extra verification delay. Each
admitted frame is checked against the C model and SDRAM before/after
presentation. Every complete active canvas scan is checked for ordering and
pixel identity. `compare-timing.py` reports admitted/presented and dropped IDs,
arrival-to-presentation cycles, and presentation rate as `(N−1)` divided by the
time from first to last presentation. Common frames' pixel hashes must match.
This interval rate is a small-sample statistic, not a sustained-throughput test.

Run `run.sh` with `BUILD_DIR` an empty scratch directory, `FIXTURE_DIR` set to
`/home/lori/gamebub-tools/network-rtl-repro-v1/fixtures`, and `BASELINE_DIR`
set to `/home/lori/gamebub-tools/bank-qspi-cadence10-v4`. Verilator 5.x, make,
a C++ compiler, Python 3, coreutils and GNU timeout are required.

The 60 Hz clock is hypothetical. No display-panel timing specification, clock
constraint, physical panel test, synthesis, FPGA timing/fit, real ESP32/QSPI
link or Wi-Fi stream is verified. The source frames are ten synthetic JPEGs,
not captured gameplay. Digital CDC and SDRAM models do not validate
metastability, electrical behavior or memory margins. Results are limited to
these ten inputs and their simulated admission/scan schedule.

Both clean runs admitted and presented all IDs 0–9 with zero busy drops. At the
original clock, arrival-to-presentation age ranged from 25.668 to 38.667 ms
and the first-to-last interval rate was 29.284 presentations/s. At hypothetical
~60 Hz, age ranged from 29.801 to 29.809 ms and the corresponding interval rate
was 29.999 presentations/s. All ten per-frame pixel dump hashes match between
runs, both runs match their C models, and the ~60 Hz run checked 19 complete
LCD canvas scans with no post-warmup modeled underruns. These observed age and
rate changes include phase alignment for this particular ten-frame schedule.
Short results are in `results/`; full scratch data are in
`/home/lori/gamebub-tools/bank-qspi-cadence10-lcd60-v1/`.
