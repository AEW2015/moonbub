# Iteration9: finite streaming ownership and selective lossless UI experiments

Iteration9 connects the frozen GM01 controller to actual serialized GF02 chunks
and GA01 feedback in a finite Python pipeline. It also tests a separate GH01
lossless RGB565 display-patch wrapper. This advances the
[application-specific codec plan](gamebub-application-specific-codec-plan.md) and
[iteration8](custom-codec-prototype-v8-2026-11-03.md), without changing the frozen
v8 sources or installing a new Sunshine, ESP32 or FPGA mode.

The result is a stronger software contract, **not a 30 fps hardware proof**.
The two real-source measured-receiver cohorts reach 28 and 27 distinct displayed
IDs/s in the declared one-second diagnostic window. The lossless patch format
works correctly, but all 36 real-campaign/synthetic-campaign wrapped packets
exceed the 48 KiB whole-frame cap; two separately labeled favorable flat inputs
fit. Neither result justifies enabling a general lossless HUD path.

## Finite GM01/GF02/GA01 pipeline

The [finite pipeline study](../experiments/python-game-pipeline-study/README.md)
actually prepares each selected source against its current ACKed immutable key,
chunks the emitted GM01 bytes, reassembles them, decodes them and serializes
feedback. A source replaced in the latest-capture waiting slot is never encoded.
Each actual preparation call supplies its own measured service duration;
oversized rejected work still consumes that service. A separate verification
oracle is outside preparation timing. Receiver service is either declared 8 ms
or the actual selected packet's measured Python `receive()` call.

There are two sender transaction slots, two bounded ingress payload slots, two
GM01 credits, three front/pending/back framebuffer roles and one replaceable
waiting capture. Preparation rejects capture age above 100 ms; the completed
preparation and receiver path enforce the 150 ms frame-age deadline. A key
refresh due after 30 capture IDs waits for the prior credits to drain. ACK/NACK
and timeout cannot return a slot, credit or key while encoder, queued/active
forward work, QSPI or decoder reads still own it. A deterministic test forces
timeout during a 65 ms decode and checks that ownership remains until completion.

Assumed service is explicit: independent ideal 8 Mb/s forward/reverse links,
160 Mb/s GM01-payload QSPI, 10 ms feedback propagation and 60 Hz vblank. Every
actual GF02/GA01 byte, including lost and duplicate transmissions, is charged
before the corresponding completion/feedback event. Capture acquisition is an
external assumed delay, default zero: clips were decoded and scaled beforehand.

| Primary 60 captures | Controller | Receiver service | Strict / eventual presentations | Diagnostic distinct IDs/s |
| --- | --- | --- | ---: | ---: |
| Combat | normal or cheap gate | assumed 8 ms | 57 / 58 | 29 |
| Combat | normal or cheap gate | measured Python | 54 / 55 | 28 |
| Second clip | normal or cheap gate | assumed 8 ms | 58 / 59 | 29 |
| Second clip | normal or cheap gate | measured Python | 52 / 55 | 27 |

Strict presentations occur in `[0,2000)` ms; diagnostic presentations are
recomputed from timestamps in `[500,1500)` ms; eventual presentations include
the separate 1,000 ms drain. They are different measures. None of these cases
delivers all 60 captures or reaches 30 diagnostic IDs/s. Strict-window p95 age
is 66.7 ms with assumed receive, 83.3 ms for measured combat and 100 ms for
measured second clip. Equal normal/gate totals do not imply identical capture
histories; the study records common-ID quality separately.

There are 12 cases: eight baselines, two second-clip initial-key fault runs and
two 12-capture noise-to-quiet stress runs. Initial key chunk loss gives 49 strict,
51 eventual and 27 diagnostic IDs/s; initial key ACK loss gives 47/50 and 28.
The former recovers after partial assembly timeout and a bound NACK; the latter
cannot use the decoded key until feedback permits it and recovers after timeout.
Later configured duplicate IDs are checked against observed events because
overload can skip a configured capture ID.

Both stress runs eventually present six quiet frames, with five inside their
400 ms capture interval. Normal prepares eight of twelve captures, cap-rejects
two and replaces four waiting inputs. Cheap gate prepares twelve and cap-rejects
six: it inspects more noisy inputs without displaying an additional quiet frame.
There is no diagnostic FPS window for this short stress run.

Across the separate cases, 624 capture-policy events produce 576 preparations,
567 hash-checked decodes and 567 eventual presentations. All slots, credits,
waiting captures and source dispositions drain. Summed nominal IPv4/UDP traffic
is 6,399,336 forward bytes and 29,588 feedback bytes, including drain; this sum
across experiments is not a measured link rate.

## GF01 ownership correction and GF02/GA01 contract

The [feedback study](../experiments/python-game-feedback-study/README.md) and
[protocol](../experiments/python-game-feedback-study/PROTOCOL.md) preserve the
old GF01 fixtures and reproduce an ownership defect: conflicting metadata could
remove a completed frame's delivered pin before its decoder committed it.
Immutable Python bytes survived, but the logical slot was prematurely freed and
the original completion could no longer commit. GF02 retains that pin through
the exact reader's commit/reject, rejects conflicting delivered traffic without
reclaiming it and refuses reset while delivered readers remain.

GF02 has a 31-byte header and canonical 1,024-byte chunk payload. Every chunk
carries both whole-packet CRC and a content-specific GM01 body CRC tag. GA01 is
a real 24-byte feedback packet binding epoch, frame ID, ACK/NACK status, reason
and that body tag. Nominal IPv4/UDP adds 28 bytes each way. CRC32 of a valid
GM01 packet including its appended CRC has constant residue; it cannot identify
the content. The body tag excludes that footer. All eight golden packets share
the whole-packet residue but have distinct body tags. CRC is not authentication.

Eight golden packets are actually re-chunked, reordered, duplicated and decoded
against their stored RGB565 output; all drain. Their traffic totals 40,843
forward bytes and 416 reverse bytes. Three additional fault campaigns cover a
delivered conflict, missing-chunk timeout and valid outer transport with invalid
inner GM01 CRC. The regression compares old pin loss with new pin retention.
GF02/GA01 requires new negotiated peer support; installed JPEG/MSV1 and GF01
peers cannot silently consume it.

## Separate GH01 lossless display-patch experiment

The [HUD study](../experiments/python-game-hud-study/README.md) encodes up to
four bounded, opaque, disjoint rectangles as exact RGB565 words using 1/2/4/8-bit
palette indices or RAW565 fallback. Its GH01 wrapper validates lengths, CRCs,
geometry, palettes and base GM01 before stateful decode. Patches change display
pixels only; the reconstructed YUV predictor remains the GM01 base. Temporal
key/P tests verify that separation. **GH01 is not integrated into the finite
GF02 pipeline.** There is no transport, feedback or presentation scheduler in
this separate wrapper experiment.

The main campaign contains 18 source frames with four profiles each: 72 actual
decodes, including 36 wrapped frames and 72 patch encodes. The two configured
rectangles total 47,360 pixels; they are declared priorities, not detected or
verified real HUD locations. All 36 wrappers have zero original-RGB565 word
mismatches within those rectangles, and all 36 exceed 49,152 whole-frame bytes.
ROI8-base plus patches averages 79,188 bytes on combat, 95,754 on the second
clip and 143,534 on seeded synthetic inputs. Full-rectangle eight-bit indices
alone nearly consume the cap; textured regions can require RAW565.

Two deliberately favorable flat fixtures with non-antialiased glyphs fit:
17,894 bytes with 1-bit/1-bit patches, and 19,963 bytes with 2-bit/1-bit patches.
Both reproduce RGB565 exactly. They establish format functionality for low-color
content, not representative gameplay throughput or readability. RGB565 word
exactness does not remove RGB888-to-RGB565 quantization error.

Small component costs must not replace complete service costs. Palette/index
construction averages 0.80/1.05/0.85 ms across combat/second/synthetic, and overlay
write/conversion about 1.21 ms. However complete ROI-base plus wrapper preparation
averages 63.83/53.52/155.88 ms and complete receive 75.09/54.92/224.96 ms. Those
calls include base validation/decoding and intentionally duplicated generic
validation work. There is no demonstrated complete-frame speedup.

## Evidence, audit and limits

The new components have seven pipeline tests, six transport tests, six HUD tests
and seven independent audit tests. Their READMEs link stored results, logs,
source/input/version pins and reproduction commands. The
[independent v9 audit](../experiments/python-game-audit-v9-study/README.md)
rederives timestamp-window counts, capture outcomes, rejected service costs,
wire bytes, feedback identity, drain state and HUD cap/exactness scope. Its
diagnostic counts use the actual `[500,1500)` ms presentation timestamps,
including 29 diagnostic IDs for the first baseline. Capture, strict, diagnostic
and drain counts remain separate. All 25 declared source pins and both media hashes match.

The media remain related, already-compressed native 25/29.88 fps Mass Effect
clips with repeated content, scheduled at hypothetical 30 capture IDs/s. Runs
are short and host load, affinity and warmup are uncontrolled. Actual capture,
scaling and acquisition costs are absent. Transport construction/reassembly and
feedback parsing execute for correctness but their CPU costs are not separate
charged services. RGB/oracle metrics are outside encoder/receiver service where
documented. Framebuffer roles and two-slot bounds are logical ownership evidence;
source arrays, Python copies, verification buffers, codec workspaces and reference
arrays consume extra memory. There is no native firmware, physical SDRAM/DMA/CDC
drain, ESP32/QSPI bandwidth, FPGA timing/resource or panel-rate proof here.

Run `python experiments/verify_prototype_v9.py` from the repository root to
check the [frozen provenance inventory](prototype-v9-provenance.json), executed
source pins, test logs, stored window counts, fault regression and byte/exactness
checks. This reads stored timed results; it does not rerun their benchmarks or
unit tests. Each study README provides its unit-test and benchmark commands.
Recorded environment: Python3.14.4, NumPy2.5.4, Pillow13.0.0 and PyAV19.0.2.
External media paths/hashes are in the inventory; golden replay uses committed
fixtures without requiring those clips. On another checkout the verifier resolves
recorded source paths relative to the repository and lists absent external media.

The v9 handoff branch is `handoff/gamebub-app-codec-v9-20261103` in both forks.
Keep v8 as the unchanged comparison snapshot. These Python formats supply
contracts and vectors for development; existing JPEG hardware work remains a
separate integration path.

## Next application-specific codec work

1. Keep bounded GM01 ROI quantization as the general path. Prototype small,
   configured low-color HUD spans/rectangles using actual palette and packet
   costs. Admit lossless patches only with measured whole-frame headroom;
   otherwise retain the cap-respecting GM01 base. Measure full preparation and
   receive service, not just the patch component. RLE/spans and acknowledged
   patch reuse are candidates to compare, not implemented v9 capabilities.
2. Add measured capture/scale and native packetization/reassembly/feedback CPU
   stages to the finite model. Preserve per-call rejection work, finite ownership
   and delayed credit release. Model target memory traffic/copies and real QSPI
   framing before deriving a target frame-rate budget.
3. Run longer, distinct native-30-fps game/UI sources and hold-out scenes, with
   capture/link/vblank phase sweeps, long high-entropy bursts, loss/reorder/
   duplicate/corruption and mid-read timeout regressions. Report strict-window
   delivery, age tails, common-source quality and visible continuity separately.
   Preserve the existing 1,800-distinct-frame qualification gate.
4. Port the frozen integer parser/transform/reference contract into native code,
   then RTL with the same golden packets and negative vectors. Specify GF02/
   GA01 capability negotiation and ownership handshakes at every DMA boundary.
   A GH01 display blitter needs its own bounded-memory contract and pipeline
   integration before it can inherit any GF02 feedback or throughput claim.
5. After native/RTL service and memory checks, test a separately negotiated
   Sunshine sender and ESP32/FPGA receiver on hardware. Prove sustained 30 fps,
   bounded age, fault recovery and per-game readability there; this Python
   iteration does not establish that deployment result.
