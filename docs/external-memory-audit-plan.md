# External memory architecture: audit and revised plan

Audit date: 2026-11-03. Input: the supplied “Game Bub External Memory
Architecture for Video Streaming.” This updates the memory work in the
[codec development plan](codec-development-audit-plan.md) and
[developer handoff](dev-handoff-2026-11-03.md). It is an architecture decision
plan, not a claim that the advertised memories are integrated or measured.

## Decision

Keep **SDRAM for reconstructed/display/reference frames and BRAM for the
immediate CDC FIFO, line buffers and hot state**. Evaluate external SRAM as a
compressed-data alternative rather than making it a prerequisite for streaming.
Continue the existing SDRAM JPEG staging path as the control while the
hardware team qualifies SRAM and the second SDRAM chip in parallel.

SRAM could remove compressed staging traffic from the shared SDRAM bus and
release FPGA BRAM. It adds another controller, constrained I/O, arbitration,
byte packing and ownership path. Adopt it when those costs and measured
worst-case service improve the complete streaming pipeline. Assigning display
to SDRAM chip 0 and references to chip 1 is a possible layout policy; it does
not create independent data channels or guarantee useful concurrency.

## What is confirmed, and what is implemented

The [official Rev4 overview](https://docs.gamebub.net/developing-cores/overview/)
documents 64 MiB SDRAM across two chips, a shared-width 16-bit memory interface,
and 512 KiB asynchronous SRAM. The [interface reference](https://docs.gamebub.net/developing-cores/reference-interfaces/)
exposes SDRAM chip selects and a separate raw SRAM interface with address,
byte masks, read/write strobes and data direction. These establish the intended
board/framework interfaces, not the fitted parts, timing or this bitstream's
support. Check the board revision, schematic/BOM and chip markings first.

| Resource | Current evidence in this checkout | Missing before use |
| --- | --- | --- |
| SDRAM chip 0 | Existing controller, functional model and display/JPEG simulations | Board identity, address-alias tests, physical I/O timing and sustained measurements |
| SDRAM chip 1 | Pin/advertised interface exists; current RTL holds it disabled | Selection/address decoding, initialization, refresh, per-chip state, model and hardware tests |
| External SRAM | Advertised raw interface; generic firmware access helpers exist | Streaming top ports/constraints, controller/arbiter, memory model and board qualification |
| BRAM | Retained routed baseline and isolated inference experiments | Complete modified-design fit and timing; nominal capacity is not free capacity |

Both [`moonshine_sdram.sv`](../fpga/rtl/moonshine_sdram.sv) and the experimental
[`moonshine_sdram_burst.sv`](../fpga/experiments/throughput30/burst/moonshine_sdram_burst.sv)
drive `sdram_cs_n = 2'b10` and enable only the first clock-enable bit.
Their address state is for one chip. [`moonshine_top.sv`](../fpga/rtl/moonshine_top.sv)
does not expose SRAM pins. The generic firmware's
[`sram_read`/`sram_write`](../firmware/handheld/src/device/drivers/fpga/mod.rs)
helpers, including a three-cycle comment, do not prove the streaming image
implements that mapping or meets SRAM electrical timing.

The memory model covers **2 MiB**, not the advertised 64 MiB. Its passing
tests do not qualify high addresses or chip 1. There is also an unresolved
display difference: official documentation says 720×480, while the current
prototype models portrait 480×800 scanout around the coded 720×480 canvas.
Freeze actual panel geometry, orientation and clocks before deriving deadlines.

## Corrections to the supplied proposal

| Proposal | Audit | Plan change |
| --- | --- | --- |
| 691,200-byte RGB565 frame; five frames about 3.3 MiB | Correct: 675 KiB each; five use 3.2959 MiB | Preserve, but separate advertised capacity from currently addressed memory |
| 518,400-byte YUV420 frame | Correct for tightly packed 8-bit 4:2:0; it technically fits 512 KiB with only 5,888 bytes left | Do not generalize “no full frame fits SRAM”; RGB565 does not, and a YUV framebuffer would leave almost no workspace |
| Two chips share one bus | Correct architectural warning | Model chip/bank/row changes and shared-bus turnaround, not two independent bandwidth pools |
| 100 MHz × 16 bits = 200 MB/s | Correct raw data-cycle ceiling | Do not substitute it for request service rate or measured goodput |
| 60% efficiency gives 120 MB/s usable | An unverified assumption | Report it as a what-if parameter only; replace it with measured service distributions and a deadline model |
| 37.1 MB/s left for motion at 60 fps | Omits even one full-frame reference read | A fully predicted example needs 124.416 MB/s before other costs; see below |
| 256 KiB ring + 128 KiB assembled-frame buffer | Capacity sums correctly but conflicts with the existing 256 KiB frame limit | Define zero-copy ownership or a compatible frame cap; do not promise every legal frame fits the assembly region |
| SRAM gives low-latency irregular access | Plausible, not established for this part/controller | Measure read/write/turnaround latency, decoder stalls and contention; SRAM is single-port unless proven otherwise |
| Create three memory RTL modules | Repeats work already present for SDRAM | Reuse and extend the current controllers, arbiter and JPEG writer/reader experiments; add only the missing SRAM path |
| Scalar 16-bit request struct | Useful sketch, insufficient for the actual integration | Specify address units, bursts, tags, response backpressure, errors and completion/drain semantics |
| 60 fps before custom decoding | Premature change to the first milestone | Qualify 30 fps with independent display refresh first; promote 60 only after full service and panel validation |

## Correct bandwidth accounting

Use decimal MB/s for bandwidth and binary KiB/MiB for allocation. A coded
RGB565 frame is 691,200 bytes. Display refresh and arrival/decode frame rate
are independent: a repeated front frame still consumes scanout bandwidth.

| Coded video / display refresh | Scanout reads | Reconstruction writes | One complete reference read | Total |
| --- | ---: | ---: | ---: | ---: |
| 30 / 60 Hz | 41.472 | 20.736 | 20.736 | **82.944 MB/s** |
| 30 / ~65.076 Hz model | 44.981 | 20.736 | 20.736 | **86.453 MB/s** |
| 60 / 60 Hz | 41.472 | 41.472 | 41.472 | **124.416 MB/s** |

The reference column assumes every output pixel fetches one RGB565 reference
pixel once. Intra/fill modes, caching and reference reuse can reduce it;
unaligned blocks, burst overfetch, repeated reads or more complex prediction
can increase it. This is a workload example, not a universal codec lower bound.
An independent intra decoder needs no temporal-reference read. A full
reference-to-back-buffer copy is another architecture with its own reads and
writes; do not add both copy and prediction traffic indiscriminately.

At 60/60 the proposal's assumed 120 MB/s would already be **4.416 MB/s short**
for this simple prediction example. Refresh, commands, direction/chip changes,
JPEG staging, scratch, retries and arbitration are not included. Available
capacity cannot resolve this deficit. At 30 fps the arithmetic looks less
demanding, but average demand alone cannot establish line-fetch deadlines.

Current RTL evidence illustrates why an efficiency constant is inadequate:
the isolated burst controller accepts same-row BL8 writes/reads every 13/15
cycles, or alternating-row writes/reads every 21/23 cycles, in its bounded
handshake test. These are serialized request intervals with refresh omitted
from that short measurement; they are not a physical memory benchmark.
See the [controller budget and assumptions](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/sdram-storage-model/README.md).

Compressed input at 8 Mb/s is 1 MB/s. SRAM storage read once and written once
costs at least **2 MB/s** of SRAM payload traffic; copying ring→assembly before
decode makes it **4 MB/s**. At 15 Mb/s those become 3.75 and 7.5 MB/s. Add
descriptors, padding, arbitration and scratch accesses. FPGA-connected SRAM
is not ordinary ESP32 address-space RAM; all incoming bytes still traverse
the actual host/QSPI/CDC path.

A 256 KiB ring holds 262.144 ms at 8 Mb/s or 139.810 ms at 15 Mb/s. Those
capacity calculations are correct. They are far larger than a desirable
interactive queue age: bound occupancy by a predeclared burst/age policy and
discard stale complete frames safely. Buffer size is not a latency target.

## Memory placement and ownership to specify

### Address map and second SDRAM chip

Use byte addresses at software/protocol boundaries and explicit conversion to
16-bit word addresses in controller adapters. A 26-bit **byte** address spans
64 MiB; a 26-bit **word** address spans 128 MiB. The supplied struct must state
which one it means. SRAM needs 19 byte-address bits or 18 word-address bits.
Define chip selection separately from the SDRAM's internal bank bits; they
are not interchangeable.

For 64 MiB, a linear 16-bit-word address needs 25 bits; the existing 24-bit
word interface spans one 32 MiB chip. Changing an address width without adding
and verifying chip decode can silently alias the new range onto chip 0.

The current controller uses `[23:22]` as bank, `[21:9]` as row and the low
nine bits as column in a one-chip word address. Extending it needs a defined
chip bit or separate field, device initialization/mode setup for each enabled
chip, refresh accounting, open-row state indexed by **chip and bank**, and
safe shared-DQ turnaround. Test that no out-of-range address silently wraps.
Do not enable both chips to drive read data simultaneously.

The proposed 1 MiB framebuffer/reference slots are reasonable reservations,
but are not current addresses. Derive slots from verified capacity, image
stride/orientation and worst burst length. Current framebuffer bases are
`0x000000` and `0x080000` **words** (0 and 1 MiB bytes), with portrait-row-major
storage and 480-word line fetches. A new raster-linear or tiled reference
layout requires explicit address conversion and caches; codec tiles are not
automatically identical to the display's memory layout.

Start with a display buffer, reconstruction buffer and one immutable committed
reference, allowing aliasing only when ownership proves it safe. Additional
references are optional. Named chip roles and tiled reference storage should
be selected by measured row locality and service, not fixed merely because
two packages are present.

### SRAM compressed pool

Do not freeze the proposed 256/32/128/64/32 KiB split yet. It duplicates payload
storage, makes the complete-frame region smaller than the permitted JPEG, and
does not justify descriptor or scratch sizes. Choose one measured scheme:

* A descriptor-held zero-copy ring: committed bytes remain pinned until decode
  and outstanding reads drain. Specify wrap, split-frame reads, head/tail
  generation, full/empty distinction and out-of-order/incomplete-frame reclaim.
  A ring must not overwrite a decoder's reference to old data.
* Fixed compressed slots: simpler ownership and abort behavior, but each slot
  has a negotiated hard cap. For example two 224 KiB slots plus 32 KiB metadata
  and 32 KiB reserve total 512 KiB; this would reduce the current 256 KiB cap.
  This is an illustrative allocation, not the selected implementation.
* One 256 KiB complete slot with the remainder assigned after measurement:
  preserves the present cap, but does not itself enable two maximum-size
  frames concurrently. Two 256 KiB slots consume the entire SRAM, leaving
  metadata/scratch elsewhere.

Expose **free ingress-FIFO space**, free storage capacity and committed-slot
ownership separately. Packet descriptors must refer to a session/generation;
they cannot make stale payload reusable. Commit follows exact length,
integrity validation and the real write-drain contract. Abort invalidates the
slot, preserves the displayed/reference image, and delays reuse until all
accepted writes/reads drain. Neither completion nor reset erases memory.

### BRAM and SRAM timing

607.5 KiB is nominal physical FPGA BRAM capacity, including its organization;
it is not a free byte pool. The retained baseline already uses 120.5 of 135
BRAM-tile equivalents. Preserve CDC FIFOs and safe line buffering; profile
scratch/caches and verify target packing before assigning more BRAM.

For SRAM, identify the actual part and derive read/write cycles from its
datasheet plus FPGA/PCB delays: address access, output enable, read/write
cycle, setup/hold, byte masks and data-bus high-impedance/turnaround. Constrain
and verify I/O for both directions and avoid bus contention. “No refresh” does
not imply one FPGA cycle per access or fixed zero-wait service. Measure mixed
reader/writer contention rather than just sequential bandwidth.

Specify mask polarity in each adapter: the raw SRAM interface's `writeMaskN`
is active-low, whereas an internal byte-enable convention may be active-high.
Verify both byte lanes and odd-length tails without altering adjacent bytes.

## Controller and arbitration contract

Reuse the current scalar controller as a reference and the burst experiments
as candidates. The current [four-client arbiter](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/sdram-arbiter-study/README.md)
has strict display priority and can starve background work. Its read sinks
must always be ready; it is not a general production memory fabric.

The replacement interface must define request ready/valid, canonical address
units, client/transaction/epoch tag, read/write, bounded burst length, write
payload and byte mask; responses need valid/ready, tag, beat/last and error.
Keep controller acceptance distinct from write completion or a drained range.
The current BL8 candidate uses 16-byte write payloads; a lone 16-bit `wdata`
does not specify the burst data channel or trailing odd-byte behavior.

Use scanline deadlines/watermarks with a bounded maximum background burst
and refresh interruption. Also guarantee measured service to ingress,
reconstruction and references, or they can fill queues while scanout looks
perfect. Add response FIFOs/backpressure, outstanding limits, range checks,
late-response attribution, timeout and reset/abort quiesce. Any priority/fairness
choice must be tested for both display deadlines and bounded frame age.

`HostV0` is indeed a scalar request/completion interface. It does not establish
the throughput of this fork's current custom QSPI endpoint. Measure the exact
firmware and bitstream path with Wi-Fi active. Preserve compatibility with the
framework's reserved mappings; do not assume a generic firmware SRAM helper
works with the streaming top or rewrite the framework unnecessarily.

## Revised work packages

| Order | Owner | Work | Acceptance evidence |
| --- | --- | --- | --- |
| M0 | hardware + integration | Identify board/panel, SRAM/SDRAM parts, pinout, clocks, framework revision and reserved regions; preserve JPEG control | Signed-off manifest/map and datasheet-derived timing assumptions; 30 fps remains first goal |
| M1 | verification + FPGA | Reproduce existing SDRAM writer/reader/LCD tests; model second-chip decode and SRAM access separately | Exact bytes/pixels, timing assertions, negative tests and source-bound artifacts; model limits explicit |
| M2 | hardware | Qualify SRAM and both SDRAM chips on the accessible board in reserved regions | Address/data walking, checkerboard/March-style and random patterns, byte masks, cross-chip alias/retention, refresh, turnaround and reset checks; bounded failures logged |
| M3 | FPGA + firmware | Measure exact SRAM/SDRAM/QSPI service under concurrent traffic | Sequential and mixed rows/banks/chips, burst sizes, maximum stalls, refresh, FIFO occupancy, decoder backpressure and end-to-end ingress counters |
| M4 | integration | Compare BRAM48, existing SDRAM256 and SRAM-backed compressed storage | Same frames/transport/phase; full-design resource/timing and per-line/frame service evidence; select the smallest useful change |
| M5 | FPGA + firmware | Integrate the selected allocator, tags/CRC/drain and real packet path | No stale/partial publication, safe wrap/abort/reset/reclaim, bounded age, no unexplained memory/FIFO errors |
| M6 | all | Run real 30 fps gameplay with independent panel refresh, then controlled loss and long soak | Actual presented IDs, age/gaps, RF/QSPI counters, optical or calibrated latency and power; promote 60 fps only after passing this gate |

M0 and host codec benchmarking can proceed in parallel. SRAM qualification
must not block the already-developed SDRAM path. Full memory-pattern tests
write data: the board-owning team must reserve test regions and coordinate
display/core ownership before running them. Walking bits alone do not test
address aliasing, chip selection, retention or worst-case access scheduling.

Current reusable components and their boundaries:

* [SDRAM burst writer](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/sdram-jpeg-writer-study/README.md):
  byte packing, padding, stalled abort and external-drain tests.
* [SDRAM reader](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/sdram-jpeg-reader-study/README.md):
  bounded BL8-to-decoder words, tail strobes and backpressure tests.
* [Writer→SDRAM→reader→decoder→LCD simulation](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/sdram-jpeg-full-study/README.md):
  two synthetic frames with testbench-supplied bytes and integrity guard;
  not physical qualification or integrated network/CRC ownership.
* [Tagged command gateway](../fpga/experiments/throughput30/burst/dual-compressed-bank-study/tagged-gateway-rtl/README.md):
  synchronous identity/replay research; not proof of physical drain or CDC.

## Decision gate for adopting SRAM

Choose SRAM compressed staging if it demonstrably improves complete-design
BRAM use, decoder stall tails or scanout/frame deadlines at comparable
quality/rate, while meeting input storage and protocol limits. Keep the
SDRAM option if the extra SRAM controller/ports do not improve the measured
system. Do not require a second SDRAM chip or multiple references merely to
use capacity: add them when a codec workload justifies the service cost.

Report capacity, payload traffic, controller cycles, worst latency and
physical measurements separately. The proposal's 60% efficiency remains a
scenario input until measured; it is not available engineering margin.

Primary references checked 2026-11-03: [official hardware overview](https://docs.gamebub.net/developing-cores/overview/),
[raw memory/HostV0 interfaces](https://docs.gamebub.net/developing-cores/reference-interfaces/),
the linked local RTL, and the retained simulation/resource evidence. No new
memory-controller RTL, timing closure or board test was performed for this
audit.
