# Transform-aligned opaque HUD source masking

This study replaces only complete aligned 8×8 Y/Cb/Cr transform blocks whose
entire reconstructed RGB support lies inside the union of the four exact fixed
opaque HUD rectangles. The `core8` policy stores 128 in each safe block;
`luma8` applies the same rule to Y only. No decoder syntax changes.

The frozen chroma upsampler reads the current sample at even output positions
and averages the current and right/below samples at odd positions, clamping at
the final row/column. `model.py` independently enumerates these scalar reads to
find each sample's support. A chroma block beginning at `(x,y)` away from the
canvas boundary influences RGB from `(2x−1,2y−1)` through
`(2(x+7)+1,2(y+7)+1)`, inclusive. Checking only the doubled block rectangle is
unsafe. Integral coverage over the exact rectangle union admits a block only
when every influenced RGB pixel is covered. Odd rectangles, overlapping or
adjacent rectangles, clipped support at canvas edges, and partial plane blocks
are handled explicitly. Partial 8×8 plane blocks are preserved.

For the fixed HUD this masks 256 Y blocks and 19 blocks on each chroma plane:
18,816 constant stores/frame (16,384 Y and2,432 chroma). The input arrays stay
unchanged; the returned planes are owned copies. They occupy 1,036,800 bytes in
the actual int16 source representation, or 518,400 logical uint8 bytes. Coverage
and integral arrays are temporary host working storage; these figures are not
RSS measurements. Masking adds no decoder picture/state allocation and does
not skip decoder processing of the covered pixels.

All 96 original sources pass exact RGB8 equality outside the HUD and exact
RGB565 equality after the original exact HUD overlays. Scalar dependency tests
independently enumerate every RGB pixel for every candidate tile in a small
fixture and check both accepted and rejected blocks. Tests cover the rectangle
union, odd bounds, partial edges, clamping, luma-only operation, ownership and
invalid inputs. A corrupt inner HX33 with repaired outer digest/CRC cannot
publish the masked base or change receiver state.

The RAW causal experiment gives each scene its own accepted masked decoded
reference history. It uses unchanged shared zero/half32 incumbent and strict
band encoders, background 16 then 32, keys 0/24, actual GM27/CP34/HX33 packets,
and actual JA34 ACKs. All 376 trials are serialized, archived and replayed.
Every selected complete packet fits 49,152 bytes. Source formation before lossy
coding is visibly exact, but altered transform data and accepted references
can still change visible reconstruction quality.

| 48-frame scene | Original same-HX33 control bytes | RAW core8 bytes | Saving | Original MSE | RAW core8 MSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| `mass-effect-2600` |441,224|422,312|18,912 (4.29%)|14.386886|14.391345|
| `mass-effect-7200` |1,068,678|1,036,928|31,750 (2.97%)|26.303889|26.349431|

The MSE regressions are 0.0310% and 0.1731%; this RAW policy does not establish
quality-preserving savings. Maximum complete packets are 22,484 and 41,155 bytes.
The comparison uses the frozen root controller-v34 `control` packets, which
carry exactly the same HX33 and 60-byte binding. Every metric uses the original
RGB source after exact HUD; a masked source is never the quality target.

The twelve native comparisons use the exact frozen standard-v24 PyAV options
and the same original or core8 input. Every actual AU is retained and charged,
extradata is charged once at frame 0, and each frame also includes the same
actual HX33 and 60-byte binding cost. Both requested processed brackets are
retained, including settings that do not meet RAW core8 quality.

| Scene | Codec | Parameter | Input | Accounted bytes | Original-source MSE |
| --- | --- | ---: | --- | ---: | ---: |
|2600|HEVC/libx265|32|original|238,738|11.210939|
|2600|HEVC/libx265|28|core8|257,577|9.023268|
|2600|HEVC/libx265|32|core8|239,507|11.356621|
|2600|AV1/libsvtav1|48|original|222,451|12.248229|
|2600|AV1/libsvtav1|38|core8|236,731|8.911405|
|2600|AV1/libsvtav1|48|core8|222,648|12.471908|
|7200|HEVC/libx265|28|original|606,532|22.161878|
|7200|HEVC/libx265|28|core8|608,246|21.799157|
|7200|HEVC/libx265|32|core8|557,890|29.658332|
|7200|AV1/libsvtav1|38|original|601,387|19.767521|
|7200|AV1/libsvtav1|38|core8|596,944|20.025998|
|7200|AV1/libsvtav1|48|core8|535,308|29.885062|

At the scene anchors, both same-core8 native codecs have lower accounted byte
cost and lower error than RAW custom. Core8 does not uniformly improve the
native encoders. The weaker 7200 HEVC32/AV148 settings have worse quality than
RAW custom. This is a finite settings comparison, with no bitrate-parity or
universal codec-superiority claim. The native binding is cost accounting,
not a CP34 native packet format or a Gamebub HEVC/AV1 decoder implementation.

All 576 native AUs have PTS/DTS 0..47, keys 0/24, one AU emitted in each input
call, and one decoder output immediately for each AU. No packets or frames
appear only at flush. The archives retain AUs, extradata, encoder options,
library versions, call-level encode/decode/display timings, output hashes,
and original-source metrics. `verify.py` decodes the retained AUs again.

The measured custom policy means are 227.11/320.52 ms per frame, covering all
paid analysis, shared candidate encoding, quality and binding. Preparation,
fixture conversion and exact source-equivalence proofs are separately recorded
per call (means 20.70/22.07 ms); those preparation measurements also read fixtures
and prove equality, so they are not just mask cost. `offline_mask_cost.json`
records a separate mask-only postcampaign sample per source, including
validation, scalar dependency derivation, rectangle coverage, copies/stores.
Native source preparation is likewise separately recorded. These host clocks
exclude preencoded HX33, archive IO, network, display and hardware execution.
No native-FPS, end-to-end 30fps, FPGA fit, clock closure or physical memory
claim follows from this experiment.

Run from this directory using the repository's configured virtualenv:

```
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest discover -s . -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

`results.json` pins all actual producer sources and the frozen input/control
artifacts. The parent commit is c50df93e313c9402c3741e5f6c921ee40e6f10a3.
Only this study directory is modified. The root's guarded experiment uses the
same frozen `mask_source(..., policy='core8')` API on a separate causal history;
its results are reported separately.
