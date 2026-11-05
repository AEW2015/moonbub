# Guarded same-reference motion (v50)

**The strict local guard rejects every grid proposal on these four prefixes.** All 96 selected frames remain fixed-zero and match the separately retained zero-control bytes and quality. This study protects the control from the measured global-grid trades; it supplies no compression gain and adds host evaluation cost.

Both real complete CS38 proposals use the same currently selected incoming reference. Each fitting proposal is independently received on a fork, its original-source RGB565 active-region SSE is measured, and only then is the winner published. A grid proposal is admitted only when its complete byte count and integer active SSE are both no worse than zero and at least one strictly improves. Ties select zero. A grid must fit 49152 bytes; otherwise a fitting zero is used, and if neither is selectable the prefix stops without advancing either base or HUD history.

| Cohort | Selected bytes | Selected active MSE | Grid proposals with fewer bytes | Grid proposals with lower SSE | Grid admitted |
| --- | ---: | ---: | ---: | ---: | ---: |
| mass-effect-10000 | 368,327 | 17.20233 | 5 | 0 | 0 |
| mass-effect-4500 | 235,896 | 27.03509 | 3 | 0 | 0 |
| mass-effect-1600 | 77,365 | 10.49460 | 0 | 1 | 0 |
| mass-effect-combat | 700,546 | 28.43519 | 15 | 0 | 0 |

Across 96 inputs,23 grid proposals are smaller, one different grid proposal has lower original-source SSE, and the four keys tie exactly. None improves the joint objective. The selected total is 1,382,134 bytes, with active MSE 20.79180365 and 2,027,520 exact HUD words. All 192 proposals fit; no prefix stopped. All 1152 full/compact AB38 alternatives,192 intermediate CS37 proposals,192 final CS38 proposals, vector maps, coefficients, source canvases/descriptors and quality records are retained. The source canvases are the four previously retained v40 windows, not a claim of unseen media.

## Construction and reference semantics

Both proposals reuse the frozen v47 constructor and search primitives unchanged: fixed-zero analysis-v37 versus `global_grid` from global-v33, block 32, ROI 8/background 16, RDO lambda 1, keys every 24 frames and exact shared HX33 HUD. The intermediate CS37 cap is deferred locally until final complete CS38 selection; legacy/global RDO reversion occurs before hidden suppression. Every proposal pays its own analysis, quantization/RDO, legacy entropy/reconstruction/normalization and all six AB38 encodes. Actual legacy/full/compact bytes choose each plane, with stable ties.

The guard uses actual complete packet bytes and actual original RGB565 SSE, not source SAD, unrounded coefficient proxies, rounded MSE or a future frame. Fitting candidates receive on fresh copies of the same selected state. The receiver validates all coefficients, maps, vectors, reference identities and HUD words before the new selected state is published. Nonselected forks are discarded.

A local guard does not generally guarantee future nonregression against a separate fixed-zero history: selecting different pixels changes future references. Here no grid is selected, so the complete selected histories do remain byte-identical to the fixed-zero controls. This distinction also separates the local proposal trades from the accumulated own-history damage observed in v47.

## Paid scope and limits

`paid_sender_ms` includes both full sender paths. `paid_policy_with_receive_quality_ms` additionally includes both fork receives, exact source-quality measurements, comparisons and the selector. Input read/conversion, previously paid shared HUD generation and archive I/O are outside those clocks and recorded separately. Both selected and losing work is retained. This is a Python proof and service-cost study; it makes no physical 30 fps, FPGA/ESP32 memory/cycle/fit, new native-codec frontier or HEVC/AV1 superiority claim.

The next motion optimization must change the search/objective or candidate granularity rather than assume that the existing sampled-SAD grid helps. Quantized per-block distortion plus coefficient and motion-map cost is one candidate objective, still requiring actual whole-packet and causal validation. This study does not claim that such a change will succeed.

## Reproduce

```sh
cd experiments/python-game-guarded-motion-v50-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_verify
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

Three producer tests cover integer Pareto decisions, strict ties, byte/SSE trades, cap admission, missing-safe-fallback rejection and refusal of float/proxy values. Seven independent tests and the final replay pass: 96 selected frames, 192 same-reference proposals, 1152 AB38 alternatives, four selected plus four fixed-zero histories, 96 identical-context byte goldens, 2,027,520 exact HUD words and 1322 source pins. The independent verifier owns separate source/search/quantization/reversion/receiver/selector checks and imports no new producer encoder. All earlier studies remain frozen.
