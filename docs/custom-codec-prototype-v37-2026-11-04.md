# V37: exact sender optimization and implicit hidden-block grammar

V37 removes redundant proof work from the CN36 sender and implements actual
implicit hidden-block syntax as a separate CS37 research profile. The direct
CN36 sender uses **30.04% / 38.17% less time in the paired fixed-policy workload**,
with all 102 tested packets byte-identical to v36. CS37 further reduces complete
bytes by **1.5050% / 0.2775%**, with exact causal reference and display equality.
It is a separately measured transcoder, not combined with those sender clocks.
A further integrated zero-motion analyzer optimization measures 46.13 / 57.75 ms
per sender decision in its own paired campaign, with unchanged CN36 bytes.

Neither result establishes physical 30 fps or HEVC/AV1 superiority. Resolution
remains 720×480 coded / 720×405 active with 21,120 exact RGB565 HUD words and a
49,152-byte complete frame cap. Both short Mass Effect windows are reused;
directed motion probes are not held-out gameplay.

## Direct sender: preserve decisions, remove redundant serialization

[Direct implementation and verification](../experiments/python-game-direct-v37-study/README.md).
The v36 proof sender encoded a complete full packet, reparsed coefficients,
re-encoded hidden-zero residuals and reconstructed another output. V37 instead
emits the chosen skip packet directly. It retains original quantization, RDO and
the unmasked plane-global legacy size/reversion decisions before zeroing hidden
coefficients. Moving suppression earlier could alter a visible coefficient via
a changed whole-plane rate decision.

It then constructs three chosen entropy components, performs one final output
reconstruction, applies the precompiled v36 mask plan and emits CN36 framing.
No discarded full packet, coefficient parser or extra final reconstruction is
needed. Original forward transforms and inverse work inside RDO remain paid;
"one final reconstruction" is not a claim of one inverse call in the sender.

| 48-frame scene | Equivalent one-output proof sender | Direct sender | Time reduction |
| --- | ---: | ---: | ---: |
| Primary | 88.401518ms | 61.847014ms | 30.0385% |
| Complex | 119.159953ms | 73.675718ms | 38.1707% |

Values are means of per-frame paired medians: three alternating pairs on every
frame. Both scopes include fresh source analysis, forward transforms, quantize,
RDO, required unmasked planning, entropy, reconstruction, normalization and one
wrapped skip output. Fixture/HUD reads or generation, verification, archive I/O,
receiver, queueing, transport and display are outside these sender clocks.
Compiled-plan setup is once outside the per-frame clock.

The proof baseline fairly produces **one skip output**; it excludes the unused
full-output normalization and wrapper charged by the published v36 two-output
experiment. These timings must not be substituted into the old two-output table.
The six-frame fractional-motion prefix also preserves exact wire bytes; its
paired means are 133.610669→85.985486 ms, not representative searched-motion FPS.

All96 main packets plus six fractional-motion packets are byte-identical to v36,
including full causal normalized references, displayed images, HUD, qmaps,
vectors and coefficient values. Three producer and three independent tests pass.
A scoped behavioral test forbids full packet encoding and coefficient parsing.
The corpus takes no original global-RDO reversion branch, so a directed test
forces all three plane reversions and checks exact proof parity and restoration.
That post-timing test-only strengthening is disclosed in source metadata; the
timed implementation and numerical results were unchanged.

## Diagnostic profile: identify remaining work

The [six-frame profile](prototype-v37-sender-profile.json) instruments actual
causal complex-scene sends, verifies every output byte against the archive and
records function-level work. cProfile changes runtime; its 0.4952 s total is
diagnostic, not another uninstrumented sender measurement.

The old host predictor consumes 0.0764 s self / 0.0885 s cumulative despite zero
vectors. Thirty-three inverse calls remain across six sends: final output work
plus RDO reconstruction. Frozen entropy encoding consumes 0.1202 s cumulative;
Rice counting/emission and string formatting also appear in the hottest calls.
Cumulative times overlap and must not be added into a partition of total time.

This identifies two exactness-preserving directions: integrate the existing
tap-aware predictor into host analysis, and replace Python entropy/cost loops
with measured native code. The analyzer integration is measured below.

## Integrated analyzer: actual additional sender improvement

[Analyzer experiment](../experiments/python-game-analysis-v37-study/README.md)
constructs the same owned `Prepared` state explicitly using frozen source and
reference validation, zero-vector estimation, vector serialization and forward
transforms. For zero motion it uses the already-verified v28 copy predictor
instead of the generic four-tap implementation. It never calls the old analyzer
or runs a slow prediction first, and does not patch frozen globals.

| 48-frame scene | Paired direct sender with old analysis | Sender with exact fast analysis | Time reduction |
| --- | ---: | ---: | ---: |
| Primary | 62.002376ms | 46.128825ms | 25.6015% |
| Complex | 73.459265ms | 57.746688ms | 21.3895% |

Every frame has three alternating pairs, including analysis through one CN36
output. The source/HUD fixture, checks, archive, receiver and network/display
exclusions remain explicit. The direct baseline is freshly measured here; do
not multiply this campaign's ratio by the earlier campaign's sender ratio.

All96 packets reproduce the retained direct sender exactly. The independent
verifier recomputes the original frozen analysis against each actual causal
reference and checks 288 prediction/raw-coefficient/retained-source hashes.
Three producer and three independent tests pass, including ownership after
source mutation, rejected inputs and scoped proof that old analyze/predict are
never called. The new analyzer is explicitly restricted to the fixed zero-motion,
720×480, block32, half-pixel/epoch25 policy. It is not generalized searched-motion
acceleration, and its dataset does not include an additional fractional-motion
campaign. Both measured means still exceed 33.33 ms before receiver or transport.

## Implicit CS37 grammar: measured additional bytes

[Implicit implementation](../experiments/python-game-implicit-v37-study/README.md)
adds inner residual dispatch 4. It transmits only nonhidden 8×8 blocks in raster
order, entropy-coded at logical width 1. A bound fixed opaque profile determines
missing positions; the decoder restores zeros without a bitmap or block indices.

Every plane also retains the old full-grid representation as a fallback. Its
ordinary dispatch 0..3 needs no added prefix. Compact dispatch 4 pays an extra
byte, and must be strictly smaller to win; ties keep the old representation.
Visible-block reflow changes entropy prediction, so omitting 3.63% of samples is
not treated as a proportional byte saving.

| 48-frame scene | CN36 skip bytes | CS37 actual complete bytes | Additional saving | Saving vs matched fixed legacy |
| --- | ---: | ---: | ---: | ---: |
| Primary | 441,520 | 434,875 | 1.5050% | 5.5461% |
| Complex | 1,060,332 | 1,057,390 | 0.2775% | 4.4537% |

All102 actual CS37 packets, including the fractional-motion probe, are no larger
than their CN36 inputs and preserve entire normalized references, coefficients,
HUD and displayed pixels exactly. The independent decoder imports no new
encoder and re-evaluates all 306 compact alternatives with frozen entropy
primitives to verify the exact winner/fallback/tie policy. Across all packets,
227 plane payloads use implicit syntax. Four producer and three independent
semantic-corruption tests pass, including wrong tags and invalid dispatch with
no modeled publication.

Active MSE stays 14.383661 / 26.544696 and complete maxima 22,569 / 41,224 bytes.
Nominal complete rates at 30 decisions/s are 2.174375 / 5.286950 Mbps. These are byte
arithmetic, not measured transport or display rates. The six-frame motion probe
saves 1.4489%, separately from the two gameplay totals.

CS37 outer and GS37 inner magic plus a new profile digest identify changed
syntax. The outer wrapper remains 80 bytes; bitmap cost is zero. Geometry,
reference/output tags, exact HUD rectangles, CRCs and semantic decode precede
modeled publication. This needs a new negotiated receiver and is not an unchanged
CN36/CP34 firmware mode, a new ACK protocol or a hardware fence proof.

The proof starts from **already encoded CN36 skip**. Transcode medians average
19.85 / 36.98 ms, including original packet parsing, compact entropy construction,
fallback selection and sealing. Input encoding is externally paid. These clocks
must not be added/subtracted from the separate direct-sender experiment to claim
an integrated pipeline. Python expands arrays and still runs existing inverse
reconstruction; FPGA implicit inverse bypass is proposed, not implemented.

## HEVC/AV1 gap: improve prediction and residuals next

[Deterministic accounting](prototype-v37-comparison.json) uses the verified,
frozen original-input v36 anchors. **No fresh native encode or decode was run in
v37.** Exact CS37 output parity preserves the same source metrics. All budgets
include the same actual HX33, 80 binding bytes per frame and native extradata once.
The native 80-byte binding is modeled accounting, not CS37 syntax support.

| Scene / method | Complete budget bytes | Active MSE |
| --- | ---: | ---: |
| Primary CS37 | 434,875 | 14.383661 |
| Primary HEVC q32 | 239,698 | 11.210939 |
| Primary AV1 q48 | 223,411 | 12.248229 |
| Complex CS37 | 1,057,390 | 26.544696 |
| Complex HEVC q28 | 607,492 | 22.161878 |
| Complex AV1 q38 | 602,347 | 19.767521 |

All four native points remain smaller at lower mean MSE. These are sampled
points, not matched-quality BD-rate, optimal standard encoding, perceptual
equivalence or equal hardware resources. We have not beaten HEVC/AV1.

Stripping the identical HUD and 80-byte bindings makes the actual video coding
gap clearer:

| Remaining codec bytes, including codec headers/extradata | CS37 | HEVC | AV1 |
| --- | ---: | ---: | ---: |
| Primary | 231,469 | 36,292 | 20,005 |
| Complex | 591,030 | 141,132 | 135,987 |

The custom remainder is 4.19–11.57× the sampled standard remainder while its
quality is worse. This is a byte-component comparison, not matched-quality
BD-rate. HUD/header-only optimizations cannot close it. The next compression
study should prioritize causal block prediction, residual modeling and spatial
prediction modes that a bounded FPGA decoder can implement, with fair native
source/HUD treatment and original-source/temporal quality gates.

## Deployment direction and remaining gates

1. Combine implicit syntax with the direct coefficient path so no paid packet
   parse or discarded entropy serialization is needed. Measure complete sender
   service again; do not multiply independently measured speedups.
2. Extend fixed-policy equality into real searched motion and a matched old
   reference-policy control. Preserve hidden/visible support semantics and add
   longer held-out pans, cuts and dynamic HUD geometry before choosing a default.
3. Prototype bounded host-selected inter/SKIP/copy and spatial predictors with
   actual residual packets. Require visible/temporal quality and full-byte
   improvements beyond the current HUD-dominated totals; retain losing points.
4. Port the exact host analysis/entropy hot paths to native code and measure
   sender tails against the 33.33 ms budget. FPGA work must include entropy,
   inverse/prediction, reference memory arbitration, reset and publication fences.
5. Qualify actual ESP32 transport, DMA/copies, Wi-Fi contention/retry and QSPI
   flow control separately. A smaller packet or host optimization does not prove
   gateway throughput, FPGA fit or physical 30 fps.

[Deployment gates](v37-next-deployment-gates.md) retain these distinctions.
JPEG, v20 and all prior frozen studies remain unchanged. No firmware, bitstream
or physical hardware was modified in this iteration.

## Reproduction

```sh
python experiments/verify_prototype_v37.py
```

The manifest freezes v36 dependencies except the two mutable indexes, all new
actual packets, producer code/source hashes, focused test logs, independent
replays, comparison accounting and the instrumented profile. Numerical timings
are retained measurements; replay proves data and causality rather than repeating
the benchmark speed. There are 19 focused passing tests and 300 archived frame
cases across direct 102, implicit 102 and analyzer 96 causal frame decodes.
These reuse the same retained content; the profile's six sends are duplicate
diagnostic checks, not additional gameplay evidence. The independent grammar
replay also checks 306 compact entropy alternatives; analysis replay checks 288
prepared-array hashes. All counts are retained in the manifest and replay summary.
