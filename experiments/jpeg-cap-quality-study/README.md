# q90/q80 cap retry image-quality study

Offline image-quality comparison for the same 1,493-frame local
`media/mass-effect-combat.mp4` clip used by the adjacent cap-size study. It
uses Sunshine's existing `host.clip_frames` and `host.canvas` to sample native
25 fps and build the 720×480 canvas, and calls the sender's existing
`msv1.encode_receiver_jpeg` function directly at q90 and q80. It never creates
a sender session or transmits packets.

For every canvas, the script measures RGB PSNR between the decoded JPEG and
the same 720×480 RGB canvas before encoding. It reports fixed-q90 theoretical
quality, q90 frames that fit the 49,152-byte (48 KiB) JPEG cap under drop-only,
fixed q80 quality, and the selected output from q90 followed by one q80 retry
only when q90 exceeds the cap. The retry policy drops only if q80 also exceeds
the cap. Oversized q90 images remain in the theoretical q90 distribution but
are excluded from the drop-only sent-frame PSNR distribution.

PSNR describes pixel error against an already-compressed 512×288 H.264 source
that is upscaled into the Sunshine canvas. It includes the black letterbox and
is not a perceptual metric. The source's limited resolution and compression,
short combat scene, and repeated in-game visual conditions limit how well it
represents direct gameplay. No visual acceptability threshold is asserted.
The JPEG cap excludes MSV1 headers, network transport and receiver memory use.
These measurements do not establish real-time encoding, frame delivery,
receiver behavior, display presentation or gameplay visual acceptance.

Reproduce from the prototype root using its Python environment:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python \\
  repos/moonbub-30fps-study/experiments/jpeg-cap-quality-study/measure.py
```

`per-frame.csv` contains per-frame sizes, PSNRs and selected policy output;
`results.json` and `SUMMARY.md` contain aggregate distributions and caveats.

Run focused math, threshold, and generated-result consistency checks with:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest \
  repos/moonbub-30fps-study/experiments/jpeg-cap-quality-study/test_measure.py
```

## Second clip at 29.88 fps

`mass-effect-29_88/` preserves a separate study of `media/mass-effect-2600.mp4`
(1280×720, native average rate 747/25 fps, 360 decoded frames). It measures
the sender JPEG encoder at q75/q80/q85/q90, 48 KiB overflow, sequential offline
encode time, and a q90 then same-frame q80 retry policy. No retry was needed in
this particular clip. Results are intentionally separate from the 25 fps,
512×288 combat clip above; they are not pooled or treated as representative
gameplay. The source remains a short compressed prerecorded segment.

Reproduce and test from the prototype root:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python \
  repos/moonbub-30fps-study/experiments/jpeg-cap-quality-study/mass-effect-29_88/measure.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest \
  repos/moonbub-30fps-study/experiments/jpeg-cap-quality-study/mass-effect-29_88/test_measure.py
```
