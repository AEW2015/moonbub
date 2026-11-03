# Experimental abort recovery at the JPEG-to-memory boundary

This is isolated behavioral research, **not production RTL or a hardware fix**. An explicit register abort is wired to the tile buffer and to the experimental collector in the testbench. The host then waits for memory idle before starting another frame. The original front buffer must stay unchanged; after draining, another complete frame must decode and be published correctly.

A 64 × 64 JPEG fixture drives the actual experimental JPEG core, tile transpose, BL8 burst controller, functional SDRAM model and LCD logic. The expected image is the first valid frame from the same decoder, rather than an independent JPEG reference. This is a directed corruption/recovery test, not an image-quality test.

Verilator 5.020 results:

| Case | Configuration | Result |
|---|---|---|
| Abort during partial tile | Original tile abort tied low | **Expected failure:** subsequent decode reports `RECOVERY_FAULT` |
| Abort during partial tile | Tile abort connected | Pass; old front preserved and frame 3 recovered |
| Abort with 1–2 collector words staged | Collector flush disabled | **Expected failure:** partial collector cannot drain (`ABORT_STAGING_NOT_DRAINED`) |
| Abort with 1–2 collector words staged | Candidate collector flush | Pass; old front preserved and frame 3 recovered |
| Abort with a complete BL8 staged while controller is not ready | Candidate collector flush | Pass under the test's selected cycle |
| Abort during an already-issued BL8 SDRAM write | Candidate collector flush | Pass; issued write drains, old front preserved and frame 3 recovered |

Run `run-verilator.sh` with Verilator and C++ build tools on PATH. Set `BUILD_DIR` to choose a writable output directory, and `JPEG_FILE` to override the fixture. The script verifies that each negative control fails with its **specific expected error**, and the candidate tests exit successfully. Tests are bounded by timeout and core dumps are disabled. Logs are retained in the build directory.

The candidate drops unissued partial or full collector data and blocks a new write on an abort cycle. Already-issued writes and active line reads continue. The tile buffer must also receive the abort. This is only safe under the test's deliberate idle-before-reuse assumption; it is not a verified automatic cleanup protocol.

Not covered: lost COMMIT response, source/QSPI ordering and stale commands, concurrent automatic decoder/protocol errors, reset and clock-domain races, repeated aborts, all possible timing interleavings, a full-resolution random regression, independent JPEG reconstruction, or physical SDRAM/FPGA timing. In particular, software quarantine alone cannot undo a frame already committed for presentation. A production design needs an acknowledged abort/quiesce and a separately verified frame ownership protocol before any integration.

The in-flight-burst candidate also passed Vivado 2025.2 XSim behavioral simulation via the Vivado MCP flow using a generic installed part, with no Vivado errors. XSim warned that `$fread` did not fill the entire oversized input array; the test verifies the actual JPEG length. XSim finished at 46.10042 ms of simulated time. This is another RTL simulator result, not target-device synthesis, place-and-route, physical SDRAM validation, or hardware proof.

A further directed Verilator test asserts a core abort on the exact clock edge on which a decoded frame would otherwise be published at vertical blank. The existing core publishes the pending frame despite the abort (`ABORT_VBLANK_PUBLISHED_ABORTED_FRAME`, frame 2). A separate test-only core copy gives the abort priority on that edge; it preserves the old front and later successfully publishes frame 3. `run-verilator.sh` includes both the expected-failing control and candidate. **An abort after a frame was already presented cannot undo that presentation**; a command may also be lost or reordered before reaching this logic. The candidate does not address those cases or establish a complete abort acknowledgment/ownership protocol.
The same candidate vblank test also passed Vivado 2025.2 XSim behavioral simulation on a generic installed part (same oversized-`$fread` warning); it is not target-device or physical timing validation.

`run-sweep.sh` independently repeated the candidate recovery test for each input-collection index 0–63 and each output-emission index 0–63 of the tile (128 selected cases). Every case passed the explicit abort, bounded memory-drain, prior-front integrity and next-frame recovery checks under Verilator 5.020; `sweep-summary.log` records the clean wrapper run. This deterministic sweep uses the same 64×64 JPEG, one set of clock phases and the test-only tile/collector abort wiring. It does not cover all clock interleavings, other fault sources, QSPI command loss, or remove the documented need for an acknowledged quiesce protocol.
