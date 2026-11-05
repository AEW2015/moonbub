# Fixed display-filter qualification on all retained gameplay frames (v67)

The unchanged strong v60 filter improves original RGB565 active SSE in **all 457 retained CS38 frames**, with zero regressions or ties in this corpus. Aggregate SSE falls from **8,266,662,386 to 8,055,798,880 (−2.55077%)**. Complete encoded bytes remain **7,954,123**, canonical references remain unchanged and every HUD word stays exact.

This extends the two 24-frame windows by **265 additional temporal canvases**, not new captures or unseen games. All four related clips were already archived in v40, and are precompressed source material. The strong profile was calibrated only on the first 24 fixed-zero trajectories before the later experiments. No threshold or codec parameter was tuned here. Keys every 24 frames and the original full causal CS38 histories are replayed.

| Clip | Frames | MSE reduction, full clip | Additional IDs ≥48 | MSE reduction, additional IDs |
|---|---:|---:|---:|---:|
| Mass Effect 10000 | 119 | 2.90719% | 71 | 3.03761% |
| Mass Effect 4500 | 119 | 2.30843% | 71 | 2.29975% |
| Mass Effect 1600 | 119 | 2.51229% | 71 | 2.32033% |
| Mass Effect combat | 100 | 2.57152% | 52 | 2.48144% |

The result retains identity/strong per-frame source SSE, matching sample counts, display/luma hashes, packet/canvas descriptors, canonical tag and the unchanged filter work diagnostic. Separate partitions cover IDs 0–23, 24–47 and 48 onward. Regression counts are measured rather than inferred from average improvement. Three unit tests cover weighted means with a hidden individual regression, zero-error/tie cases and mismatched/missing observations.

This is a full-plane display-only Python proof. It introduces no new encoder, FPGA logic, physical throughput or memory-fit result. The v64 line implementation is a separate bounded-row equivalence experiment. Improving every frame in this known corpus does not guarantee improvement on other games or future frames, and MSE is not a subjective quality test. HEVC/AV1 have not been re-encoded or compared on this extended qualification.

```sh
cd experiments/python-game-filter-qual-v67-study
python -m unittest -v test_model
python benchmark.py
python verify.py
```

The independent verifier passes all 457 causal presentations / 914 variants, 157,939,200 filtered luma samples, 9,651,840 HUD words and 384 overlapping variants against frozen v60/v62. Six independent directed tests pass, including a perfect-source example where filtering worsens error; the corpus result is not a universal guarantee. Original videos and physical devices are unnecessary; stored source canvases and packets are sufficient.
