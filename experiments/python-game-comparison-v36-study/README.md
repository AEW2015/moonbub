# V36 standards comparison: retained original-input anchors

`compare.py` redecodes the four original-input HEVC/AV1 anchors from v35 and
checks every output hash, original-source active MSE, ordered PTS/DTS, key0/24,
immediate decode output, actual AU lengths, exact HUD bytes and once-only
extradata. These192 AUs are replayed here; **no fresh native encode was run**.

CN36 receives the original common YUV input. Its new reference normalization
happens inside its codec; this is different from giving only one codec a masked
source. The standards anchors receive the same original common YUV source and
same exact HUD. Both budgets below charge80 binding bytes/frame. This adds20
bytes/frame to the old native budget and is explicit modeled accounting, not a
native CN36 implementation or an actual new native wire packet.

| Window / method | Complete budget bytes | Active MSE |
| --- | ---: | ---: |
| Primary CN36 skip | 441,520 | 14.383661 |
| Primary HEVC q32 | 239,698 | 11.210939 |
| Primary AV1 q48 | 223,411 | 12.248229 |
| Complex CN36 skip | 1,060,332 | 26.544696 |
| Complex HEVC q28 | 607,492 | 22.161878 |
| Complex AV1 q38 | 602,347 | 19.767521 |

All native points fit the49,152-byte complete frame cap. Each sampled native
point is smaller and has lower mean MSE than CN36 skip on the same scene.
This is a four-point comparison, not matched-quality BD-rate or proof of optimal
standards settings, perceptual superiority or equivalent FPGA resources.
The custom same-profile exact skip benefit is useful but does not close this gap.

```sh
cd experiments/python-game-comparison-v36-study
python verify.py
```

The deterministic check replays the native decoders and compares its regenerated
evidence with `results.json`. All inputs, retained packets and code are pinned in
the v36 portable inventory. No device timing or physical30fps is implied.
