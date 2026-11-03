# LCD capture-phase sensitivity candidate

This isolated copy of `../qspi-cadence-jitter` adds `CAPTURE_PHASE_CYCLES`:
extra modeled 100 MHz cycles after display warm-up and before the first
nominal capture. This varies the capture-to-LCD phase while the LCD clock keeps
running; it does not change the panel or implement a target FPGA clock. All
other stimulus, pixel checks, assumptions and limits are as in that experiment.

A phase-zero ten-frame smoke using hypothetical ~60 Hz and ±2 ms jitter passed
pixel/accounting checks and reproduced exactly the first ten presentation
cycles of the independent original ~60 Hz jitter run.

**The shifted-phase 300-frame run failed the strict ten-second capture window.**
All 300 distinct inputs were admitted and eventually displayed, with no busy
drops or modeled underruns; all 103,680,000 RGB565 pixels matched the related C
model, and 599 complete LCD scans passed. Only 299 frames appeared within the
ten seconds after first nominal capture; the last was 5.06446 ms late. Capture
age p50/p95/p99/max was 38.26589 / 38.38461 / 38.39516 / 38.39780 ms. Every
frame exceeded one 33.333 ms capture period. The maximum display gap remained
33.33422 ms: regular presentation and strict capture-window completion are
separate measurements. `CADENCE_ANALYSIS_PASS` means simulation accounting and
pixel comparisons completed; it is not the strict-window verdict.

This uses `CAPTURE_PHASE_CYCLES=833333` (8.33333 ms), hypothetical ~60 Hz and
the same ±2 ms arrival pattern and 300 synthetic input hashes as the unshifted
run. That comparison presented 300 within the window and had capture-age p95
30.05083 ms. The difference shows substantial phase sensitivity in this one
model and traffic pattern, not a physical panel or gameplay measurement. Full
logs, per-frame analysis and C-comparison records are in `results/phase-833333/`;
`results/comparison.json` contrasts the unshifted and shifted runs.

Use `build.sh` with an empty `BUILD_DIR` and `run.sh` with the same variables
and dependencies described in `../qspi-cadence-jitter/README.md`, plus e.g.
`CAPTURE_PHASE_CYCLES=833333 PCLK_HALF_PS=18470 JITTER_CYCLES=200000`. The
wrapper records the fixture-manifest SHA-256. `analyze.py` reports nominal
capture age, presentation gaps and window accounting. This is a hypothetical
one-phase behavioral test, not a physical timing or 60-second proof.

Before full validation, an independently C-checked checkpoint of the first 30 frames was retained in
`results/checkpoint-30/`: all 10,368,000 RGB565 pixels matched the related C
model, and full LCD scans passed. Their capture ages ranged 38.13486–38.16037 ms
and gaps 33.33421–33.33422 ms. This checkpoint establishes only that prefix;
it does not report completion or a ten-second-window verdict. The full model
run continued after the log snapshot and subsequently completed as above. For the checkpoint, C-model PPMs were
produced from the first 30 matching JPEG fixtures and compared to completed RTL
frame dumps using this directory's `compare.py`; the generated per-frame JSONs
and log snapshot were then checked using `checkpoint.py RUN CHECKS FIXTURES
OUTPUT`. The C oracle shares implementation with the RTL and is not an
independent decoder.
