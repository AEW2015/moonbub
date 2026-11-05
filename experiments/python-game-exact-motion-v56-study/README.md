# Exact post-RDO motion mixture (v56)

**The exact-reference gate admits no motion on these retained game prefixes. There is no compression gain.** All 96 selected frames retain the fixed-zero packet bytes, normalized references, displayed RGB565 images, source quality and exact HUD words. This negative result removes the future-quality ambiguity found in v53.

| Cohort | Nonzero grid macroblocks | Exact eligible MBs | Selected MBs | Selected bytes |
| --- | ---: | ---: | ---: | ---: |
| mass-effect-10000 | 2306 | 0 | 0 | 368,327 |
| mass-effect-4500 | 1268 | 0 | 0 | 235,896 |
| mass-effect-1600 | 674 | 0 | 0 | 77,365 |
| mass-effect-combat | 3379 | 0 | 0 | 700,546 |

The 7627 nonzero grid vectors do not yield even one 32×32 luma / 16×16 chroma macroblock whose **every canonical normalized YUV sample** matches the zero proposal. No proxy map is selected; the new serializer reproduces all 96 zero packets exactly. The selected total remains 1,382,134 bytes, active MSE 20.79180365 and 2,027,520 exact HUD words. There are 288 retained actual packets and 1728 retained full/compact AB38 alternatives; every source proposal and candidate fits the final 49152-byte cap.

## Exactness rule and future reference induction

At each selected incoming reference, the frozen source encoders construct actual zero and global-grid proposals, including their original quantization, RDO and full-plane legacy-size reversion before hidden suppression. The direct receiver validates both source proposals. A nonzero grid macroblock is eligible only if all normalized YUV samples across all three corresponding macroblock slices exactly equal the zero output, including the partial rightmost macroblock. Equal SSE or equal average color is insufficient.

Eligible blocks would choose grid only if the **already selected post-RDO** visible coefficient fine-bit proxy plus a fixed 16-bit nonzero-MV charge is strictly smaller than zero. Ties retain zero. Both exact-equality counts and the full post-RDO cost tensor are archived.

The candidate mixes those already selected coefficients and predictions by aligned 8×8 transform blocks, then packs the actual mixed vectors. It does **not** quantize, prune, rerun RDO or revisit original plane-reversion decisions. An explicit serializer only plans/constructs actual legacy/full/compact entropy options, reconstructs the fixed coefficients, checks exact normalized zero output, and writes a new pre-normalization tag and complete CS38 packet. All six AB38 alternatives are paid for the mixed packet too.

A candidate can publish only if its complete packet is strictly smaller than the validated fitting zero packet and remains within the final cap. Otherwise zero publishes. The whole canonical output is always zero, so the next reference is exactly the separate fixed-zero reference by induction. This is stronger than v53's immediate source-error guard and prevents its future-history drift. This study does not relax that guarantee to manufacture rate savings.

## Directed nonzero serializer coverage

The real game campaign has no nonzero mixed map. A separate pinned directed test therefore constructs a gradient reference, a nonzero `[4,0]` half-luma motion vector on one macroblock, and DC coefficients that exactly correct its +2 predictor offset in Y/Cb/Cr. The resulting packet contains nonzero vectors and coefficients and roundtrips through the qualified direct-v43 receiver to the exact zero canonical reference. It runs with quantization and RDO calls replaced by failing mocks. This is functional coverage, **not a compression win or a retained gameplay result**.

That directed test was added after the campaign clocks. Only `test_model.py` and its source pin were updated; helpers/model/benchmark, packet bytes and timing records were unchanged. `results.json` discloses the update explicitly.

## Evidence, paid scope and reproduction

Four producer tests and six independent tests pass. Independent replay rederives all source proposals, post-RDO coefficients, full canonical MB equality, fine-bit/MV costs, map assembly, actual mixed prediction, fixed-coefficient reconstruction/tags, all entropy alternatives and complete reference induction. It validates all 1329 source pins and all 96 zero-control byte goldens. Actual losing proposals, costs, masks, coefficients, vectors, original source/HUD descriptors and output metrics remain archived.

Sender work includes both source analyses, two full source encodes, exact eligibility/proxy evaluation, mixed materialization and entropy serialization. The policy clock additionally includes receives and exact source-quality checks. Source conversion, previously paid shared HUD generation and archive I/O are separate. Full host arrays remain; no physical 30 fps, FPGA/ESP32 fit/cycles, new native frontier or HEVC/AV1 superiority is claimed.

```sh
cd experiments/python-game-exact-motion-v56-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_verify
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

All earlier studies remain frozen. The independent verifier imports no new producer encoder.
