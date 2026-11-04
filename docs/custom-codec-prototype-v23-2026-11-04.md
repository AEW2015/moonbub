# Iteration 23: actual HD22 joint packets and shared source analysis

V23 implements the first two v22 follow-ups in Python: actual integrated HD22
dispatch and reusable prediction/forward analysis across bounded map retries.
It preserves **720×480 coded /720×405 active** and the 30-ID/s goal. Existing
native endpoints and the frozen v20 hardware kit remain unchanged.
All **49 tests pass**: 25 joint-profile, 16 shared-analysis and 8 independent-audit
tests. The retained whole-sequence verifier and byte/work/quality audit pass.

## Actual new-profile bytes replace the v22 projection

The new laboratory grammar is **HC22/HA22 → CP23/JA23**. HC22 actually selects
and transmits the smaller legacy full patch or HD22 packet. Its receiver decodes
HD22 merged-zero spans, validates all exact RGB565 words and participates in the
joint private prepare/write-drain/presentation/whole-pair ACK transaction.
No frozen module globals are patched to substitute the new decoder.

| Structure | Actual complete overhead/length |
| --- | ---: |
| HC22 header +CRC, before four patch bodies |83 B |
| HA22 complete decoded HUD ACK |54 B |
| CP23 pair binding +CRC, before AR03/HC22 components |57 B |
| JA23 complete joint ACK including AF03/HA22 |134 B |

Old HC21/CB21/JA22 profiles reject the new bytes; new parsers reject old profiles.
Magic/version selection is explicit, but a capability/reset negotiation handshake
is still absent. These are actual Python packets, not installed firmware support.

The fixed-v20-map control holds the video base, decoded YUV and complete display
identical to the earlier reference. Its actual packet sizes exactly match every
v22 HD22 projection row:

| Native window | V22 HC21 complete bytes | Actual CP23 complete bytes | Saving at identical image | Maximum CP23 bytes |
| --- | ---: | ---: | ---: | ---: |
| 2600,48 frames |934,451 |919,967 |1.55% |27,693 |
| 7200,48 frames |2,017,112 |1,975,430 |2.07% |48,477 |

This closes the former dispatch/projection gap. The fixed control is deliberately
an offline replay of stored v20 chosen maps; it is an image/byte control, not a
deployable causal selector or fair mode-search timing baseline. Adaptive controls
choose maps from the current complete encoded size instead.

## Adaptive application-specific profile

All policies preserve all four requested HUD regions, totaling 21,120 original
RGB565 words/frame. HD22 saves exact display-patch bytes without changing the
YUV predictor contract. The adaptive policy can use some saved space for a finer
background within the 49,152-byte complete cap.

| Complex7200 policy | Complete bytes | Mean active expanded-RGB565 channel MSE | Fine/coarse frames |
| --- | ---: | ---: | ---: |
| V22 adaptive, HD21 |2,072,408 |31.0812 |34 /14 |
| V23 adaptive, HD22 |2,057,435 |30.0839 |37 /11 |

The new sequence uses 0.72% fewer bytes and has 3.21% lower mean squared error.
This is the measured combined HUD/video allocation policy, not solely an entropy
efficiency comparison at equal base quality. In this window all 48 predictor
identities/tags still match v22; three additional ordinary frames use a finer
background. Other clips or refresh histories may diverge. The primary window
keeps the same 14.4290 MSE and saves1.55% complete bytes.

Fine/coarse means ROI8/background16 versus ROI8/background32. MSE is measured
after RGB565 channel expansion over720×405 active pixels; it does not establish
human legibility, perceived flicker or game feel. All exact HUD words remain
protected. Resolution and requested frame count are not reduced to fit.

## Shared prediction/DCT work is byte-exact

`SharedEncoder` keeps one source-analysis context on the host. A context contains
one prediction and raw forward coefficients. Each map still executes actual
quantization, entropy coding, reconstruction when required, reference hashing,
serialization, complete-cap admission and losing-candidate discard. Analysis
reuse does not skip or pretend these costs are free.

Source/frame/epoch/geometry/configuration/reference identity guards reject stale
reuse. The borrowed RGB source is SHA256-checked on each attempt. A referenced
context holds an extra reader descriptor; the winning candidate retains its own
lease after context cleanup. Contexts must end before semantic commit. Rejection,
callback failure and input/configuration mutation preserve external reader owners
and do not manufacture an issued identity.

| Adaptive case,48 frames | Plain analyses /plane transforms | Shared analyses /plane transforms | Paid build ms plain →shared |
| --- | ---: | ---: | ---: |
| 2600, no losing map |48 /144 |48 /144 |1,503.45 →1,552.08 |
| 7200,11 losing maps |59 /177 |48 /144 |1,920.60 →1,845.64 |

The complex case removes 11 analyses /33 plane forward calls, an18.64% reduction
in those calls, while preserving every selected CP23/JA23 packet, displayed word
hash and YUV tag. Its measured whole-build work improves3.90%. The no-retry case
**regresses3.23%**: eager context validation has cost without reusable work.

The two adaptive controls execute interleaved for each source, alternating order
by frame ID. Their same 96 packets/ACKs/images and map choices are verified exactly.
Timings are one paired host trial, not a distribution, universal speedup, native
host calibration, ESP32/DSP result or achieved streaming FPS. Offline acquisition,
diagnostic image/tag/quality comparisons and object export are excluded; all
source-context preparation, guards, failed candidates and cleanup are inside
`build_ms`. BOX preprocessing is measured once per acquisition and shared by the
three controls, not counted as288 independent preprocessing calls.

## Memory and ownership costs remain explicit

At720×480 a source context retains **5,184,000 host-array bytes**:
1,036,800 bytes of int16 prediction and 4,147,200 bytes of int64 raw coefficients.
It borrows 1,036,800 RGB bytes without retaining another source copy. Canonical
byte copies for SHA guards are transient and paid; across 96 adaptive shared
preparations,203 guards copy/hash210,470,400 source bytes. These are host array
operations, not wire bytes or measured bus transactions.

The context extends array lifetimes between map attempts. The retained count
is not an additional independent5.18MB at every phase or a total heap peak.
Quantized coefficients, private decoded/visible frames, packet data, hashes,
interpreter objects and the existing bank/cache arrays are additional. No full
source-analysis cache is added to the ESP32. Native buffer ownership and target
memory mapping remain separate implementation work.

One referenced preparation needs **two free reader slots**, its analysis hold
and candidate hold. With max8 readers,7 external owners cause early clean
rejection while6 permit construction and exact cleanup. The descriptor limit is
not silently increased. Byte/admission parity therefore applies to matching
admissible ownership conditions, not every possible saturated-reader state.

Hash guards detect changes between synchronous calls; they do not lock out a
concurrent writer during encoding. NumPy read-only flags are a trusted local API
contract, not a security boundary. A native immutable capture-buffer owner/fence
is needed before replacing repeated whole-source hashes with cheaper generations.

## Retained campaign and evidence

Six48-frame cases reuse96 acquisitions from the same two precompressed29.88 fps
Mass Effect regression windows: fixed-map CP23, adaptive plain and adaptive shared
for each window. There are **288 actual joint decisions**, not288 unique captures.
All fit the complete cap and preserve6,082,560 requested original HUD words.

The retained verifier replays all complete sequences from empty banks, decodes
456 actual HD22 span patches, checks288 corrupt-packet rejections,576 write/vblank
gate failures and 576 old-profile pair/ACK rejections. It independently recomputes
30 retained-source quality checks and verifies all96 plain/shared packet/ACK/image
pairs exactly. Output-hash coverage of 99,532,800 display words and 149,299,200 YUV
samples is sequence consistency evidence, not lossless original full-frame video.

The 25 joint-profile tests cover old/new grammar rejection, actual merged spans,
private-publish/ACK ownership, fixed geometry, deadlines and factory cleanup.
The 16 shared-analysis tests cover byte/ACK/output parity in GM/exact/pruned modes,
four failed caps with ID reuse, source/config/reference mutation, source==promotion
destination, callbacks, end-before-commit and near-reader-cap cleanup.

## Remaining rate and hardware gates

Projecting the actual fixed-image CP23 packet sizes to 30 IDs/s gives 4.9804/10.6515
Mb/s forward (2600/7200); adaptive complex gives 11.0919 Mb/s. Reverse projections
are0.3509/0.6501 Mb/s for fixed images and 0.6732 for adaptive complex. Arithmetic
includes GF03/token/IP/UDP chunks, two forward/three reverse FG19 controls,
one PC18 per fragment and JA23. It still excludes queries/retries, real Wi-Fi
airtime, capture, audio and input. The new CP23 transport routing itself is not
integrated into that older gateway protocol; rates are not network measurements.

Logical write-drain/vblank events are still injected. There is no native
Sunshine/ESP32 endpoint enablement, real reset/rekey handshake, DMA/CDC/memory-order
proof, RF/QSPI/FIFO schedule, mapped FPGA fit/Fmax, physical scanline test or
sustained physical 30 fps result. Keep the working JPEG path and frozen v20 kernel
goldens available while native teams port these experimental Python contracts.

## Next application-specific steps

1. Prototype capture-buffer ownership and lazy retry reuse. Keep the first-map
   path inexpensive, retain analysis only when needed, and prove the same packet,
   source lifetime and rejection behavior. Charge any private source copy or
   ownership/guard work; no unsafe removal of mutation checks.
2. Add a real capability/reset/rekey state machine with one-sided reboot, lost
   control messages and exact full-refresh recovery. Old peers must remain
   selectable and cannot infer a profile from compatible-looking field lengths.
3. Integrate the actual CP23/JA23 bytes with bounded packet/frame credits, then
   a shared-worker/shared-memory schedule. Model RF bursts, QSPI/DMA contention,
   ACK RTT, reader drain, deadlines and input/audio under declared target limits.
4. Explore bounded pipelined source/cache generations only with explicit extra
   storage/credits; stop-and-wait remains a per-frame RTT gate in this model.
5. Port stable inverse/span/parser/ownership kernels to native/RTL and compare
   all golden outputs under stalls/reset/abort. Measure fresh long gameplay,
   resource/timing fit, memory/scanout service and actual presented IDs/age before
   choosing defaults or claiming30 fps.

Run `python experiments/verify_prototype_v23.py`. See
[joint profile](../experiments/python-game-hd22-joint-study/README.md) and
[shared analysis](../experiments/python-game-shared-analysis-study/README.md).
