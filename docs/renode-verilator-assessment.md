# Renode and Verilator assessment

## Verilator evidence

On 2026-11-02, Verilator 5.020 with `--timing --assert` compiled the actual
8×8 tile-transpose prototype and self-checking testbenches in this branch. The
short test passed 128 pixels with input/output aborts, output backpressure and
invalid-address handling. The full trace test passed 5,400 blocks and all
345,600 pixels, including backpressure. The logs are in
`fpga/experiments/throughput30/*-verilator.log`. These confirm function for
the test vectors and are not a complete decoder or FPS test. No timing closure,
board behavior, analog SDRAM timing, actual FPS or ESP32 performance is implied.

The memory/LCD bench compiled under Verilator but timed out after 300 seconds
of wall-clock time without a result or PASS marker. Its outcome is inconclusive
and does not independently confirm or refute the previous passing XSim run. The test uses a
functional SDRAM model and a fixed front framebuffer; the decoder, QSPI and
ESP32 are not included. Verilator warnings include width truncation and an
incomplete case in the model; `-Wno-fatal` permits the experiment, but those
warnings should be reviewed for a production verification flow. Verilator is
primarily two-state: X/Z and contention differences need separate verification.

To compile and run all three benches, install Verilator 5.x, a C++ compiler,
make and GNU timeout, then run `fpga/experiments/throughput30/run-verilator.sh`.
The memory bench has a 300-second wall-clock timeout. No PASS is inferred from
compilation, an empty log, timeout or simulator exit alone.

## Renode gap

[Renode supports Verilator co-simulation](https://renode.readthedocs.io/en/latest/advanced/co-simulating-with-an-hdl-simulator.html),
but this is not by itself a Game Bub platform model. An upstream platform
inventory at renode/renode commit `96e96239597d14898ce26d2126daab48b74491a4`
contained a generic Xtensa sample controller, not an ESP32-S3 CPU platform file.
No Renode+Verilator Game Bub co-simulation or ESP32 firmware boot was run in
this investigation. ESP32-S3 CPU/interrupt/clock/memory models and working
firmware boot, a faithful Wi-Fi ingress and QSPI/DMA/credit interface, a
cycle-accurate bridge to the FPGA, and calibrated external memory/display
models are still needed. Even with functional models, RF rate and device timing
require hardware measurements; simulation can prove behavior only under its
stated assumptions.

## Proof target

Run multiple representative decoded game frames through the actual receiver
and decoder, model clock crossings, capture a new framebuffer ID at each
presentation, and check at least 30 unique complete frames per simulated second
with no overflows or scanout underruns. Include realistic frame sizes, resource
contention, service variability, losses, bounded queueing and recovery; record
frame age as well as cadence. Then corroborate on the real device. The current
RTL includes single-pixel SDRAM writes; the previously measured XSim workload
exceeded the 33.33 ms budget even with its experimental tile reorder. A new
burst-write path is a candidate, not a tested implementation.

## Follow-up: memory/LCD Verilator timeout resolved

The original Verilator run above timed out; profiling identified excessive
reevaluation around the testbench and behavioral model's delayed continuous
clock assignments. A verification-only model changes these two simulated clock
delays to edge-triggered delayed nonblocking assignments. Production RTL and
hardware clocks are unchanged. The full 345,600-pixel Verilator test then
completed with 8,875,956 cycles for original order and 5,310,461 cycles for
the transpose candidate; both exactly match the earlier XSim results for this
trace and report zero observed scanout underruns. The test still has a fixed
front buffer and excludes decoder, ingress and frame swaps. This agreement is
not formal equivalence, SDRAM electrical timing or a 30 fps demonstration.
The detailed progress log and updated reproduction runner are in
`fpga/experiments/throughput30/`.
