# V40 checkpoint: additional-scene qualification and fresh standards anchors

This checkpoint qualifies the unchanged AB38/CS38 coefficient syntax on 457
additional causal frames. It saves 10.2732% of complete bytes against its matched
CS37 control without changing reconstructed pixels. Fresh HEVC/AV1 anchors remain
substantially smaller on the three walkthrough cohorts at sampled comparable
quality. This is an intermediate checkpoint of the six-hour run, not a physical
30 fps, FPGA fit, or standards-superiority result.

## Additional source windows and exact qualification

[Source bundle](../experiments/python-game-source-v40-study/README.md) stores 457
unique RGB24 canvases selected by actual timestamps from four Mass Effect clips.
Three walkthrough variants contribute 119 frames each and combat contributes 100.
Their image hashes do not overlap the 12-frame AB38 calibration prefixes. These
are related, precompressed same-game sources, not independent games or native
30-fps captures. Combat is 25-fps, low-resolution footage upscaled into the fixed
720×480 canvas; all original PTS, gaps and formation metadata remain recorded.

The [causal control](../experiments/python-game-control-qual-v40-study/README.md)
accepts all 457 frames, including 20 periodic keys, at ROI8/background16. No retry,
background32 fallback or rejection occurs. The separate
[key cap probe](../experiments/python-game-key-cap-v40-study/README.md) retains both
quantization choices for the four initial keys; its eight successful packets do
not prove that every future frame fits.

[Arithmetic qualification](../experiments/python-game-binary-qual-v40-study/README.md)
retains all 2,742 actual full/compact arithmetic alternatives. Every selected
packet preserves source bindings, exact HUD words, full normalized reference,
future causal state and displayed RGB565 against CS37. All 1,371 selected planes
use arithmetic syntax; no old coefficient fallback is needed.

| Cohort | CS37 bytes | CS38 bytes | Saving | Largest CS38 packet |
| --- | ---: | ---: | ---: | ---: |
| Walkthrough 10000 | 2,279,340 | 2,062,089 | 9.5313% | 27,063 |
| Walkthrough 4500 | 2,679,319 | 2,424,218 | 9.5211% | 38,504 |
| Walkthrough 1600 | 584,524 | 465,031 | 20.4428% | 16,249 |
| Combat | 3,321,646 | 3,002,785 | 9.5995% | 44,032 |
| Total | 8,864,829 | 7,954,123 | 10.2732% | 44,032 |

The largest control packet is 48,540 bytes; CS38 reduces the maximum to 44,032,
leaving 5,120 bytes under the 49,152-byte complete-frame cap. These byte counts
include actual HUD, maps, entropy termination, wrappers and checksums. The cap is
an explicit protocol/test constraint, not a newly measured BRAM capacity.

## Fresh HEVC/AV1 comparison

The [native grid](../experiments/python-game-native-qual-v40-study/README.md)
encodes and independently redecodes 5,484 actual access units across 48 points:
four cohorts × two codecs × six quality settings. Both encoders receive the same
frozen full-range YUV420 and the same actual exact-HUD overlay bytes as the custom
path. Original RGB565 pixels define error. Keys are every 24 frames, B frames and
lookahead are disabled, and actual immediate encode/decode output is checked.
All settings and all cap failures are retained.

Complete native accounting charges actual access units, actual HUD, extradata
once and 80 modeled binding bytes. It is a byte budget, not an implemented native
Gamebub transport. Native CPU decoders do not establish FPGA feasibility.

[Comparison JSON](prototype-v40-comparison.json) selects only among measured
settings. Its separate gates require (1) mean MSE, (2) mean plus peak-frame MSE,
or (3) every individual frame's SSE to be no worse than custom; each also requires
zero complete-frame cap failures. There is no interpolation or BD-rate claim.

| Cohort | Custom complete bytes | Best sampled HEVC, mean-MSE gate | Best sampled AV1, mean-MSE gate |
| --- | ---: | ---: | ---: |
| 10000 | 2,062,089 | 1,122,621 | 1,066,933 |
| 4500 | 2,424,218 | 1,299,688 | 1,227,015 |
| 1600 | 465,031 | 225,293 | 186,681 |
| Combat | 3,002,785 | None in coarse grid | None in coarse grid |

Combat's coarse-grid gap is not a custom win: high-quality native points exceed
the packet cap while coarser points exceed custom mean MSE. A subsequent targeted
peak-rate-control study is testing whether native VBV/CBR controls close that gap.
The coarse grid is neither exhaustive nor an optimal standards encoder search.

## Exact spatial experiments and host cost

The [exact-output spatial pilot](../experiments/python-game-exact-v40-study/README.md)
requires all 64 samples of every reconstructed block to equal its mode0 control,
then applies a strict actual-complete-byte guard. This preserves future references
by induction and rejects equal-error-but-different-pixel substitutions. All 27
candidate packets lose to control, despite 34,695 eligible nonzero alternatives.
Seven focused tests pass; independent replay recomputes 1,686,096 block proposals,
162 rank trials and 27 old byte-identical controls. There is no compression gain
from this local proxy to deploy.

Control qualification pays HUD generation as well as integrated base encoding.
HUD generation alone totals 29.42 / 31.85 / 13.06 / 25.71 seconds across the four
cohorts and dominates this Python pipeline. Arithmetic candidate-only costs are
107.08 / 132.32 / 33.31 / 189.92 ms per frame, with old CS37 generation externally
paid. Neither component clock proves a complete sender frame rate. The existing
arithmetic receiver adapter also stages full arrays and re-encodes frozen syntax;
it is a correctness oracle, not a target streaming decoder.

The next implementation priorities are an exact-byte, winner-only HUD encoder;
a direct bounded arithmetic receiver; actual whole-plane rate-aware spatial
choices; and native peak-rate controls before interpreting packet-cap advantages.
Each needs independent replay before hardware handoff. No firmware or bitstream
is changed by this checkpoint.
