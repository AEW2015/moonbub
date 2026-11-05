# V40 fresh low-delay native quality grid

This study freshly encodes and decodes all457 source-v40 frames at48 sampled
points: four scenes ×two codecs ×six parameters. It uses the frozen v24 reference
codec configuration: single-thread x265 ultrafast atCRF20/24/28/32/36/40 and
SVT-AV1 preset8 atCRF28/34/40/46/52/58, low delay, zero B/lookahead and key24.
These are sampled settings, not an optimal standards encode or GPU test.

All5484 actual AUs decode independently with matching PTS/DTS, key IDs,
immediate outputs, source hashes and RGB565 metrics. Every source frame is the
same archived post-BOX canvas/common integer YUV used by CS37/CS38. The same
actual lossless HX33 is overlaid and charged per frame, with80 modeled binding
bytes and extradata once. Native binding is byte accounting, not a custom-protocol
implementation. Five sampled points have at least one over-cap complete frame;
all failed quality/cap points are retained rather than silently discarded.

`results.json` retains actual AU/extradata objects, encoder/decoder call logs,
all per-frame quality/hash/PTS/cap fields, complete budgets and source-code pins.
The independent verifier imports only the frozen native decoder/arithmetic, never
calls encode, and rechecks all5484 AUs against source pixels and actual HUD.
No new codec unit-test count is attributed to this extended frozen-code grid.

The v40 comparison selects the smallest of the SIX tested settings meeting each
explicit quality gate (mean, mean+peak, or every-frame source MSE), while requiring
all complete frames to fit. It performs no rate/MSE interpolation and reports no
BD-rate, perceptual equivalence, equal FPGA resources or optimal parameter result.
If a gate has no feasible sampled point, that absence remains explicit.

Source25/29.88-Hz cadence and PTS gaps remain metadata. Encoding uses nominal30-Hz
frame IDs as the prior references do; these are not30-distinct-frame acquisition
or measured capture/display claims. Wall encode+decode clocks and library call
timings are host diagnostics, not a complete Sunshine/Moonbub/ESP32/FPGA service.
Actual HUD generation is separately costly and shared by both custom/native
hybrid paths, as recorded in control-qual-v40.

```sh
cd experiments/python-game-native-qual-v40-study
python verify.py
```

`benchmark.py --resume` can continue an interrupted grid from stored completed
points after source-pin checks. The verification path requires no source video
download; archived RGB24 canvases and frozen manifests suffice.
