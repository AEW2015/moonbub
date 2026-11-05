# V39 source qualification notes

This note records the source formation and usable timestamp windows for a
qualification run. It is not a new media encode or codec result. All candidates
are already-compressed Mass Effect footage from one walkthrough/source lineage;
new local windows are not new games, new captures, or project-wide unseen
content.

## Exact common input formation

The v24 native-input helper is
[`python-game-service-study/benchmark.py`](../experiments/python-game-service-study/benchmark.py)
(`native`). It opens the selected video stream with PyAV, decodes in stream
order, and keeps frames whose frame timestamp `Fraction(frame.pts) *
frame.time_base` is at or after the requested start time. V24 requests
`start=4`, `n=48` in
[`python-game-standard-v24-study/benchmark.py`](../experiments/python-game-standard-v24-study/benchmark.py)
(`source_inputs`). The selection means 48 decoded frames after the threshold,
not four seconds of output resampled to a target rate.

Each decoded frame becomes RGB24. The common transform is
[`corpus._letterbox`](../experiments/python-codec-study/corpus.py): aspect-fit
with Pillow `Image.Resampling.BOX`, center on a black 720×480 canvas, retain the
active rectangle, and do not duplicate or interpolate frames. For the 1280×720
clips this yields 720×405 active pixels, y=37 through y=441 inclusive; there
are 37 black rows above and 38 below. V24 then derives two common representations:

- `corpus.rgb565` truncates RGB to R5/G6/B5 and packs little-endian uint16 words.
  These are the `original_rgb565` metric/HUD source pixels on the **scaled
  720×480 canvas**.
- `fixed_codec.rgb_to_planes` converts that same RGB24 canvas with integer
  full-range BT.601 approximations: `Y=(77R+150G+29B+128)>>8`,
  `Cb=((-43R-85G+128B+128)>>8)+128`, and
  `Cr=((128R-107G-21B+128)>>8)+128`, clipped to 0..255. Cb/Cr are 2×2 box
  averages with `(+2)//4` rounding. It returns int16 planes shaped 720×480,
  360×240, 360×240; common YUV bytes are each plane cast to uint8 and
  concatenated. This exact buffer is used as the common encoder input and is
  SHA-256 bound in v24 results.

The v25 source-based studies reuse these retained v24 canvases and common YUV
planes. They do not perform another source decode, resize, or color conversion.
When comparing custom and native codec paths, feed both the same stored YUV
planes; score decoded output against the stored original RGB565 canvas with the
same exact HUD treatment.

## Media files and candidate windows

The files below were inspected with PyAV metadata and timestamp-only frame
enumeration; no encoding was run. The three short 1280×720 files report average
rate 747/25 (about 29.88 fps), time base 1/11952, and 12-second extracts. Their
container `stream.frames` values disagree with decoded counts (reported 440,
420 and 488 versus 360 decoded frames each). Do not use `stream.frames` or a
filename as a frame-rate or sample-count substitute. The combat file is
512×288, 25 fps, time base 1/25, and decodes 1,493 frames through 59.68 s.

| File | SHA-256 of current local file | Inspected decoded PTS/time span | Candidate qualification interval |
|---|---|---|---|
| `mass-effect-10000.mp4` | `5922669cd29b32407b1eb3d75e78a0bc2c851f388ba825e7e277dca6b00daa2d` | 360 frames, PTS 0–144400, 0–12.081660 s; one PTS gap reaches 0.100402 s | local PTS time `[6,10)` s |
| `mass-effect-4500.mp4` | `56221ded0e71335960195574f579ee7f82ed6c25e22736461824345d0687b23e` | 360 frames, PTS 0–143600, 0–12.014726 s; maximum observed gap 0.033467 s | local PTS time `[6,10)` s |
| `mass-effect-1600.mp4` | `41318d8042b44b56d441c19f698abf528f6549ea67b32744ab317b8d9fd505b4` | 360 frames, PTS 0–143600, 0–12.014726 s; maximum observed gap 0.033467 s | local PTS time `[6,10)` s, after documenting this file's origin |
| `mass-effect-combat.mp4` | `defff415bc1fdff6e18a70b0a0fbbddebb0429c5c0b8b5d5d04d8283bb315d3b` | 1,493 frames, PTS 0–1492, 0–59.68 s | local PTS time `[20,24)` s |

These intervals are candidate slices, not assertions of distinct scene content
or unseen qualification. The shared
[`media/SOURCES.md`](../../media/SOURCES.md) and
[`results/mass-effect-benchmark/source-manifest.json`](../../results/mass-effect-benchmark/source-manifest.json)
attribute the 4500 and 10000 extracts to approximate source positions 4500 s
and 10000 s in Noire Blue's precompressed Mass Effect (2007) walkthrough, each
stream-copied as a 12-second window. The 10000 clip has additional known use in
the FPGA gameplay study: its 90-frame near-30-Hz JPEG source starts at local
second 1 and spans about three seconds. The reviewed manifest does not list the
1600 or combat files, so their source provenance and extraction details should
be added to the qualification manifest rather than inferred from their names.

The combat file was used extensively in earlier codec and predictor studies.
It is useful as an additional content/geometry/cadence regression cohort, not
as new game evidence. The 4500/1600/10000 clips are also from the same walkthrough
as the established 2600/7200 clips; they widen scene coverage within that source
but do not establish independent-game generalization.

## PTS-based cohort selection and exclusions

Define each qualification window by a half-open media-time interval `[t0,t1)`.
For each decoded frame, retain its exact PTS, frame time base, rational
timestamp, decoded order, and hash of the post-letterbox RGB24 canvas. Include a
frame only if its timestamp satisfies `t0 <= PTS*time_base < t1`. Keep frames in
decoded stream order, preserve timestamp gaps, and report the selected PTS list
and observed deltas. Do not select “N frames at assumed 30 fps,” fill gaps,
interpolate, or silently deduplicate repeated pictures. If a frame has no PTS,
timestamps go backwards, or a gap exceeds the declared policy, split/reject the
segment explicitly. For rate projections, state the playback cadence separately
from the source PTS; 30 Hz byte arithmetic is not native 30-fps acquisition.

Before encoding, compute and freeze a manifest containing file SHA-256,
container/stream codec and dimensions, stream time base and average rate,
requested time interval, actual decoded PTS/time values, per-frame RGB24 hashes,
post-letterbox hashes, active rectangles, unique-image counts and the shared
RGB565/YUV hashes. Record PyAV/Pillow versions and the exact common transform
source hashes. Require the file SHA to match the intended qualification input;
a redownload, remux or different stream-copy is a different input even if its
filename matches.

Exclude the current AB38 calibration data: the first 12 frame IDs from the
`mass-effect-2600` and `mass-effect-7200` CS37 histories. In the frozen v24 source
manifest these histories start at PTS 48000 (timestamp 4.016064257 s), and IDs
0–11 end at PTS 52400 (4.384203481 s), time base 1/11952. Exclusion should be
checked using the actual stored source/frame hashes and PTS lineage, not only
scene labels. These two prefixes are calibration/training data for V38 and must
not reappear in a claimed held-out cohort.

Finally, check experiment inventories before using the words “held out” or
“unseen”: clips from this walkthrough, combat footage, and even later PTS ranges
have prior uses across this repository. Describe any new data honestly as a
new timestamp window or a new local cohort unless an inventory and provenance
audit establishes a stronger claim.
