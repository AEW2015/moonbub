# Iteration 24: HEVC/AV1 comparison, owned lazy analysis and recovery

The comparison now uses actual low-delay HEVC and AV1 software encodes on the
same **720×480 coded /720×405 active** source frames as v23. Both standards need
substantially fewer coded bytes than our custom base on these clips. Adding the
same exact HUD protection narrows the complete-body gap to roughly **1.9–2.0×**
at the selected measured quality points. No standards decoder has been fitted
to Gamebub by this study.
All **42 tests pass**: 7 standards, 16 owned-source, 11 recovery and 8 independent
audit tests. Retained native/custom decodes and offline evidence checks pass.

## Same exact HUD: the main comparison

Each entry uses all 48 frames from its source window and preserves the same
21,120 original RGB565 HUD words per frame. MSE is expanded-RGB565 channel error
over the 720×405 active area, with lower values better. Body rates project the
actual coded counts to 30 IDs/s and exclude network overhead.

| Window | Method | Body Mb/s at 30 | Active MSE | Fits49,152 B complete budget |
| --- | --- | ---: | ---: | ---: |
| 2600 |Custom CP23 adaptive |4.5998 |14.4290 |48/48 |
| 2600 |HEVC x265 q32 +exact HUD |2.3350 |11.2109 |48/48 |
| 2600 |AV1 SVT q48 +exact HUD |2.2535 |12.2482 |48/48 |
| 7200 |Custom CP23 adaptive |10.2872 |30.0839 |48/48 |
| 7200 |HEVC x265 q32 +exact HUD |5.3778 |29.7453 |48/48 |
| 7200 |AV1 SVT q48 +exact HUD |5.2800 |29.5866 |48/48 |

These are actual sampled operating points meeting or improving the custom mean
MSE threshold. They are **not identical-quality encodes, equivalent CRF values,
BD-rate or perceptual equivalence**. In the complex scene the selected HEVC/AV1
points are close in MSE; AV1 uses about 1.8% fewer body bytes than that HEVC point.
That limited observation does not rank every encoder/preset/workload.

Standards-hybrid body accounting includes each actual native access unit,
extradata once, the actual v23 HC22 sidecar and a reserved57-byte binding cost.
The pixels are actually decoded and overlaid. The standards+HUD envelope is a
**prospective integration budget**, not a standards-compatible CP23 packet: the
current CP23 decoder accepts AR03 bases, not HEVC/AV1. The custom counts are real
complete CP23 bytes. Any native standards transport needs its own negotiated
parser/reference/ACK contract and may add metadata.

## Bare codec versus exact-pixel UI cost

Without the exact HUD sidecar, standards coding is much smaller, but its HUD
pixels are lossy. At sampled base-quality thresholds the byte gap against the
custom base is about 7.6–24.5× depending on source and operating point. This must
not be presented as the complete exact-HUD streaming gain.

The actual exact-HUD sidecars alone project to 2.1398/4.9069 Mb/s for 2600/7200.
They account for roughly 91–95% of the selected standards-hybrid body rates. That
explains why improving the base codec cannot deliver the bare-codec bandwidth
gain while these full exact rectangles remain unchanged.

For example, on 7200 HEVC q32 alone is0.4572 Mb/s and AV1 q48 alone0.3594 Mb/s,
but their bare MSE34.3580/33.9340 is slightly worse than the custom bare
base33.3149. These two bare points therefore do not meet that base-quality
threshold. The sampled selector instead chooses HEVC q28 or AV1 q38 for the
at-least-quality bare comparison. Overlaying exact HUD words changes the metric
and accounts for most of the hybrid body rate.

Exact RGB565 mismatch counts establish lossless-region compliance, not visual
unreadability: a one-bit word difference still counts as a mismatch. These short
regression windows do not establish HUD readability, flicker or broad game quality.

## Native method and retained evidence

- 96 source acquisitions:48 frames at 4 seconds in each existing
  `mass-effect-2600.mp4` and `mass-effect-7200.mp4`, BOX-letterboxed identically
  to v23. Footage is precompressed29.88 fps, not fresh live30 fps capture.
- All encoders consume the **same frozen GM integer YUV420 sample planes** and
  use the same frozen YUV-to-RGB conversion and final RGB565 quantization.
  Retained original RGB565 canvases and input YUV planes support offline
  quality/color-floor checks. Original RGB888 is linked by v23 input hashes;
  regeneration from media is needed to independently reconstruct those original
  RGB888 canvases, rather than infer their low bits from RGB565.
- HEVC uses libx265 ultrafast/zerolatency and requested one-thread/no-pool/no-WPP,
  no-B-frame/no-lookahead operation. AV1 uses SVT-AV1 preset8, low-delay prediction,
  zero requested extra lookahead and temporal filtering disabled. Requested and
  effective options/logs are retained. These settings do not prove a restricted
  syntax or small FPGA-decoder subset. See the
  [x265 preset documentation](https://x265.readthedocs.io/en/master/presets.html)
  and [FFmpeg encoder documentation](https://ffmpeg.org/ffmpeg-codecs.html).
- 20 actual native cases /960 decoded pictures;192 custom reference outputs and
  192 no-compression color-roundtrip checks. HEVC samples20/28/32/36/44;
  AV1 samples20/28/38/48/56. Quality numbers are encoder-specific.
- All retained streams have actual key IDs0/24, PTS=DTS, one-to-one decoded source
  association and no packets produced only at flush. Per-call emissions and
  encoder/decoder CPU times are recorded. This does not prove zero internal
  queueing or end-to-end streaming latency.
- Standards maintain their own reconstructed reference histories and were decoded
  with complete reliable delivery. Loss, deadline and reference-publication policy
  were not matched to CP23's acknowledged-bank model.
- All960 bare/hybrid pairs are redecoded offline;20,275,200 hybrid HUD words match
  exactly. The 20-case bare streams have12,745,777 HUD-word mismatches. Actual
  bitstreams/extradata, source word canvases, common planes and HC22 packets
  occupy about 27.17MB of retained objects. Decode images are regenerated rather
  than stored once per quality point.

All raw native access units fit49,152 bytes in this campaign. Some higher-quality
complex hybrids do not: HEVC q20 and AV1 q20/q28 each fit46/48 after exact HUD and
binding costs. Selected table points all fit. A fixed quality number is not an
instantaneous complete-frame cap controller or a sustained-rate guarantee.

The hypothetical forward IPv4/UDP projections for the selected exact-HUD points
are 2.5472/2.4605 Mb/s (HEVC/AV1,2600) and 5.8176/5.7128 Mb/s (7200), versus
custom4.9804/11.0919 Mb/s. These add the declared token/fragment/control model;
real Wi-Fi airtime/retries, capture, input/audio and a native standards reference
protocol remain excluded. Body and network figures must not be mixed.

## Owned lazy analysis removes the repeated-source guards

The custom-codec optimization takes one actual private RGB snapshot **before
both HUD and base preparation**. Its NumPy view is backed by immutable bytes;
normal writes or reenabling array writes cannot mutate it. A bounded two-slot
capture pool uses epochs, generations and at most eight unique reader tokens.
Release/reset/reuse and token exhaustion fail closed while owners remain live.

Analysis starts on the first map build, then remains reusable across actual
retries. Ownership/generation checks replace whole-source SHA guards; no arbitrary
borrowed ndarray is accepted as immutable merely because a flag was set. Capture
copying, validation, all candidate work and cleanup are inside the measured build.

|48-frame window |Plain build ms |V23 eager-sharing ms |Owned/lazy ms |
| --- | ---: | ---: | ---: |
|2600, no losing maps |1,508.14 |1,548.96 |1,503.72 |
|7200,11 losing maps |1,926.54 |1,848.70 |1,798.83 |

The complex mean improves6.63% versus plain; the primary0.29% difference is
effectively near parity in this one trial. Both improve roughly2.7–2.9% versus
the eager implementation. Controls rotate order per source; this is one
interleaved host trial under ordinary concurrent work, not statistical or target
CPU calibration. Native codec timing and Python controller timing are different
implementations and must not be compared as hardware decoder complexity.

All three cohorts emit identical CP23, JA23, image hashes, YUV tags and quality
on 96 paired source decisions;288 actual encode/decode decisions preserve
6,082,560 exact HUD words. Plain complex uses59 analyses/177 forward-plane calls;
both shared variants use48/144. No-retry source work stays48/144 in every cohort.

Owned snapshots copy99,532,800 bytes total, once per 96 preparations, versus
210,470,400 copied/hashed source bytes in the eager guards. Owned source SHA
guard traffic is zero. The normal campaign peaks at 1,036,800 snapshot bytes;
the pool permits two slots. Prediction/transform arrays still occupy5,184,000
bytes during active analysis, and referenced preparation still consumes one
extra bank-reader descriptor. These are **host** storage costs; the ESP32 receives
no full source-analysis cache. Pool capacity, context scratch and native heap are
not inferred from these named arrays.

The bytes snapshot fixes subsequent source mutation, not a concurrent writer
tearing the copy itself. Actual capture ownership, immutable GPU-readback buffers
and native fences remain integration work.

## RS24: functional reset/profile agreement

A separate synchronous control prototype agrees the exact CP23 profile and
waits for old owners to drain before replacing reference state. It binds host/
target boot identities, a profile digest and a monotonically reserved epoch.
Normal HELLO/reply, OFFER/READY, COMMIT/COMMITTED and GO/ACK cost 8 messages,
368 application /592 IPv4+UDP bytes. Every retry and lost message is counted.

Nine nominal/single-loss campaigns recover; permanently lost GO_ACK replies
produce host SAFE_STOP while target is RUNNING, and host data remains blocked.
Actual CP23/JA23 refresh probes use new epochs1/2/3 after target/host reboots and
reject stale data. The first new epoch requires an independent video key plus
full nonreferenced HUD. Duplicate old controls cannot clear new live banks.

The persistent epoch ledger and transport-drained/write/vblank signals are
**model inputs**. This is not durable atomic storage, cryptographic rekey,
network discovery, real nonce generation, full packet-credit/FIFO drain or an
installed recovery service. Persistent BUSY and retry exhaustion fail closed.
The data probes use one static synthetic canvas, not gameplay/FPS evidence.

## What the comparison changes in the plan

1. Use the standards curves as measured compression references. The large base
   gap points to bounded block motion/skip and temporal prediction as higher
   priorities than another few header bytes. Preserve exact reconstructed
   references and charge host search, decoder refetches and metadata. Compare
   more frequent acknowledged reference updates against their reconstruction,
   hash, bank-write and feedback costs rather than assuming free new references.
2. Study motion-compensated exact HUD deltas or a more selective negotiated UI
   mask. Current exact rectangles contain changing pixels too; protection may
   not be silently weakened to make bandwidth look better. Keep the full-patch
   and JPEG controls and test on fresh long footage.
3. Integrate actual CP23/JA23/RS24 with bounded frame/packet credits and shared
   worker/memory scheduling. Apply real ESP32 SRAM/DMA/QSPI/RF and input/audio
   constraints before frame-rate claims.
4. A conformant HEVC or AV1 route needs a matching decoder. This experiment
   supplies no RTL, synthesis/resources, constrained syntax proof, memory/scanout
   qualification or physical 30 fps result. Continue the frozen v20 kernel/fixture
   handoff while investigating a bounded custom decoder and standards subsets.

Run `python experiments/verify_prototype_v24.py`. Detailed methods and artifacts:
[standards comparison](../experiments/python-game-standard-v24-study/README.md),
[owned source](../experiments/python-game-lazy-owned-study/README.md),
[reset agreement](../experiments/python-game-recovery-v24-study/README.md).
