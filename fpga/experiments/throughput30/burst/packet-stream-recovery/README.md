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

## Missing-final-packet timeout control

The current wrapper reruns the middle-packet loss case and separately suppresses frame 0's final MSV1 packet while preserving every original packet timestamp. In this second case, the testbench models a **2 ms inactivity timeout from completion of the most recently forwarded payload**; it polls this timer while the packet queue is empty. This is a hypothetical test policy and timing choice, not the production receiver's timeout or target execution. It issues an explicit QSPI abort on timeout, without sending commit, and waits for the original trace's next valid frame.

The missing-final case forwarded 25 frame-0 packets (25,600 bytes). At 100 MHz, the last payload completed at cycle 7,376,963, timeout triggered exactly 200,000 cycles later at 7,576,963, and the abort command completed at 7,577,043. A separately preloaded prior front remained valid and its memory matched the saved image at abort; no additional frame completed, decoded or wrote pixels. Frame 1 then forwarded all 26 packets, committed and presented successfully. Both the prior and recovery images matched all 345,600 pixels against the related C model. Peak descriptor-queue occupancy remained 1,064 bytes. All 52 source arrivals, their enqueue/omission actions, forwards and abort/recovery events are in `results-final/run.log`.

The full two-mode `run.sh` wrapper passed in the development container (exit 0), with a 400-second limit on each RTL run; output is at `/home/lori/gamebub-tools/packet-stream-recovery-wrapper-v3` and its log at `/home/lori/gamebub-tools/packet-stream-recovery-wrapper-v3.log`. This adds no test of actual firmware timer scheduling, delivery failure of the abort, timer race with a late packet, packet buffering on a real ESP32, or physical display behavior. The prior original-core abort/vblank warning and all other limitations above still apply.
