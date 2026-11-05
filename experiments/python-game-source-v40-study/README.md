# V40 PTS-selected source qualification bundle

This directory freezes PTS-selected input canvases for later codec qualification.
It does not encode video, run native codec comparisons, or select quality/rate
points. For each media frame in the declared half-open PTS interval, it archives
only the post-letterbox RGB24 canvas. RGB565 and common YUV420 are re-derived by
the verifier and retained as per-frame SHA-256 values, avoiding duplicate plane
archives.

## Selected inputs

| Media file | PTS interval in local clip time | Frame cap | Current media SHA-256 |
|---|---:|---:|---|
| `mass-effect-10000.mp4` | `[6,10)` seconds | 144 | `5922669cd29b32407b1eb3d75e78a0bc2c851f388ba825e7e277dca6b00daa2d` |
| `mass-effect-4500.mp4` | `[6,10)` seconds | 144 | `56221ded0e71335960195574f579ee7f82ed6c25e22736461824345d0687b23e` |
| `mass-effect-1600.mp4` | `[6,10)` seconds | 144 | `41318d8042b44b56d441c19f698abf528f6549ea67b32744ab317b8d9fd505b4` |
| `mass-effect-combat.mp4` | `[20,24)` seconds | 144 | `defff415bc1fdff6e18a70b0a0fbbddebb0429c5c0b8b5d5d04d8283bb315d3b` |

The first three extracts are 1280×720 H.264 at average rate 747/25 with 1/11952
time base; decoded PTS gaps are preserved. `mass-effect-combat.mp4` is 512×288
H.264 at 25 fps and 1/25 time base. PyAV's reported `stream.frames` differs
from decoded frame counts for the short extracts. `prepare.py` therefore walks
actual decoded frames and selects by rational `frame.pts * frame.time_base`,
never by assumed frame count or converted FPS.

Common source formation follows the frozen v24 path: decode RGB24; call
`corpus._letterbox` with Pillow BOX into 720×480; then derive original packed
RGB565 with `corpus.rgb565` and YUV420 with the frozen
`python-transform-study/fixed_codec.py::rgb_to_planes`. For 16:9 inputs the
active rectangle is `[0,37,720,405]`; the canvas has 37 upper and 38 lower
letterbox rows. Source pixels, timestamps, and transform implementation hashes
are recorded in `manifest.json`.

These are local timestamp cohorts from previously compressed Mass Effect footage
in one walkthrough lineage. The 10000 extract already appears in a separate
FPGA JPEG replay starting at local second 1. The combat clip has extensive prior
codec-study use. The shared provenance manifest does not list the 1600 or combat
files; their source origin should be recorded before any stronger provenance
claim. The V38 calibration prefixes from the first 12 frames of the v24
`mass-effect-2600` and `mass-effect-7200` cases are explicitly hash-compared and
excluded from the selected media. This bundle makes no project-wide unseen-data
claim.

## Reproduce and verify

From the repository root, with the existing environment:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-source-v40-study/prepare.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-source-v40-study/verify.py
```

`prepare.py` checks each original media SHA before and after decoding and refuses
more than 144 actual frames per clip. It archives RGB24 canvases as bounded
content-addressed zlib objects. The independent offline `verify.py` reads no
encoder: it checks source pins, media hashes, object bounds/digests, PTS ordering
and intervals, active geometry, RGB565/YUV derivation hashes, counts, and overlap
against the frozen V24 calibration hashes. `prepare.log` and `verify.log` retain
the run outputs. `manifest.json` keeps external media hashes in a separate field
from repository-relative source-code pins.
