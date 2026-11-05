# V32 wider-motion feasibility probe

This component tests whether GM27's ±18 half-luma-vector limit (±9 luma pixels)
is restricting prediction. It is a **non-causal matched-reference probe**, not a
new implemented streaming format. Each trial uses the current source and the
actual previously accepted v30 strict reconstructed reference. Neither narrow
nor wide trial output becomes a later reference.

## Search and arithmetic

The baseline recomputes v29 adaptive-zero2 block32 prediction on those references.
It is not the original v30 complete controller decision: this probe always tests
the block predictor rather than selecting between zero and searched candidates.

The wide search keeps the same current-source weighted sampled-MAE quiet gate
at threshold 2. Active blocks score 289 coarse vectors, each component from
−64 to +64 half-luma units in steps of 8, followed by 81 refinements in
−4…+4 units. Final vectors are bounded at ±68 half-luma units (±34 luma pixels).
Stride-4 coarse and stride-2 refinement scores retain full-resolution final
prediction, quantization and reconstruction. Two extra map scores compare the
wide result and existing narrow incumbent on the same stride-2 points; narrow
wins ties. Their cost is paid, and sampled SAD cannot increase against that
incumbent. This is not a full-source quality guarantee.

The arithmetic-only predictor reuses the frozen interpolation core after explicit
shape/type/±68 validation. Public GM27 validators are unchanged and still reject
vectors beyond ±18. Full interpolation uses the existing luma/chroma denominators,
floor division, separately clamped coordinates and one final rounding. Tests
check the wider negative/positive boundaries against scalar interpolation.

Both candidates execute actual fixed-Q14 residual transforms, quantization and
legacy original/pruned choices. Wide residual planes are actually encoded with
the existing minimum legacy/EC26 format, decoded again and reconstructed. There
is **no serialized valid wide GM27 frame**, new negotiated decoder limit, atomic
receiver or hardware implementation in this experiment.

## Results on 12 sources per window

| Window | Narrow residual bytes | Wide residual bytes | Narrow active RGB MSE | Wide active RGB MSE |
| --- | ---: | ---: | ---: | ---: |
| 2600 | 64,898 | 64,220 | 14.411132 | 14.395347 |
| 7200 | 163,007 | 160,612 | 26.377120 | 26.327146 |

Actual residual bytes fall **1.04% / 1.47%**. Wide decisions exceed the old limit
in **114/3,795 (3.00%)** primary P blocks and **153/3,795 (4.03%)** complex P
blocks. When the unchanged key frame is excluded, full-source P-frame YUV
prediction SSE falls **1.50% / 25.01%**. The larger complex prediction improvement
does not translate into equally large serialized residual savings.

The wide MV syntax has not been implemented. A deliberately conservative
hypothetical budget uses one mode byte plus two raw bytes per block: **691 bytes
per P frame**, versus actual narrow compressed-map totals of 1,529 / 2,597 bytes
across the 11 P frames. Reserving the same 80-byte frame header, actual current
HU25 bytes and 60-byte composition binding gives:

| Window | Narrow complete-body budget | Wide hypothetical raw-MV body budget |
| --- | ---: | ---: |
| 2600 | 152,292 | 157,686 |
| 7200 | 355,962 | 358,571 |

That grows body bytes **3.54% / 0.73%**. These hypothetical totals are neither
accepted CP27 packets nor a new profiled/cap-controlled stream. A compressed
wide-vector syntax could reduce the conservative penalty, but is not measured
here. Do not label residual-only savings as an end-to-end compression gain.

Mean baseline source work is **101.56 / 139.56 ms**. Combined incumbent plus
wide work is **253.92 / 411.93 ms**, including **83.31 / 182.44 ms** of incremental
wide search. The wide experiment depends on the incumbent and pays its analysis,
encoding and metric work; it does not treat narrow search as free. Final residual
stages also include actual serialization and coefficient decode checks. Source
acquisition, preencoded HUD generation, archives and later accepted-reference
debug replay are outside these clocks. These are host Python timings, not native
ESP32, FPGA, RF/QSPI, memory service or physical 30 fps measurements.

## Interpretation

The old motion limit misses some useful larger movement, especially in the
complex P-frame prediction errors. However, only a small fraction of blocks
choose wide vectors, residual byte savings remain small, and raw vector overhead
can erase them. Wider bounds alone do not close the HEVC/AV1 gap or establish
whole-stream superiority. A new profile would also need a correct larger-window
reference-memory/cache design and explicit bounds/capacity validation.

The next useful test is a bounded compressed wide-vector mode with actual packet
serialization/parser validation, causal reconstructed-reference histories and
source-quality admission, followed by a real memory/bandwidth budget. Preserve
narrow mode as a fallback and compare all overheads. This probe does not warrant
silently changing GM27's decoder limits.

## Verification

```sh
python -m unittest discover -s experiments/python-game-wide-motion-v32-study -v
python experiments/python-game-wide-motion-v32-study/verify.py
```

Four tests cover narrow-math equivalence, scalar wider-coordinate/edge rounding,
quiet-map behavior, malformed vector domains, sampled-incumbent non-regression
and exact candidate counts. Retained replay checks all 24 sources, 72 actual
residual planes, selected vectors/search operation counts, current-reference
identity, full predictions, source metrics, plane packet hashes and all declared
budgets/work accounting. It explicitly checks rejection by the old GM27
validator for out-of-limit maps and reports zero valid serialized wide frames.
