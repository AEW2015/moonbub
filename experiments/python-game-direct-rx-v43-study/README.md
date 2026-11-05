# Direct CS38 receive path (v43)

This experiment receives the retained CS38/GS38 streams directly. It removes the old proof adapter's coefficient re-encoding, converted CS37 packet construction, and repeated converted-packet parse. It preserves every encoded coefficient, motion vector, quantizer, normalized reference, exact HUD word, and displayed RGB565 frame.

`receiver.parse(packet)` validates the original bounded envelopes, CRCs, profile and identities, then dispatches legacy 0–4 and AB38 full/visible 5–6 payloads. Visible payloads expand into zero-filled coefficient arrays. Hidden nonzero coefficients are rejected. `Receiver.receive(packet)` predicts using the same frozen predictor, reconstructs once, checks the pre-normalization GS38 identity, normalizes, checks the outer identity, validates and privately copies the HUD, then publishes state. Any failure before that final commit leaves all prior state unchanged.

Published YUV, HUD, parsed coefficient, quantizer, and vector arrays are read-only. Coefficients and full YUV arrays remain allocated: each full int16 coefficient or YUV set is 1,036,800 bytes; the four retained RGB565 HUD patches contain 42,240 bytes. These are array sizes, not measured total process peak memory or an FPGA/ESP32 allocation proof.

## Qualification and timing

The benchmark replays eight separate actual causal histories: 24 retained v38 frames, 96 v39 frames, and 457 v40 frames. Each frame receives three alternating whole-call pairs from the same incoming state. State forks, comparisons, display checks, archive reads and writes are outside both clocks. Both clocks include validation, entropy decode, prediction, inverse transform, normalization and HUD validation. The baseline includes all work performed by the frozen proof adapter; the new path retains the original predictor to isolate the receive-path change.

Across all 577 frames, the mean of the per-frame three-sample medians fell from **145.341 ms** for the proof adapter to **89.006 ms** for direct receive: **38.760% less receive time (1.633×)**. All 9,674,118 input bytes and all decoded output semantics are unchanged. The streams used 196 full-grid and 1,535 compact AB38 planes.

| History | Frames | Adapter ms | Direct ms | Reduction |
| --- | ---: | ---: | ---: | ---: |
| binary-v38 / mass-effect-2600 | 12 | 95.894 | 62.540 | 34.78% |
| binary-v38 / mass-effect-7200 | 12 | 159.698 | 98.934 | 38.05% |
| binary-full-v39 / mass-effect-2600 | 48 | 87.298 | 58.758 | 32.69% |
| binary-full-v39 / mass-effect-7200 | 48 | 151.760 | 94.037 | 38.04% |
| binary-qual-v40 / mass-effect-10000 | 119 | 146.982 | 90.073 | 38.72% |
| binary-qual-v40 / mass-effect-4500 | 119 | 169.173 | 102.372 | 39.49% |
| binary-qual-v40 / mass-effect-1600 | 119 | 74.531 | 49.779 | 33.21% |
| binary-qual-v40 / mass-effect-combat | 100 | 228.283 | 132.602 | 41.91% |

Results and exact timing summaries are in `results.json`; all input packet bytes are retained in content-addressed `objects/`. `source_sha256` binds the timed producer, frozen implementations, and original campaign records. Independent verification checks those pins, original packets, all coefficient/maps/vectors, exact causal YUV/HUD/display state, reported work and all timing summaries. Scoped failing mocks prove the direct path does not invoke frozen entropy planning or construction; the same guard detects the old adapter's re-encoding.

All four producer tests and ten independent tests pass. The independent replay validated all 1,298 producer source pins, 577 causal frames (553 distinct packets), eight chains and 4,504,062 visible coefficient blocks.

Four producer tests cover actual key/P no-reencode behavior, private/read-only ownership, legacy 0/1/2 decode fixtures, and six retained fractional-motion histories using legacy 3/4 payloads. Independent tests additionally exercise CRCs, identity and geometry binding, nested arithmetic errors, hidden coefficients, replay and late tag/HUD failures with atomic state preservation.

This is Python host receive service timing. It does not prove physical 30 fps, real-time end-to-end streaming, FPGA cycles or fit, ESP32 memory/bandwidth, or compression superiority to HEVC/AV1. This change does not change compression or image quality. It removes proof-adapter overhead that was never intended as a native receiver architecture.

## Reproduce

Use the repository virtual environment with NumPy installed:

```sh
cd experiments/python-game-direct-rx-v43-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_verify
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

All earlier study files are frozen. New implementation files are confined to this directory. The independent verifier belongs to a separate agent and does not import a new coefficient encoder.
