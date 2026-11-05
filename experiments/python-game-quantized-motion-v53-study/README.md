# Quantized macroblock motion admission (v53)

**Sparse mixed motion saves bytes, but its accepted histories have higher source error than separate fixed-zero histories.** Local whole-packet Pareto admission does not guarantee future quality. This experiment retains that negative distinction rather than calling the result a quality-preserving compression win.

| Cohort | Fixed-zero bytes | Selected bytes | Byte change | Fixed-zero active MSE | Selected active MSE | MSE change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mass-effect-10000 | 368,327 | 365,391 | -0.797% | 17.20233 | 17.46648 | +1.536% |
| mass-effect-4500 | 235,896 | 230,742 | -2.185% | 27.03509 | 27.14622 | +0.411% |
| mass-effect-1600 | 77,365 | 77,123 | -0.313% | 10.49460 | 10.52423 | +0.282% |
| mass-effect-combat | 700,546 | 695,592 | -0.707% | 28.43519 | 29.43159 | +3.504% |

There are 96 selected frames across four independent 24-frame histories, 288 actual complete candidate packets and 1728 retained full/compact AB38 alternatives. The final controller selects 45 zero, 42 score-proxy mixed and 9 local-Pareto mixed frames. All candidates fit 49152 bytes; all selected HUD patches are exact (2,027,520 RGB565 words). All actual candidates, including rejected rate/quality trades, remain archived.

## Shared source analyses and measured MB costs

Each frame pays for one frozen zero analysis and one frozen `global_grid` analysis at the same actual incoming selected reference. The grid search supplies **one alternative vector per macroblock**, not an exhaustive motion search. Blocks are 32×32 luma and 16×16 chroma, including the partial rightmost macroblock. That partial macroblock contains 12 transform blocks, compared with 24 for a full interior macroblock.

Before the original encoder RDO stage, both analyses are quantized and inverse reconstructed with ROI 8/background 16. Exact int64 YUV squared error is aggregated per macroblock. The frozen fine39 function supplies the unrounded isolated CP02 coefficient-bit proxy; a fixed 16-bit charge is added once per nonzero macroblock vector. Every fully canonical-safe hidden 8×8 block has its coefficients forced zero, all 64 samples excluded from proxy SSE, and its proxy bits excluded. Normalized hidden output remains 128. Other blocks remain included; this is a proxy for the full actual stream, not an arithmetic-entropy or final RGB565 rate/distortion oracle.

Two predeclared maps are built from the tensor `[15,23,2,3]`: zero/grid × (YUV SSE, coefficient bits, MV charge).

- `mixed_score4` uses grid only when its SSE+4×(coefficient bits+MV charge) is strictly smaller; ties use zero.
- `mixed_pareto` uses grid only when both YUV SSE and proxy bits including MV charge are no worse, and at least one improves; ties use zero.

## Exact mixed analysis and actual final guard

Each map assembles prediction samples and original **unquantized** forward coefficients from aligned 8×8 blocks of the two shared analyses. It constructs an owned `m.Prepared`, privately copies its source planes, and packs the actual mixed vectors. It does not repeat search or forward transforms. The producer and independent verifier compare this assembly with a fresh frozen prediction/forward calculation using the materialized mixed vector map, including partial macroblocks. This establishes exact assembly, not a hardware memory or cycle result.

Zero and both mixed proposals then each pay the full frozen47 source encoder: original quantization, global RDO and legacy plane-size reversion before hidden suppression, actual CS37 entropy construction, and all six full/compact AB38 encodes. The intermediate CS37 cap remains locally deferred; the final complete CS38 cap is 49152 bytes. All coefficient, motion, quantizer, HUD and reference identities are checked by forked receivers. No new frozen function is patched.

Each fitting candidate is decoded on a fork of the same incoming selected state. Final admission uses its actual complete byte count and actual **original-source RGB565 active SSE**, both no worse than zero with at least one strict improvement. Among admitted mixed proposals, minimum(bytes,SSE,proposal order) wins; without an admitted mixed proposal, a fitting zero is used. If none is selectable, the prefix stops without publication. Only the chosen fork becomes the next reference.

This final guard measures an immediate comparison against zero at the current adaptive reference. It does not measure against the separate fixed-zero reference at every future step. The observed cumulative MSE increases in the table are precisely that future-history effect. Compression improvements are small and carry measured source-quality cost; HEVC/AV1 superiority is not established.

## Paid scope and archives

All source/search/forward work is paid once in `shared_analysis_work`. Both mixed map materializations, three full source encodes and 18 AB38 candidate encodes per frame are paid. `paid_sender_ms` sums those actual stages. `paid_policy_with_receive_quality_ms` also includes candidate receives, exact quality calculations and checks. Source read/conversion, shared previously paid HX33 generation and archive I/O are separate. These are host proof costs, not a 30 fps encoder or hardware throughput claim.

Archives retain the per-MB cost tensor, both maps, original global and actual mixed packed vectors, full CS37/CS38 packets, all entropy alternatives, quantizers, coefficients, owned Prepared evidence hashes, source/HUD descriptors, current reference IDs/tags and original RGB565 metrics. All old studies are frozen.

## Reproduce

```sh
cd experiments/python-game-quantized-motion-v53-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_verify
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

Three producer tests pass: arbitrary checkerboard mixed-vector prediction/forward equality and private ownership, partial-edge block count and fine-bit/MV/selector calculations, and actual whole-packet guard ties/trades/cap behavior. Six independent tests and the final replay pass: 96 selected frames, 288 actual proposals, 1728 AB38 alternatives, 1180/607 proxy-selected macroblocks, 1324 valid source pins, exact mixed prediction/forward and original RDO/plane-reversion checks. The independent verifier independently confirms the future source-error increases and imports no new producer encoder.
