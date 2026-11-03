# Incremental packet abort and recovery with a prior front

This isolated Verilator bench tests one narrow three-frame sequence:

1. Preload and display fixture 2 as a prior valid front. This initial image is a whole-fixture QSPI preload, not trace-timed network traffic.
2. Start a fresh simulated session at a new epoch. Replay synthetic MSV1 frame 0 at its actual stored packet-arrival times, deliberately suppressing packet at offset 5,120. Five packets / 5,120 payload bytes have been forwarded over QSPI before the next packet reveals a 6,144 offset. The testbench issues abort **before commit** and verifies the prior front remains intact.
3. Replay the valid MSV1 frame 1 at its original timestamps relative to that same epoch, forward it incrementally and CRC-gate commit, and verify it is presented. Check the old framebuffer has not changed and compare both the preload and recovery outputs against the related C JPEG model.

`packet_trace.py` regenerates and SHA-256 checks all 52 actual MSV1 datagrams against the clean synthetic trace; it also reassembles both undamaged frames and checks their CRCs before the bench injects the loss. All 52 original arrivals, including the one intentionally omitted and those discarded after abort, are retained in `results/run.log`; the checker verifies their IDs, offsets, lengths and arrival cycles against `results/trace.txt`. The first valid SOF follows the abort in this specific no-loss, in-order trace. The consumer drops remaining packets from the aborted frame, accepts the next SOF only if the core is ready, and aborts the test on queue overflow, busy SOF or any unexpected offset. This is a hypothesized testbench policy, not the firmware's actual receive loop.

The complete wrapper ran in the dev container and passed (exit 0):

- Prior fixture 2 presented at cycle 4,610,042; that cycle is the new packet-trace epoch. Frame 0 abort occurs at cycle 5,398,123 with prior front intact; frame 1 commits at 10,777,616 and presents by cycle 13,830,101. Clock is 100 MHz.
- Of 52 original arrivals, 31 packets were forwarded: the first five of interrupted frame 0 and all 26 of valid frame 1. There was one abort, one recovery commit and two total presentations including the preload. Maximum modeled packet staging was **1,064 bytes** of a five-slot, 5,320-byte limit, counting headers and the in-service packet.
- Both displayed frames matched the related C model in all **345,600 RGB565 pixels**. Checks before recovery and after its presentation show that the prior framebuffer's stored contents remained unchanged. The interrupted frame produced no additional complete or decoded frame, framebuffer writes or display output before recovery began.

The QSPI endpoint and CDC FIFO, burst memory controller and SDRAM are experimental functional models. Packet entries reference preloaded whole-fixture stimulus arrays, with payload availability controlled by the arrival trace; target packet-buffer allocation is not modeled. The expected CRC is computed before the epoch to represent metadata available in each SOF, and host/CPU CRC and scheduling cost zero simulated time. The related C decoder shares code with the RTL design and is not an independent oracle. No real Wi-Fi, UDP stack, Rust Receiver, ESP32, DMA or physical FPGA executes here.

## Original versus candidate RTL

This narrow abort happens during incomplete receive, before JPEG commit or decode; the bench uses the **original** `fpga/rtl/moonshine_core.sv`, so no candidate core was needed. It does not claim the original is generally abort-safe. A separate `../abort-study/` control demonstrates that an original-core abort coincident with pending-frame vblank can still publish the aborted frame; its test-only abort-priority candidate fixes that directed case under its documented assumptions. Neither this replay nor that candidate establishes acknowledged abort/quiesce, CDC ordering, or all abort/vblank interactions.

Not covered here: missing EOF and timeout, packet reordering, queue exhaustion or backpressure recovery, a missing/ambiguous abort write, abort during decoding or pending presentation, simultaneous abort/vblank, session authorization, a physically displayed panel or long-running 30 fps. The trace and staged buffers cannot prove ESP32 memory use or real-time performance. Real integration needs bounded receiver/queue behavior and verified hardware ownership and acknowledgment.

## Reproduce

First run `../network-rtl-study/run.sh` and retain its build directory. Set `BASE_BUILD_DIR` to that completed directory and `BUILD_DIR` to a new empty directory, then run `./run.sh`. It regenerates the two-frame packet trace, compiles Verilator, runs the RTL under a 400-second timeout, verifies every event, and compares both output frames exactly with the related C model. Compilation and model comparison are outside the timeout. The successful complete output is outside the repo at `/home/lori/gamebub-tools/packet-stream-recovery-wrapper-v2`; the wrapper log is `/home/lori/gamebub-tools/packet-stream-recovery-wrapper-v2.log`.
