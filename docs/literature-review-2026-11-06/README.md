# Game Bub codec literature review after V90

Reviewed 2026-11-06 against baseline commit
`7c24b4d80b2a79a45a9a06ddc82a9ef8f83ce030`.

Planning update: the findings below now feed the
[V91–V110 roadmap](../gamebub-v91-v110-development-plan.md). V91–V99 cover the
codec experiments; **V100–V110 focus on 7-series RTL mapping, placement, routing
and timing closure**, including DSP48E1, BRAM/SRL, LUT/carry logic, fanout, CDC
and complete routed-design qualification. These phases are planned work, not
new literature benchmark results or completed implementation milestones.

V103 implementation follow-up: [geometry and parser studies](../cu66-v103/README.md)
retain exact component behavior across 288 paired case/profile runs and 304
directed checks, with independent function probes and a source/provenance audit.
Reconstruction-only synthesis improves LUT count/slack modestly; admission's
full-domain arithmetic identity saves area but worsens setup timing. Matched
routed comparisons decide the successor rather than a shorter expression.
A separate aligned-window prefix model passes 1,548,910 Python comparisons
and prepares a bounded parser RTL experiment; it is not native mapping or
whole-parser proof. The next architecture plan records concrete state/owner
obligations for cached coordinates and registered active-cell writes. These
are implementation/model findings, not new HEVC/AV1 quality comparisons or
hardware 30-fps/under-10-ms validation. E7/E6, clock/boundary/I/O and full-system
qualification remain open.

The final V103 routed A/B retains V102: reconstruction-only reduces LUTs to
48,179 but has −14.036-ns WNS; combined reduces LUTs to 47,740 but has
−17.586-ns WNS, versus V102's −13.976 ns. Both route without errors. This
negative timing result strengthens the need to measure dependency depth and
owner-safe pipelining, rather than infer a win from source operator count.

V102 implementation follow-up: the [memory/predicate experiment](../cu66-v102/README.md)
turns the literature's implementation focus into measured native results.
Paired RTL traces and canonical bytes remain equal. Combined synthesis cuts
LUTs 74,340→49,040 and LUT RAMs 22,286→3,854 while using 32 RAMB36 and 28 DSPs.
The exact-device component now places/routes (72,867/72,867 routable nets,
zero routing errors), but fails 100-MHz timing with routed WNS −13.976 ns.
The next bottlenecks are measured tile/index/enable control cones; parent
clock/boundary/I/O contracts and E7/E6 complete-path/shared-memory work remain
open. These are new implementation measurements, not published-codec quality
comparisons or achieved hardware 30-fps/under-10-ms results.

V101 implementation follow-up: [constraints and scratch evidence](../cu66-v101/README.md)
now include historical timing Tcl, reset/crossing provenance and explicit open
board/controller obligations, with the comparison clock loaded before synthesis
in the prepared flow. The priority-loop candidate preserves actual component
outputs and cycles across paired regressions and independent focused-trace
replay. Old Yosys still fails on a different converted function iterator. These
results now include native Vivado 2026.1 component synthesis and measured
capacity/timing blockers: 22,286 distributed-RAM LUTs versus 19,000 compatible
sites, with −16.629-ns synthesis WNS at 10 ns. Placement did not run. This
prioritizes the admission-memory read architecture and fixed-geometry control
predicates while leaving E7/E6 whole-path, memory-service, timing and hardware
qualification open. It adds no new codec quality, compression or
published-benchmark comparison.

V100 implementation follow-up: the [frozen baseline](../cu66-v100/README.md)
now has fresh-input component RTL parity and a two-seed original/converted
V91k behavioral regression, including canonical bytes, cycles and public ports.
Generic reconstruction leaf mapping repeats; full mapping and exact target
placement/routing remain blocked at their separately recorded frontend/device
prerequisites. This is new implementation-readiness evidence, not a new codec
benchmark or confirmation of any published physical result. The E7 whole-path,
E6 shared-memory and hardware 30-fps/under-10-ms gates stay open.

V99 E7-to-implementation follow-up: [fresh-input RC1](../cu66-v99/README.md)
now generates actual CU66/CS88 from the retained RGB corpus, with independent
native/pixel/BR88/C2 parity. The selected all-BR88 q16 candidate uses the actual
V91 metadata subset; all120 selected frames fit the cap. Direct packet equality
and cross-key controls are verified, with new RTL-facing goldens exported.
[Measured results](../cu66-v99/results.md) still show a slow Python sender,
not hardware 30 fps or under-10-ms FPGA decoding. This closes the fresh-encoder
comparison gap, while original raw/perceptual/held-out and complete physical
integration gates stay open. No published-codec superiority is inferred.

V98 E7 follow-up: [common-input controls](../cu66-v98/README.md) now retain
52 HEVC/AV1/JPEG/historical-GM01 software runs, 1,560 round trips and a new
user-supplied 30-Hz selected combat sample. Actual bytes, shared color arithmetic,
emitted syntax, host costs and ROI/temporal pixel proxies have an independent
6,459-check integrity/arithmetic audit. [Results](../cu66-v98/results.md) do not
justify promoting the historical custom or unconditional global motion.
All game sources are precompressed, and the current CU66 fresh-RGB encoder is
not in this lane; those facts leave the raw/current-codec gap open. No new
literature benchmark reproduction, perceptual superiority, target FPS or FPGA
latency result is inferred. Longer original captures, current encoder/receiver
parity and earlier complete-path gates precede V99 freeze.

V97 transport follow-up: [bounded compact transport and live native-Rust/RTL](../cu66-v97/README.md)
now exercise actual FIFO credit/ACK feedback and explicit capability negotiation.
An independent 469-row comparison measures 3.528% fewer IPv4/UDP bytes including
setup; body bytes/quality are unchanged. Native and RTL recovery tests do not
establish ESP32 CPU/Wi-Fi/QSPI service or complete decoder throughput. Production
worker/driver integration, target memory telemetry and hardware calibration
remain open. [Results](../cu66-v97/results.md) distinguish ingress completion,
opaque custom-profile testing and native-host substitutes from decoded output.

V96 E6 follow-up: [bounded materialized copies and constant service](../cu66-v96/README.md)
now have an exact accepted-reference inventory and standalone timed-controller
RTL evidence. 64/256-entry dictionaries expose 2.76%/4.68% of active residual
blocks as additional exact copies; source reads and destination writes remain
charged. 2,601 component checks cover actual addressed memory, leases and
cancel/retry. A separate Python constant-display model identifies a potential
3.63% read-command reduction while charging generation work. These are not
full-path latency, compression or HEVC/AV1 wins. E6's complete shared-display,
validation/HUD and no-underrun promotion gate remains open; no arbitrary alias
or compacted physical window is introduced. [Results](../cu66-v96/results.md)
retain the control and name the required integration.

V95 E5 follow-up: [exact pixel palettes](../cu66-v95/README.md) now have
bounded own/reused palettes, TOP/LEFT runs, escapes, RAW and actual residual
fallback. Independent readers and 4,113 complete native frames preserve exact
canonical/HUD/display commitments. No minimum-byte gain appears on the retained
457 sources. Work5/work15 bypass 2.15%/6.88% of active residual blocks for
3.47%/12.22% extra complete bytes; no measured decode speed follows from that
proxy. Retain the control and require integrated memory/latency evidence before
promotion. [Results](../cu66-v95/results.md) are a new custom experiment inspired
by screen-content tools, not an HEVC/AV1 palette-mode reproduction. Original
coefficients are preserved only on fallback tiles; the exactness contract for
palette tiles is their reconstructed pixels. Lossy clustering and broader raw
captures remain deferred.

V94 E3 follow-up: [bounded inline byte-rANS](../cu66-v94/README.md) now has
two/four-state, precision-8/9/10 packets and a real RTL category kernel. All
model/state overhead is charged. Rate-aware parameter tuning improves the local
minimum by only eleven complete bytes across the retained 457 sources; this
does not justify default promotion. A cap-tail tradeoff remains: tuned uniform
rANS fits all sources while uniform BR exceeds the cap once, at higher mean
bytes. [Results](../cu66-v94/results.md) separate native full-frame parity from
partial RTL evidence. Actual tANS, calibration-only fixed models, acknowledged
caches and integrated physical timing remain open; this is not a reproduction
of the referenced FSE/tANS benchmark or an FPGA throughput result.
The no-refill RTL follow-up saves 17.93% of matched kernel clocks on selected
actual-source contexts; it retains the staged control pending physical timing.

V93 E2 follow-up: [fixed suffix bypass and small-block Rice](../cu66-v93/README.md)
now have actual-byte and independent software evidence. Uniform HY removes
41.30% of uniform AB's arithmetic decisions for 3.101% more complete bytes.
SG32's lower plain-bit count loses after group headers; exact minimum bytes
remain unchanged from V92. The all-suffix bypass rule and group size were fixed
before observation; histograms are descriptive rather than a trained held-out
policy. [Results](../cu66-v93/results.md) include complete-frame parity,
recovery, cap failures and host costs. These experiments do not reproduce a
published benchmark, qualify a mixed-method RTL path or establish FPGA speed.

Follow-up experiment: [V92 E2 actual per-context choices](../cu66-v92/README.md)
now has independent software evidence on the retained 457-source corpus.
Minimum-byte coding saves only 2,560 complete bytes versus the frozen AB38
control. At the same 15% byte allowance, finer selection reduces remaining
adaptive decisions by 980,296 versus whole-plane choices, using 31,453 more
bytes. The byte/work result supports further integrated costing, not a claim
of faster FPGA decoding or improved picture quality. Mixed-context RTL, physical
memory service and V92d promotion remain open; the original literature findings
and their reported benchmark scope are unchanged. See the
[measured results](../cu66-v92/results.md).

The strongest next experiment is **a word-oriented BR88 parser coupled to a
decoder-cost-aware host policy**. For better compression, compare a small-table
interleaved ANS candidate and a prefix/suffix hybrid against the current
arithmetic/Rice choices. For a more application-specific format, the most useful
new lead is HLC's palette/prediction combination, with clustering on the PC and
bounded lookup on the FPGA. A wholesale HEVC/AV1 implementation remains a separate
feasibility project.

These recommendations are an engineering synthesis of the primary sources below
and our retained experiments. No new codec, FPGA timing result, firmware deployment
or physical 30-fps result is claimed by this review.

## Review method and scope

This is a focused engineering literature review, not an exhaustive systematic
review. It extends the [V90 review brief](../cu66-v90/literature-review-prep.md)
using author papers, official standards and pinned maintainer code. Targeted
architecture, evaluation and limitations sections were read; reading selected
clauses of a standard does not establish complete conformance expertise.

The [source log](sources.json) records queries, access depth, publication versus
upload dates, implementation pins and access failures. The
[comparison matrix](comparison-matrix.csv) separates reported FPGA implementations,
RTL simulations, software algorithms and specifications. Missing results are
explicitly unreported, rather than zero. Published benchmarks have not been
reproduced here. An inaccessible full paper is not performance evidence.

## Our current control

The target remains **720×480 at 30 fps**, followed by **strictly under 10 ms for
complete validated FPGA decoding**. The current research codec uses temporal
reference reuse, fixed 8×8 residual tiles, quantized DCT reconstruction, sparse
DC/three-AC-band streams, exact HUD composition and explicit publication checks.
CS88 selects adaptive arithmetic-coded bounded Rice (AB38) or plain bounded Rice
(BR88) separately for each of three whole-plane chunks. COPY aliases, compact
mode/quantizer metadata and a separate fixed-hidden-tile constant sentinel reduce
work in different experiments. The constant sentinel is not in V90's joint timing.

| Retained result | Actual evidence | Interpretation |
|---|---|---|
| V88 AB38 control | 7,784,499 complete frame bytes / 457 sources | 17,033.91 B mean; nominal 4.088 Mbps at 30 Hz |
| V90 byte/decode-work proxy | 8,319,065 B / same 457 sources; maximum 48,744 B | 18,203.64 B mean; nominal 4.369 Mbps; all fit the 49,152 B experimental cap |
| V88 all-BR88 component coding | Removes 37,656,819 adaptive decisions and 33,238,189 renormalizations | Retains 37,656,819 plain bit reads; residual chunks grow 12.64% |
| V90 selected key, HIGH costs | 10.08595 → 8.12490 ms versus earlier 15% policy | Offline exact choice changes the representation; conditional model only |
| V90 selected hard frame | Best 10.80320 / 12.29713 ms, LOW / HIGH | Still above 10 ms after searching all eight plane masks |

These numbers come from [V88](../cu66-v88/entropy.md),
[V90](../cu66-v90/README.md) and the
[recomputed arithmetic](derived-comparison.json). Data rates count complete
research frames, excluding network/QSPI overhead, retries, ACKs, audio and input.
The cap is a profile/admission choice, **not a measured BRAM/SRAM ceiling**.

All 457 sources belong to one related, precompressed walkthrough family in four
reset histories. Native receiver parity is substantial correctness evidence;
the exact V90 timing search covers four sources, not all 457. Milliseconds assume
100 MHz and hypothetical operation/memory costs. Physical RAM ports, refresh,
continuous scanout, full HUD service and finite ESP32 ingress remain open.

Memory deserves equal priority with entropy: the addressed alias study's
maximum on-chip-descriptor decoder memory-busy work is **9.99088 ms** under its
assumptions. The separate constant-sentinel experiment lowers that necessary
work maximum to **9.80272 ms**, but does not time constant generation and is
not integrated into V90's completion graph. Faster parsing alone cannot remove
this traffic. These are service-work bounds, not measured frame latency or
numbers to subtract from another experiment's total.
See [constant and traffic evidence](../cu66-v89/constants.md).

The public Rev4 overview lists an XC7A100T, 64 MiB SDRAM and 512 KiB SRAM. Its
framework exposes raw external-memory signals; the documented host memory
interface is non-bursting. An FPGA SPI sampling-clock requirement is not a
measured MCU payload rate. Our retained JPEG routed report uses 120.5 of 135
BRAM tiles, so table/line-buffer capacity requires a new whole-design allocation.
The custom decoder has no verified replacement fit yet.
See the [board overview](https://docs.gamebub.net/developing-cores/overview/),
[interfaces](https://docs.gamebub.net/developing-cores/reference-interfaces/),
[local resource audit](../gamebub-hevc-av1-fpga-plan.md) and
[routed JPEG utilization](../../fpga/build-final/utilization.rpt).

Implementation follow-up: the [V91l live write-ACK lane](../cu66-v91l-live/README.md)
connects actual supported BR88 reconstruction to integrity/publication while
retaining the native C++ HUD endpoint. The [eight-byte tile-row comparison](../cu66-v91l-rows/README.md) now implements
that bounded writer with explicit candidate x16 transfer cost and preserved
ACK/hash ownership. The standalone physical controller bridge is qualified
below; joining that service to this live path and all x16 clients remains open. This is a local architecture proposal arising
from the implementation; it is not a new publication result or evidence of
HEVC/AV1 superiority. Use its live simulation summary for measured cycle fences,
and keep shared physical service and hardware goals unqualified.

The [physical read/base-RGB integration](../cu66-v91l-readbridge/README.md)
now joins retained canonical reads to the actual controller/timed pins and the
frozen native base RGB565 converter. Exact canonical/RGB outputs and physical
capture/drain receipts are checked. The isolated retained read consumer is about
0.847M cycles, but the actual complete scalar display consumer is about 3.36M
under physical service: roughly 33.6 ms at the assumed 100 MHz. This exposes
byte-consumer overhead and a marginal isolated 30-Hz budget; it establishes no
hardware FPS or complete validated decode result.

The [direct owned-line comparison](../cu66-v91l-burst-converter/README.md)
now removes external per-byte leases on 486,000 cache hits/frame, preserving
32,400 physical BL8 reads and exact native base RGB. Timed conversion is about
2.87M clocks (28.70 ms at assumed 100 MHz) versus the frozen scalar's 3.36M,
roughly 14.6% fewer cycles. It reuses the existing 48-byte plane cache and
unchanged registered chroma RAM/arithmetic, with no extra payload storage.
Independent byte/RGB/pin checks and directed cache ownership/error tests retain
source and artifact hashes. Physical timing of the new byte-selector path
still needs 7-series implementation evidence.

Native memory is preloaded in those isolated display controls. The following
[live shared-controller experiment](../cu66-v91l-shared-service/README.md)
now removes that preload for a serial supported BR88 reconstruction→physical
candidate writes→RTL validation→same-memory base RGB run. Four configurations
pass eight complete RGB outputs and all 8,200 actual RTL SHA digests; physical
pin/command/ownership replay is independent of the native driver's verdict.

Live start→commit is 25.06–27.68 ms, RGB about 29.04 ms, and serial closure
54.10–56.72 ms at assumed 100 MHz. The observed packet-complete→commit window
is 24.78–27.30 ms under the partial service. Reference/scratch still use finite
logical endpoints, HUD semantic decode stays in native C++, and native overlap
is unqualified. This is stronger integration evidence with exposed real costs,
not a compression improvement or a result comparable to HEVC/AV1 coding speed.

The [physical reference extension](../cu66-v91l-reference-reader/README.md)
now removes the logical reference actor: full64-tagged 64-byte tiles arrive
through four actual BL8 reads from the accepted key bank. A delta needs
7,806 tiles/31,224 reads/249,792 x16 words; 64 bytes of new reader payload are
explicitly charged. Four native configurations retain exact RGB and all 8,200
RTL SHA digests, with independent mux/descriptor/chunk/pin replay. The Python
traffic/byte model also checks three actual delta cases; the native RTL corpus
remains the selected key/delta pair.

At assumed 100 MHz the reference-inclusive delta start→commit window is
31.40 ms and subsequent RGB about 29.37 ms; serial closure is about 60.77 ms.
These more complete internal-memory costs are not new codec bitrate/quality
results or HEVC/AV1 coding speed comparisons. That retained control excludes
physical scratch and native HUD.

The [physical packed-scratch extension](../cu66-v91l-scratch-service/README.md)
now connects scratch to the same controller using a reserved bank-3 aperture.
All four external memory endpoints are RTL clients. Full 128-bit lines cost
eight x16 WRITE commands or one BL8 READ, with actual pin traffic and drain
charged. Its [results](../cu66-v91l-scratch-service/results.md) retain the same
source bytes, validation, reference and base RGB oracles. The Python contract
checks aperture bounds/nonaliasing and payload assembly; the native RTL
campaign measures scratch traffic rather than inferring it from the old C++
endpoint. The [native overlap experiment](../cu66-v91l-overlap/README.md) now measures
key RGB alongside delta decoding with an immutable display-source lease and
actual publication drain. Four natural modes are separated from a directed
final-pixel hold; the [results](../cu66-v91l-overlap/results.md) report
measured pair completion and contention costs. Lower pair completion time
comes with increased delta decode latency, so this is not 30-fps cadence
proof or new HEVC/AV1 coding performance. Next compare a bounded scheduling,
reference-reuse or prefetch change using these measurements, then close full
RTL HUD and the complete V91m cadence gate.
The natural pair interval is 18.89% lower (121.85 → 98.83 ms at assumed
100 MHz), but delta commit latency rises to about 40.12 ms. Actual pin
ACTIVATE commands increase 66.11% in one matched case, with unchanged
READ/WRITE counts and repeated bank-0 row activation. This is evidence to
investigate bounded tile-granularity read grants/locality; it is not a new
publication result, codec quality improvement or complete latency attribution.
The [bounded reference-tile grant follow-up](../cu66-v91l-tile-grant/README.md)
now tests that hypothesis with unchanged codec bytes and native C++ workload.
Pair completion decreases a further 1.807–1.810% to 97.043–97.051 ms at
assumed 100 MHz, and delta commit to 38.328–38.341 ms; key RGB is slower at
36.865–36.866 ms. A matched pin trace reduces ACTIVATE from 47,459 to
36,713 with unchanged READ/WRITE counts. Up to4:1 reference/display credit
weighting also changes, so balanced-service controls are the next experiment.
These are new local implementation measurements, not new literature findings,
HEVC/AV1 coding comparisons, fixed-cadence or hardware performance claims.

 These are local implementation
measurements, not new publication findings. Hardware 30 fps and complete
validated decoding below 10 ms remain open.

## Literature findings compared with V90

### 1. Parallel Golomb–Rice parsing: best direct fit

Moussalli et al. (FCCM 2013) process fixed-width chunks through speculative
delimiter pipelines, then reconstruct symbols spanning chunk boundaries.
Their evaluation reports about 7 Gbit/s **compressed input** throughput for a
32-bit, k=3 design on a Virtex-6 LX240T, around 10% of its logic. The smaller
one-integer builder explicitly needs FIFOs and backpressure; the rate is not a
complete image-decoder measurement.
[Author paper, §§IV–V](https://www.cs.ucr.edu/~najjar/papers/2013/FCCM-2013.pdf).

**Transfer to us:** start with a 32-bit refill and 64-bit reservoir, capped
leading-zero detection and one symbol extraction path. BR88's maximum symbol
is 39 bits, including its literal escape. Its changing Rice parameters and
escape syntax require our own parser; the published unmodified-GR design is
not a drop-in. Keep run accumulation, scatter order, CRC and downstream credit
stalls in the experiment. Wider speculation is useful only if those consumers
can accept it. This can preserve every existing BR88 byte and pixel.

### 2. Block adaptation and RLGR: cheap alternatives to test

CCSDS 121.0-B-3 uses small block-adaptive coding choices, with explicit option
identifiers, zero-block and no-compression alternatives; its standardized block
sizes are 8, 16, 32 and 64 samples. Malvar's RLGR instead adjusts run/Golomb–Rice
parameters from previously decoded codewords, addressing changing, highly
zero-peaked quantized distributions.
[CCSDS §§2–5](https://ccsds.org/Pubs/121x0b3.pdf),
[Malvar, DCC 2006, §§3–4](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/Malvar_DCC06.pdf).

**Transfer to us:** measure explicit small-group parameter selection versus
backward adaptation on our real coefficient events. BR88 already has runs and
exact parameter search; the new question is whether *local* changes repay
metadata and reset costs. RLGR removes probability tables but introduces a
symbol-to-symbol adaptation dependency. It is a control candidate, not an
assumed improvement over a host that already knows the whole block. Preserve
finite escape bounds and raw fallback in any derived syntax.

### 3. ANS/rANS/tANS: strongest entropy replacement candidate

Duda describes arithmetic-like entropy coding with a single integer state and
table-based variants. Giesen shows how independent states can share a stream
without per-symbol interleave tags; independence and state synchronization are
essential. His evaluations are CPU/SIMD/GPU work, not Game Bub FPGA results.
[Duda, v2, §§2–4](https://arxiv.org/html/1311.2540v2),
[Giesen, §§2–7](https://arxiv.org/html/1402.3392v1).

The pinned byte-rANS implementation encodes backwards but decodes forwards,
flushes four bytes per state, and uses a multiply/shift state update plus byte
refill on decode. FSE exposes normalized-count headers, table construction and
caller-managed raw/RLE cases. Its table macro allocates `4*(1+2^tableLog)` bytes:
four log-9 tables cost **8,208 logical bytes**, before ports, replication and
buffers. [Pinned rANS code](https://github.com/rygorous/ryg_rans/blob/c9d162d996fd600315af9ae8eb89d832576cb32d/rans_byte.h),
[pinned FSE API](https://github.com/Cyan4973/FiniteStateEntropy/blob/9f30e0918f87bd835fa040d922a208d7b219e50b/lib/fse.h).

**Transfer to us:** compare 2/4 interleaved states, 256/512/1,024-state tables,
fixed model IDs and explicitly updated models. Code small magnitude/run
categories plus bounded raw suffixes rather than an enormous direct run
alphabet. The PC can perform reverse encoding and table search; the ESP32
should forward opaque bounded chunks. Charge initialization, table bytes,
escapes, termination, lookup ports and model-cache recovery. ANS retains state
dependencies; interleaving helps hide their latency rather than abolishing it.

### 4. Prefix arithmetic plus raw suffixes: a useful middle option

H.265's entropy process distinguishes context-coded and bypass bins, rather
than adapting every bit alike. AV1 has CDF-based symbol decoding, not ANS.
These standards suggest testing selective statistical coding without importing
their entire decoder. [H.265 (01/2026), §9.3](https://www.itu.int/rec/T-REC-H.265-202601-I/en),
[approved AV1 specification, §§8.2–8.3](https://aomediacodec.github.io/av1-spec/av1-spec.pdf).

**Transfer to us:** AB38 currently arithmetic-codes both unary and suffix bits
(`Arithmetic::rice`). Try retaining adaptation for useful prefix decisions
while placing selected remainder/literal bits in a separate raw stream.
Our raw-stream proposal is new local syntax, not CABAC's bypass implementation.
Measure each suffix position's coding gain before bypassing it; sign/suffix
bits are not guaranteed equiprobable. This may regain part of BR88's byte
penalty with fewer feedback operations than AB38. No savings are established yet.

### 5. Decoder-cost-aware encoding: directly extends V90

Herglotz, Heindel and Kaup extend rate/distortion optimization with a
feature-based decoder-energy model and evaluate measured HEVC software energy.
The journal article is January 2019; its arXiv copy was uploaded in 2022.
Its energy tradeoffs are evidence for an optimization method, not FPGA latency
coefficients. [Paper, §§IV–V](https://arxiv.org/html/2203.01099v1).

**Transfer to us:** replace a bit-count objective with a constrained objective
using measured parser work, burst/descriptor costs and publication dependencies.
V90 already demonstrates why this matters, but its proxy nearly always chooses
all-Rice and is not a completion estimator. Calibrate on RTL counters, freeze
the model, validate on held-out frames, and charge live host preparation.
With unchanged coefficients, distortion is constant; timing and bytes decide.
When adding prediction/palette/quantization, reintroduce quality and temporal
drift constraints. A sum of energy features cannot certify a hard deadline.

### 6. HLC and HEVC screen-content tools: most useful new format direction

HLC (2026, author accepted ISCAS manuscript) combines palette and directional
prediction with rate/distortion selection and reusable entropy statistics.
Its 16×4 units reduce line-buffer depth; palette indices exploit left/top
matches. Table I reports a **50k-LUT, 4,256-Kbit, 2-DSP decoder at 300 MHz on
KC705**, alongside an 82k-LUT encoder. The evaluated targets are 1–1.75 bpp.
Those are the authors' implementation results, not a measured Game Bub fit.
[HLC, §§II–III and Table I](https://arxiv.org/html/2603.29864v1).

HEVC-SCC similarly uses palette/escape coding and intra-picture block copy
for repeated text and graphics. Referencing already reconstructed current-picture
data creates dependencies that our accepted-reference COPY mode does not have.
[Xu, Joshi and Cohen, 2015, §§III–IV](https://www.merl.com/publications/docs/TR2015-126.pdf).

**Transfer to us:** keep clustering/search on Sunshine's PC. Start with small
exact palettes and bounded left/top runs, admitted only when complete bytes or
decoder work improve. Preserve the existing HUD path and canonical hash contract.
Our previous many-color palette experiments were often dominated by raw data;
new small palettes plus prediction need evidence on actual gameplay, not another
flat synthetic success. Defer arbitrary intra-picture copying until ownership
and consumer ordering are proved. See [earlier application plan](../gamebub-application-specific-codec-plan.md).

### 7. JPEG XS and its newer prediction work: borrow the architecture carefully

JPEG's official overview emphasizes line-scale latency, parallelism and precise
rate control, typically up to 10:1 compression, with content-dependent exceptions.
It is designed for a different bandwidth/quality operating region from our
temporal codec. [JPEG XS overview](https://jpeg.org/jpegxs/).

A 2026 Artix-7 paper reorganizes wavelet coefficients around prediction groups
to improve bursts for **displacement-vector search**, reporting 38.3 Mpixel/s
on XC7A35T at 100 MHz. That is an encoder search module, with 73.01 ms reported
latency—not a complete decoder or our sub-10-ms result.
[Chen et al., §§III-D–IV](https://arxiv.org/html/2603.10671v1).

**Transfer to us:** organize fetched coefficients/reference tiles around the
actual consuming group and amortize address generation over bursts. Test the
display's access pattern too: decoder-friendly tiling can hurt raster reads.
Wavelet replacement or temporal differential coding is a separate lossy-format
study; line latency does not survive automatically through full-frame validation.
The XS whitepaper/requirements PDFs could not be retrieved in this review, so no
claims depend on their unread contents.

### 8. DSC and a formal buffer contract: important for real 30 fps

The VESA DSC whitepaper describes line-buffered prediction, indexed-color
history, bounded-rate coding and substream parallelism; its 8-bpp quality
example is much larger than our wire target. The VESA HRD presentation specifies
both arrival/removal schedules and checks every intermediate buffer occupancy,
not just final packet size.
[DSC whitepaper, pp. 2–4](https://vesa.org/wp-content/uploads/2014/04/VESA_DSC-ETP200.pdf),
[HRD presentation, slides 4–8](https://vesa.org/wp-content/uploads/2024/03/HRD-Buffer-Model-Intro121026.pdf).

**Transfer to us:** add a Game Bub-specific buffer/service contract covering
Wi-Fi bursts, ESP32 copies, QSPI transactions, parser consumption and scanout
deadlines. V90 starts with fully buffered input; that is a different latency
fence. Maintain validation before whole-frame publication unless a separately
versioned authenticated stripe contract is developed. Skipping validation to
show the first line earlier is not the same milestone.

### 9. Recent accelerator claims that need restricted interpretation

RAS (2025 preprint) uses multi-lane rANS with cached probabilities and speculative
CDF search. Its evaluation is Icarus RTL cycle simulation against a Python
baseline, excluding probability generation and host I/O; silicon PPA is future
work. This supports exploring bounded lookup/search, not quoting its speedup as
FPGA frame performance. [RAS, §§IV–V](https://arxiv.org/html/2511.04684v1).

PaGoRi (DDECS 2024) targets neural-network weights. Only its institutional
abstract was available here; process, complete resource conditions and full
implementation were not reviewed. It remains a reading lead, excluded from
performance ranking. [Institutional record](https://portal.fis.tum.de/en/publications/pagoria-scalable-parallel-golomb-rice-decoder/).

## Comparison with full HEVC and AV1

There are two independent questions: compression efficiency and whether a
complete decoder fits and meets deadlines on this board. Our
[existing same-window native comparisons](../custom-codec-prototype-v67-2026-11-05.md)
still favor HEVC/AV1 for complete bytes at the sampled mean-quality gates:

| Earlier 24-frame window | HEVC fewer bytes than that custom control | AV1 fewer bytes |
|---|---:|---:|
| Clip 10000 | 48.44% | 50.54% |
| Clip 4500 | 46.75% | 49.05% |
| Clip 1600 | 56.38% | 65.61% |
| Combat | 32.89% | 37.50% |

This is historical V63/V67 evidence, **not a new V90 quality-matched benchmark**.
Mean gates differ from every-frame gates, and native totals include an 80-byte
binding allowance rather than a deployed serialized native wrapper. Current
entropy/layout changes preserve existing quantized pictures; they do not erase
the earlier prediction/quality gap. Fresh common-source curves are required.

A pinned public AV1 RTL project reports 292k LUT, 831 DSP and 271 URAM for its
50-MHz U200 inter build. That version cannot fit the A100 unchanged; the report
does not prove a smaller restricted decoder impossible. Its host and unsupported
features also matter. [Pinned openav1 README](https://github.com/Jonahss/openav1/blob/be076c470dbb8d775535c3bd8c927a336ef80c31/README.md).

Maintain a constrained HEVC feasibility lane: fixed 8-bit 4:2:0, no reorder,
declared reference/tool limits, actual syntax checks and independent decode.
The supported stream subset must be enforced; an encoder preset alone proves
no bound. Borrowing selected tools into a custom syntax gives no HEVC/AV1
compatibility. See the [existing standard-decoder plan](../gamebub-hevc-av1-fpga-plan.md).

## What the bandwidth arithmetic says

The [reproduction script](../../scripts/literature-review-2026-11-06/derive_comparison.py)
calculates the following. Published bpp examples are not quality-matched tests:

| Operating point at 720×480, nominal 30 Hz | Bytes/frame | Rate, before external transport |
|---|---:|---:|
| V90 selected mean, complete research frames | 18,203.64 | 4.369 Mbps |
| Current complete-frame admission cap | 49,152 | 11.796 Mbps |
| HLC evaluated 1-bpp target, image coding only | 43,200 | 10.368 Mbps |
| HLC evaluated 1.75-bpp target, image coding only | 75,600 | 18.144 Mbps |
| 10:1 example from 8-bit YUV420, image coding only | 51,840 | 12.442 Mbps |
| DSC whitepaper 8-bpp example, image coding only | 345,600 | 82.944 Mbps |

HLC's lower evaluated rate is worth benchmarking near our peak budget, but
already exceeds our measured mean. JPEG XS/DSC latency does not imply comparable
compression at our mean rate. Their architecture ideas can be more useful than
adopting their complete format.

## Recommended experiments and decision

[V91 implementation follow-up](../cu66-v91/README.md) tests the first parser
recommendation: exact full-corpus coefficients and fewer cycles in a clocked
real-stream RTL component, with negative Python/native CPU speed results.
These are project experiments, not new published literature or physical
frame-rate evidence. The [V91b follow-up](../cu66-v91b/README.md) adds
metadata-derived context requests, run/scatter validation and finite output
credit; its real-context word path uses 26.92% fewer cycles than its matched
serial control. V91c below extends packet and memory work. This is implementation
evidence following the review, not another published-literature result or new
source-count increase.

[V91c](../cu66-v91c/README.md) follows with full BR88 packet/CRC/raw RTL and an
E6 packed-scratch prototype: direct block/raster/value records reuse parser
addresses, three AC lookahead heads recover implicit zeros locally, and the
corpus peak allocation falls from 658,432 B dense to 134,352 B packed. This
trades value-record bytes for capacity and sequential access; a dense/bitmap
control retains a useful-byte advantage under ideal memory service. Physical
RAM ports/controller, frame consumers and routed performance remain unqualified.

[V91d](../cu66-v91d/README.md) connects that packed layout to packet validation
in RTL over an acknowledged finite-latency memory interface. A local validity
mask removes 63 serial clear cycles per coded tile, reducing actual-packet
coefficient-endpoint cycles 34.43%/27.10% in two explicit memory scenarios.
This is application-specific implementation evidence; external-memory overlap,
the pixel/reference/HUD/hash path and physical timing remain open.

[V91e](../cu66-v91e/README.md) supplies per-stage/event observability, exact
legacy metric parity and broader peak-memory coverage. In its explicit slower
scenario, dense delivery/consumer hold dominates ACK waits; both memory and tile
service need attention. This is measured coefficient-endpoint occupancy, not
a new literature result, a scheduling speedup or validated full-frame latency.

[V91f](../cu66-v91f/README.md) tests the bounded-write-overlap recommendation:
two line owners and one accepted physical request reduce actual-packet service
cycles 6.79–6.80% in the stated slower-memory scenario, with unchanged bytes and
exact dense coefficients. FAST is effectively neutral. Two final seeds and
integrated/direct ownership recovery tests pass; an abstract Python reference
checks bounded ACK/cancellation/epoch events. This is implementation follow-up,
not a new literature finding or a HEVC/AV1 compression win. Read/tile overlap,
synchronous ports and complete-frame validation remain ahead of hardware gates.

[V91g](../cu66-v91g/README.md) adds a measured needed-line read-prefetch
checkpoint, reusing four cache payloads with one physical outstanding request.
Actual-packet coefficient service improves another 0.94% FAST and 5.18% SLOW
versus V91f, preserving bytes and exact output. Two seeds pass matched controls,
canonical reordered-service accounting and read-specific recovery/hold tests;
a bounded Python ownership reference is retained separately. This qualifies a
prefetch implementation, not full next-tile merging, compression superiority,
physical timing or hardware frame rate. The V91g2 follow-up below addresses
next-tile merge; synchronous ports and complete-frame validation follow.

[V91g2](../cu66-v91g2/README.md) completes the next-tile scheduling follow-up:
two bounded banks overlap actual DC/AC preparation with delivery, preserving
RAW controls, all bytes and intended coefficients. Actual-packet service uses
16.08% fewer FAST cycles and 16.30–16.31% fewer SLOW cycles than V91g prefetch.
Two final seeds, bank-owner/recovery tests and an independent abstract Python
model pass. This is implementation evidence, not a new literature finding,
compression-quality win or hardware frame-rate result. Next make staging ports
synchronous, then integrate the full reconstruction/validation path.

[V91h](../cu66-v91h/README.md) replaces zero-latency packet-array assumptions
with a static registered byte-read port, preserving exact bytes/coefficient
output and rejection behavior. The measured actual-packet cost is +0.1000%
FAST and +0.0865–0.0921% SLOW versus V91g2. Two seeds, separate static controls,
byte/purpose accounting and cancellation/held-output tests pass. This qualifies
functional port semantics, not inferred BRAM, routed timing or hardware frame
rate; outer-frame and full reconstruction/validation integration remain next.

[V91i1](../cu66-v91i/README.md) adds restricted structural admission on actual
CS88 packets without changing wire bytes or quantization. Independent Python
parsing and two strict RTL seeds agree on 51 retained native variants, one
synthetic zero-residual case and 34 rejection vectors; each seed also passes
14 interface/recovery checks. These fixtures cover eight cohort/frame identities,
not new held-out gameplay. Typed AB38/BR88 descriptors remain unconsumed, and
accepted references/HUD/content seals/publication remain later gates. This is
implementation progress toward a complete application-specific receiver, not
compression superiority over HEVC/AV1 or hardware throughput evidence.

[V91i2a](../cu66-v91i2/README.md) connects the actual all-BR88 frame subset to
the coefficient RTL with provisional plane/tile/qcell/qscale binding. Two
seeds each pass 4,058,368 exact coefficient/tuple checks under two finite memory
models, 63,412 observed tile records and 10 recovery checks. Four related native
frames reuse existing exact goldens; synthetic variants do not broaden content
coverage. It explicitly budgets 98,304 bytes of duplicate packet staging and
measures a worst tested native coefficient path of 1,140,868 cycles from start.
This is a new integration baseline, not a codec-rate/quality gain, full pixel
decoder, physical memory-fit result or hardware frame-rate proof. Next compare
bounded refill overlap while retaining safe ownership, then complete entropy
fallback and transform/reconstruction/validation consumers.

[V91i2b](../cu66-v91i2b/README.md) closes the bounded refill experiment:
native coefficient cycles fall 5.1656% FAST and 4.2342–4.2450% SLOW, with exact
disabled-control parity and no coefficient/quantization change. FAST isolates
deterministic refill cost; SLOW uses the same seeded service rule without an
identical absolute stall trace. V91j below qualifies the actual inverse blocks
behind bounded tile/epoch ownership, extending the prior constant-compatibility
check (384 quantizers, 64 DCT values) to live-stream arithmetic. Reconstruction
and hardware milestones remain open. More V91i nesting is not a prerequisite,
and this is not a rate/quality gain over HEVC/AV1.

Proceed in this order; [the executable work specification](experiments.md)
defines controls, gates and failure cases:

1. **Calibrate word-window BR88 parsing and the full memory/validation path.**
   Preserve format and quality; measure stall-inclusive work before spending
   more resources on entropy parallelism.
2. **Try finer AB38/BR88 selection and prefix/raw-suffix coding.** Price actual
   emitted bytes, framing and host search. Keep V90 as a control.
3. **Add a bounded-table 2/4-state ANS challenger.** Compare table-inclusive
   bytes, DSP/BRAM/ports and worst completion against both AB38 and BR88.
4. **Prototype small palettes and bounded exact copy for UI/repeated regions.**
   Use host search, explicit fallback and causal reference checks. Introduce
   lossy choices only in a separate matched-quality study.
5. **Integrate an arrival/service buffer contract and common raw-capture
   HEVC/AV1 benchmarks.** Include scene changes, noise, HUD readability and
   temporal stability; measure host encode time as well as receiver work.

The application-specific opportunity is the **joint host decision, simple FPGA
decode, memory layout and robust publication contract**. It is not a claim of
a newly invented entropy principle or present superiority over HEVC/AV1.

| Component | Recommended division of work to test |
|---|---|
| Sunshine PC | Search prediction/palette/model candidates; encode and select using actual bytes and calibrated receiver cost; retain exact selected bytes and accepted-reference/model identities for replay. |
| ESP32-S3 | Forward opaque bounded chunks through credited queues; instrument Wi-Fi/QSPI concurrency, copies and UI/audio/input contention; keep entropy tables and clustering out of this bridge initially. DMA/zero-copy gains require implementation measurements. |
| FPGA | Parse words with bounded escapes; use modest table/state machinery where profitable; allocate DSPs to dequantization/inverse work and any justified rANS state multiply; schedule external memory, hash/HUD and continuous scanout together. |

DSP occupancy itself is not a success metric: Rice parsing, palettes and buffer
control mostly need logic and memory. A useful decoder spends resources where
they shorten the measured critical path, while the host absorbs expensive
search. This partition is a proposed design, not a deployed ESP32/FPGA change.

The next milestone remains 1,800 distinct frames over 60 seconds on hardware,
then 18,000 over 600 seconds with bounded queues and zero underruns; complete
validated FPGA decode strictly below 10 ms remains a separate open gate.

```sh
python3 scripts/literature-review-2026-11-06/derive_comparison.py --check
```


[V91j](../cu66-v91j/README.md) now qualifies the proposed bounded-transform
integration on actual BR88 frames. Two coefficient banks overlap assembly with
real dequantization and two-pass Q14 IDCT; independent Python arithmetic checks
exact signed residuals. This changes neither the wire format nor quantization
and makes no compression-superiority claim. V91k below adds reconstruction
against accepted references and base RGB565 conversion; HUD/content validation
and atomic publication remain later gates.
Residual completion cycles include actual transform service and must not be
compared as a speedup against earlier coefficient-only endpoints. Physical
30 fps, complete validated sub-10-ms decoding and 7-series fit/timing remain open.


[V91k](../cu66-v91k/README.md) extends the measured path to actual canonical
reconstruction and base RGB565 conversion from replayed actual candidate-memory
writes. Accepted native references and full expected pixels are source-backed;
all reference reads, candidate writes and converter reads have finite service.
The uncached converter exposes 3,110,400 acknowledged byte reads/frame as a
new cost baseline. A two-row, 1,440-byte chroma cache targets 518,400 total
external reads/frame while preserving exact interpolation and signed rounding;
this sixfold read-count opportunity is not yet a measured cached-RTL speedup.
No representation/quality or HEVC/AV1 superiority claim follows. Next integrate
HUD/content checks and atomic publication, then qualify finite full-frame
service and physical implementation.


The [V91k chroma-cache experiment](../cu66-v91k-cache/README.md) measures the
row-reuse proposal in RTL. Four registered row/parity banks add 1,440 logical
payload bytes; external reads fall sixfold to 518,400/frame. Exact FAST RGB565
conversion falls from 10,022,400 to 2,938,320 cycles (70.68247% fewer), with
prefill startup explicitly retained (first accepted read → first word grows
from 28 to 4,328 cycles). Both current-source seeds compare the unchanged
control, source-backed candidate memories and a separate nonuniform edge
pattern; cancellation during partial fill and later eviction also passes.
SLOW traces share service rules but differ in random draw consumption. This
is an exact memory-scheduling win, without changing codec bytes, quantization
or claiming compression superiority. Bounded aligned multi-byte service and
local lookup overlap are subsequent candidates; HUD/content validation,
publication, full finite-service integration and physical milestones stay open.


[V91l's heterogeneous validation partition](../cu66-v91l/README.md) now measures
real RTL C2/HUD/seal hashing and atomic reference/presentation ownership. All
28,700 SHA-job digests across two seeds match an independent hashlib oracle;
54 directed entries per seed cover late errors, identity/replay, pending-write
abort and negative presentation gates. Native C++ HUD decode is an explicit
endpoint outside the RTL cycle fence. Full RTL HUD and the live producer/shared
memory/display joins stay open; this does not complete all-RTL V91l/V91m.

The [aligned read follow-up](../cu66-v91k-lines/README.md) preserves exact RGB565
while reducing external transactions to 32,400 gathered 16-byte responses/frame.
The service model charges eight x16 payload beats for each response, consistent
with the board interface width, plus response/stall costs. FAST cycles improve
another ~6.62% over the byte-service chroma cache, with both inner and outer
owners tested on reset/ACK coincidence. No codec/quality superiority or
physical SDRAM/timing result follows from this converter-only replay.
