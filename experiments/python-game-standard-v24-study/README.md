# V24: HEVC/AV1 versus the current custom Gamebub codec

HEVC and AV1 encode these retained game windows much more efficiently than the
current custom video base. When all methods also carry the **same exact HUD**,
the observed native hybrid points use about **1.91–2.04× fewer complete body bytes**
while meeting or beating the custom profile's measured MSE. This is a comparison
of actual sampled operating points, not matched-quality BD-rate or hardware fit.

These are native host CPU reference encoders/decoders. No HEVC/AV1 decoder,
Sunshine endpoint or FPGA bitstream has been installed on Gamebub by this study.

## Same source and color contract

The campaign uses the exact v23 windows: 48 frames beginning at four seconds in
each of `mass-effect-2600.mp4` and `mass-effect-7200.mp4`, for 96 unique acquired
source images. They are previously compressed 29.88-fps footage, not fresh live
30-fps capture. Every canvas is BOX-letterboxed to **720×480 coded /720×405 active**
with identical RGB source hashes to v23. The hypothetical codec clock is 30 IDs/s.

All native encoders receive the frozen custom `rgb_to_planes` eight-bit YUV420
samples. Native decoded YUV samples use that same frozen `planes_to_rgb` function
and RGB565 quantization. Metrics compare active expanded-RGB565 channels against
the original source RGB565 canvas. This avoids attributing a different RGB/YUV
conversion or chroma-upsample floor to compression.

The no-compression color roundtrip has active mean MSE3.6707 /9.9603 (2600/7200),
or3.4120 /8.0475 with exact HUD overlay. This is a diagnostic reference, not a
proven theoretical RD lower bound. Retained original words **and** common input
YUV planes allow all floor and quality metrics to be rederived without media.

## Actual low-delay native settings

- HEVC: libx265, ultrafast/zerolatency, requested one reference, zero B frames and
  lookahead, one frame thread, no pools/WPP, fixed key interval24 and scenecut off.
  Requested quality values20/28/32/36/44 are retained for both windows.
- AV1: SVT-AV1v4.2.0, preset8, PSNR tune, requested low-delay prediction,
  lookahead0, temporal filter off, parallelism level1 and fixed key interval24.
  Requested quality values20/28/38/48/56 are retained. Its startup log reports
  low-delay **CQP** handling of the requested quality number; do not assume CRF
  behavior equivalent to x265.
- PyAV19.0.2 exposes the installed libraries; a host `ffmpeg` executable is not
  required. HEVC decode uses FFmpeg `hevc`; AV1 decode uses `libdav1d`.

All20 streams have48 packets with PTS=DTS0…47, key IDs0/24, one packet emitted
on each input call and no packets/frames returned only at flush. Both decoded
formats report eight-bit planar420/full-range. These observations do not prove
zero internal latency or the hardware decoder's supported syntax/reference count.
Consumed encoder options and requested reference limits are not a substitute
for a complete syntax audit before a constrained standards decoder port.

Primary option references: [x265 low-latency presets](https://x265.readthedocs.io/en/master/presets.html),
[x265 CLI options](https://x265.readthedocs.io/en/master/cli.html), and
[FFmpeg codec options](https://ffmpeg.org/ffmpeg-codecs.html).

## The exact-HUD comparison

Bare native HEVC/AV1 output is lossy in the HUD. It cannot be compared with the
custom profile's exact HUD guarantee using bitrate alone. The hybrid comparison
decodes each actual retained HC22 sequence, overlays its four exact patches over
each native decoded image, and counts those real sidecar bytes plus57 bytes of
hypothetical pair binding. All selected hybrid points below fit49,152 bytes/frame.

| Window /method | Body Mb/s at 30 IDs/s | Active RGB565-channel MSE | Exact HUD |
| --- | ---: | ---: | --- |
| 2600 custom adaptive |4.5998 |14.4290 |Yes |
| 2600 HEVC q32 +same HUD |2.3350 |11.2109 |Yes |
| 2600 AV1 q48 +same HUD |2.2535 |12.2482 |Yes |
| 7200 custom adaptive |10.2872 |30.0839 |Yes |
| 7200 HEVC q32 +same HUD |5.3778 |29.7453 |Yes |
| 7200 AV1 q48 +same HUD |5.2800 |29.5866 |Yes |

These native points are the lowest-byte **sampled** choices meeting the custom
hybrid MSE threshold. Their qualities are not exactly matched, and numerical q
values are not equivalent across codec families. On the primary window, HEVC's
point has lower MSE than AV1's while using slightly more bytes; this is not a
universal AV1-over-HEVC ranking. Actual full curves, fixed-map controls and source
error sums remain in `results.json`.

The hybrid is real Python composition of two actually decoded components, but
it is **not a CP23-compatible native endpoint**: CP23 currently expects AR03 as
its video base. Binding/control/framing for a future standards+HUD profile is
explicit prospective accounting. The constant extra HUD/body cost dominates much
of the resulting bitrate, so its roughly2× complete improvement is much smaller
than pure video-base byte ratios.

For the selected HEVCq32 /AV1q48 points, projected forward IPv4/UDP+fragment/control
rates are 2.5472 /2.4605Mb/s (2600) and 5.8176 /5.7128Mb/s (7200). The corresponding
custom rates are 4.9804 and 11.0919Mb/s. This assumes1008-byte chunks,75 forward
overhead bytes/chunk, two64-byte FG19 forward controls, three reverse controls,
one57-byte PC18 per chunk and one134+28-byte joint ACK. This transport is not
implemented for the native standard base. Wi-Fi airtime, queries/retries, capture,
input and audio are excluded.

At quality20 the complex HEVC/AV1 hybrids fit only 46/48 complete frames; complex
AV1q28 also fits46/48. Those high-quality points are retained, not silently
truncated or reported as a valid49,152-byte profile. Every bare native access unit fits
the cap; the maximum is47,754 bytes. A cap fit is not a bandwidth/latency guarantee.

## Pure video-base comparison is a different contract

The custom bare column below strips HUD and binding but retains its AR03 headers.
Native bare bytes include elementary packets and encoder extradata. No UDP/mux/
feedback is included in the following body rates.

| Window /method | Bare body Mb/s at 30 | Active MSE | HUD behavior |
| --- | ---: | ---: | --- |
| 2600 custom adaptive base |2.4463 |15.0605 |Lossy |
| 2600 HEVC q32 |0.1815 |12.3022 |Lossy |
| 2600 AV1 q48 |0.1000 |13.5251 |Lossy |
| 7200 custom adaptive base |5.3666 |33.3149 |Lossy |
| 7200 HEVC q32 |0.4572 |34.3580 |Lossy; slightly worse MSE |
| 7200 AV1 q48 |0.3594 |33.9340 |Lossy; slightly worse MSE |

The complex q32/q48 bare native points are close but worse in MSE than custom;
they must not be labeled matched or at-least quality. Lower-quality-parameter
observed points meeting that bare threshold are HEVCq28 at 0.7057Mb/s /MSE25.6998
and AV1q38 at 0.6799Mb/s /MSE22.8784. The JSON's operating-point selector separately
records each quality threshold and the nearest sampled point. Its
`sampled_quality_range_covers_target` is only coverage by the min/max sampled MSE,
not proof of monotonicity, adjacent bracketing or an interpolated BD-rate.

All methods have key IDs0/24, but their prediction/reference policies differ.
The custom path uses explicit ACKed reference-bank updates/promotions; standards
use their native reconstructed-reference tools. The gap cannot be attributed to
one specific standard tool without additional ablation experiments. It motivates
testing bounded motion compensation, skip/copy and reference updates in the
custom format while keeping decoder complexity measurable.

## Evidence, CPU scope and limitations

There are **960 actual native outputs** across 20 native profiles, each independently
redecoded from retained elementary packet/extradata blobs. The verifier recomputes
1,920 bare/hybrid metric records,192 actual custom reference outputs and 192
color-roundtrip checks without external video. Native hybrid tests compare
20,275,200 exact HUD words; bare native outputs collectively differ in 12,745,777
HUD words. All frame IDs, key flags, timing metadata, decoded hashes and encoded
source hashes are retained. Seven unit tests cover common-plane padding, malformed
layouts/domains, metric/overlay correctness, bounds/accounting and actual native
HEVC/AV1 association/immediate emission.

Per-call encoder/decoder/plane-wrapper/display-conversion CPU costs are retained
separately in JSON; startup and flush are explicit. These are host software
component timings on one run. Comparing optimized native libraries with Python
custom encoder timings is not a fair implementation-speed ranking. No native
host capture, RF transport, ESP32 cycle/heap/QSPI model, hardware standards decoder,
FPGA resource/timing/BRAM/DSP fit or physical 30 fps proof is supplied.

## Reproduction

From this directory, using the project Python environment with NumPy/Pillow/PyAV
and the listed native libraries:

```sh
python -m unittest -v test_model.py
python verify.py
```

`verify.py` needs retained objects and frozen local sources, not media. Regenerating
`benchmark.py` additionally requires both clips via `GAMEBUB_MEDIA_DIR` (or the
existing project media directory). It pins all executed helpers and frozen v23
references. Do not change pinned sources during a campaign. No old source,
installed application or board state is changed by this comparison.
