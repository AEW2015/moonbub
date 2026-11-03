# Same-source HEVC / AV1 references for the custom Game Bub codec

The custom codec is not yet close to the tested HEVC/AV1 coding efficiency on
these short samples. This experiment measures the gap instead of inferring it
from shared transform/prediction vocabulary. It supplies **native CPU reference
encodes/decodes**, not a Game Bub HEVC/AV1 decoder, hardware resource estimate,
latency result or sustained30fps proof.

## Inputs and two explicit color paths

Each of two precompressed Mass Effect clips supplies60 native frames from1second,
BOX-letterboxed into720×480 with720×405 active content. Every codec/profile gets
identical RGB captures and key IDs0/30. GM01 has uniform16, ROI8/background16 and
ROI8/background32 profiles. HEVC uses libx265 quality parameters28/36/44; AV1 uses
SVT-AV1 parameters28/38/48. CRF/quality numbers are not equivalent across codecs.

`results.json` first uses PyAV default RGB/YUV420 conversion for native codecs,
compared to unchanged GM01 integer conversion. `color-floor.json` measures the
no-compression round trips: second-clip active PSNR is35.19dB for PyAV defaults
versus37.48dB for GM integer arithmetic. That difference must not be attributed
solely to compression.

The preferred follow-up, `common-color-results.json`, feeds **GM01's frozen YUV420
sample planes to every native encoder**, extracts decoded sample planes and uses
GM01's same display RGB conversion. All outputs are then quantized RGB565 before
area-weighted MSE/PSNR against original RGB888. Common color arithmetic removes
that particular confound; it does not equate codec reference structures, loss
recovery, memory traffic or decoder complexity. GM records are reused from the
pinned first campaign, not encoded/decoded a second time.

## Common-color rate/distortion points

|Source/profile|Coded Mb/s at hypothetical30IDs/s|Active PSNR|Declared-region PSNR|
|---|---:|---:|---:|
|Combat GM01 ROI8/bg16|2.1126|34.02dB|35.74dB|
|Combat HEVC q36|0.2074|35.90dB|36.39dB|
|Combat AV1 q48|0.1312|36.52dB|37.24dB|
|Second GM01 ROI8/bg16|2.8861|35.20dB|36.24dB|
|Second HEVC q28|0.1985|36.59dB|36.61dB|
|Second AV1 q38|0.1212|36.57dB|36.47dB|

These selected native points use roughly10–24× fewer coded bits while scoring
higher in both measured regions. **That is a comparison of recorded operating
points, not a matched-quality BD-rate, universal codec gap or visual-quality
claim.** All18 points in each campaign remain in JSON, including points with
lower regional quality. Source pictures and codec settings are pinned.

The first clip has only32 distinct RGB hashes among60 inputs; the second has60.
Both are related, precompressed25/29.88fps footage rather than native30fps live
captures. Repeated content particularly favors reference/skip coding. Do not
extrapolate these ratios to particle-heavy Elden Ring gameplay, uncompressed
captures or broad game coverage. No subjective HUD readability test was performed.

## What the native configuration does and does not prove

HEVC uses x265 ultrafast/zerolatency, no B-frame/lookahead path, one frame thread,
no pool/WPP and key interval30. AV1 uses SVT-AV1 v4.2.0, preset8, PSNR tune,
requested low-delay prediction, zero extra lookahead and disabled temporal filter,
with parallelism level1. Its log reports low-delay CQP handling of the requested
quality value. Actual options, effective startup logs and packet PTS/DTS are saved.
Native decode uses FFmpeg HEVC or libdav1d. No original native codec was installed
or reconfigured on the Windows Sunshine machine.

Both campaigns recover every source ID with PTS=DTS, keys0/30 and no packets
returned only at flush. That does not establish zero internal queueing or real
stream latency. Initial-campaign per-call CPU times exclude capture/network/
reference-memory/display and differ fundamentally from Python GM01 costs.
The common-color supplement deliberately makes no timing claim.

Rate counts elementary packet bytes and encoder extradata. GM01 includes its own
headers/CRC; native formats have their own syntax overhead. UDP, muxing, QSPI,
FEC and feedback are excluded. Native access units fitting49KiB do not establish
a target streaming buffer or reset/recovery contract. The standards keep their
own reconstructed references; GM01's immediate-ACK immutable-key policy differs.

## Implication for the application-specific codec

The near-term direction is a custom subset, borrowing useful concepts rather
than combining incompatible HEVC and AV1 bitstreams. Prototype bounded host-side
block motion and explicit skip/copy decisions before adding decoder complexity.
Keep exact reference identity and physical read lifetime in the protocol. Combine
that temporal base with selective HR01/HP01 UI regions only after their new wrapper
is integrated and the complete frame/deadline budget is measured.

Full HEVC or AV1 transmission requires a matching standards decoder. Neither
exists in the current Game Bub custom path, and this study does not quantify its
fit in the target FPGA or ESP32. Similar coding primitives are not compatibility.

## Reproduce and evidence

Use the recorded Python3.14.4 / PyAV19.0.2 / NumPy2.5.4 / Pillow13.0.0 environment.
PyAV must include libx265, libsvtav1, HEVC decode and libdav1d; the host's `ffmpeg`
executable is not required. From this directory:

```sh
python -m unittest -v
python benchmark.py
python color_floor.py
python common_color.py
python verify.py
```

Five tests check native roundtrip frame association, coded-byte accounting,
full-range plane copies including padded rows, unsupported layout rejection and
invalid inputs. Main campaign18×60 gives1,080 actual codec outputs, including720
native and360 GM. The common-color follow-up adds720 native outputs and reuses
360 GM records: **1,800 actual codec outputs across both campaigns**, not2,160.
The240 no-compression color outputs are separate probes. Results pin executed
sources, input/packet/output hashes, returned frame IDs and runtime library versions.
`verify.py` reads stored evidence and recomputes source equality, pooled metrics,
key IDs, byte accounting and reuse; it does not rerun encoding or prove hardware.

Primary background references: [HEVC recommendation](https://www.itu.int/rec/t-rec-h.265),
[AOM AV1 tool description](https://aomedia.org/docs/AV1_ToolDescription_v11-clean.pdf),
[x265 low-latency options](https://x265.readthedocs.io/en/stable/presets.html), and
[SVT-AV1 parameters](https://gitlab.com/AOMediaCodec/SVT-AV1/-/raw/master/Docs/Parameters.md).
