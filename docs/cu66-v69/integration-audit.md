# CU66 connected-pipeline testbench audit

Independent read-only review of `fpga/experiments/cu66-v69/integration/tb_pipeline.cpp` and `scripts/cu66-v69/run_pipeline_regression.py`, 2026-11-05. RTL and testbench sources were frozen during this review. The captured 8-frame write-ack smoke is useful for fault-path review, but is not the full corpus qualification.

## Sampling and source path

The harness captures each ready/valid transfer and its payload after driving inputs with `clk=0` and evaluating combinational logic, then raises the clock and advances the software memory model from the captured transfer event. Read response bytes and reference tile values are driven before that sampling edge; write completion is held as a testbench input until sampled. This ordering matches synchronous ready/valid sampling for the modeled interfaces.

Each corpus `.cu66` is first accepted by the frozen native `cu66::Decoder::receive`, with decoder history reset at each source-chain boundary. Its resulting frame is the pixel oracle. The harness manually extracts qmap and three AB38 plane slices from that already accepted packet, feeds the base-layer RTL, and compares every returned Y/Cb/Cr pixel, tile identity/order/last, canonical tag, and SHA digest. P-frame reference pixels come from the corresponding previously decoded native `Frame`, not from an actual RTL reference-bank readback; prior RTL output is checked pixel-for-pixel against that oracle. Thus this verifies the datapath against causal golden references, not physical bank retention or SDRAM semantics.

The manual packet parser uses fixed CU66 offsets and bounds-checked `Bytes::at` reads for scalar fields. Native acceptance supplies the independent top-level validity check. Corpus completeness must still be checked from the terminal frame count and command arguments; the runner's general PASS parser permits a requested per-chain prefix.

## Latency and modeled memory

Per-frame `clocks` begin after the frame-start handshake and end after accepted tag output. They include the RTL pipeline and the selected software memory-service schedule. They exclude native packet parsing, native oracle decode, packet qualification/HUD work, real controller activity, ESP32 transport and physical scanout. They are simulated cycles, not device-clock measurements or FPS evidence.

In shared mode, the harness models one 16-bit bus beat per available cycle, round-robin among three outstanding transaction classes: one compressed byte (one beat), one 64-byte reference tile (32 beats), and one accepted 64-byte writer transaction (32 beats). It reserves alternate cycles for display and 16 cycles per 7,800 for refresh, then drops 10% of otherwise available bus opportunities for deterministic-seed contention. The qmap port is modeled separately as a one-cycle response with randomized request-ready; it is **not charged to the shared bus**. This is an explicit local-qmap-port assumption, not a complete SDRAM schedule. The display reservations are modeled occupancy, not simulated pixels or controller commands.

Writer queue acceptance (`tile_ready`) and transaction completion (`write_done`) are separate. The model holds the write lease until completion, can inject a completion error, and makes the final tag wait for all accepted writes. Abort cases drain accepted compressed, reference, and writer transactions before the model allows a new frame. The per-frame `writes` log field counts accepted writer requests, while the latency covers subsequent completion; do not interpret that field as completed physical writes.

## Audit gate for full-corpus claims

The runner's PASS regex validates an explicit terminal marker and seed, and checks all recorded mode-0 rows have 8,100 tiles. For any claim of a complete shared-schedule replay, independently confirm all of the following in `results-shared.json` and its exact retained command/log:

- argv includes `--shared-bus` and per-chain limit `9999`;
- terminal marker reports `shared_bus=1` and `actual_frames=457`;
- 457 actual mode-0 frames each report 8,100 tiles, followed by the separate recovery case;
- all five fault modes and all three seeded abort/drain modes are present and the exact expected errors/recovery pass;
- source hashes before and after match the current testbench, RTL, native index, headers and fixture files.

The runner accepts `--per-chain` truncation and parses but does not compare the terminal `shared_bus` field to the CLI flag. Therefore the word `PASS` by itself is not evidence of the full 457-frame shared-bus gate; check argv and terminal fields independently.

The completed shared run was audited against that checklist: [`results-shared.json`](../../fpga/experiments/cu66-v69/integration/results-shared.json) records seed 6901, argv ending `6901 9999 --shared-bus`, exit 0, `shared_bus=1`, and 457 actual frames. Its log has 466 `FRAME_PASS` lines: 458 mode-0 lines (457 corpus frames plus recovery), one each for five fault modes and three abort modes. All 457 corpus rows have 8,100 tiles. Fault modes report decimal errors 18/49/51/80/97 (0x12 CRC, 0x31 qmap, 0x33 reference identity, 0x50 output tag, 0x61 write completion); the three abort modes complete with no error and recovery succeeds. The shared terminal totals are 746,775,268 simulated cycles across the run, 237,366,596 modeled bus beats, 372,621,696 display-reserved cycles and 1,531,848 refresh-reserved cycles. Per-valid-frame clocks range from 1,185,675 to 2,708,663, with mean 1,627,146.52. The runner recorded 475 input source hashes; each currently matches the on-disk source/fixture, and the runner's pre/post stability assertion passed.

The independent ideal-service run `seed0.log` also ends with `actual_frames=457`, five faults, recovery, seed 0 and `shared_bus=0`; its log has 463 rows (457 corpus frames, five faults and recovery). That run has no shared-bus schedule and must not be blended with the shared results.

Even after those gates pass, the scope remains connected behavioral RTL plus a synthetic memory/arbitration schedule. It does not prove SDRAM command timing, QSPI/ESP32 limits, CDC correctness, HUD RTL, atomic display/reference-bank publication, Vivado target fit/routed timing, or physical frame rate.
