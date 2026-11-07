# V98 measured comparison and decision

The common-input refresh completed **52 runs / 1,560 encode/decode round trips**.
Thirteen bounded unit tests and an independent 6,459-check integrity/arithmetic
audit pass. The audit recounts retained ledgers; it does not independently
re-decode every stream to recompute all source-pixel errors.
Four sequences contain 120 source frame identities, with 109 unique RGB hashes
when counted within their respective clips. Re-encoding a frame in thirteen
profiles does not add independent source coverage. The full benchmark took
90.19 seconds on this host, including verification, quality analysis, syntax
inspection and artifact writes; that duration is not a streaming FPS result.

## Inputs and controls

| Input, 30 selected frames each | Selected cadence | Unique RGB frames | Provenance |
|---|---:|---:|---|
| Earlier Mass Effect 2600 window | 29.88 fps | 30 | Existing H.264, 1280×720 source |
| Earlier combat window | 25 fps | 19 | Existing H.264, 512×288 source; repeats retained |
| Supplied Legendary Edition combat, 20 seconds | 30 fps | 30 | H.264, 1280×720 at 60 fps; every second native frame |
| Original motion/HUD/scene-cut fixture | 30 fps | 30 | Generated synthetic content; cut at frame 15 |

The new file's SHA-256 is
`fb01977e41e649bfb9fd53d1ee0e6db436127fb86e4b3b7ec303158e0568aff5`.
Its selected native timestamps are exactly 1/30 second apart. Game images
are aspect-fitted to a 720×405 active area with black bars on the 720×480 canvas.
The 512×288 source is enlarged; it supplies no additional native image detail.
Every method receives the exact same retained RGB arrays. All three game files
were already H.264-compressed, so the independent raw-gameplay gate remains open.

There are three HEVC CRFs (28/36/44), three AV1 CRFs (28/38/48), three JPEG
qscales (2/6/12), and four historical GM01 controls (uniform scales 8/16/32 and
global-motion scale 16). Parameter numbers are not common quality units.
All share the frozen GM01 YUV420 sample arithmetic and common inverse, followed
by RGB565 display quantization. The common conversion-only active-area PSNR
is 37.50 dB on the new sample and 34.60 dB on the synthetic sample; this floor
includes chroma reduction and RGB565, not just codec loss.

## New combat sample: complete elementary bytes and pixel quality

| Profile | Mbps at selected 30 fps | Active PSNR dB | Geometric ROI PSNR dB | Largest AU, bytes | AUs over 49,152 B |
|---|---:|---:|---:|---:|---:|
| HEVC CRF 28 | 0.738 | 34.14 | 32.25 | 17,173 | 0 |
| HEVC CRF 36 | 0.279 | 31.67 | 29.88 | 8,437 | 0 |
| HEVC CRF 44 | 0.115 | 28.65 | 26.72 | 4,763 | 0 |
| AV1 CRF 28 | 1.918 | 35.88 | 33.83 | 27,992 | 0 |
| AV1 CRF 38 | 0.900 | 34.68 | 32.85 | 16,406 | 0 |
| AV1 CRF 48 | 0.417 | 33.00 | 31.19 | 8,878 | 0 |
| JPEG q2 | 9.186 | 36.74 | 34.46 | 49,508 | 1 |
| JPEG q6 | 4.505 | 35.19 | 32.90 | 23,453 | 0 |
| JPEG q12 | 2.932 | 33.52 | 31.09 | 14,508 | 0 |
| Historical GM01 scale 8 | 10.055 | 35.29 | 32.60 | 57,210 | 8 |
| Historical GM01 scale 16 | 6.311 | 34.07 | 31.24 | 36,530 | 0 |
| Historical GM01 scale 32 | 3.788 | 32.33 | 29.41 | 21,635 | 0 |
| Historical GM01 global scale 16 | 6.782 | 33.66 | 30.81 | 41,255 | 0 |

Rates include every coded packet and extradata; they exclude transport overhead.
No cap-based dropping or silent quality adjustment is allowed in this comparison.
The 49,152-byte column is a diagnostic against the research cap, not a universal
JPEG/HEVC/AV1 limit or an assertion that these codecs can run on Game Bub.
JPEG q6 is a useful conservative sampled control; its observed maximum is not
a guarantee for other frames or a reason to remove runtime cap checking.

The frontier in [CSV](../../experiments/python-gamebub-v98/frontier.csv) and
[summary JSON](../../experiments/python-gamebub-v98/summary.json) minimizes bytes,
active MSE and ROI MSE separately for each source. Every tested GM01 point is
dominated on those three metrics in these four short sequences. This says
nothing about unmeasured decoder area/power, recovery, visual equivalence or
the latest CU66 quality. No BD-rate or matched-perceptual-quality superiority
is claimed from these coarse curves.

## Host cost and startup fences

These values are native x86_64 software/Python measurements on an AMD Ryzen 7
H 255, with serial controls and requested one-thread/low-parallelism encoders.
They are not ESP32 or FPGA timings. Frontend includes RGB conversion and plane
copy plus encode; backend includes packet decode/receive and canonical RGB
conversion. Both exclude RGB565 packing, transport, capture and display.

| New sample control | Frontend median ms | Backend min / median / max ms | First RGB output, ms after sequence start |
|---|---:|---:|---:|
| HEVC CRF 28 | 16.65 | 3.10 / 3.41 / 4.69 | 32.93 |
| AV1 CRF 38 | 14.38 | 2.45 / 3.04 / 4.03 | 38.91 |
| JPEG q6 | 7.02 | 2.60 / 2.76 / 2.97 | 10.08 |
| Historical GM01 scale 16 | 24.72 | 30.94 / 40.62 / 57.46 | Not instrumented with the same fence |

First-output fences begin immediately before input 0 conversion, after codec
contexts open; encode and decode occur in the same unpaced pass. Open costs
are recorded separately. Thus these startup times are not capture-to-display
latency. Thirty samples give only diagnostic extrema and nearest-rank p95,
not a validated production tail. Native standard-codec decode below 10 ms
does not establish under-10-ms complete FPGA decoding.

Every measured standard stream emits and decodes each frame during its matching
input call, with PTS equal to DTS, zero observed future-input lag and no
flush-only output. Emitted HEVC syntax has I/P slices, zero signaled reordering,
buffering-minus-one 2 and SAO disabled. AV1 emits key/inter displayed frames,
no show-existing frames, with CDEF/restoration availability enabled. JPEG is
8-bit baseline SOF0 with 4:2:0 sampling. Raw traces, consumed settings and
versions are retained. Reference-slot indices or signaled buffer limits are
not actual measured reference-memory allocations.

## Application-specific decisions

Keep JPEG as the existing hardware-facing intra control and HEVC/AV1 as software
rate/quality anchors. Do not promote historical GM01 as the new codec. Its
single immutable key and Python implementation differ from current CU66 mode,
reference, HUD and entropy paths. The missing fresh-input CU66 frontend is now
an explicit prerequisite for the next meaningful current-codec comparison.

The global-motion control produces identical packets/output to zero motion on
the two older windows. On the new sample it uses 847,707 bytes versus 788,874,
with lower active and ROI PSNR; on the synthetic fixture it also uses more bytes
with slightly worse scores. Do not turn it on unconditionally. A future
current-codec policy must price actual prediction/residual/metadata bytes and
quality, with the unmodified candidate available as fallback; encoder search
cost and decoder reference-memory service must remain separately charged.

The synthetic scene cut is included in worst-frame and temporal error records,
with the fixed key policy unchanged. Those diagnostics are not exhaustive
scene-change recovery, packet-loss or visual-artifact tests. ROI errors are
not a HUD readability test; two synthetic masks are interior probes that omit
the last drawn panel-border pixel.

Before closing V98: obtain original held-out 30-fps captures, connect and verify
the current CU66 fresh-RGB encoder, extend corpus duration and quality points,
and add HUD/temporal perceptual checks plus held-out tail calibration. Before
hardware promotion: complete the decoder/reference/HUD/shared-display joins,
validate unique-content 30 fps on target and separately validate full decoding
under 10 ms. V100–V110 continue to cover 7-series mapping, placement, routing
and timing with a frozen selected codec.
