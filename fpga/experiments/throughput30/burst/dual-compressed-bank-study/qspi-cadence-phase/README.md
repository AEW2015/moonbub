# LCD capture-phase sensitivity candidate

This isolated copy of `../qspi-cadence-jitter` adds `CAPTURE_PHASE_CYCLES`:
extra modeled 100 MHz cycles after display warm-up and before the first
nominal capture. This varies the capture-to-LCD phase while the LCD clock keeps
running; it does not change the panel or implement a target FPGA clock. All
other stimulus, pixel checks, assumptions and limits are as in that experiment.

A phase-zero ten-frame smoke using hypothetical ~60 Hz and ±2 ms jitter passed
pixel/accounting checks and reproduced exactly the first ten presentation
cycles of the independent original ~60 Hz jitter run. A 300-frame run with
`CAPTURE_PHASE_CYCLES=833333` (8.33333 ms) is in progress; no full-run result
is claimed until the simulation and all C pixel checks finish.

Use `build.sh` with an empty `BUILD_DIR` and `run.sh` with the same variables
and dependencies described in `../qspi-cadence-jitter/README.md`, plus e.g.
`CAPTURE_PHASE_CYCLES=833333 PCLK_HALF_PS=18470 JITTER_CYCLES=200000`. The
wrapper records the fixture-manifest SHA-256. `analyze.py` reports nominal
capture age, presentation gaps and window accounting. This is a hypothetical
one-phase behavioral test, not a physical timing or 60-second proof.

An independently C-checked checkpoint of the first 30 frames is retained in
`results/checkpoint-30/`: all 10,368,000 RGB565 pixels matched the related C
model, and full LCD scans passed. Their capture ages ranged 38.13486–38.16037 ms
and gaps 33.33421–33.33422 ms. This checkpoint establishes only that prefix;
it does not report completion or a ten-second-window verdict. The full model
run continued after the log snapshot. For the checkpoint, C-model PPMs were
produced from the first 30 matching JPEG fixtures and compared to completed RTL
frame dumps using this directory's `compare.py`; the generated per-frame JSONs
and log snapshot were then checked using `checkpoint.py RUN CHECKS FIXTURES
OUTPUT`. The C oracle shares implementation with the RTL and is not an
independent decoder.
