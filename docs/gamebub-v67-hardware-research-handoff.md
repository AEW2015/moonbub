# Gamebub application-specific streaming: research handoff v67

This handoff describes Python reference models and measured software evidence from the six-hour research run on 2026-11-05. It does not deploy a codec, change the ESP32 firmware, synthesize FPGA logic or prove physical 30 fps. The existing v20 hardware handoff remains a separate branch.

The immediate engineering objective is a reliable 720×480 coded canvas at 30 complete presentations per second, with exact HUD overlays, bounded buffers and recovery after a lost or rejected frame. The canvas is the model's chosen geometry, not verified Gamebub panel timing or a claim of 1280×720. Confirm the actual panel mode, memory parts and clocks before integration.

## What to carry forward

| Component | Python evidence | Implementation boundary |
|---|---|---|
| CS38 adaptive binary residual coding | 457 stored frames: 8,864,829 → 7,954,123 complete bytes, identical reference and displayed pixels | Define a negotiated backend; the current firmware/FPGA receive path supports JPEG, not CS38 |
| Direct receive parsing | 577 causal calls; removes redundant synthetic packets and entropy re-encoding, with identical outputs | Preserve validation and atomic reference publication; do not copy the proof adapter into production |
| Tile coefficient iterator | One coefficient tile and bounded entropy cursors, independently checked | Integrated v48 accepts arithmetic dispatches 5/6 only; legal legacy 0–4 need another path or explicit rejection. Compressed input and external banks remain |
| Symmetric inverse transform | Exact fixed-point output and rounding; about 49.9% fewer logical sparse products on the tested work | Map DSPs, check signed widths and synthesize; Python operation counts are not cycle counts |
| Display-only luma filter | Fixed before the later temporal window; custom MSE improves 2.56–2.87%, HUD exact | Filter scanout only. Never write filtered pixels back into the canonical prediction reference |
| Filtered YUV scanout | 33,177,600 exact luma samples and RGB565 words; four cached vertical rows, one pending row, two-row lookahead | 7,200 bytes of logical row/output data with one outstanding line; excludes full frames, HUD, static mask, metadata and temporaries |
| Verified reference binding | v66 evaluates cached reference tags and a single canonical output pass | Candidate profiles are explicitly configured, fixed to epoch 25/720×480; live negotiation remains to implement. Keep the hash domains separate |
| Tile-to-row hash input | v67 reproduces canonical tags from 8×8 tiles with one 5,760 B strip | Serialized-row temporaries, SHA context, ports and control are additional; no SHA RTL or timing result |

Keep these gains separate. They concern different components and cohorts and cannot be added into a system speedup or assumed to compound into 30 fps.

## Codec and host owner

Start with the causal zero-motion CS38 baseline. Keep its full/compact arithmetic choices and exact HUD binding. Preserve all stored packet fixtures and source hashes, then implement a bounded native sender and receiver against those fixtures. The Python sender's HUD stage became about four times faster in isolation; full Python encoding and decoding still exceed a 33.33 ms frame period in several experiments.

The 577 retained packets use arithmetic dispatches 5/6. The integrated v48 tile receiver rejects other legal CS38 dispatches 0–4; frozen v43 is the compatibility control for those cases. Either implement and test the remaining dispatches or advertise a restricted arithmetic capability. Do not present v48 as a drop-in receiver for every legal CS38 packet.

Do not enable the tested global-grid or mixed-motion policies as a quality-preserving default. The mixed policy saves around 1.3% of bytes in the later window but increases source SSE by about 4.5%. The exact 32-pixel-block and 16-pixel-cell motion substitutions found no selected rate benefit. Local RDO comparisons did not prevent future reference drift. A future inter-frame experiment should explicitly budget cumulative distortion over its own decoded history and include scene changes, fine text and fast camera motion.

HEVC and AV1 remain the compression references. The v63 comparison evaluates every one of 69 measured native points with both fixed display options. It charges complete codec/HUD/binding bytes, extra data once, the per-frame 49,152-byte cap and explicit mean, mean-plus-peak or every-frame quality gates. The displayed mean-gate winners use about 33–56% fewer bytes for HEVC and 38–66% fewer for AV1 than equally filtered custom zero motion. Those are sampled points, not an optimal encoder frontier. None of these native CPU decoders has been implemented on the Gamebub FPGA.

The application-specific advantage to pursue is bounded work and storage, exact HUD treatment, explicit recovery and an inexpensive FPGA decoder—not an unsupported claim of better compression than HEVC/AV1. Keep a JPEG backend for real hardware bring-up while implementing and negotiating any new backend.

## FPGA owner

1. Build an independently checked coefficient-stream → dequantization → symmetric inverse → predictor pipeline. Maintain the specified integer rounding boundaries. Test valid/ready stalls and reset during every stage; use the exact Python tile outputs as the oracle.
2. Read the canonical reference from external memory and write a separate reconstruction bank. Treat produced tiles as provisional until the entire frame, HUD, output binding and integrity checks pass. Publish a bank descriptor atomically; a rejected frame must not become a reference or scanout source.
   Prediction-reference and display-front leases are separate. If the panel still reads an older bank, two banks may require a stall or an additional bank. Do not overwrite an active reader to meet the frame-rate target.
3. Implement the display-only filter with the v64 row schedule. Its four-row cache, pending row and two-row lookahead are logical payload bounds. Count RAM port widths, simultaneous reads/writes, FIFOs, RGB conversion, mask/HUD storage, CDC and actual panel timing separately. Output lines must remain stable under backpressure.
   The separately verified v67 fixed-mask program replaces a hypothetical full boolean-mask input with four aligned rectangles (32 B packed constants) and an owned 720 B row mask. It matches all pixels and four-tap protection footprints for this exact HUD profile. It is not integrated into v64; regenerate and verify it for different geometry, and count descriptor/query/port logic separately.
4. Decide the reference content-binding profile before sizing a SHA engine. Legacy i16 serialization hashes 1,036,804 bytes for a 720×480 YUV420 frame, even when all canonical samples fit in eight bits. Repeated software proof passes can dominate an iterative hardware SHA engine. Do not silently replace the hash domain with packed eight-bit samples; negotiate and verify the new profile.
   The v67 hash reorder component uses one 8×720 uint8 strip to convert normalized tile-raster output into planar row order. It also creates a transient 1,440 B legacy or 720 B packed-u8 serialized row. Hash-strip and display-filter storage serve different frame banks/stages; count them independently unless a real schedule proves sharing. Hash completion does not bypass the full-frame/HUD publication fence.
   Drain each serialized row before overwriting its strip, or count additional/ping-pong buffering. V64's bound assumes one outstanding returned line; a queued consumer needs a separate bound. Honor a hash input error after finalization by aborting an unpublished controller transaction even though the completed digest API remains idempotent.
5. Synthesize for the actual fitted part and memory interfaces. Report resource use, routed clock, external-memory traffic and worst-case frame latency with entropy stalls, HUD work and hashes included. The v49 schedule deliberately excluded several of those costs; it is a component schedule, not a complete system model.

Reference banks, decoded YUV, compressed input, HUD and staging buffers remain external-memory models. The v48 traced Python allocation reduction and v64 row bounds do not prove BRAM, SRAM or total memory fit. The v52 memory budget assumes a shared 16-bit bus and a 60 Hz scanout scenario; efficiencies and clocks in its sweep are explicit assumptions.

## ESP32 owner

The v65 audit follows the actual Rust forwarder: 40-byte chunk header, 1,024-byte payload chunks, 1,065 requested DMA-buffer bytes, two identity reads and one credit read per forwarded chunk, lock acquisition and a write at a configured maximum of 40 MHz. The current backend accepts JPEG; CS38 needs explicit capability negotiation and FPGA support. Keep parser bounds and fail-closed backend selection.

Across 457 custom packets there are 7,988 fragments. The largest packet is 44,032 bytes / 43 fragments. At nominal 30 frames/s the mean IPv4/UDP data-only demand is about 4.46 Mbps, before Wi-Fi airtime, retransmissions and other traffic. A single maximum-size frame per period would demand about 11.27 Mbps by the same accounting. This does not demonstrate measured RF capacity.

The ideal 40 MHz QSPI command/address/payload phase for that largest packet is 2.2188 ms. With an assumed 10 ms reserve, its remaining average service allowance is approximately 491 microseconds per fragment. Unknown lock, MMIO, scheduling, DMA setup and transport costs must be measured; the inequalities are not an ESP32 instruction-set simulation. Reducing a hypothetical header from 40 to eight bytes saves roughly 3% of L3 traffic here and does not reduce payload QSPI time or fragment count.

Record timestamp distributions at receive, checksum, lock acquisition, credit check, DMA submit/complete and FPGA acknowledgement. Include Wi-Fi and UI allocations, socket buffers, stack high-water marks and allocator headroom. Separate per-session setup/programming scratch from concurrent steady-state allocation. Never use the single DMA-buffer size as proof of total SRAM fit.

## Integration acceptance

Use the frozen source objects and protocol fixtures before live gameplay. Run static, scrolling, camera motion, scene cuts and deliberately oversized packets. Then replay drop, duplicate, reorder, retry, CRC, tag and late-HUD failures. The Python recovery tests demonstrate API-level atomic state and key recovery; FPGA bank fences and panel recovery still need their own tests.

A hardware 30 fps result needs timestamped evidence of complete, unique presentations over at least ten minutes, bounded queues and end-to-end latency distributions—not just a 30 fps host request, repeated display refreshes, a theoretical bus calculation or a decoder kernel clock. Count dropped/repeated frames and audio/input contention. Re-run memory and link tests with the actual firmware UI enabled.

The fixed display filter and streaming scanout models can move to RTL/native implementation now. The entropy/inverse decoder can move as an experimental negotiated backend. Additional motion policies and full HEVC/AV1 FPGA decoders remain research work.

## Reproduction map

The final v67 report and provenance manifest identify all inputs, stored packet fixtures, unit logs and independent verifier entry points. In the repository:

```sh
python experiments/verify_prototype_v67.py
python experiments/render_prototype_v67.py
```

Use the pinned Python environment recorded with the report. The portable verifier replays stored evidence; it does not need the original source video URLs or physical devices.
