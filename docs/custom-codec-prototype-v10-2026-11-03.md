# Iteration10: bounded UI admission, row-run patches and charged CPU stages

Iteration10 advances the [application-specific codec plan](gamebub-application-specific-codec-plan.md)
with executable Python studies: a whole-frame-cap-aware lossless patch
selector, a row-run patch candidate with a cheaper validation contract, and a
finite GM01 model that charges measured BOX/transport CPU service. This continues
[iteration9](custom-codec-prototype-v9-2026-11-03.md). The handoff branch
is `handoff/gamebub-app-codec-v10-20261103` in both forks; preserve v9 unchanged.

The concrete progress is improved control of **where exact UI pixels are worth
their bytes**, rather than a general replacement for modern video codecs.
Selective patches now fall back to the actual GM01 base when capacity or observed
work is exhausted. Row-run coding reduces complete compact packets by 22.1% on
16 real sampled frames, with exactness over the same selected pixels. The charged
GM01 service model still delivers 28/27 diagnostic IDs/s; no 30 fps hardware
result follows. These are separate experiments: neither GH01 nor HG01 patches
are integrated into the finite GF02/GA01 GM01 service pipeline.

## Actual selective admission and fallback

The [selective study](../experiments/python-game-selective-study/README.md) tries
up to four declared rectangles once each in priority order, using their actual
HP01 encoded bytes plus GH01 wrapper overhead. It caches accepted patch bytes,
counts rejected work and continues to a later small priority if an earlier large
one cannot fit. Every admitted complete packet respects the 49,152-byte cap.
If no patch is admitted, output is the original GM01 bytes without a wrapper;
an over-cap base is explicitly rejected.

The same source and independent GM01 ROI8/background16 key are used for the
control and each selector. Broad priorities cover 47,360 pixels; compact ones
cover 21,120 pixels, all inside broad. These are configured synthetic priorities,
not verified real-game HUD locations. Compact cannot claim broad's exactness
coverage. Selected pixels match original RGB565 words; that does not eliminate
RGB888-to-RGB565 quantization error.

| Policy, 16 real inputs | Mean whole-frame bytes | Maximum bytes | Exact selected pixels | Common broad ROI MSE | Mean complete service |
| --- | ---: | ---: | ---: | ---: | ---: |
| GM01 control |25,320|31,570|0|17.280|62.37 ms|
| Broad selective |39,375|47,092|15,360|16.964|117.18 ms|
| Compact selective |40,048|41,511|21,120|15.289|119.16 ms|
| Compact, observed 35 ms preparation budget |25,320|31,570|0|17.280|90.63 ms|

Compact selects all four rectangles on all 16 real inputs: 44.59% of broad's area,
with zero selected RGB565 word mismatches. Broad selects its first rectangle
and pays for all 16 rejected second-rectangle attempts. Outside the selected
rectangles, displayed RGB565 exactly matches the same GM01 base. MSE uses the
same broad ROI denominator, so it does not credit a smaller selector with a
smaller error region.

Across 20 inputs and three selectors there are 54 admitted decisions and six
base rejections. The 16 real inputs and two favorable flat fixtures fit every
policy; the two seeded noisy bases already exceed the cap and are rejected
without palette work. Those synthetic cases remain separate evidence.

The optional 35 ms observer checks preceding GM01 preparation plus selection
work before/after attempts and assembly. It is a cooperative fallback, not a
hard deadline. In this run mandatory base preparation/validation already uses
that budget, so no patches are attempted on cap-valid inputs. Its 90.63 ms mean
complete service still charges prior work and decoding. A fallback cannot refund
work already performed, and the selector does not meet 30 fps in Python.

A separate 12-native-frame functional sequence decodes eight GH01 packets and
four byte-identical GM01 fallbacks, preserving the immutable YUV key anchor
through P frames. This checks mixed dispatch and prediction, not a paced network
or fault recovery. Seven tests and the stored-result verifier pass.

## HR01 row-run coding and the HG01 atomic decoder

The [row study](../experiments/python-game-row-study/README.md) adds HR01 alongside
frozen HP01. The host tries raw RGB565, direct word runs and, when a palette fits,
palette-index runs; it also tries HP01 and chooses the shortest complete patch
with HP01 winning ties. All attempted candidate work is paid.

Runs and literals reset at each row. Every coded row has an explicit length;
tokens carry 1–128 symbols and cannot cross rows. The bounded decoder checks
CRC, exact consumption, row/pixel bounds and palette/index validity. This offers
a simple candidate for a future FPGA row decoder, but no RTL, BRAM/DSP utilization
or target memory bandwidth has been demonstrated.

HG01 is a new wrapper around GM01 and HP01/HR01 patches. It validates geometry,
nonoverlap and patch syntax before stateful base decoding. Geometry is checked
before decoded patch allocation. Then the existing atomic GM01 receiver parses
and validates the full base once before committing state. This removes the
redundant full base entropy parse from the wrapper preflight while preserving
invalid-patch/invalid-base atomicity. The preflight alone does not validate GM01
coefficients. Invalid inputs and key/P YUV-anchor separation have explicit tests.

| Same selected area, 16 real inputs | HP01 mean complete bytes | Adaptive mean complete bytes | HP01 / adaptive fit 48 KiB |
| --- | ---: | ---: | ---: |
| Broad, 47,360 pixels |87,470.7|45,557.5|0 / 8|
| Compact, 21,120 pixels |40,047.7|31,216.4|16 / 16|

Complete bytes fall 47.9% for broad and 22.1% for compact. All 32 real paired
region-set comparisons improve, and HR01 is selected for all 96 real patches.
All 80 wrapped decodes across the 20-source campaign preserve their full selected
RGB565 words, including packets that exceed the cap. Those oversize decodes are
algorithm checks, not admitted streaming frames. The broad adaptive candidate
still fails the cap for eight real inputs; capacity admission remains necessary.

| Real 16 inputs | HP01 patch work / charged preparation | Adaptive patch work / charged preparation | HP01 / adaptive receive |
| --- | ---: | ---: | ---: |
| Broad |0.96 / 27.27 ms|11.15 / 37.47 ms|35.15 / 37.42 ms|
| Compact |0.58 / 26.90 ms|6.34 / 32.66 ms|34.95 / 35.77 ms|

The byte gain costs host Python work. Charged preparation adds the measured
base key, paid once per source and reused across profiles, to actual patch work.
Priority-map construction occurs before the base timer and is excluded; capture
and source scaling are excluded too. Receive includes full
wrapper/patch validation, atomic GM01 decode and display overlay/conversion.
Near-33 ms mean preparation is not a deadline bound, and receive is slower still.
Timing differences against the separate selective study are not a controlled
paired speedup: the wrapper contract and measurements differ.

Seeded antialiased broad packets shrink from 143,533.5 to 102,934.5 mean bytes but
still fail, including their already-oversize GM01 bases. Favorable flat broad
packets shrink from 18,928.5 to 16,935.5 bytes; keep those artificial cases
separate. Eight tests and the stored-result verifier pass. GH01 and existing
GF02/GM01 peers do not accept HG01/HR01 without a new negotiated profile.

## Charged BOX and transport CPU services

The [service study](../experiments/python-game-service-study/README.md) leaves
GM01/GF02/GA01 sources unchanged and measures actual Pillow BOX/canvas work,
datagram construction, per-chunk reassembly feed, feedback construction and
feedback parsing. Failed preparation/feed/parse work retains its cost. The
zero-added-CPU control still executes these calls and records their bytes and
wall times, but assigns zero virtual duration to the additional stages.

Each stage is one serialized virtual server. Encoder semantic publication waits
until encode completion, preserving concurrent P ACK removals. Reassembly read
pins remain owned through charged feed, QSPI and decoding. Matching epoch/frame/
body-CRC feedback cannot ACK before decode/read finish, feedback serialization,
propagation and parsing. Timeout cannot release an active CPU/read owner. Two
sender slots, two ingress slots, two credits, three framebuffer metadata roles,
one active/one latest resize capture and four feedback descriptors are bounded.

| Same 60 native sources | Zero / charged strict | Zero / charged eventual | Zero / charged diagnostic IDs/s |
| --- | ---: | ---: | ---: |
| Combat |54 / 54|55 / 55|28 / 28|
| Second clip |54 / 54|56 / 56|27 / 27|

Strict is `[0,2000)` ms, diagnostic is `[500,1500)` ms and eventual includes the
separate 1,000 ms drain. Both pairs happen to retain identical prepared/presented
IDs and GM01 packet hashes: 55 combat and 56 second-clip packets. Preparation and
receive are remeasured per case; uncontrolled host timing can change histories
on another run. Equal counts here are not a general zero-cost claim.

Charged BOX means are 1.551 ms on 512×288 combat input and 3.324 ms on 1280×720
second-clip input, both aspect-fit into 720×480. Charged transport CPU totals
4.321/5.843 ms across 55/56 packets, including 502/699 fed chunks. Those costs
are small beside mean P preparation of 19.05/19.56 ms and P receive of
20.56/23.71 ms. Summing costs from independent servers does not give end-to-end
latency. Charged strict-window p95 age is 66.7/100 ms.

Two charged initial-key fault cases present 50/52 strict/eventual after chunk
loss and 48/50 after ACK loss. Both have 28 diagnostic IDs/s, illustrating how
that window alone hides startup losses. On separate seed1009 noise-to-quiet
stress, normal presents three eventually and gate six, while charging all
attempted rejects; this differs from v9's seed909 fixture and is not a paired
wall-time ablation. Across eight runs: 384 capture inputs, 343 preparations,
333 hash-checked decodes/eventual presentations and complete resource drain.
Fourteen deterministic tests and the verifier with 17 executed-source pins pass.

This is a causal finite software model, not a shared physical-CPU scheduler.
Independent CPU servers overlap virtually; actual calls execute offline to learn
costs. Native RGB is extracted by offline PyAV. BOX is measured preprocessing,
not desktop acquisition; GPU capture/readback and source decode are excluded.
The assumed links remain 8 Mb/s each way, QSPI 160 Mb/s, feedback propagation
10 ms and vblank 60 Hz. Real radio/socket/framing, target memory/DMA/CDC and panel
service remain absent. Hash/oracle/error work is outside documented service timers.

## How close to HEVC/AV1: measured common-color references

The [standard-codec study](../experiments/python-game-standard-study/README.md)
now measures both against the same GM01 input sources. An initial native-PyAV
color path exposed different round-trip floors, so a separate follow-up feeds
GM01's frozen YUV420 planes into every native encoder and reconstructs every
output using GM01 color arithmetic. RGB565 display quantization and active/ROI
area-weighted PSNR then use the same definition. Key IDs are0/30 in all profiles.

|Common-color point|Coded Mb/s at hypothetical30IDs/s|Active PSNR|Priority-region PSNR|
|---|---:|---:|---:|
|Combat GM01 ROI8/bg16|2.1126|34.02dB|35.74dB|
|Combat HEVC q36|0.2074|35.90dB|36.39dB|
|Combat AV1 q48|0.1312|36.52dB|37.24dB|
|Second GM01 ROI8/bg16|2.8861|35.20dB|36.24dB|
|Second HEVC q28|0.1985|36.59dB|36.61dB|
|Second AV1 q38|0.1212|36.57dB|36.47dB|

At these recorded operating points HEVC/AV1 use roughly10–24times fewer coded
bits and score higher in both measured regions. This is a substantial remaining
gap, **not a universal codec ratio, matched-quality BD-rate or visual acceptance
claim**. Both clips are short and precompressed; combat has32 unique RGB frames
among60, while the second has60. Reference/skip coding benefits from this content.
Full18-point results, including worse-quality points, remain available.

The main campaign decodes1,080 outputs:360 GM01 and720 native HEVC/AV1. The
common-color supplement adds720 new native outputs and explicitly reuses360 GM01
records. Thus there are1,800 actual codec outputs across the campaigns, with240
separate uncompressed color-roundtrip probes. Five component tests and stored
verification check native packet/frame association, padded color-plane copies,
source equality, key IDs, output hashes, byte totals and pooled metrics.

These references use CPU libx265 and SVT-AV1/libdav1d, not target FPGA decoders.
Low-delay settings and effective startup configuration are recorded; PTS=DTS
and zero packets returned only at flush do not prove zero live latency. Rates
exclude UDP/mux/QSPI/FEC/feedback. Native codecs retain their own references;
GM01's immutable-key/ACK rules are different. Common color removes one confound,
not memory, loss recovery or scheduling differences.

HEVC and AV1 are separate bitstream/decoder contracts. A custom application-specific
combination should borrow useful algorithms, then retain one explicit custom
syntax and bounded receiver behavior. Next test host-side block motion, skip/copy
and reference choices before adding decoder complexity; retain selective exact565
UI and high-entropy fallback. There is no current Game Bub HEVC/AV1 decoder or
resource/timing proof. Background: [HEVC](https://www.itu.int/rec/t-rec-h.265),
[AV1 coding tools](https://aomedia.org/docs/AV1_ToolDescription_v11-clean.pdf).

## Evidence boundaries and next work

The selective, row, service, standard-reference and independent-audit components
have7,8,14,5 and7 passing tests: **41 tests**. The
[v10 audit](../experiments/python-game-audit-v10-study/README.md) rederives the six
supplied artifacts,31 distinct source pins and both media hashes with no missing
result inputs. Target hardware, live capture/transport/scanout and physical30fps
remain unqualified.

Run `python experiments/verify_prototype_v10.py` from the repository root to check
the [frozen inventory](prototype-v10-provenance.json), test logs, source bindings,
all four stored-result helpers and common-color operating-point comparisons.
This checks stored evidence; study READMEs give unit-test and benchmark commands.
Recorded environment is Python3.14.4, NumPy2.5.4, Pillow13.0.0 and PyAV19.0.2.
The service study's portable `check_stored_results.py` is read-only by default and
lists absent external media; its original pinned `verify.py` remains unchanged.

Each study retains source/input/runtime pins, results, test logs and stored-result
verification. No live Sunshine mode, ESP32 firmware or FPGA bitstream is installed.

Sources remain short, related, precompressed native 25/29.88 fps Mass Effect clips
with repeated content, plus separately labeled synthetic fixtures. The combat
60-source service window contains only 32 unique RGB frames, making explicit
unchanged-content/skip evaluation useful and independent-frame claims premature. Declared
rectangles are not detected/verified game HUDs. Exactness is RGB565 word equality;
subjective readability, temporal flicker and native 30-distinct-frame coverage
remain unqualified. Python arrays, packet copies, source/oracle/output buffers,
transform/reference workspaces and patch allocations are extra memory beyond
metadata roles. A 48 KiB cap is neither a sustained wire-rate nor a frame-time
budget. No component result can simply be multiplied into a combined 30 fps claim.

1. Integrate HR01 minimum-size choices into selective whole-frame admission under
   an explicit new HG01 peer profile. Preserve measured rejected work, original
   GM01 fallback and per-rectangle coverage, then run the same source decisions
   end to end. Do not infer that selective GH01 already uses HR01.
2. Add bounded motion/skip decisions for unchanged or predictably moved content,
   using only the current capture and ACKed reconstructed state. Compare actual
   emitted bytes, complete service, quality and loss recovery against GM01; retain
   independent-key recovery and conservative high-entropy fallback. Motion/skip
   beyond existing GM01 modes is next work, not implemented by the row study.
3. Put the negotiated selective HG01 stream through the finite transport model
   with measured whole-wrapper receive cost. Replace independent CPU-server
   assumptions with the intended host/ESP32/FPGA resource schedule; measure live
   acquisition/readback and target copies/framing before deriving a frame budget.
4. Extend distinct native-30 sources and held-out games/UI, then run long phase,
   load and fault regressions. Keep strict delivery, diagnostic cadence, age tails,
   common-ID quality and exact-area coverage separate. Use the independent audit and common-color standard-codec references
   to assess each new mode against the same source IDs.
5. After the format and selective/motion policy stabilize, port bounded parsing,
   row counters/palette and transform/reference contracts into native code and
   RTL with golden/negative vectors. Verify physical memory ownership, bandwidth
   and timing before hardware qualification. Existing JPEG hardware development
   can continue independently while these custom formats mature.
