# Tile predictor follow-up

MP01 compares two compact RGB565-index predictors with the earlier row-reset
DPCM: left prediction with above at the first column, and tile-local median
edge prediction (MED). Both retain bounded RAW/FILL/RLE/palette/old-DPCM modes
and select the new zero-run/Rice mode only when its complete payload is smaller.
All predictors reconstruct exactly the existing q2/q4 quantized image; this is
not a new quality advantage or hardware-speed result.

`med_codec.py` defines its versioned syntax, independent decoder, reset/escape
rules, padding, dimensions and CRC. `tests.log` records six passing tests,
including malformed valid-CRC packets, edges, quantizer endpoints, known
predictor values and bounded mutations.

## Reproduce

Use the existing [pinned Python environment](../python-codec-study/requirements.txt),
the paired Sunshine tools and the same project/media layout as the previous
study. `GAMEBUB_SUNSHINE_TOOLS` overrides the tools directory. The generator's
`MEDIA` constant identifies the local media directory; exact file/frame hashes
are in the result manifests. From this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_med_codec.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python jpeg_baseline.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
```

`jpeg-results.json` measures exact receiver-profile JPEG q35/50/65/80/90.
`results.json` measures four predictor profiles against its exact inputs;
all recaptured source hashes, PTS, canvases and active rectangles must agree.
The predictor driver verifies executed helper/input hashes before and after
the run. The final study-wide source snapshot is separately recorded in
`docs/prototype-v2-provenance.json`; it is not a fabricated start-of-run check
for the JPEG generator.

The corpus contains 60 native decoded frames starting at one second from each
of two precompressed Mass Effect clips, plus separate 30-frame windows starting
at four seconds. Input unique-image counts are 32/60 and 60/60 for the primary
windows, 21/30 and 30/30 for held-out windows. Adjacent windows from the same
two clips are limited held-out evidence, not broad game/capture coverage. No
frames are duplicated or interpolated. All inputs use the common BOX-scaled,
letterboxed 720×480 canvas. Source rates remain 25 and 29.88 fps.

## Result

Rates below project the native image sequence's measured sizes to hypothetical
30 fps, with 40 application +28 IPv4/UDP bytes per 1,024-byte chunk. RF,
link-layer, retries, input/audio and processing/queue delays are excluded.
Active PSNR pools MSE before converting to dB and compares RGB565-expanded
output against the common RGB canvas. It is not a perceptual/HUD acceptance
test. Python wall timings are reference-program costs, not FPGA/ESP32 timing.

| Window | q2 above, Mb/s | q2 MED, Mb/s | Same q2 output PSNR | MED q2 frames over 48 KiB |
| --- | ---: | ---: | ---: | ---: |
| Combat primary | 22.833 | 16.852 | 34.54 dB | 60/60 |
| Second clip primary | 20.056 | 16.182 | 35.55 dB | 60/60 |
| Combat held-out | 19.459 | 14.722 | 34.70 dB | 25/30 |
| Second clip held-out | 20.373 | 16.113 | 35.37 dB | 30/30 |

Against the original q2 row-reset DPCM, primary MED saves about 38–42% wire
bytes with identical reconstructed pixels. This is a useful predictor gain,
but receiver JPEG q65 is still only 6.812/4.137 Mb/s at 34.67/35.80 dB on
the same complete primary windows. MED therefore does not win the selection
gate against JPEG.

At q4 MED, the second clip fits 48 KiB on all primary/held-out frames, but
needs roughly 10.94/10.92 Mb/s and yields only 29.77/29.65 dB. Combat q4 MED
still overflows all 60 primary frames and 19/30 held-out frames. Storage
capacity and rate/quality remain separate failures. Nearest-JPEG-by-PSNR
fields name a discrete measured quality with an explicit PSNR difference;
they do not claim matched perceptual quality or interpolate an encoder result.

MED needs tile-local previous-row state, comparisons and addition; DSP use
is not established or necessary for this arithmetic. The separate
[fixed-transform study](../python-transform-study/README.md) evaluates a
multiply-intensive custom-codec direction. Keep existing JPEG as the control.
