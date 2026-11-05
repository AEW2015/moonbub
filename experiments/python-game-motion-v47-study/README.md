# Global-grid motion qualification (v47)

**The frozen fixed `global_grid` policy loses on these four fresh prefixes. Keep the fixed-zero control.** Every policy completed all 24 frames per cohort; no proposal exceeded the final49152-byte cap. The global search increases both actual complete bytes and original-source RGB565 error in every cohort. This is a measured negative result, not a new preferred codec mode.

| Source cohort | Zero bytes | Grid bytes | Byte change | Zero active MSE | Grid active MSE | MSE change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mass-effect-10000 | 368,327 | 399,341 | +8.42% | 17.20233 | 21.24708 | +23.51% |
| mass-effect-4500 | 235,896 | 264,547 | +12.15% | 27.03509 | 28.86712 | +6.78% |
| mass-effect-1600 | 77,365 | 89,982 | +16.31% | 10.49460 | 10.81528 | +3.06% |
| mass-effect-combat | 700,546 | 720,672 | +2.87% | 28.43519 | 43.68621 | +53.63% |

The source is the first 24 actual retained frames from each of the four v40 cohorts:96 unique canvases, each evaluated through two separate accepted-reference histories (192 complete CS38 packets). All 96 fixed-zero packets are byte-identical to the prior binary-v40 controls. Each displayed frame has exact source HUD patches:4,055,040 HUD words across the 192 accepted frames, with zero errors. The underlying RGB565 quality measurements use the original source, not the previous decoded image.

## What changed

`python-game-global-v33-study/model.py:analyze_with` runs unchanged with `policy='global_grid'`, block 32, and `avoid_rects=n.ROIS`. Global coarse samples use stride 16 and81 candidate vectors (-16..16 in steps of 4 half-luma units); local samples use stride 4 with zero and a3×3 grid around the global estimate. Quiet threshold 2 and the frozen strict SAD winner rules are unchanged. Vectors remain divisible by 4, so both luma and chroma prediction are integer aligned. The fractional refinement used by the separate `global_cross` policy is disabled.

Both policies use epoch25, keys every 24 frames, ROI quantizer 8/background 16, original RDO lambda 1, and the same externally generated HX33 sidecar from v40. The zero side uses the frozen fast analysis-v37 path; the motion side uses its own most recently accepted normalized reference. Their predictions, reconstructed references and future quality can differ. A same-source input does not make these same-history or lossless comparisons.

The local CS37 proposal constructor explicitly copies the frozen integrated-v38 decisions, including full-plane legacy-size RDO reversion **before** hidden-coefficient suppression. Only its intermediate 49152-byte cap is deferred. The already owned selected coefficients feed both full-grid and compact AB38 encoders directly; no over-cap intermediate is reparsed. All six AB38 encodes/frame are paid and archived, including losing options. Each plane chooses the shortest actual legacy/full-AB/compact-AB payload, preserving that stable tie order. Only the final complete CS38 packet is eligible for publication under 49152 bytes. A cap failure would retain the proposal, leave both base and HUD histories unchanged, and stop that policy prefix; none occurred here.

The qualified direct-v43 receiver checks every selected packet and commits its own state only after validation. Decoded coefficients and normalized planes must exactly match the proposal; HUD patches must match source RGB565 words; final quality and display hashes are archived. All actual intermediate packets, final packets, legacy payloads, 1152 raw AB38 trials, selected vector maps, qmaps, coefficient arrays and source/HUD descriptors are retained in `objects/` and `results.json`.

## Interpretation and scope

The search optimizes a sparse SAD proxy, not actual encoded bytes or the final quantized RGB565 error. A smaller search SAD does not guarantee a better rate/distortion result, and own-history reference changes can amplify the difference. The combat prefix demonstrates this particularly clearly. A useful follow-up would compare actual zero/grid candidate packets at the same incoming reference and select with an explicit whole-packet rate/distortion rule, then evaluate that selector through a separate causal history. This experiment does not assume such a selector will win.

Sender clocks include source analysis/search/prediction/forward transform, quantization/RDO/legacy entropy, reconstruction/normalization, all six AB38 encodes and wrappers. Input read/conversion, externally paid shared HUD generation, receive checks, quality metrics and archive I/O are reported separately. These are single host service measurements, not a paired CPU speed test or physical 30 fps proof. No new native HEVC/AV1 encode, compression-superiority claim, FPGA/ESP32 cycle/fit claim, or hardware test is made here.

## Reproduce

```sh
cd experiments/python-game-motion-v47-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_verify
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

Three producer tests pass: exact fresh-key golden parity, private owned grid preparation and legal nonzero integer-chroma vectors on a translated fixture, and deferred intermediate cap with final bounded-receiver rejection/no publication. Six independent tests and the complete replay pass: 192 own-history frames, eight chains, 96 zero-control byte goldens, 92 independently recomputed global searches, 1152 independently decoded AB38 alternatives, 4,055,040 exact HUD words and 1317 valid source pins. The independent verifier is maintained separately and imports no new producer encoder. All earlier studies remain frozen.
