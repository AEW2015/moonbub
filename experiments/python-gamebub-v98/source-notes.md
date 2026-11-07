# V98 common input corpus

`sources/manifest.json` describes the four shared inputs. Every NPZ has one
array only: `rgb`, with dtype `uint8` and shape `[30, 480, 720, 3]`. The
per-frame SHA-256 values hash contiguous RGB bytes; each NPZ SHA-256 hashes the
complete file. `active_rect` uses `(x, y, width, height)` coordinates.

## Game video inputs

`mass-effect-2600` and `mass-effect-combat` use the local video files
`/home/lori/gamebub-streaming-prototype/media/mass-effect-2600.mp4` and
`mass-effect-combat.mp4`. These are decoded source-video windows, not raw
gameplay captures. The local source hashes, source frame rates, stream time
bases, and each selected frame's original PTS/time base are in the manifest.
The selected frames are the first 30 decoded frames with timestamps at or after
1 second. There is no cadence conversion, interpolation, or deliberate frame
duplication. Repeated decoded RGB frames, if present in an input source, remain
in sequence; `unique_rgb_count` reports that fact (the combat window has 19
unique RGB frames among 30 selected frames).

Frames are converted to RGB and aspect-fit to 720x480 with Pillow BOX
resampling over a black canvas. The selected game inputs have a 720x405 active
rectangle at `[0, 37, 720, 405]`. Their generic geometric probe rectangles are
`[16, 48, 192, 80]` and `[160, 352, 400, 80]`; no HUD semantics or gameplay
meaning are verified. Existing source-codec artifacts are part of the decoded
source and are not represented as raw capture quality.

`mass-effect-legendary-combat-20s` uses the user-supplied
`/home/lori/Downloads/YTDown.com_YouTube_Media__luGrl_3Ajc_Mass-Effect-Legendary-Edition-Combat_004_720p.mp4`
and selects 30 frames by decimating the native frames at or after 20 seconds. The
source is H.264, 1280x720, 60/1 fps, with a 1/15360 time base and reported
stream duration 132.25 seconds (7935 frames). A visual preview at 20 seconds
shows active combat gameplay with HUD elements rather than a title or black
segment. Every second decoded source frame is selected, yielding a 30/1 fps
input by decimation only; each selected frame retains its original PTS and no
interpolation or duplicate scheduling is used. The manifest records the source
SHA-256, source/selected rates, decimation factor, and exact selected PTS
values. It is decoded source video, not a raw gameplay capture.

The two earlier source videos are windows from Noire Blue's [Mass Effect (2007)
walkthrough](https://www.youtube.com/watch?v=Z8v7xCIGoQA), as noted in
[`media/SOURCES.md`](/home/lori/gamebub-streaming-prototype/media/SOURCES.md).
The supplied Legendary Edition file has separate user-provided provenance;
its publisher is not inferred from the earlier files. No media was downloaded
or modified for this corpus.

## Synthetic input

`synthetic-motion-hud-cut` is an original deterministic NumPy/Pillow fixture,
not captured gameplay or source video. It contains 30 frames at exactly 30/1
fps, with moving geometry, changing texture, legible text and drawn HUD-like
elements. Frame 15 is a hard visual scene cut. Its HUD ROI rectangles are
explicitly defined by the generator and therefore describe synthetic elements
only. It uses the full 720x480 canvas as its active rectangle.

## Rebuilding

Run `source_prepare.py` with the project virtual environment:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python \
  experiments/python-gamebub-v98/source_prepare.py \
  --user-source /home/lori/Downloads/YTDown.com_YouTube_Media__luGrl_3Ajc_Mass-Effect-Legendary-Edition-Combat_004_720p.mp4
```

The manifest records the preparation script SHA-256, Python, PyAV, FFmpeg
library, NumPy, and Pillow versions used for the generated files. Rebuilding
requires the two shared media files and, when rebuilding all four inputs, the
optional user video passed with `--user-source`. Synthetic frames use
Pillow's default bitmap font; library versions are recorded because rendered
glyph pixels are part of the frame hashes.
