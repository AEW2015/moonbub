# FPGA game-streaming codec: audit and revised development plan

Audit date: 2026-11-03. Input: the supplied “FPGA Game Streaming Codec:
Development & Evaluation Plan.” This document proposes experiments; it does
not select a production codec or establish hardware performance. Use the
[developer handoff](dev-handoff-2026-11-03.md) for the current implementation
and evidence. Current work is on paired `handoff/gamebub-app-codec-v11-20261103`
branches in [Moonbub](https://github.com/AEW2015/moonbub/tree/handoff/gamebub-app-codec-v11-20261103)
and [Sunshine](https://github.com/AEW2015/Sunshine/tree/handoff/gamebub-app-codec-v11-20261103).
Earlier study/handoff branches remain frozen.

## Recommendation

### Python prototype progress, 2026-11-03

Current follow-up: [iteration11 temporal UI integration and reduced target](custom-codec-prototype-v11-2026-11-03.md)
connects actual selected HG01/GM01 bodies to GF02/GA01, tests bounded block motion
and512×28830/20fps, and investigates constrained/full HEVC/AV1 FPGA architectures.
Short diagnostic cadence improves with reduced dimensions; startup/drain and
refresh-policy limits remain. BM01 has mixed results and is not enabled generally.
Read the [decoder architecture plan](gamebub-hevc-av1-fpga-plan.md) before claims
about standards compatibility, memory allocation or proportional RTL shrink.

Previous follow-up: [iteration10 selective UI, row coding and reference-codec comparison](custom-codec-prototype-v10-2026-11-03.md)
implements bounded actual patch admission, row-run/HP01 minimum coding and measured
BOX/transport CPU services. Common-color HEVC/AV1 references expose a substantial
remaining coding-efficiency gap. Motion/skip and reference decisions, selective
HR01 integration, shared-resource scheduling and target implementation are next.
No wrapper/finite-model results establish physical30fps or full-standard decoding.

Previous follow-up: [iteration9 finite transport, feedback and UI experiments](custom-codec-prototype-v9-2026-11-03.md)
connects actual GM01/GF02/GA01 bytes to finite measured-service replay. It corrects
a GF01 delivered-pin ownership bug and tests separate exact565 UI patches.
The full-path short diagnostic counts stay below30 IDs/s; broad antialiased UI
patches fail the cap while two low-color probes fit. Capture/transport CPU,
long distinct-source coverage, native/RTL and hardware gates remain open.

Previous follow-up: [iteration8 combined GM01 application-specific codec](custom-codec-prototype-v8-2026-11-03.md)
implements temporal residuals plus the explicit priority map, one-analysis
two-candidate admission, size guards and replayable golden packets. Normal
preparation is promising, while fallback/noise tails and physical30 fps gates
remain. The application-specific plan now tracks implemented software and
remaining capture/feedback, native/RTL and hardware integration.

Previous follow-up: [iteration7 application-priority coding](custom-codec-prototype-v7-2026-11-03.md)
adds a faster compatible decoder, a real macroblock ROI format, and a negative
dirty-tile comparison. The [application-specific codec plan](gamebub-application-specific-codec-plan.md)
selects temporal residuals plus a quality map as the next combined prototype,
with byte-cap, paid-search, reference-state and physical-memory gates retained.

Previous follow-up: [iteration6 key preparation, measured services and arithmetic](custom-codec-prototype-v6-2026-11-03.md)
reduces key preparation to27.67 ms mean in a paired token-entropy experiment,
retains over-budget tails, and charges actual selected-packet Python service.
The short model still misses30 diagnostic IDs/s; decoder, refresh, memory and
native-capture gates remain open.

Previous follow-up: [iteration5 host optimizations, asynchronous anchors and quality recovery](custom-codec-prototype-v5-2026-11-03.md)
adds byte-identical faster preparation, explicit reference-only refresh, causal
quality restoration and an independent corpus-overlap audit. Measured key stalls
and conditional model failures remain open; this does not qualify hardware30 fps.

Previous follow-up: [iteration4 actual codec/capture/feedback coupling](custom-codec-prototype-v4-2026-11-03.md)
tests re-encoding after skips, bounded immutable-anchor overlap and cap backoff.
It records rate/cap/quality failures and slower measured Python service; virtual
30-ID/s cases do not establish real-time or hardware performance.

Latest: [iteration3 coefficients, compressed stripes and temporal prediction](custom-codec-prototype-v3-2026-11-03.md)
now implements those next custom-codec steps. Its temporal samples are promising
against JPEG, with different reconstructed pixels and unclosed feedback/memory
gates; this does not qualify a hardware replacement.

The [executable codec study](../experiments/python-codec-study/README.md)
now implements bounded intra tile modes, spatial DPCM, compact quantization
indices, zero-residual runs, temporal reference ownership/recovery checks and
a receiver-compatible JPEG size-budget search. A companion
[memory-service study](../experiments/python-memory-study/README.md) compares
compressed storage and background-reference traffic. These advance packages
B–D and memory M3/M4 in software; they do not close native-capture, physical
memory, FPGA fit, RTL or board gates.

The initial same-canvas gameplay samples favor JPEG over the tested custom
methods. Keep it as the control. Temporal mean-size savings must survive
refresh bursts, reference loss and reference-copy traffic; average bitrate
alone is not a reason to select temporal RTL. The linked reports preserve
failed strict-window counts and differentiate model inputs from measurements.

### Development direction

The [next Python iteration report](custom-codec-prototype-progress-2026-11-03.md)
extends this with MED prediction, a fixed-point DCT candidate, a sample-stripe
oracle and finite-buffer/jitter/phase delivery tests. It records the actual
custom-codec results and the remaining coefficient, stripe-protocol and motion
steps; these software experiments do not complete the hardware gates.

Proceed with a bounded custom-codec research track alongside the existing
JPEG implementation. First reproduce the existing models and establish a
fair benchmark; then evaluate tile modes and intra-block DPCM in software.
Implement one selected FPGA candidate only after it earns an advantage over
receiver-compatible JPEG. Temporal tile deltas and motion compensation require
an explicit reference and recovery protocol before RTL integration.

Keep **720×480 at 30 distinct displayed frames/s** as the first hardware goal.
Treat 60 fps, 4–8 Mb/s, and sub-50 ms capture-to-photon latency as independent
stretch objectives. The supplied plan is a useful direction, but its phase
order and effort estimates understate memory, protocol and verification work.

The follow-up [external-memory audit and plan](external-memory-audit-plan.md)
adds required memory gates to this sequence. External SRAM is a compressed
storage candidate to qualify, not a new prerequisite; the existing SDRAM
writer/reader simulations remain the comparison path.

## Audit findings

| Priority | Finding | Required change |
| --- | --- | --- |
| Critical | Phase 0 restarts work already present: JPEG receiver, QSPI, SDRAM, LCD, telemetry and extensive simulation. | Extend that path as the control and rollback baseline. Do not replace it merely to demonstrate Tile/RLE. |
| Critical | The physical-display assumption conflicts with local implementation. | Official Rev4 documentation says 720×480; the prototype models an 800×480 panel with a centered 720×480 canvas. Identify the fitted panel, framework revision, clocks and board before changing display timing. Neither source alone verifies this particular board. |
| Critical | Tile deltas hide reference preservation and framebuffer-copy costs. | Specify reference ownership, construction of unchanged regions, atomic publication and reference lifetime. Measure the actual memory transactions. |
| Critical | ACKs alone do not define safe temporal decoding. | Distinguish packet receipt, reconstructed-reference commit, presentation, and physical memory drain. Define loss, lost ACK, reset, duplicate and stale-packet behavior. |
| High | Lossless Tile/RLE is unlikely to compress arbitrary moving 3D footage by the required ratio. | Measure it as a low-cost/reference candidate; retain RAW fallback and record overflow. Do not promise an early playable 3D-game solution. |
| High | DPCM over packed RGB565 values is underspecified. | Predict separate R5/G6/B5 channels; fix signed residual representation, quantization rounding, clipping and encoder reconstruction. Start with tile-local spatial prediction. |
| High | Capturing 60 fps while first delivering 30 adds work and can distort comparisons. | Capture native 30 fps for the first experiment. Use a separate genuinely native 60 fps corpus for the stretch goal; do not count duplicated or accelerated frames as native 60. |
| High | H.264/AV1 comparisons need actual encoder/profile constraints. | Separate low-delay real-time settings from offline compression ceilings. The RTX 2070 supports NVENC H.264/HEVC, not NVENC AV1. Verify which GPU Sunshine actually uses. |
| High | A 15k-LUT goal ignores the full memory/timing budget. | Budget LUT/FF/BRAM/DSP, FIFOs, references, memory service and routing for the complete design. Target-part implementation is required. |
| High | Independent UDP regions do not make dependent reconstruction independent. | Reset entropy/spatial predictors at region boundaries and name the exact immutable temporal reference. A tile with its own entropy state can still depend on a missing reference. |
| Medium | Published Wi-Fi throughput is treated as available pipeline margin. | Measure simultaneous Wi-Fi receive, QSPI, input/audio and memory use. A lab iperf value is not Game Bub goodput. |
| Medium | The openav1 citation is stale, and schedule/checklist values look more definite than their evidence. | Pin primary sources and report project claims as such. Replace day promises and “0/5” with evidence-backed work-package gates. |

Official documentation confirms the Rev4 XC7A100T, 64 MiB across two SDRAM
devices and a 16-bit bus, plus 512 KiB asynchronous SRAM. It does not prove
that this prototype addresses both chips or uses the current core framework.
The inspected model exposes only 2 MiB and the current memory wrapper does
not establish access to the entire advertised capacity. See the
[official overview](https://docs.gamebub.net/developing-cores/overview/),
[interface specification](https://docs.gamebub.net/developing-cores/reference-interfaces/),
[screen FAQ](https://docs.gamebub.net/faq/), and local
[SDRAM map study](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/sdram-storage-model/README.md).

Current controller sources select only SDRAM chip 0, and the streaming top
has no SRAM ports. Generic firmware memory helpers do not establish support
in this streaming bitstream. Package A must qualify chip selection, address
aliases and SRAM pin/timing/controller support before allocating the advertised
memories. Keep software/protocol byte addresses distinct from controller word
addresses.

## Numerical constraints to put in the specification

All rates below are decimal Mb/s and exclude framing, loss repair and audio.
RGB565 means 16 bits per coded pixel; it is already a quantized representation
of an RGB888 source. “Lossless Tile/RLE” must therefore mean lossless relative
to the canonical RGB565 image, not lossless relative to captured RGB888.

* 720×480 RGB565 is **691,200 bytes/frame**: 165.888 Mb/s at 30 fps and
  331.776 Mb/s at 60 fps. The supplied 332 Mb/s arithmetic is correct.
* A 16×16 tile is 512 raw bytes; there are **45×30 = 1,350 tiles**. A tile
  bitmap alone takes 169 bytes before other metadata. RLE must fall back to
  RAW whenever its tokens would expand the representation.
* At the nominal 40 MHz quad-QSPI ceiling of 20 MB/s, one raw frame alone
  needs at least **34.56 ms**, before commands or stalls. Raw frames are a
  local correctness baseline, not a full-rate network fallback.

| Video budget | Bytes/frame at 30 fps | Bytes/frame at 60 fps |
| --- | ---: | ---: |
| 4 Mb/s | 16,667 | 8,333 |
| 8 Mb/s | 33,333 | 16,667 |
| 12 Mb/s | 50,000 | 25,000 |
| 15 Mb/s | 62,500 | 31,250 |

For perspective, at 8 Mb/s a raw-tile delta stream can update at most about
4.82% of the full image per 30 fps frame, or 2.41% per 60 fps frame, before
any headers. Fills and long runs improve this; camera pans, particles and
lighting changes may eliminate most unchanged tiles. This is a capacity
calculation, not a measured codec result.

The 48 KiB BRAM candidate is a maximum storage bound, not an 8 Mb/s frame
budget: filling it every frame costs 11.80 Mb/s at 30 fps or 23.59 Mb/s at
60 fps before transport overhead. A 256 KiB SDRAM slot similarly permits a
large frame but does not make its transmission timely. Enforce both storage
capacity and a bitrate/deadline policy.

If unchanged pixels are preserved by copying an entire RGB565 reference into
the next framebuffer, the read plus write costs **41.472 MB/s at 30 fps** or
82.944 MB/s at 60 fps, in addition to scanout and changed-tile work. Tile
indirection or extra buffers can avoid some copies, but add ownership,
fragmentation and scanout complexity. Two physical SDRAM chips sharing a bus
do not double instantaneous bus bandwidth.

The external-memory proposal's 60% efficiency assumption is not measured
headroom. At 60 video fps and 60 Hz scanout, scanout plus reconstruction writes
and one complete reference read require **124.416 MB/s**, already above the
assumed 120 MB/s before other costs. At 30 video fps with 60 Hz scanout the
same example is **82.944 MB/s**. Use the actual access mix, controller service
and line deadlines to select BRAM, SRAM or SDRAM compressed storage.

The retained baseline used 7,362 LUTs, **120.5/135 BRAM tiles**, and 32 DSPs,
with only +0.031 ns reported setup slack. These belong to a particular routed
design; replacing a JPEG decoder is different from adding another decoder.
Neither arithmetic subtraction nor a standalone kernel proves fit. See the
[resource audit](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/baseline-resource-audit/README.md).

## Revised codec and protocol architecture

Use a common measured pipeline:

```text
owned PC capture → one canonical scale/color conversion → selected encoder
 → bounded packetizer/pacer → ESP32 DMA forwarding → bounded FPGA ingress
 → codec-specific reconstruction → immutable committed reference/back buffer
 → atomic display publication → independently clocked scanout
```

Keep the current JPEG/MSV1 mode available. Experimental codecs require an
explicit codec/version/profile identifier and capability agreement; they
cannot be labeled H.264 or passed to stock Moonlight as if compatible.
Sunshine integration, pairing, audio and input are separate deliverables from
a standalone codec sender.

### First custom syntax: independent tile modes

Define a frozen RGB565 byte order and an exact bounded syntax for RAW, FILL,
and RLE. Start with fully specified intra frames and standalone tile tests.
Measure palette mode as an optional candidate rather than a required feature.
Require tile coordinates, bounded decoded count and compressed length; reject
zero/oversize runs, overlaps, duplicates with conflicting contents, invalid
palette indices and out-of-frame writes. No token may cross a tile boundary.
Record whole-frame and tile hashes after reconstruction.

Only then add SKIP/reference modes. Unchanged regions must come from a named
committed reconstruction. Pick and implement one back-buffer strategy before
claiming bandwidth savings: reference copy, immutable tile map, or a separately
owned reference/reconstruction/display-buffer pool. Do not update the displayed
front buffer in place and silently accept tearing.

### DPCM: spatial first, temporal separately

Predict channels independently, with declared tile-edge seeds. Define exact
residual width, signed-to-unsigned mapping, quantization step, signed rounding,
saturation and reconstruction order. The host must reconstruct the same
pixels as the FPGA before they can be used as a future reference. Bound Rice
unary prefixes and add an escape/RAW mode for large residuals; malformed input
must not create an unbounded decode loop. Quantization alone is not rate control.

Compare RGB565-channel DPCM with an explicit YUV mode in software. A YUV420
mode needs its own color matrix/range, chroma siting, rounding, subsampling and
RGB565 output definition. It is not a register switch on the RGB565 decoder.

DPCM, RLE and Rice primarily use adders, shifters and control logic. Artificially
consuming DSPs is not a goal. DSP multipliers become useful if measured results
justify transforms, color conversion or filtering. Motion compensation is
often limited by reference-memory access before arithmetic.

### Temporal state and recovery contract

Specify these before temporal RTL:

1. A session epoch, frame ID, codec/profile, reference ID, region IDs,
   lengths and integrity fields. Define wrap, reset and stale-packet rejection.
2. A full-frame completion manifest or equivalent bounded completeness rule.
   Packet receipt is not reconstructed-reference validity.
3. Separate `REFERENCE_COMMITTED` and `PRESENTED` observations. Reference ACK
   follows validated reconstruction and required memory drain. Presentation
   can occur later. Define a bounded in-flight window; do not add a network
   round trip per tile or accidentally serialize every frame on a display ACK.
4. Start with complete-frame atomicity: on incomplete frame, retain the last
   good image, reject dependent work, and recover at a bounded independent
   refresh. Send no delta against a reference whose availability is ambiguous.
   Progressive/partial refresh requires a separate per-region validity model.
5. Test lost data, lost/duplicated ACKs, delayed previous-session packets,
   reorder, corruption, missing EOF, reset during drain, and scene cuts.
   Specify a finite recovery bound conditional on a decodable refresh arriving;
   no protocol can guarantee recovery during permanent loss of all packets.

Reuse the [tagged gateway research](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/tagged-gateway-rtl/README.md)
and [SDRAM writer/reader integration](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/sdram-jpeg-full-study/README.md).
They are useful components; production CRC, temporal reference ownership,
CDC, physical drain and complete custom packet decoding remain open.

## Execution plan and gates

| Package | Owner | Concrete deliverable | Exit gate |
| --- | --- | --- | --- |
| A. Reconcile baseline and constraints | integration + hardware | Exact board/panel/framework IDs, preserved JPEG artifacts, memory audit M0–M3 including SRAM/chip selection and actual service, clocks, concurrent Wi-Fi/QSPI measurements, resource/timing report | One agreed manifest; unresolved facts labeled; do not assume 60 Hz, SRAM support or full advertised RAM access |
| B. Common corpus and harness | host + verification | Native 30 fps captures, separate native 60 fps set, hashes/PTS, one preprocessing path, encoder/decoder adapters, structured metrics | Identical source IDs and aligned output; existing JPEG and software baselines reproduce |
| C. Tile/RLE software study | codec + verification | Bounded intra syntax, encoder, separate decoder, RAW/FILL/RLE results and worst-case tests | Exact RGB565 round trip; expansion bounded; complete size/decode-cost accounting |
| D. DPCM software study | codec + verification | Tile-local predictor/quantizer/Rice-or-fixed-width alternatives, matched reconstructed-reference tests | Independent decoder exact to encoder reconstruction; measurable advantage over simpler modes |
| E. Select one FPGA candidate | hardware + integration | Written comparison against JPEG and existing custom work, full-design resource/service estimate, frozen profile, measured storage choice from memory gate M4 | A measured benefit and a credible memory/timing implementation, not just lower average bytes |
| F. RTL and firmware integration | hardware + firmware | Codec parser/reconstructor, bounded transport, CRC/length/drain, reference protocol and real display path | Verilator adversarial tests, independent reference outputs, target synthesis/place/route and correct fault behavior |
| G. Physical gameplay qualification | hardware + host + verification | Actual board, real Windows capture/encode, weak-link/reconnect tests and synchronized/optical latency | Predeclared sustained cadence/age/loss/quality gates met with complete artifact provenance |
| H. Motion or transforms | codec + hardware | One-reference integer-motion or transform branch chosen by evidence | Incremental benefit survives memory/latency/quality/resource accounting |

Packages A and B run in parallel. C and D share syntax/metrics but initially
avoid temporal dependencies. Existing JPEG hardware integration continues
during software comparison. F starts only after E; H is optional after the
baseline custom path is justified. Scope separate worktrees and interfaces so
hardware, firmware and host agents do not edit a common protocol differently.

For E, proposed selection thresholds are either at least **25% lower total
wire bytes at an agreed comparable quality**, or at least **20% lower measured
decode latency or constrained FPGA memory use** at comparable rate/quality.
These are suggested project decisions, not measured achievements; agree them
before examining final results. Reject a candidate that meets the average but
fails frame-size tails, recovery, HUD readability or latency. A stronger JPEG
or existing GBD1/MPEG-2 result is a valid reason to stop adding custom features.

The supplied 2–4 day/3–6 day estimates may describe small software models.
They should not be used as end-to-end delivery estimates. Estimate each
package after its inputs exist, with separate model, RTL, firmware, target
implementation and hardware-validation effort. Board access, Artix tool
support and measured memory service are current dependencies.

## Benchmark contract

Preserve JPEG as the primary deployable comparison. Reuse the previous GBD1,
MPEG-2, JPEG, H.264, HEVC and AV1 experiments and their source limitations;
do not rebrand the same methods as a new codec without recording differences.
Local prior research is in `gamebub-streaming-prototype/src/codec.py`,
`results/mass-effect-benchmark/`, `results/codec-comparison/`, and
`STREAMING-COMPARISON-ROADMAP.md` outside this checkout. Pin and transfer any
reused source and manifests into the relevant developer branch before relying
on those local-only paths. Those short compressed-source tests do not qualify
live gameplay.

For each new corpus include HUD/text, foliage, particles/noise, fast pans,
dark scenes, cuts, pixel art and 2D scrolling; split tuning and held-out scenes.
Native captures should include Elden Ring at the user's configured 720p30.
Keep actual capture timing and avoid repeating frames to manufacture FPS.

Compare 4/8/12/16 Mb/s targets and also matched quality, recording **achieved**
rate. Use two clearly labeled encoder tracks: real-time low-delay settings
on the actual Windows host, and an offline efficiency ceiling. Record codec,
encoder build, pixel format, range/matrix, GOP, profile, B-frame/reordering,
lookahead, thread settings, actual frame types and first/steady-frame time.
RTX 2070 NVENC H.264/HEVC may be measured; AV1 needs a software encoder or
different hardware. Confirm the installed FFmpeg build's encoders/filters,
rather than assuming a library is enabled.

Measure final display-format reconstruction for every candidate. Report both
codec error before RGB565 output and final RGB565-expanded display error
against a common source so color quantization is visible. Report full-canvas
and active-content/cropped-HUD PSNR and SSIM; black bars can inflate scores.
Include 1:1 visual inspection and temporal artifacts. VMAF is optional with a
declared model/scale; it is not automatic evidence at this small raster.

Every result row should include source/encoder/RTL hashes, native cadence,
sent/admitted/decoded/committed/presented counts, repeats/drops, payload and
wire bytes, p50/p95/p99/max frame size, encode/decode/stage time, queue age,
presentation gaps, recovery time, FPGA resources/timing, memory traffic and
measurement scope. Measure power/temperature on hardware with display and
Wi-Fi conditions controlled; software estimates do not establish battery life.

### Rate, latency and loss acceptance

Predeclare a token-bucket or equivalent average/peak/burst budget. “Peak
sustained bitrate” needs a window and maximum burst size; a keyframe cannot
silently exceed the receiver's queue or deadline. Include packet headers,
ACK/repair traffic and reserved audio/control traffic. Compare average
bitrate, peak frame bytes and worst short-window rate separately.

Use transport-stage latency, source-to-frame-swap age, capture-to-photon and
input-to-photon as separate metrics. A 60 Hz display alone contributes up to
approximately one refresh interval of scheduling wait before scan position
and panel response. Existing one-fixture SDRAM results already contain about
22 ms of modeled reader/decode time. Therefore “under 20 ms transport” and
“under 50 ms glass-to-glass” must be budgeted and measured, not inferred from
codec speed or average FPS.

For nominal 30 fps, first exercise 1,800 distinct frames with predefined
phase/jitter cases, then a 10-minute hardware run. Define warm-up, observation
interval, permitted clock-rate error and final drain before running. Preserve
the original strict capture-window result, but also report continuous
steady-state cadence and each frame's age. A finite capture-window count
includes startup/end latency and is not by itself the steady-state service
rate. Do not shift a window after the fact to manufacture a pass. The existing
[phase counterexample](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/qspi-cadence-phase/README.md)
shows smooth spacing with a missed strict capture-window deadline.

Nominal tests should have no unexplained CRC/FIFO/SDRAM errors, stale or partial
publication, or unbounded queues. Loss tests must deliberately inject isolated
and burst loss, reorder, duplication and reset, and report counted frame
loss/repeats plus recovery. Run physical RF tests in addition to synthetic
packet faults. Promote 60 fps only after measured panel support, unique-frame
delivery, encoder deadlines and complete memory service pass the 30 fps gate.

## First reviewable work items

1. Preserve the JPEG control and publish the board/panel/clock discrepancy
   with a hardware-identification and external-memory qualification checklist
   for the board-owning team. Reuse the existing controllers; qualify SRAM and
   second-chip support separately before assigning their storage.
2. Inventory and reproduce the existing custom/standard software studies;
   add a common source/decoder adapter and explicit result schema rather than
   starting a second incompatible harness.
3. Write the intra tile and spatial DPCM format specifications and separate
   software decoders. Run corruption/bounds tests and game-corpus sweeps.
4. Freeze the reference/ACK/drain contract and perform memory-traffic replay
   before enabling SKIP or motion references.
5. Select a single RTL experiment using the agreed gate; keep JPEG available
   for immediate gameplay testing and regression comparison.

## Primary-source checks

Checked 2026-11-03; web and upstream branches can change.

* [Game Bub hardware/framework overview](https://docs.gamebub.net/developing-cores/overview/)
  and [interfaces](https://docs.gamebub.net/developing-cores/reference-interfaces/):
  official Rev4 hardware and framework contracts. The online framework is
  versioned; verify compatibility with the local fork.
* [ESP-IDF 5.4.3 ESP32-S3 Wi-Fi guide](https://docs.espressif.com/projects/esp-idf/en/v5.4.3/esp32s3/api-guides/wifi.html):
  the 30 Mb/s UDP figure is an upstream performance reference, not measured
  concurrent Game Bub service. Use the actual firmware version/configuration.
* [NVIDIA support matrix](https://developer.nvidia.com/video-encode-decode-support-matrix):
  RTX 2070/Turing supports H.264/HEVC encoding; AV1 NVENC is unavailable there.
* [FFmpeg encoder documentation source](https://github.com/FFmpeg/FFmpeg/blob/master/doc/encoders.texi)
  and [filter documentation source](https://github.com/FFmpeg/FFmpeg/blob/master/doc/filters.texi):
  available encoders and metric filters depend on the built binary.
* [openav1 README pinned at be076c4](https://github.com/Jonahss/openav1/blob/be076c470dbb8d775535c3bd8c927a336ef80c31/README.md):
  the supplied intra-only roadmap description is outdated. The project now
  reports inter prediction and FPGA testing; its documented U200 build is far
  larger than the XC7A100T budget. These are upstream self-reported results,
  not a decoder we have reproduced or a drop-in Game Bub implementation.

Replace favicon/image proxy links in the supplied text with these direct
technical sources. Preserve upstream license notices for any reused code;
custom syntax and open-source implementations do not themselves establish
patent freedom or compatibility with existing Sunshine/Moonlight negotiation.
