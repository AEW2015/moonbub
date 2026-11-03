# Connected X-to-transpose acceptance stress

This is a finite directed simulation of the unchanged connected `jpeg_idct`, not a bounded formal or inductive proof. Eight runs each send 256 blocks (2,048 blocks, 131,072 X beats total); every observed beat was accepted. See `results/` for complete counters, source hashes and tool version. Each run resets for four cycles and pulses `img_start`, with valid and EOB low during reset/start; the monitor excludes those five cycles. It checks `dut.idct_x_valid_w && !dut.idct_x_accept_w` at every rising edge outside reset/start and stops on the first rejection.

Input assumptions: 256 complete blocks, each having 1–8 distinct ascending coefficient indices 0, 8, ... 56, with deterministic data and 0–3 cycle gaps. Each beat and a separate EOB is presented only when input accept is observed; valid/EOB are then deasserted. The ID increments per block. This is an IDCT-interface workload, not a bitstream decoded by the actual JPEG front end: no claim is made that every generated pattern is reachable from it. The test waits for all 16,384 expected X beats after injection and enforces a simulation timeout.

Output accept is held high in mode 0 and driven by a deterministic pseudo-random signal with both high and low cycles in mode 1. It is an unconstrained synthetic approximation of downstream backpressure, not a model or proof of parent `jpeg_output` behavior. Seeds alter gaps and readiness, although mode 0's readiness is constant. The real parent ties transpose output ready high, as in the instantiated IDCT; only parent-level IDCT output accept varies here. Two-state Verilator execution and these finite vectors cannot establish arbitrary-state, timing, malformed-stream, or reset-interruption behavior. No reject was observed; no counterexample to a property was found or ruled out formally.

Reproduce from this directory using fresh output path:

```sh
FPGA_DIR=/path/to/moonbub-30fps-study/fpga BUILD_DIR=/tmp/idct-accept-new ./run.sh
```

The retained run used Ubuntu 24.04's Verilator 5.020 with `--timing --assert -Wno-fatal`. Input and original IDCT source hashes are recorded. For an exhaustive result a future formal harness needs actual JPEG front-end assumptions, reset/start sequencing and downstream ready constraints, plus proof across an unbounded number of blocks; the finite test does not supply those obligations.
