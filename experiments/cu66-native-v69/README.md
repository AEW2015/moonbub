# Native CU66 decoder reference (v69)

This directory implements a portable C++17 decoder for an explicitly restricted CU66/GU66 research capability: fixed epoch 25, 720×480 YUV420, arithmetic coefficient dispatches 5/6 and **zero base motion only**. It is a native host implementation, not ESP32 firmware, FPGA RTL, network negotiation or hardware 30 fps proof. CS38/CS66 and legacy coefficient dispatches 0–4 are rejected; the capability does not silently accept a broader format.

`cu66::Decoder::receive(const Bytes&)` in `decoder.hpp` validates framing, original CRCs, profile/identity/reference bindings, qmap and motion grammar, AB38 entropy (including raw/arithmetic branches), exact two-pass signed Q14 inverse, hidden-block normalization and canonical uint8 SHA256[:16]. It decodes HU25/HX32/HX33 HUD envelopes and their actual HD25/HS32/HS33/HP01/HR01 fallback payloads, validates exact reference/output HUD fingerprints, converts the canonical YUV to RGB565 and overlays exact HUD words last. No Python is called inside C++ decoding.

The output is an owned `shared_ptr<const Frame>` containing canonical planes, HUD and displayed words. A candidate stays local until every check and display construction succeeds; only then is `state_` replaced. Prior returned frames remain alive and unchanged. The verified canonical tag is cached beside that immutable published state. Const ownership is a C++ API contract, not DDR ECC, authentication or protection against privileged `const_cast`/memory faults.

All 457 retained source-v40 CU66 packets are exported from the frozen v66 archive. The native runner checks full SHA256 of every canonical planar-u8 output, concatenated little-endian HUD words and complete displayed little-endian RGB565 against Python goldens. Twenty keys and 437 P frames use four independent causal histories. Component entropy fixtures additionally retain all 1,371 original AB38 payloads and exact encoded-order coefficient hashes, including compact scattering metadata for RTL users.

## Build and reproduce

The code uses only the C++17 standard library. The tested dedicated Ubuntu 24.04 container provides GCC 13.3 and CMake 3.28; no OpenSSL or zlib library is needed by the decoder itself. Python fixture export uses the pinned project venv and frozen retained archives. The formatter is Ubuntu clang-format 18.1.3 (`apt-get update -qq && apt-get install -y -qq clang-format` as container root).

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python export_fixtures.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python make_negative_fixtures.py
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j2
./build/test_native .
./build/ab38_check planes.tsv
./build/test_entropy_directed entropy-directed.tsv
./build/test_hud_directed hud-directed.tsv
./build/fuzz_native .
./build/native_decoder index.tsv 3
```

The exported manifest describes packet and expected-output hashes. Per-plane `.ab38` files omit the dispatch byte; `blocks`/`blocks_w` describe encoded entropy order, `full_blocks`/`full_blocks_w` and `.mask` describe placement, and `.coeff.i16.zlib` contains the expected encoded-order signed little-endian coefficient tiles. Compact scattering remains a separate integration step. The first frame of each cohort also retains full uncompressed expected YUV/HUD/display files for debugging.

## Validation and timing scope

All 457 frames pass the native golden replay and the complete AddressSanitizer/UndefinedBehaviorSanitizer replay. The separate entropy check passes 1,371 planes / 3,586,687 coefficient tiles. Directed suites cover 32 HUD branches and 31 entropy cases (six valid, 25 rejected), including raw signed extremes, row-reset DC, Rice escapes, padding and exact termination. The 28 malformed/unsupported full-packet cases preserve published state after wrong references/replay, nested CRCs, hidden nonzero coefficients and late HUD errors. Actual valid legacy-coefficient and nonzero-motion CU66 packets, independently accepted by frozen Python v66, are intentionally rejected by the native capability. Independent key 24 recovery and prior-returned-object ownership pass.

A sanitized seeded mutation run (seed 6903) rejects 507 of 512 variants; the five accepted variants retain the bound canonical/HUD/display outputs exactly. It checks failed-state/source immutability and makes no claim that every mutation is invalid. Frozen-Python fixture replay verifies all 457 presentations, 9,651,840 exact HUD words, all coefficient fixtures, generated constants and 1,304 normative source pins. These are producer and frozen-oracle checks; a separate agent source audit is additional work, not implied by this suite.

`native_decoder` times only `Decoder::receive`: wire/integrity/entropy/inverse/normalization/HUD/display construction/publication are included. Fixture reads, incoming-state forks, golden-output hashes/comparisons, report output and summaries are outside that clock. Repeated trials start from the same accepted incoming immutable state. The host/container is shared and not an isolated target processor.

The completed matched campaign (`paired_benchmark.py`, `results.json`) performs three alternating pairs per frame: frozen Python CU66 receive **plus the same RGB565/HUD composition**, versus native `Decoder::receive`. All 1,371 trials per path match the canonical/HUD/display goldens. Mean per-frame three-trial medians are **97.33174 ms Python / 7.60878 ms native** (native/Python 0.07817, about 12.79× lower host call time). Worst native per-frame median is 10.21305 ms; the largest raw native sample is 11.84083 ms. This is measured complete-presentation CPU work on an AMD Ryzen 7 H 255, not a target-device or physical frame-rate result. Native runs in a shared Ubuntu container capped at 4 CPUs and 4 GiB; Python uses the host project venv, with no OMP/OpenBLAS/MKL thread limits set.

`native_worker` excludes request transport, prepared-file I/O, incoming-state forks and golden hashes from its C++ clock. Python excludes equivalent fixture/fork/check work from its call clock. Both retain one accepted fork per frame. The retained orders alternate by `(frameID + repeat) % 2`. `verify_results.py` rederives every median, scene/overall mean, order and ratio. The standalone smoke and sanitizer clocks are qualification observations and are not the matched-campaign numbers.

Older frozen Python v66 receive timings exclude display construction, so those older numbers are **not a matched speedup denominator** for this C++ path. Likewise an FFmpeg decode-only timing excludes custom HUD, RGB565 composition and matching integrity work. A fair common-presentation comparison must charge those stages consistently or report codec-only and complete-presentation scopes separately. Native CPU timings cannot establish FPGA/ESP32 resource fit, display timing or end-to-end physical 30 fps.

This implementation uses straightforward bounded full coefficient arrays per encoded plane, dense two-pass inverse arithmetic and full external-model output/reference/display banks. It does not claim the streaming-storage or mirrored-DSP implementation bounds of other studies. The current live Gamebub JPEG firmware/backend remains unchanged and does not support CU66.

The shared-container paired campaign can be reproduced with `paired_benchmark.py` after building `/build/native/native_worker` in the documented Docker environment. `run_native_checks.sh` builds the complete release suite with CMake and runs all retained checks. `verify_fixtures.py` and `verify_results.py` audit semantic fixtures and retained observations separately. Final source/log hashes, capabilities and environment details are recorded in `qualification.json`; native decode source and timed results are frozen.
