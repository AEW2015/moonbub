# New source-frame CU66 offline bridge

This isolated experiment generates CU66 from newly supplied RGB source frames. It does not export retained CU66 packets. No socket was opened, firmware installed, FPGA programmed or physical playback attempted.

## Executed result

The selected `package12/manifest.json` has status `PASS_FRESH_SOFTWARE_REFERENCE_AND_FAULTS` and was read successfully by the existing, unchanged `host/dy71-sequence-v3/sequence_sender.py::Sequence` loader. Every adjacent packet passes that loader's actual identity/profile/cap/hash validation. This is a software qualification status, not a hardware-ready or timing signoff.

- Twelve distinct source frames, canonical YUV outputs, HUD outputs and complete displayed RGB565 outputs. KEY 0 followed by P 1–11; each P references exactly the preceding frame.
- Complete CU66 packets are 10,091–18,757 bytes, below 49,152. The fixed profile is CU66/GU66 epoch 25, zero base motion, arithmetic coefficient dispatch 5/6 only. ROI scale 8/background 16 was selected for every frame. These settings have no automatic correspondence to JPEG Q30/Q35.
- HUD envelopes: HX33 for frames 0–8; HU25 for frames 9–11. HX32 was evaluated by the inherited HUD selector but was not the chosen outer envelope in this sequence.
- Fresh independent Python CS37, CS38 and CU66 decoding match every canonical plane and HUD patch. Every HUD word also equals its source RGB565 patch. The exact native-v69 C++ decoder independently matches complete canonical YUV, all HUD words and full composed display hashes for all twelve packets.
- Native-v69: 38 malformed/truncated/late-HUD/replay/reference fault checks pass with accepted-state and prior-output ownership preserved. Exact V48 native HUD endpoint: sequential Prepare → full actual READ comparison → explicit write-drain ACK → Commit passes all 253,440 words. Its 98,304-byte tracked arena peaks at 95,053 bytes, with zero allocation failures. Twenty-four malformed HC70/late-HUD checks retain accepted words; twelve fresh-generation recovery checks pass.

The V48 arena check uses the actual bounded allocator and allocation-order implementation on the 64-bit host. It is not evidence about ESP32 heap fragmentation, internal-SRAM reserve, scheduler behavior, runtime stack margin or physical QSPI/SDRAM timing. The native-v69 full-frame oracle uses its original STL allocation model; it does not establish ESP32 memory fit. No larger arena cap was substituted to obtain the selected pass.

The first three new synthetic frames also passed the same full-frame checks. The first three local-video frames were repeated before the twelve-frame extension and reproduce byte-identical packets. Final selected executions are `native04/execution.json` and `endpoint04/execution.json`.

## Source and preparation

Local source: `C:/moon/dev/host/fixtures/motion-test.mp4`, SHA-256 `d2ef7085d11a0a43741adb052c99df9814a8994018d8ca8922dfebc9b2bef9b4`. This is **not** the requested two-minute Mass Effect source.

`prepare_video.py` selected the first twelve decoded frames from offset zero, without looping or temporal resampling. Source 1280×720 RGB was resized with Pillow bilinear to 720×405 and placed in a black 720×480 canvas at (0,37): no side padding, 37 rows above and 38 below. PTS values are 0,512,…,5632 with time base 1/15360. This covers eleven source intervals, about 0.367 seconds—not twelve seconds or a two-minute replay. Preparation metadata and exact arrays are `video12-source.json` and `video12-source.npy`.

## Architecture and bindings

1. Frozen integrated-v38 `encode_prepared`, after causal analysis-v37, encodes the new source canvases as independently checked CS37.
2. Frozen binary-v38 AB38 encoder constructs full/compact arithmetic alternatives; the bridge chooses only dispatch 5/6, never a legacy coefficient fallback. Independent arithmetic decoding checks the chosen coefficient arrays.
3. Frozen canonical-v66 `convert(..., 'CU66')` binds the verified canonical uint8 reference/output tags. Independent canonical-v66 receive and native-v69 receive validate the resulting packets.
4. The exact V48 endpoint independently checks HUD decoding, range READ, accepted references and generation recovery under its original arena cap.

The bridge preserves imported source hashes before and after generation. Seventy-eight imported Python files are snapshotted under `dependencies/` with relative experiment layout. A new one-frame run from the dependency snapshot reproduced the same synthetic KEY packet (`12492eaa…`), without the original experiment sources. Exact native-v69 headers/main and V48 native endpoint sources are copied into their selected execution directories with hashes. `video12/result.json`, `package12/manifest.json` and their evidence bindings retain per-frame source/canonical/HUD/display/packet hashes.

## Reproduction

Use the existing `C:/moon/tools/venvs/cu66-verify/Scripts/python.exe` environment (Python 3.11, NumPy 1.26.4, Pillow 10.4 and PyAV 18.1.0). Set `PYTHONDONTWRITEBYTECODE=1`; all tools require fresh output paths. `prepare_video.py` prepares explicit canvases; `bridge.py --rgb24-npy <array> --count 12 --output <fresh>` generates a finite sequence. An alternate caller can provide its own exact uint8 N×480×720×3 array. No implicit input scaling or live capture occurs in the encoder.

`run_native.py`, `run_endpoint.py` and `package_sequence.py` preserve concrete selected output-directory names and require fresh directories. For a replay, select new unique names and update their sequence directory references; do not overwrite selected evidence. Their execution JSON records exact compiler commands, exit codes and host process times. The UCRT GCC build uses C++17 and `-Wall -Wextra -Werror`.

The bridge is a correctness-first research composition. Per-frame offline generation includes analysis, multiple encoder alternatives, several independent decoders and golden checks. Its wall time cannot establish an optimized encoder speed or target frame rate. The native host receive clocks similarly do not establish physical playback cadence.

## Preserved initial failures and remaining gates

- `synthetic01` stopped during import because default Python lacked PyAV. The established isolated verification environment resolved that dependency; no source was mocked or changed.
- `native01` compiled but its original runner could not find a fixture because it expects slash-separated index paths. Subsequent invocations use `Path.as_posix()`; the exact native decoder remains unchanged.
- `endpoint02` exposed a test-harness mistake: it called the bounded `word_bytes` allocation helper outside an arena scope while collecting comparison bytes. The harness now copies comparison bytes into its own standard vector. Selected endpoint04 executes the corrected harness against unchanged V48 native sources.

Remaining before physical use: owner review of the adjacent manifest, exact device/firmware/FPGA/ABI identity and memory/reserve checks, fresh local recording/ownership gates, and a controlled trial. Existing V48 firmware accepts a finite count12 profile, but this new content has not been sent to it. A two-minute arbitrary-source stream, continuous receiver lifecycle, live CU66 encoder, audio/input coexistence and 30 unique displayed fps remain unimplemented or unverified here.
