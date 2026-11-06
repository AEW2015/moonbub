# Game Bub codec literature review after V90

Reviewed 2026-11-06 against baseline commit
`7c24b4d80b2a79a45a9a06ddc82a9ef8f83ce030`.

Planning update: the findings below now feed the
[V91–V110 roadmap](../gamebub-v91-v110-development-plan.md). V91–V99 cover the
codec experiments; **V100–V110 focus on 7-series RTL mapping, placement, routing
and timing closure**, including DSP48E1, BRAM/SRL, LUT/carry logic, fanout, CDC
and complete routed-design qualification. These phases are planned work, not
new literature benchmark results or completed implementation milestones.

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
