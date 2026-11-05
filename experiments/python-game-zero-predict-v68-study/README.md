# Zero-motion prediction views (v68)

This isolated Python component avoids materializing full prediction planes for the fixed zero-motion policy. It changes no packet, profile, receiver or firmware. Current hardware backend support remains JPEG-only; this is an implementation candidate, not a deployment or 30 fps result.

`key_prediction()` returns three read-only, zero-stride int16 views of one immutable two-byte scalar containing128. `predict(reference,vectors,block_size)` checks the exact720×480 YUV420 shapes, int16 dtype, read-only flags and0–255 range, plus the bounded int8 motion grid for blocksize16/32. An all-zero grid returns the **same reference tuple**. A nonzero grid uses the unchanged frozen bilinear predictor, including fractional vectors. It does not patch a frozen function or skip invalid-input checks.

Borrowing assumes the previously verified canonical bank remains immutable under its owner. Range/shape validation is not a content-tag recheck or a proof of DDR integrity. Read-only NumPy flags do not implement hardware memory protection. The key views have immutable bytes backing; they cannot be made writable through their scalar owner.

The retained proof replays all457 source40 packets through the unchanged old43 receiver, preserving its own accepted causal history. Each frame compares old and fast prediction arrays exactly in three alternating paired rounds. A separate reconstruction using the fast prediction must match the old pre-normalization tag and normalized planes, stored canonical tag, exact HUD and displayed RGB565 hash. Incoming references are hashed before and after to check they remain unchanged. The packet/HUD decoder is unchanged and no new wire is generated.

Only prediction-stage calls are timed. Fast input validation is inside its clock. Frozen causal receive, state preparation, array comparisons, reconstruction, normalization, integrity checks, display/HUD composition and I/O are outside both prediction clocks. Key allocation versus broadcast-factory results are summarized separately from P prediction; these numbers must not be presented as full-receive speedup or FPS. The host was not isolated.

The completed campaign contains20 keys and437 P frames across four accepted causal chains, with1,307 source pins. Mean per-frame three-sample prediction medians are:

| Stage/input group | Old ms | Fast ms | Fast/old |
| --- | ---: | ---: | ---: |
| P-frame prediction,437 frames |16.502854 |0.104507 |0.006333 |
| Key factory,20 frames |0.021562 |0.012711 |0.589533 |
| Mixed campaign,457 frames |15.781573 |0.100489 |0.006368 |

All prediction and reconstructed-output comparisons passed. This isolates the cost of the old generic zero-vector predictor; it does not measure an integrated receiver using the borrowed path.

Avoiding a logical1,036,800-byte int16 prediction allocation does **not** remove the actual reference samples needed by residual reconstruction, output/reference banks, memory ownership, panel scanout, entropy work or fingerprint checks. `ndarray.nbytes` reports the expanded logical extent of broadcast views; the shared key sample backing contains only two bytes. Python metadata is additional. This is no FPGA BRAM fit or DDR bandwidth measurement.

Four producer tests cover immutable shared key storage, zero identity under a forbidden old predictor, nonzero/fractional fallback equality and invalid reference/vector geometry/type/range/read-only inputs. All six independent tests and the full457-frame independent replay pass, including16/32-block fractional/nonzero edge clamps, exact reconstruction/HUD/display and all1,307 pins. Independent verification has its own entrypoints and frozen logs. Results, source pins and stage timing samples are retained in `results.json`.

```sh
cd experiments/python-game-zero-predict-v68-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_verify
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

The producer models and code are frozen before final result publication. Prior study files remain unchanged. Stage results are conditional on zero vectors; the directed nonzero tests establish fallback correctness, not a nonzero-motion throughput gain.
