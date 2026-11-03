# Long-run FPGA-side QSPI and display simulation

This is an isolated Verilator experiment, not target firmware or hardware.
It extends the 64-bit 1,800-frame long-run test by replacing its optimistic
register writer with the actual QSPI pin parser and asynchronous FIFO RTL.
The simulated source uploads each generated JPEG over a 40 MHz quad-write
interface in up-to-1,024-byte chunks, checking the real `0x0c` remaining-byte
register at 16 MHz before each chunk and actual receive count before COMMIT.
The core monitors the bridge's synchronized overflow counter. It uses the
experimental EOI parser guard, tile transpose, burst controller and functional
SDRAM model while LCD scanout runs. Every frame's decoded pixels and SDRAM
contents are checked, each actual presentation ID is recorded, and a streaming
checker compares the dump with the related fixed-color C decoder before
recording its hashes and deleting only its own verified temporary images.

The input model remains very optimistic: a complete JPEG is instantly
available in a hypothetical one-frame queue at each rational 30 Hz capture;
there is no host capture/encode, network serialization, packet loss, actual
ESP32 firmware, DMA/CPU scheduling or measured memory headroom. QSPI pins are
ideal digital signals, the SDRAM model is functional and the design has not
been implemented on the target FPGA. The parser guard and burst controller are
research candidates. The C decoder shares algorithms with the RTL and is not
an independent reference. This cannot establish real hardware FPS, Wi-Fi
capacity, physical timing, security, latency or subjective quality.

The 64-bit bench defaults to 1,800 frames and a strict aggregate 60-second
simulation window; individual per-frame arrival-to-display ages are recorded,
but not all required to be under 33.333 ms. No PASS is claimed while a run is
in progress or if it times out. Simulating 60 seconds may require several hours
of wall time and is bounded by both a 90-second simulated watchdog and a
configurable wall timeout. The verifier retires only generated images it has
already checked and recorded. Record memory pressure and free space when
running; do not start the experiment in a constrained environment.

Validation so far:

- The actual wrapper passed a 3-frame run with `STRICT_WINDOW=0`, with exact
  C-model pixel comparisons and correct ordered presentations. This short run
  is not a 30 fps result (`smoke-3-summary.json`).
- A separate 3-frame run started near 2^32 simulated core cycles; all outputs
  matched the zero-origin hashes and the normalized arrival/presentation
  timestamps matched exactly (`wrap-3-verilator.log`). This is a targeted
  arithmetic check, not formal proof for every wrap/reset.
- As a negative control, those same three frames with `STRICT_WINDOW=1`
  failed the aggregate 3-frame deadline (`strict-3-expected-failure.log`).
  This verifies that a missed deadline is not silently reported as PASS.
- The separately bounded 1,800-frame run subsequently **failed** its strict
  window; its complete records and terminal assertion are documented below.

Reproduce with Verilator 5.x, a C++ compiler, make, GNU timeout and Python /
Pillow in a new writable build directory:

```sh
BUILD_DIR=/tmp/moonbub-qspi-60s TIMEOUT_SECONDS=18000 \
  fpga/experiments/throughput30/burst/qspi-longrun/run-sixty-seconds.sh
```

Use `FRAMES=3 STRICT_WINDOW=0` for the small smoke test. Generated binaries,
fixtures and verified-hash records remain in the named build directory. The
full test's successful result would be conditional on the model assumptions
above and must not be presented as a deployed end-to-end demonstration.

## Recorded 1,800-frame result

The bounded run finished with **FAIL**, not PASS: all 1,800 frames eventually
presented and passed the related C-model comparisons, but frame 1,800 missed
the strict source-aligned 60-second window by 2.38483 ms. Detailed timing,
complete log, hashes, provenance and model limitations are in
[results-1800-strict-failed](results-1800-strict-failed/README.md). This is
behavioral FPGA/QSPI simulation with an abstract queue, not an ESP32/Wi-Fi or
physical hardware test.
