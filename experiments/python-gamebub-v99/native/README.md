# Fresh V99 native handoff

`main.cpp` includes the existing `experiments/cu66-native-v69/decoder.hpp`
unchanged. Its supported syntax remains CU66/GU66 version 1, fixed epoch 25,
720×480, zero base motion, block size 16/32, and arithmetic dispatch 5/6.
CS88 and other wrappers require an explicit future adapter; they are rejected.
This is CPU C++17 verification, not FPGA or device performance.

Run from the repository using the project Python environment:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python scripts/cu66-v99/run_native.py \
  --ledger /absolute/path/to/fresh/ledger.jsonl \
  --output /home/lori/gamebub-build/cu66-v69/v99/new-attempt
```

The output directory must not exist. Each attempt retains its source, input,
compiler, container, binary and output hash receipts and logs, including failures.
The compiler is checked on the host first. If unavailable, the runner uses the
already running `gamebub-cu66-v69-build` container. It does not install software,
create or modify containers, inspect container filesystems, prune data, or flash
hardware. Builds use one compiler process and live outside Git.

Each JSONL input row has `clip_id`, `frame_id`, `packet_path` and `expected`:

```json
{"clip_id":"clip.q3","frame_id":0,"packet_path":"packets/000.cu66","expected":{"canonical_sha256":"64 lowercase hexadecimal characters","hud_sha256":"64 lowercase hexadecimal characters","rgb565_sha256":"64 lowercase hexadecimal characters","canonical_tag":"optional 32 lowercase hexadecimal characters"}}
```

Packet paths resolve relative to the ledger. Clips must be contiguous; each new
clip gets a new decoder. These expected hashes cover:

* Canonical: contiguous Y 720×480, Cb 360×240, Cr 360×240 unsigned bytes, without geometry.
* HUD: little-endian `<HHB` width/height/count, then each `<4H` rectangle and its row-major `<u2` words.
* Display: complete row-major 720×480 RGB565 little-endian words after HUD overlay.

Only the call to `Decoder::receive` is timed; it returns an immutable published
frame with RGB565 ready. Packet reads, checks, serialization, hashing, disk writes,
Python and gzip are excluded. A single sample per fresh frame is reported; timings
are not warmed isolated benchmarks or deployment estimates.

Every packet is preceded by malformed CRC, truncation, unsupported CS88 wrapper,
unsupported version/flags/epoch,
reference identity, late canonical tag and late HUD corruption trials on the same
decoder. All must reject without changing the published pointer or content, then
the original packet must succeed in that context. Dependent packets also reject
without a cached reference. Replays reject after publication. The prior frame and
first retained frame are checked for mutation after later receives. SHA256 and
CRC32 known-answer checks run first.

`observations.jsonl` records exact native output hashes, timings, rejection counts,
and `display_rgb565_path`. These output files are deterministic gzip streams
(`mtime=0`); the runner validates decompression against the native raw dump and
published output hash before removing only its own redundant raw file. The
original `native.jsonl`, source ledger receipt, input receipt and TSV native
manifest remain available for audit. `summary.json` contains aggregate timings.
