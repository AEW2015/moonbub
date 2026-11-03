# Moonshine verification inventory

Final gate values and file hashes are in `evidence/manifest.json`. This document
records the scope of tests; it does not certify physical hardware operation.

## Executed offline checks

| Check | Evidence and scope |
|---|---|
| Host | 28 tests: packet framing, JPEG restrictions, loss/reordering/CRC recovery, frame freshness, pacing and mocked Windows keyboard release. `host/evidence/host-tests.log`. |
| Firmware protocol | Nine tests compile the production Rust receiver directly. `firmware/evidence/protocol-tests.log`. |
| Production Slint UI | Desktop real key events cover host editing, Connect, View/Home/Exit, Disconnect and Back. Persistent production ARGB1555 rendering clears every old opaque pixel in View; the complete button fits 360x240. Backend operations and diagnostic numbers are mocked. `firmware/evidence/ui-streaming-preview/result.json`. |
| Cross-language | 1,394 actual host-generated datagrams/mutations through the production Rust parser/state, including full JPEG chunking and MSF1 feedback. `evidence/integration/result.json`. |
| Full-resolution JPEG | 345,600 unique 720x480 pixels, malformed/truncated/CRC/overflow recovery, backpressure and deferred presentation. `fpga/sim/core.log`. |
| Software comparison | All 345,600 RGB565 pixels match the separately generated fixed-color C-model exactly. Unmodified upstream and independent Pillow comparison differences remain recorded. `host/evidence/decoder-comparison.json`. |
| QSPI and CDC | Actual pin parser and async bridge at simulated 40 MHz quad writes / 16 MHz reads, 1,024 FIFO bytes, metadata/checksum ordering, framework isolation, overlay byte swap, CS cancellation and reset recovery. `fpga/evidence/qspi-simulation.log`. |
| Transport overflow | 512 offers at 200 MHz into the registered bridge conserve 189 accepted plus 323 counted losses, with single-bit Gray transitions; mailbox/reset recovery and 128 normally paced words pass. `fpga/evidence/transport-overflow.log`. |
| Stock overlay | 768,125 checks over two complete panel frames: alpha, bounds, color, orientation, initialization, reset and release back to underlying video. `fpga/evidence/overlay-simulation.log`. |
| Native LCD | Independent clocks, 2,878 full-line requests, buffer swap, 345,600 pattern pixels, 1,382,400 image pixels; injected long stall caused four whole black lines and recovered. `fpga/evidence/lcd-simulation.log`. |
| SDRAM controller | Functional pin model checks initialization, BL8/CAS3/single-write mode, command timing, data and refresh. `fpga/evidence/sdram-simulation.log`. |
| Memory arbitration | 960 read words and 40 concurrent writes conserved; worst tested line 996 cycles against a 1,842-cycle budget. `fpga/evidence/memory-simulation.log`. |
| Decoder + SDRAM | Three real 16x16 decodes, two presented frames, 768 decoded/written pixels, 960 words read back through actual controller pins, malformed progressive/watchdog and transport-fault recovery. This integrated test is smaller than the separate 720x480 decoder test. `fpga/evidence/pipeline-simulation.log`. |
| Decoder backpressure + SDRAM | Three 64x64 decodes, 12,288 pixels/writes, two presented frames, 960 readback words; the JPEG Y queue reaches 414 entries, crossing its backpressure threshold. `fpga/evidence/pipeline64-simulation.log`. |

The SDRAM model is not a vendor timing model. Controller corner tests use 2 ns
and 7 ns data delay with 4 ns clock flight; board-level STA uses provisional
budgets. The native scanout test uses
a variable-latency memory transport rather than the SDRAM model. These unit tests
are separate from full board execution.

Firmware uses ESP193 and ESP-IDF 5.4.3. Its application UF2 is checked by the
production updater parser for every block, Rev4 identity, application partition
limits and a complete binary round trip. Consult the final release source binding
and build log for the delivered firmware revision.

## Findings resolved during integration

- Core registers belong at `0xE0000000`; framework windows remain separate.
- Free-byte credits now report the declared compressed length remaining.
- A prior FIFO overflow fault prevents COMMIT even if the accepted prefix has a
  valid length and CRC. A regression covers this case.
- Final timing constraints target only the first token synchronizer stage and
  bound Gray-bus delay/skew. The earlier broad-exception build was stopped during
  placement and retained as exploratory evidence.
- Streaming teardown acknowledges the stopped session before restoring the boot
  core. Late ABORT/FIFO/COMMIT operations check image identity under the device mutex.
- The native top includes the existing full-color ARGB1555 Slint overlay. The
  Game screen clears it to transparency when viewing video.
- Bridge overflow losses are exported through a Gray counter and a separate
  CSR; new losses invalidate unpublished frames while preserving scanout.

## Remaining gates and limitations

Physical LCD appearance, actual panel/board identity, Wi-Fi throughput, QSPI sink
throughput, concurrent receive/forward performance, frame age, real game footage
and sustained Game Bub FPS are unmeasured. No hardware was programmed. The PC
localhost observations in `host/evidence/loopback*.json` are separate results.

The prototype supplies a native-app subset of the framework, not HDMI/dock,
cartridge or CSC compatibility. SDRAM writes are single-word; scanout reads use
BL8. Compressed-RAM overflow and dropped transport bus words are separate counters.
The original 720x480 decoder simulation and the small integrated SDRAM test do
not establish sustained full-resolution decode-plus-scanout performance.

Sunshine pairing/app discovery and a negotiated JPEG extension remain subsequent
work. The standalone mode is labeled experimental and never advertises JPEG as
H.264. Audio capture/transmission are absent. Optional host keyboard injection
has mocked tests only; no desktop keys were injected during development.

The global GameBub native/firmware guidance and Vivado simulation/evidence skills
informed this implementation. Hybrid C helpers were unavailable; Vivado used
saved direct batch Tcl scripts. Firmware, FPGA and host had separate ownership;
a Luna agent supplied the initial bounded inventory. The coordinator retained
sole ownership of hardware access and performed no programming.
