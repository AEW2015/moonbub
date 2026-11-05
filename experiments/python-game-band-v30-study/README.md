# V30 bounded block/band residual choices

This host-side prototype preserves GM27 wire and decoder arithmetic. It
reproduces the v28 quantized/RDO incumbent, then generates bounded coefficient
candidates at full resolution. It does not change FPGA syntax or transport.

`encode_with(runtime28_module, prepared, qmap, rdo_lambda=1, policy=...)`
accepts the caller's owned Prepared value without mutating imported modules.
`encode_prepared` uses this module's own loaded runtime.

For each plane, the menu contains at most four unique candidates:

1. The incumbent.
2. Zero AC zigzag positions 21–63, but only in eligible 8×8 blocks.
3. Zero AC positions 6–63, again only in eligible blocks.
4. A mixed candidate choosing cutoff 6 where eligible, otherwise cutoff 21.

DC values always remain unchanged. All qmap-scale-8 ROI blocks and the inherited
chroma protection halo remain coefficient-identical to the incumbent. Eligibility
uses each block's **actual clipped reconstructed source YUV SSE**, not transform
energy or an isolated packet estimate. `band_strict` allows no block-SSE increase.
`band_budget` permits at most `min(floor(incumbent_block_SSE/100),64)` additional
SSE per unprotected block: 1% of incumbent error, capped at one sample-MSE unit
in a complete 8×8 plane block. These are YUV guards, not perceptual/RGB guarantees.

All unique plane candidates get the exact v29 combined legacy/EC26 cost, including
context, padding, row-reset DC and dispatch. Minimum actual cost wins; incumbent
wins ties. Only the winner is serialized. Thus every selected plane is no larger
than its incumbent; the model does not claim each individual block has an exact
independent marginal bit cost. Full trial inverse transforms, counters, copies,
selection, reconstruction and final serialization are paid in encode timing.

## Matched-reference results

The first 12 images of each retained window use the same actual accepted v28
exhaustive decoded references. Alternatives do not become later references;
root's full causal campaign measures that separate effect.

| Window | Policy | Complete CP27 bytes | Active RGB565 MSE | Encode ms |
| --- | --- | ---: | ---: | ---: |
| 2600 | Incumbent | 146,255 | 14.422069 | 35.10 |
| 2600 | Strict bands | 145,985 | 14.421377 | 81.31 |
| 2600 | Budget bands | 145,925 | 14.422778 | 82.54 |
| 7200 | Incumbent | 349,101 | 26.382324 | 45.74 |
| 7200 | Strict bands | 348,395 | 26.376124 | 101.96 |
| 7200 | Budget bands | 348,247 | 26.376892 | 102.50 |

Strict edits 188/634 blocks and removes 211/752 coefficients; 13/33 planes select
an alternative. Budget edits 231/745 blocks and removes 266/897 coefficients.
The gains are real but small: strict saves about 0.185%/0.202% complete bytes,
and budget 0.226%/0.245%. This is a candidate-generation proof, not a ready
performance optimization. Python work roughly doubles, and shorter matched
references cannot establish a causal quality or compression advantage.

All 72 actual CP27 candidates retain exact HUD data and fit 49,152 bytes. The
24 original source frames are reused across three policies at 720×480 coded /
720×405 active geometry. The model has no native encoder, ESP32 RF/QSPI timing,
FPGA synthesis/resource/memory proof, display presentation, or physical 30 fps
claim. Zlib only stores retained artifacts.

## Verification

```sh
python -m unittest discover -s experiments/python-game-band-v30-study -v
python experiments/python-game-band-v30-study/verify.py
```

Four focused tests cover exact frozen plane reconstruction, per-block strict
and budget guards, DC and ROI/chroma-halo preservation, malformed policy and
owned Prepared rejection, immutability, base-packet byte non-growth and
exact decode. Retained verification reconstructs the source decisions, actual
reference planes, every packet/choice/metric, every block bound and protected
coefficient, current-source HUD, and selected counter sizes. Source hashes bind
the inherited data and executed producers.
