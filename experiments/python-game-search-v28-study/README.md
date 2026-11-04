# Bounded sampled search for frozen GM27

This directory changes only the encoder's current-source motion-vector search.
The existing GM27 predictor, Q14 forward transform, ROI map, RDO, entropy, motion
packing and exact decoder reconstruction remain frozen imports. The accepted
reference is reconstructed YUV420 from actual CP27/GM27 packets. Source geometry
remains 720x480; quality is measured on the 720x405 active area with exact HUD.

Use `analyze_with(gm27_module, source, accepted_reference, ..., search_policy=...)`
when the caller already owns its frozen GM27 module. This returns Prepared with
that module's exact owner. `analyze_planes(...)` uses the exposed local `m`
module; encode its result with `m.encode_prepared`. No globals are patched.
Accepted parameters mirror frozen `analyze_planes`, with `search_policy` added.

Each policy examines 81 coarse maps: [-16,16] half-luma units in steps of four,
ordered by Manhattan length then y/x (zero wins exact ties). Coarse prediction
is integral in all three planes. Each plane samples coordinates starting at
(0,0) with the declared stride. It evaluates weighted absolute error (Y weight
one, U/V weight two), including partial edge blocks, with edge clamp. The
25-map half-unit refinement offsets [-2,2] surround each block's coarse vector.
It applies exact frozen integer bilinear arithmetic at sampled coordinates.
Strictly smaller costs replace the current choice. Output bounds remain ±18
half units. The optional global/penalty/integer/coarse policies are supported.

| Policy | Coarse stride | Refine stride | SAD samples per P | Reference reads per search P |
|---|---:|---:|---:|---:|
| frozen exhaustive | 1 | 1 | 54,950,400 | 93,830,400 |
| sample4 | 4 | 4 | 3,434,400 | 5,864,400 |
| sample2 | 2 | 2 | 13,737,600 | 23,457,600 |
| sample4_refine2 | 4 | 2 | 5,864,400 | 15,584,400 |

Counts describe logical executable samples/reads, not processor instructions.
Refinement pays all four taps even with zero weights; coarse pays one read.
Source fetches, candidate block costs and map-packing alternatives are reported.
Full final frozen prediction adds 2,073,600 reference reads per P, separately
reported as `prediction_reference_sample_fetches`. Every analysis retains and
counts the full prediction/raw coefficients/source; all three forward transforms
are paid. Key and zero-motion modes perform no SAD search. Final full predictor,
motion packing and transform costs remain paid for zero P frames.

The reproducible probe uses the first 12 frames of each retained scene and the
matched frozen v27 `unified_causal` accepted history. For each source it really
encodes and decodes exhaustive and all sampled candidates under the frozen
accepted background map, serializes each complete CP27 pair using the exact
accepted HUD packet, and saves packets. Candidate output is never used as a later
reference. The probe measures search tradeoffs; it is not a causal selection run.

| Policy | 24 complete packet bytes | Active MSE | Mean P analysis ms | Mean whole base encoding ms |
|---|---:|---:|---:|---:|
| exhaustive | 495,356 | 20.402196 | 597.14 | 592.56 |
| sample4 | 548,975 | 20.687495 | 118.22 | 157.18 |
| sample2 | 502,127 | 20.444976 | 312.45 | 331.57 |
| sample4_refine2 | 510,150 | 20.396342 | 190.48 | 221.02 |

All 96 candidate pairs fit 49,152 bytes, all decoded exactly to encoder output,
and HUD error counts are zero. Mixed `sample4_refine2` and `sample2` are the two
recommended profiles for the parent's full causal evaluation. Mixed saves 68.1%
of mean P analysis time at 2.99% more bytes and nearly equal aggregate MSE on
this limited fixed-history probe. `sample4` remains a cheap negative control.
Times are host Python measurements, not physical 30fps/ESP32/FPGA/RF evidence.

Run with `/home/lori/gamebub-streaming-prototype/.venv/bin/python`:

```
python -m unittest -v test_model > tests.log 2>&1
python benchmark.py > run.log 2>&1
python verify.py > verify.log 2>&1
```

`results.json` pins the benchmark implementation and frozen transitive source
files as observed before the run. `sourcepins.json` additionally pins this final
verifier/documentation, test/run logs, result and all candidate compressed objects
(excluding itself and the verifier's output log). The
verifier checks both pin sets, replays all saved candidates against accepted
packet references, checks exact image tags/metrics/counts/bounds/HUD, and
recomputes aggregate byte counts and MSE without running encoder search.
