# Incremental packet-to-QSPI RTL replay: one frame

This isolated simulation replays the 26 ordered MSV1 packet arrival times for frame 0 from the synthetic clean 8 Mbps trace in `network-rtl-study`. `packet_trace.py` reconstructs each actual MSV1 datagram from the fixture, verifies its recorded SHA-256 and header, and requires Python reference reassembly and whole-frame CRC to succeed. The RTL bench makes each packet's offset/length available at its recorded arrival time, starts the FPGA transaction on SOF, sends each payload over simulated QSPI using the **experimental** credit endpoint and CDC FIFO, calculates a streaming CRC, and commits only after the final packet and CRC check. The core independently checks its receive length, CRC and JPEG markers. The decoder, burst-memory model and LCD then run through presentation.

The queue is limited to five packets and 5,320 bytes, including the 40-byte MSV1 headers and the packet in service; overflow stops the test rather than being silently ignored. In the bench, packet entries are **descriptors referencing a preloaded whole-fixture stimulus array**, not actual allocated packet payload buffers. Bytes are only sent after the relevant arrival event, but this test does not measure or prove an ESP32 memory allocation. The expected CRC is computed from the fixture before the simulation epoch to represent the value already carried in SOF; per-packet CPU/CRC processing consumes no modeled cycles.

## Result

The full `run.sh` wrapper completed with exit 0 in the development container. For the clean single frame:

- 26 packets and 26,159 payload bytes; peak modeled packet staging **1,064 bytes**, zero queue or CDC overflows.
- First packet arrival at cycle 2,143,537; first QSPI payload byte completed at cycle 2,144,533; final packet arrived at cycle 4,838,237. Thus data actually moved before EOF arrival.
- Commit at cycle 4,846,783 and modeled LCD publication at 7,683,395, with capture epoch 2,020,037. All values use the 100 MHz testbench clock.
- All **345,600** presented RGB565 pixels matched the related C JPEG model exactly; zero modeled LCD underruns and 434 experimental credit reads.

Relative to the neighboring full-frame-staging run of the same fixture and capture phase, this commit is 3.526 ms earlier. Publication remains at the **same display boundary**, so no end-to-end age improvement was observed in this one case. This is not a throughput or 30 fps proof. The reference C model shares JPEG algorithms and is not a fully independent implementation.

The wrapper also corrupts byte 1,000 during QSPI transmission. The bench detects its own end-of-frame CRC mismatch and stops before issuing commit; the negative run contains no pass marker. This is a testbench rejection, not a test of target firmware's CRC cost, hardware abort/recovery, packet retransmission or corruption detection by an independently operating receiver.

## Scope and reproduction

This is neither live network nor target code. There is no ESP32/Rust execution, scheduling, Wi-Fi MAC/PHY, packet loss/reordering, inter-frame busy policy, session change, control-flow error handling, or actual hardware. Its trace is synthetic and its queue backings are idealized. The decoder, clocking, SDRAM and experimental FIFO have the same functional-model limitations described in `../network-rtl-study/README.md`. In particular it uses the experimental `cdc-credit` endpoint, not production firmware's QSPI FIFO handling.

Run `../network-rtl-study/run.sh` first and retain its `BUILD_DIR`. Set `BASE_BUILD_DIR` to that completed build, `BUILD_DIR` to a new empty directory, and run `./run.sh`. It compiles the bench, checks timing and queue accounting, compares the framebuffer to the related C model, and runs the corruption and missing-packet controls. The Verilator invocations have 400-second wall timeouts; compilation and C comparison are outside these timeouts. The successful full wrapper output remains at `/home/lori/gamebub-tools/packet-stream-wrapper-v3` and its log at `/home/lori/gamebub-tools/packet-stream-wrapper-v3.log`. Small recorded traces, simulation output and comparison are in `results/`.

The wrapper also runs a missing-middle-packet control with packet index 5 suppressed while all other arrival timestamps and ordering stay intact. Five packets / 5,120 bytes reach the FPGA over QSPI before the next received offset reveals a gap (expected 5,120, observed 6,144). The testbench sends the abort register command before any commit and then watches two additional LCD frame boundaries. The core reports no completed, decoded or presented frame; front-valid remains false, and there are zero decoded pixels and framebuffer writes. The full wrapper including this control passed in `/home/lori/gamebub-tools/packet-stream-wrapper-v4`; the recorded `results/missing.log` has the event cycles.

This control uses an idealized synchronous testbench to recognize the gap and explicitly issue an abort. It does not execute the Rust receiver or test the real firmware's timeout/error policy, packet reordering or recovery to a later frame. It does not exercise loss of the last packet, an ambiguous/lost abort write, concurrent abort and vblank, or verify the front buffer when a prior valid frame is already displayed. The 400-second wall timeout bounds the simulation; a genuine target timeout still needs separate implementation and verification.
