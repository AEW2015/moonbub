# Gamebub v68: exact zero-motion prediction shortcut

This final component pilot extends the [six-hour v67 research report](custom-codec-prototype-v67-2026-11-05.md). It recognizes the existing zero-motion prediction case without changing packets, codec decisions, quantization, decoded pixels or the prediction reference. It is a Python reference component, not a deployed receiver, ESP32 firmware update or FPGA bitstream.

The late v66 diagnostic showed why the inverse transform alone is insufficient: parsing/entropy/validation occupied about 45 ms, or 59% of the third timed receive sample, while other unassigned work remained. Those diagnostic stage samples are distinct from the paired whole-receive medians and were collected under a non-isolated host workload. V68 separately clocks prediction to test a narrow optimization.

For a validated, readonly, fixed-shape int16 canonical reference and a correctly shaped bounded int8 vector grid containing only zeros, `predict()` returns the same reference tuple. It still validates shape, range, dtype and ownership requirements. Nonzero/fractional motion uses the frozen predictor. Key prediction uses readonly broadcast views backed by one immutable two-byte int16 constant instead of three materialized planes.

The producer replays all **457 archived source-v40 frames in four causal chains: 20 keys and 437 P frames**. Old and new prediction arrays match exactly. Reconstructing and normalizing with the new prediction preserves the stored canonical tag, source HUD and displayed RGB565 image. References remain unchanged. Source data is the same known, related, precompressed Mass Effect corpus; there are no new captures or native-codec encodes.

| Prediction component | Mean of paired per-frame stage medians, old | New |
|---|---:|---:|
| 437 zero-motion P frames | 16.50285 ms | 0.104507 ms |
| 20 key factories | 0.021562 ms | 0.012711 ms |
| All 457 cases | 15.78157 ms | 0.100489 ms |

Each frame has three alternating paired prediction-stage trials. Causal receiving, decoding, reconstruction, normalization, source/display comparison, hashes and I/O are outside those stage clocks. Validation inside the new predictor is charged. These timings are descriptive host Python measurements; **they do not measure a complete receiver speedup or 30 fps**. The existing receiver is not silently modified.

The shortcut avoids **1,036,800 logical bytes of materialized prediction-plane elements per frame** for this geometry. A P frame borrows its existing reference storage; a key uses a shared immutable two-byte constant backing its broadcast views. View/tuple metadata, validators, reconstruction output, other temporaries and external banks are separate. Logical view `nbytes` is not backing-store allocation. This does not eliminate the actual reference reads during residual addition, provide a total peak-memory measurement or establish BRAM/SRAM fit. A hardware implementation must retain reference-bank leases and correct read addressing.

Four producer unit tests and six independent directed tests accompany the full independent replay. They cover exact zero prediction, shared key storage, readonly/range/shape/map validation and nonzero/fractional fallback. The final V68 provenance verifier checks the frozen V67 inventory and replays this new component's independent verifier; V67's 16 helpers had already passed both ordinary and access-guarded relocated replay. The frozen V67 files are preserved, apart from its explicitly mutable index allowance.

```sh
python experiments/verify_prototype_v68.py
```

The research branch is `study/gamebub-specialized-v68-20261105`, based on published V67 commit `043939f89fb2c9626accc9652884520a68c5fc8d`. Implementation details and the exact component API are in [the study README](../experiments/python-game-zero-predict-v68-study/README.md). The broader [hardware handoff](gamebub-v67-hardware-research-handoff.md) still applies: current hardware firmware is JPEG-only, and new codec/profile integration, synthesis, ESP32 measurements and physical frame-rate proof remain future work.
