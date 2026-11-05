# Fixed display-filter temporal qualification (v62)

**The frozen strong preset improves measured error on every later-window case without changing encoded bytes or codec references.** Custom zero/adaptive mean RGB565 MSE improves 2.56–2.87%; sampled native anchors improve 0.22–0.66%. This validates a modest display-quality improvement on another temporal window, not a bitrate or hardware-throughput gain.

The preset is unchanged from v60: luma only, α24/β12/strength3, vertical then horizontal 8-pixel boundaries, exact signed integer rounding and bounded delta. It was selected solely from the four fixed-zero first 24 trajectories (source IDs 0–23). This study applies only identity and that frozen strong preset to source IDs 24–47; it does not retune thresholds or choose a per-frame oracle.

| Cohort | Case | Identity active MSE | Strong active MSE | MSE change |
| --- | --- | ---: | ---: | ---: |
| mass-effect-10000 | zero | 17.25033 | 16.76973 | -2.786% |
| mass-effect-10000 | adaptive | 17.73368 | 17.22427 | -2.873% |
| mass-effect-10000 | libx265 | 16.81444 | 16.73492 | -0.473% |
| mass-effect-10000 | libsvtav1 | 15.70577 | 15.67145 | -0.219% |
| mass-effect-4500 | zero | 27.36174 | 26.66018 | -2.564% |
| mass-effect-4500 | adaptive | 29.83850 | 29.02061 | -2.741% |
| mass-effect-4500 | libx265 | 25.09784 | 24.99559 | -0.407% |
| mass-effect-4500 | libsvtav1 | 23.83004 | 23.73144 | -0.414% |
| mass-effect-1600 | zero | 10.74909 | 10.45077 | -2.775% |
| mass-effect-1600 | adaptive | 10.77392 | 10.47451 | -2.779% |
| mass-effect-1600 | libx265 | 9.75555 | 9.70733 | -0.494% |
| mass-effect-1600 | libsvtav1 | 10.25638 | 10.20768 | -0.475% |
| mass-effect-combat | zero | 30.30958 | 29.52381 | -2.592% |
| mass-effect-combat | adaptive | 31.19250 | 30.35762 | -2.677% |
| mass-effect-combat | libx265 | 28.80498 | 28.61482 | -0.660% |
| mass-effect-combat | libsvtav1 | 30.01380 | 29.89137 | -0.408% |

For custom cases, the defined grid8 error-jump metric improves 18.26–23.71%, and coordinate temporal error-change improves 2.56–3.87%. These are the explicit v57 error equations, not SSIM/VMAF or subjective flicker/visual-quality proof. All metric results, including large-error counts and non-grid diagnostics, remain archived.

## Temporal inputs and fair native anchors

There are 16 source cases: separate-zero and adaptive v59 presentations, plus one actual sampled HEVC and AV1 anchor per cohort. The four source windows contain 96 distinct canvases; 384 decoded presentations produce 768 identity/strong display variants. Custom global IDs 24–47 begin with a fresh key 24. Fresh native AUs use PTS 0–23 mapped explicitly to those source IDs and the same source HUD words.

Native candidates come from the unchanged union of the 48-point coarse temporal-v61 grid and 21 predeclared combat cap controls. Before applying the filter, each anchor is the minimum actual complete bytes among supported points with zero cap failures and original RGB565 mean SSE no greater than the separate-zero window. Ties use SSE, original parameter argument and input order. Exact integer SSE/sample totals are derived from actual row metrics; unsupported alternatives are retained. All eight anchors exist.

This is **exploratory anchor selection**, not an independently held-out encoder choice or an optimal HEVC/AV1 frontier. The strong filter remains frozen independently of that selection. The same identity and strong choices are applied to every chosen custom/native presentation, with no post-filter reselection.

| Cohort | HEVC anchor | AV1 anchor |
| --- | --- | --- |
| 10000 | CRF 32 | CRF 46 |
| 4500 | CRF 28 | CRF 40 |
| 1600 | CRF 32 | CRF 46 |
| combat | CRF 24 + `vbv-maxrate=4000:vbv-bufsize=160:vbv-init=1` | CBR 3000 kbps, `rc=2:tbr=3000:buf-sz=60:buf-initial-sz=60:buf-optimal-sz=60:overshoot-pct=0` |

The combat AV1 source's `parameter=34` is a legacy argument, not an active CRF/QP when bitrate/CBR options strip CRF. Each source file/case index, actual `extra_options` and bitrate is retained; full `encode.requested_options` is available in the pinned native source record.

The fixed combat AV1 anchor passes the **unfiltered** quality/cap gate, but after applying the same strong preset its MSE 29.89137 is above equally filtered zero 29.52381. That outcome is preserved rather than reselecting an encoder to force a matched-quality result. Combat HEVC remains below filtered zero. The display filter also does not erase v59's adaptive-history quality regression relative to equally filtered zero.

## Unchanged references and exact HUD

Only a private luma presentation copy is filtered; U/V and the original decoded/canonical planes stay unchanged. Both full decoded-input hashes and actual custom canonical-reference hashes are checked after every call. Native decoder input/output arrays are immutable and no modified plane feeds back to its decoder. Exact source HUD words are overlaid **after** color conversion and filtering. Both presets preserve all HUD words and every original encoded byte count.

The excluded luma footprint is exactly the frozen canonical normalization mask, uniformly applied to custom and native cases. Each row retains full filtered-luma SHA256 as well as display/input/reference hashes, enabling verification even when RGB565 rounding would hide a one-level luma difference.

## Evidence and limits

Four producer tests pass before campaign clocks: frozen calibration and later source identity, custom reference immutability, native PTS→source-ID mapping, actual pre-filter anchor cap/mean rules including unsupported cases, identity equality and excluded-footprint preservation. Six independent tests and the complete replay pass: 16 cases, 384 decoded presentations, 768 display variants and 1354 source pins. An independent per-edge oracle checks every one of the 265,420,800 luma samples, filtered-Y/work hashes and all diagnostics. It verifies all 192 custom canonical references plus native inputs remain unchanged. The independent verifier rederives calibration from only four first-window zero trajectories, all anchor candidates/row sums, exact full-plane signed32 filter operations, every error57 equation, display hashes, HUD-last composition and reference immutability.

The prototype stages a full luma plane in Python. A streaming line buffer, DSP/BRAM/ports, implementation timing and physical 30 fps are not provided. This study changes no encoder decisions, canonical reference updates or bitrate. It makes no HEVC/AV1 superiority, new native frontier or hardware result claim. This is another temporal policy window from known v40 media, not project-wide unseen footage.

```sh
cd experiments/python-game-filter-temporal-v62-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_verify
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

All earlier source files, the filter model and its calibration remain frozen.
