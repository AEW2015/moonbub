# V37 follow-up: exact fixed-zero analysis without redundant four-tap prediction

The direct sender still called the frozen generic analyzer, whose zero motion
prediction uses four taps with zero interpolation weights. A diagnostic profile
identified that work; the timings below are a **new unprofiled paired campaign**,
not extrapolated from cProfile or obtained by subtracting profile samples.

This experiment constructs the owned frozen `Prepared` contract explicitly,
using frozen source/reference/identity/grid validation, the zero-vector estimator
and vector packer, frozen forward transform, and owned read-only source arrays.
It replaces only prediction with the already-qualified frozen taps28 predictor,
whose whole-zero-map path copies the reference. No old analyzer is called first,
no slow predictor work is paid and discarded, and no frozen globals are patched.

| Scene, 48 frames | Frozen direct sender | Same sender with exact zero-map analysis | Ratio | Time reduction |
| --- | ---: | ---: | ---: | ---: |
| Primary | 62.002376 ms | 46.128825 ms | 1.344× | 25.6015% |
| Complex | 73.459265 ms | 57.746688 ms | 1.272× | 21.3895% |

Each number is the mean of per-frame paired medians, with three alternating
paired repetitions for **every** frame. Both clocks include source/reference
validation and identity/tag checking, zero estimation/vector packing, prediction,
three forward transforms, owned immutable source retention, and the same frozen
direct CN36 sender's quantization/RDO/unmasked reversion planning, entropy,
inverse, normalization and wrapper. Key frames create the same128 prediction.

Fixture/HUD reads or generation, precompiled geometry initialization, archive I/O,
hashes/metrics/equality checks, receiver, network, queueing and display are outside
the paired clocks. Actual causal receiver output supplies each next reference.
These timing groups are separate from the earlier direct-vs-proof campaign;
**do not multiply ratios or subtract measurements across campaigns**.

## Exact output and preparation proof

All96 actual CN36 packets are byte-identical to the frozen direct-v37 and v36
skip packets. Complete budgets remain441,520 /1,060,332 bytes with maxima22,569 /
41,224; active MSE remains14.38366067 /26.54469598. No compression or quality
change is claimed.

The API is deliberately bounded:

```python
analyze_planes(source, reference, *, epoch=25, frame_id=0,
               reference_id=NO_REF, block_size=32, motion_mode='zero',
               penalty=0, motion_precision='half') -> frozen_owned_Prepared
```

Other geometry, epoch, motion modes, precision, penalty or block size are rejected.
The returned source, prediction and raw transform arrays are read-only, and
source/prediction do not alias caller source/reference arrays. Frozen ownership
identity is preserved so the same direct sender accepts the preparation.

Three focused producer tests cover key/P preparation equality, frozen owner and
immutable copies, invalid identity/geometry/policy/sample inputs without source
mutation, caller mutation after preparation, and behavioral scoped mocks forbidding
both old analyzer and old four-tap predictor calls.

The independent replay imports no new analyzer or sender. It checks all96 actual
packets and causal normalized references through frozen decoding, and separately
recomputes the frozen original preparation for every accepted reference. Hashes
of full prediction planes, raw coefficients and retained source must match exactly.
It also reconstructs all paired timing medians, scene means and ratios. Focused
independent tests and verification logs are retained.

## Limits

This is an explicit fixed-zero profile; it does not replace a searched-motion
analyzer or qualify a new motion policy. The input windows are reused short Mass
Effect clips, not held-out gameplay. Even after the exact optimization, measured
Python sender service exceeds33.33 ms before receiver, transport and display.
No physical30fps, native ESP32/FPGA timing or HEVC/AV1 compression advantage follows.
The separate implicit-coefficient grammar has not been combined with this sender.

```sh
cd experiments/python-game-analysis-v37-study
python -m unittest -v test_model
python -m unittest -v test_verify
python verify.py
```

Producer/source pins freeze the actual timed implementation. Independent replay
files and all retained evidence are bound by the outer v37 portable inventory.
