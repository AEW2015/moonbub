# Narrow X/Y candidates in the ten-frame QSPI display model

This optional, separate experiment uses the unchanged source-hash-pinned bench
and fixtures from `../qspi-cadence10`, replacing the vendor JPEG X and Y IDCT
stages with the individually studied narrow candidates. Their module names are
changed only in copies created inside the scratch build. The wrapper checks
candidate, baseline source, fixture and original-run hashes, performs the same
ten-frame QSPI/CDC, framebuffer, C-model and LCD checks, and compares each
RGB565 dump hash and every recorded admission, decode, presentation and scan
event to the pinned original-X/Y run. `baseline.sha256` pins that run's log and
per-frame dumps.

Set `BUILD_DIR` to an empty scratch directory; set `FIXTURE_DIR` to
`/home/lori/gamebub-tools/network-rtl-repro-v1/fixtures` and `BASELINE_DIR` to
`/home/lori/gamebub-tools/bank-qspi-cadence10-v4`; run `run.sh`. It requires
Verilator 5.x, make, C++ compiler, Python 3, coreutils and GNU timeout. The
source candidates are `../../idct-dsp-study/narrow-x/jpeg_idct_x_narrow.v` and
`../../idct-dsp-study/narrow-y-coeff/jpeg_idct_y_coeff.v`.

The separate stage proofs are conditional two-state results at default
parameters after a synchronous reset edge; the composition audit requires
coupled unchanged initial RAM/FIFO state and a no-differing-X-write condition at
the first reset edge. The simulation does not establish that physical power-up
satisfies these assumptions or prove full-decoder equivalence. See
`../../idct-dsp-study/idct-composition-audit/README.md`. This ten-frame synthetic
model uses a test-only QSPI bus adapter and no ESP32, RF or physical hardware;
it does not establish sustained 30 fps, physical timing, DSP usage or fit.

The clean run passed all ten C-model comparisons and 21 scan checks, with
identical per-frame RGB565 hashes and recorded event/presentation cycles to
the pinned original baseline. Both runs admitted and presented IDs 0–9 without
modeled busy drops or post-warmup underruns. Short evidence is in `results/`;
the complete run is `/home/lori/gamebub-tools/bank-qspi-cadence10-narrow-v1/`.
