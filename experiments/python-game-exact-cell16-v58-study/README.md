# Exact 16-cell post-RDO motion (v58)

**Finer cells create exact eligibility, but still produce no compression gain.** All 96 selected packets retain the actual zero32 bytes and exact canonical references, source quality, RGB565 display and HUD. This tests whether v56's 32-macroblock granularity caused its zero eligibility.

| Cohort | Nonzero repeated-grid cells | Exact eligible cells | With visible blocks | Hidden-only | Selected cells |
| --- | ---: | ---: | ---: | ---: | ---: |
| mass-effect-10000 | 9168 | 443 | 21 | 422 | 0 |
| mass-effect-4500 | 5010 | 438 | 1 | 437 | 0 |
| mass-effect-1600 | 2696 | 487 | 86 | 401 | 0 |
| mass-effect-combat | 13278 | 411 | 2 | 409 | 0 |

Across 30152 nonzero cell occurrences, 1779 are exactly equal to zero, including 110 with visible transform blocks and 1669 hidden-only cells. None reduces the post-RDO fine-bit proxy plus a 16-bit nonzero-motion charge. No cell or candidate frame is selected. Total selected bytes remain 1,382,134, active MSE 20.79180365, and all 2,027,520 HUD words are exact. There are 288 actual retained packets and 1728 retained full/compact AB38 alternatives; all fit the final cap.

Independent supplementary inspection confirms that all 110 visible eligible cells have **identical zero/grid post-RDO coefficient arrays and equal fine bits**. Removing the motion charge would therefore expose no coefficient proxy saving in these cells.

## Fixed source proposals, finer mixture grammar

The actual source zero32 and global-grid32 proposals are unchanged from v56. Their original quantization, RDO and global legacy-size reversion are paid before coefficient suppression. The global32 vector map is repeated 2×2 and cropped to a 30×45 map. Each new cell is 16×16 luma and 8×8 chroma, containing exactly six transform blocks. There are no partial 16-cells in 720×480 geometry.

Exact eligibility requires a nonzero repeated vector and equality of **every normalized YUV sample** across the three cell slices. Canonical hidden samples remain part of that equality check. Visible fine coefficient bits exclude fully safe hidden blocks; a hidden-only cell has no coefficient saving and still pays the motion proxy. Visibility classification is archived independently of eligibility so that hidden-only equality cannot be presented as a gameplay compression result.

An eligible cell would choose grid only if its already selected post-RDO fine coefficient bits plus 16 motion bits are strictly smaller than zero. Ties retain zero. Coefficients and predictions are mixed by aligned 8×8 blocks. Quantization, RDO and original plane-reversion decisions are **not rerun**. The direct mixed serializer advertises block size 16, packs the actual 30×45 vectors, evaluates actual legacy/full/compact entropy representations, reconstructs a new pre-normalization tag, and requires its complete normalized output to equal zero32 exactly.

Only a strictly smaller fitting complete packet could replace zero32. Otherwise the actual original zero32 packet publishes. An all-zero16 candidate changes the block-size byte and CRCs, so it is **not byte-identical to zero32**, even though it has the same length and canonical output. This experiment claims no new16 byte golden. The retained fallback bytes are the existing zero32 goldens, and their canonical-reference equality gives exact future zero32 history by induction.

## Proof coverage and paid work

Four producer tests pass before the campaign clocks. They cover the zero16/zero32 wire distinction, exact output and equal length; a directed nonzero16 packet using one child of a corrected32-source predictor under forbidden quantization/RDO mocks; all six blocks per cell and a one-sample last-column equality failure; and the strict byte/cap guard. The directed fixture is functional coverage, not a compression result.

Eight independent tests and the complete replay pass, checking all 1334 producer source pins, 96 zero32 byte goldens, 288 actual packets, 1728 AB38 alternatives and 2,027,520 exact HUD words. The independent verifier rederives source proposals, repeated/cropped maps, every three-plane cell difference, visible/hidden classifications, post-RDO fine-bit/MV costs, mixed16 prediction/fixed coefficients, explicit block-size header/CRC/tags, all entropy choices and the complete zero32 reference induction. Source pins and every original source/HUD descriptor are retained in `results.json`; arrays and all losing packet bytes are archived in `objects/`.

All source analysis, two source encodes, cell evaluation, map materialization, mixed serialization and 18 AB38 encodes per frame are paid. The policy clock additionally includes receives and source-quality checks. Source conversion, previously paid shared HUD generation and archive I/O remain separate. No physical 30 fps, FPGA/ESP32 cycle/fit, new native-codec frontier or HEVC/AV1 superiority is claimed. All earlier studies remain frozen.

```sh
cd experiments/python-game-exact-cell16-v58-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_verify
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```
