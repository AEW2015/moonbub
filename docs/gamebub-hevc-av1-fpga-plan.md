# Game Bub HEVC / AV1 decoder investigation

Research date: 2026-11-03. Scope: Python modeling and primary-source review;
no RTL, HLS, synthesis, implementation, installation or hardware operation.

Proceed with two research tracks: benchmark a tightly specified HEVC stream
subset against the custom codec experiments, and develop a custom decoder
architecture that borrows useful block/prediction ideas. A complete AV1 port
is a substantially larger project. The public implementation examined here
exceeds this FPGA's resources unchanged; that does not establish that every
serialized 720×480 AV1 or HEVC architecture is impossible.

Keep **720×480 coded video at30fps** as the primary product target.
The512×288 and20fps cases below are sensitivity studies used to understand
compute/memory bottlenecks. They do not replace the required spatial resolution
or frame rate. Keep the assumed720×48060Hz display service independent.

At the primary resolution, investigate a constrained conformant HEVC stream
and a custom inspired decoder with explicit tool/reference/transform limits.
Prioritize native decoder/entropy service, reference reuse and refresh scheduling
before accepting a lower-resolution target. No decoder or hardware behavior has
been changed by this planning update; whole-design fit and30fps remain unproved.

## Target and memory constraints

The retained [routed utilization report](../fpga/build-final/utilization.rpt)
identifies XC7A100TCSG324-1. Its totals agree with
[AMD DS180 v2.6.1](https://docs.amd.com/api/khub/documents/2LByHkO~nSZXcei2D55fTg/content).

| Resource | Device total | Existing JPEG design | Arithmetic remainder |
| --- | ---: | ---: | ---: |
| LUTs | 63,400 | 7,362 | 56,038 |
| DSP slices | 240 | 32 | 208 |
| 36 Kb BRAM tiles | 135 | 120.5 | 14.5 |
| UltraRAM | 0 | 0 | 0 |

The report contains 113 RAMB36 and 15 RAMB18 primitives. Total nominal BRAM
bits correspond to 607.5 KiB; the arithmetic remainder corresponds to 65.25
KiB. Those counts include parity capacity and say nothing about usable port
width, placement, banking or fragmentation. Replacing JPEG can reclaim some
existing resources, so the remainder is not a fixed new-decoder budget. A new
whole-design report is required to establish actual fit and clock timing.

The [official Rev4 overview](https://docs.gamebub.net/developing-cores/overview/)
lists 64 MiB SDRAM across two chips on a shared 16-bit bus, plus 512 KiB
asynchronous SRAM. The
[raw interface reference](https://docs.gamebub.net/developing-cores/reference-interfaces/)
exposes both. The [local memory audit](external-memory-audit-plan.md) establishes
the integration limits: the streaming controller enables chip 0, the streaming
top has no SRAM ports, and its functional memory model covers only 2 MiB.
Advertising two chips provides neither independent bandwidth nor a verified
64 MiB streaming allocation. Panel geometry/orientation and actual refresh
also remain to be frozen; this study explicitly assumes coded 720×480 and
60 Hz RGB565 reads.

The 2 MiB figure is a verification-coverage limit, not proof that chip 0's
controller cannot address its larger nominal 32 MiB range. Physical memory
qualification remains open.

## Available decoder evidence

| Primary source | What it establishes | Practical implication |
| --- | --- | --- |
| [Fraunhofer HHI architectures](https://www.hhi.fraunhofer.de/en/departments/vca/research-groups/embedded-systems/research-topics/advanced-architectures-for-multi-media-signal-processing/hevc-hardware-architectures.html) | Author reports complete Main-profile decoding on Stratix V with DDR3, 1080p60 around 150 MHz and about 66k ALMs; separate intra-only Stratix IV design handles 1080p30 below 150 MHz | Real decoder architecture precedent; Intel ALMs cannot be compared directly with Artix LUTs. Intra-only throughput cannot establish inter-decoder cost |
| [HHI decoder IP](https://www.hhi.fraunhofer.de/en/departments/vca/technologies-and-solutions/h265-hevc/hevc-4k-live-hardware-decoder.html) | Offers hardware decoder IP, including FPGA netlist / VHDL delivery | Commercial/research access route, not a downloaded verified Artix core |
| [openav1 pinned README](https://github.com/Jonahss/openav1/blob/be076c470dbb8d775535c3bd8c927a336ef80c31/README.md) | Public SystemVerilog decoder project, Apache-2.0 as declared; software parses headers. Author reports 50 MHz U200 inter build at 292k LUT / 271 URAM / 831 DSP. K26 intra core reports 102.5k LUT at 80 MHz, omitting CDEF, restoration and super-resolution | Both builds exceed A100 LUT capacity; inter also exceeds DSP and requires absent URAM. These are author's reports, not independently reproduced results. Board intra evidence is distinct from inter simulation/build evidence |
| [AOM products](https://aomedia.org/products/) | AOM supplies reference software, not official hardware RTL; lists commercial hardware suppliers | Do not mistake reference C software for FPGA-ready RTL |
| [OpenHEVC](https://github.com/OpenHEVC/openHEVC) | Software decoder | Useful independent output oracle, not an RTL decoder |
| [xk265](https://github.com/openasic-org/xk265) | Hardware encoder | Exclude from decoder resource evidence |

openav1 was pinned to commit `be076c470dbb8d775535c3bd8c927a336ef80c31`
(committer timestamp 2026-11-03T04:42:27Z); README status is 2026-10-25.
Its verification scope, omitted stages and host assumptions require review
before reuse. No repository setup or simulation was run. The source manifest
records its README hash. This review located no demonstrated public drop-in
complete HEVC decoder for this Game Bub configuration; it is not an exhaustive
proof that none exists. Transform, intra-prediction and motion-compensation
subblocks are not complete decoder evidence.

## Three different implementation routes

| Route | Bitstream contract | Work before FPGA implementation | Decision |
| --- | --- | --- | --- |
| Constrained standard HEVC | Conformant HEVC stream within an explicitly enumerated supported subset | Software encoder/decoder benchmark, syntax audit, bit-exact reconstruction, entropy/transform/filter/memory demand traces | Worth a bounded feasibility study if standard encoder interoperability matters |
| Complete AV1 implementation / port | Signaled features of the supported AV1 profile and declared limitations | Reproduce pinned implementation, understand host parsing and conformance gaps, redesign memories and area, test complete stage behavior | Long-term research; no unchanged fit on this FPGA |
| Custom HEVC/AV1-inspired codec | New local syntax; no standard-decoder interoperability claim | Compare fixed/adaptive blocks, intra/inter prediction, residual transforms and simpler entropy coding using exact Python reconstruction | Most direct architecture experiment alongside the current codec work |

For HEVC, start with 8-bit 4:2:0 Main-compatible coding, fixed dimensions,
low delay without B-frame/reorder requirements, one temporal reference, and
a finite declared set of block/transform/prediction tools. This is an
application-specific subset contract, not a new normative HEVC profile.
Only omit filters/tools when their absence is signaled and enforced in every
accepted stream. Encoder switches are hypotheses: inspect parameter sets,
slice headers, block syntax and motion vectors in actual output. A low-delay
preset does not prove a one-reference or limited-partition contract; integer
luma motion can still require fractional chroma prediction. Disabling filters
does not remove entropy decoding, transforms or reference dependencies.
Reject unsupported syntax before publishing a frame.

For AV1 use the [approved AV1 specification](https://aomediacodec.github.io/av1-spec/av1-spec.pdf),
not a transform-only model, as the compatibility contract. Entropy/CDF state,
reference updates and display ordering, prediction, inverse transforms,
in-loop filtering, super-resolution and signaled output processing each need
an explicit support decision. The study's 1/2/4/8-reference sweep is a memory
what-if, not a claim that a one-reference core accepts arbitrary AV1 streams.

For the custom route, first freeze exact bounded syntax and an independent
decoder. Then compare fixed 8/16/32 blocks; skip/fill/copy/intra modes; one
immutable committed reference; bounded integer or limited subpixel motion;
small integer residual transforms; and bounded coefficient codes. Add one
tool at a time and measure rate, reconstruction quality and worst service.
Do not describe the resulting format as HEVC/AV1 compatible.

## Executable capacity and traffic model

The [Python study](../experiments/python-game-decoder-architecture-study/README.md)
retains every scenario in JSON. Storage assumes one current YUV420 buffer,
the listed references, and two RGB565 display buffers. It excludes syntax,
motion maps, padding, filter scratch, caches and compressed input.

This architecture model assumes **two physical RGB output buffers**. The
hybrid-link finite model uses **three metadata framebuffer roles**; those
are separate assumptions and do not establish identical physical allocations.
If the complete pipeline requires three physical 720×480 RGB565 buffers,
add 691,200 bytes (0.659 MiB) to every corresponding table allocation.
Compressed storage, context state and caches require further space beyond
these frame allocations. A metadata-role count needs an explicit ownership
and physical-buffer mapping before the models can be combined.

| Stored references | Frame allocation | Allocation in MiB |
| ---: | ---: | ---: |
| 1 | 2,419,200 bytes | 2.307 |
| 2 | 2,937,600 bytes | 2.802 |
| 4 | 3,974,400 bytes | 3.790 |
| 8 | 6,048,000 bytes | 5.768 |

Nominal external capacity can hold these frame allocations, but even the
one-reference case exceeds the existing 2 MiB simulation coverage. One tightly
packed YUV420 frame is 518,400 bytes and fits advertised SRAM with only 5,888
bytes left; RGB565 is 691,200 bytes and does not fit. Frame-role aliasing can
reduce storage only after ownership/lifetime analysis.

Default payload: 30 fps YUV reconstruction write, separate YUV→RGB conversion
read, RGB output write, 60 Hz RGB scanout, one no-halo reference read, and
8 Mb/s compressed staging write/read. It totals **110.864 MB/s**. A fused
color-output path removes the conversion reread, giving **95.312 MB/s**.
Three separate full-YUV filter read/write passes add **93.312 MB/s**; this is
a deliberately simple external-memory pattern, not mandatory codec traffic.
Storing eight references does not mean reading eight references per pixel.

| Assumed efficiency of 100 MHz × 16-bit SDR bus | Assumed service | Default no-halo slack | 16×16 independent-halo slack |
| ---: | ---: | ---: | ---: |
| 30% | 60 MB/s | −50.864 MB/s | −66.538 MB/s |
| 40% | 80 MB/s | −30.864 MB/s | −46.538 MB/s |
| 60% | 120 MB/s | +9.136 MB/s | −6.538 MB/s |
| 80% | 160 MB/s | +49.136 MB/s | +33.462 MB/s |

The halo example uses `(block_width+taps−1)×(block_height+taps−1)` fetches
per block/plane, 8-tap luma and 4-tap chroma, no inter-block reuse, and
fractional filtering in both axes. With luma blocks 8/16/32/64 it produces
147.638/126.538/118.109/114.513 MB/s total traffic. These tap counts are
illustrative, not a complete AV1 filter model. Cache reuse can lower fetches;
compound prediction, warp/scaling, row changes and burst alignment can raise
service cost. Positive average slack proves neither scanline nor frame-age
deadlines. Refresh/commands/arbitration are represented only by the assumed
efficiency, without a controller schedule.

## Reduced resolution and frame rate

These additional scenarios keep two **720×480 RGB565 display buffers** and
60 Hz scanout. They assume each decoded frame writes a display-sized scaled
RGB image and reads its coded YUV image once for conversion. Scaling compute,
extra filter reads, aspect-ratio handling and line deadlines require further
modeling. Lower coded resolution reduces YUV/reference traffic while leaving
scanout at **41.472 MB/s**. At 20 fps the display repeats completed frames;
the compressed input is still the same conservative 8 Mb/s scenario input.

| Coded picture / fps | YUV frame bytes | Frame allocation, 1 reference | No-halo / independent-halo MB/s | Dense 8×8 transform million MAC/s |
| --- | ---: | ---: | ---: | ---: |
| 720×480 / 30 | 518,400 | 2.307 MiB | 110.864 / 126.538 | 248.832 |
| 512×288 / 30 | 221,184 | 1.740 MiB | 84.115 / 90.802 | 106.168 |
| 512×288 / 20 | 221,184 | 1.740 MiB | 70.567 / 75.025 | 70.779 |
| 480×270 / 30 | 194,400 | 1.689 MiB | 81.704 / 87.607 | 94.003 |
| 480×270 / 20 | 194,400 | 1.689 MiB | 68.960 / 72.895 | 62.669 |
| 320×180 / 30 | 86,400 | 1.483 MiB | 71.984 / 74.698 | 43.008 |

The JSON includes 1/2/4/8-reference allocations for each row. At 512×288,
one/two/four/eight references plus reconstruction and display buffers use
1.740/1.951/2.373/3.217 MiB; frame rate changes no buffer capacity. The
800×480 display alternative with 512×288@30 instead needs 1.887 MiB with
one reference, 46.080 MB/s scanout and 91.027 MB/s total no-halo payload.
These alternatives make the unresolved display geometry explicit.

The 512×288 one-reference figure becomes approximately **2.399 MiB** if
three physical 720×480 RGB565 output buffers are required. The 1.740 MiB
two-buffer calculation therefore does not prove that the actual complete
pipeline fits within the existing 2 MiB memory-model coverage. That coverage
is a verification limit, not an actual controller-capacity limit.

At 150 MHz, the coded-pixel cycle budgets for the rows above become
14.47/33.91/50.86/38.58/57.87/86.81 cycles. Lower resolution and fps make a
serialized datapath more plausible. They do **not** shrink an unchanged
complete RTL design in proportion to pixel count: syntax/entropy machinery,
tool choices, transforms and header processing remain. Parameterized line
buffers, frame memories, context maps and reference storage may shrink;
reducing supported tools and parallel lanes may reduce logic at the cost of
an explicit restricted-stream contract and throughput. Any proposed hardware
reduction still needs new complete-design synthesis, routing and conformance
evidence. Accepting only an application-specific subset is substantially
different from accepting generic HEVC/AV1 streams.

## Arithmetic bounds and complete architecture

At 720×480×30 there are 10.368 million luma positions/s. Requested clocks
100/150/200 MHz allow **9.65/14.47/19.29 clock cycles per luma position**
averaged over a frame; the 60 fps budgets are half those values. None of these
clocks has been achieved by a new decoder here. Independent pipelined stages
overlap, whereas shared engines and dependency stalls consume this budget.

The naive separable NxN transform model counts `2N³` MACs/block over all three
planes, with each plane padded to full blocks. For N=4/8/16/32/64 it gives
124.416/248.832/501.350/1055.785/2264.924 million MAC/s at 30 fps. Eight ideal
MAC lanes at 150 MHz would use 10.4/20.7/41.8/88.0/188.7% of their abstract
arithmetic capacity. This does not map one lane to one DSP: butterfly
factorization, coefficient constants, zeros, precision/rounding and scheduling
change the implementation. HEVC does not acquire AV1's 64-point transform
requirements merely because the generic sweep includes N=64.

| Pipeline stage | State / data to quantify in Python before RTL |
| --- | --- |
| Packet/frame admission | Complete-frame boundary, length cap, integrity, bounded queue age, abort/drain |
| Header and entropy decode | Supported syntax, context/CDF/CABAC storage and serial symbol dependencies |
| Prediction | Neighbor edges, motion maps, immutable reference ownership, cache locality and outstanding requests |
| Coefficients / inverse transform | Sparsity, signed precision, intermediate scratch, exact rounding and per-block cycles |
| Reconstruction / in-loop stages | Saturation, edge dependencies, line buffers, stage overlap and reference-ready boundary |
| Color output / display | Format conversion, orientation, independent scanout deadlines and atomic buffer publication |

BRAM is needed for hot entropy state, line buffers and caches as well as
compressed FIFOs. External memory capacity and a small arithmetic operation
count cannot establish fit. Serial entropy dependencies, irregular reference
fetches and in-loop boundaries may dominate a design with ample DSP capacity.

## Evidence gates

1. Freeze the exact standard-subset or custom syntax contract, panel geometry,
   stream rate/quality targets and supported error behavior. Keep JPEG as the
   comparison control.
2. On identical gameplay clips, retain actual encoded bytes, inspected tool
   usage, independent decoded frames, bitrate/quality and host encode time.
   Do not extrapolate a software decoder's runtime to FPGA throughput.
3. Trace worst symbol/transform work and reference accesses on those streams;
   refine the parameter model with real distributions, cache assumptions and
   finite-buffer service/deadline simulation. Include scene changes and motion.
4. Only after choosing a route, authorize a separate complete architecture
   implementation and resource/timing study. Qualify the actual memory path
   before declaring 30 fps or adding 60 fps as a target.
5. Require exact reconstruction against the declared oracle, complete-frame
   ownership and reset/loss behavior, routed whole-design fit/timing and
   measured display/frame-age service before claiming a working hardware codec.

All source URLs were checked on 2026-11-03. The
[source manifest](../experiments/python-game-decoder-architecture-study/sources.json)
records primary links, commit metadata and local input hashes; the study's
offline verifier regenerates the retained arithmetic, and optional online
verification refetches only the pinned README. Nine arithmetic tests
and both verifier modes passed. These results establish a repeatable
investigation, not codec conformance, measured bandwidth or FPGA feasibility.
