# V79 memory feasibility study

The unchanged-resolution target remains open. The retained V78 30-source run
measures validated decode at **14.08760–29.10779 ms**. This study implements a
Python prototype, exact traffic accounting, and bounded tile-dependency
counterfactuals; it implements no production RTL optimization and establishes
no new frame rate or decode latency.

Run from the repository root:

```sh
python3 scripts/cu66-v79/memory_budget.py
python3 scripts/cu66-v79/memory_budget.py --check
```

Both commands use Python's standard library and existing evidence only. The
second recomputes the study and compares all four generated artifacts byte for byte. Results,
actual per-frame traffic, scenario CSV, checks and frozen input hashes are in
`fpga/experiments/cu66-v79/memory-study/`. Earlier sources and evidence remain
frozen. No HDL build, physical implementation, container or board is required.

## Exact traffic from the actual V78 campaign

The source is
`fpga/experiments/cu66-v78/system/frames30-fixed30-tac2/results.json`.
The counted physical window is admission through processor commit ACK. The
validated-ready timestamp is earlier by 4 clocks, or 70 for the deliberate
first retry. Display requests can cross those boundaries. Those counted
windows must not be silently relabeled validated-decode intervals.

| Traffic | BL8 commands per source | Physical bytes |
| --- | ---: | ---: |
| Canonical YUV420 writes, 8,100 tiles | 32,400 | 518,400 |
| Packed HUD writes | 2,640 | 42,240 |
| Stored reference reads, each delta | 31,224 | 499,584 |
| Functional HUD verification reads | 2,640 | 42,240 |
| Non-display total, each delta | 68,904 | **1,102,464** |

The two keys are source IDs **0 and 24**; they have no reference reads.
These traffic and latency ranges describe only this V78 short cohort. The
expanded V79 monitor cohorts are not model inputs; different compressed
histories, qmaps or reference footprints require their own traffic accounting.
Every source writes exactly 35,040 BL8 blocks / 280,320 physical x16 beats.
Canonical layout is the V74 tile-major layout: plane offsets 0/172800/216000
x16 words, 32 words per tile and four aligned BL8 commands per tile. There is
no portrait RGB framebuffer write/copy traffic in V78.

There are no P0/P1 read cache hits in this campaign. P0 read requests equal
P0 misses; P1 misses equal the 2,640 HUD verification reads. Consequently the
remaining actual SDRAM read commands are exactly display reads:

```text
display BL8 = actual_read_bursts - p0_cache_misses - p1_cache_misses
```

For the 28 deltas these admission-to-ACK display reads range from
**54,658 to 68,832 BL8**, or **874,528–1,101,312 bytes**. They include repeats
and partial cache epochs, rather than one display raster per source. The
first key has no display reads in its counted window; key 24 has 53,040.
No display traffic is allocated to a source merely by dividing whole-run
counts by 30. `actual-frame-traffic.csv` retains every source separately.

One V76 cold synthetic display trace is 32,400 YUV plus 2,640 HUD reads,
**560,640 bytes per panel trace**. Its largest eight-row strip fetches 576
BL8 / 9,216 bytes. This trace is reused below as an explicitly synthetic
LCD-demand schedule; it is not the actual V78 memory-request chronology.

## Bus and controller service analysis

At the assumed 100 MHz x16 SDR bus, delta non-display traffic alone has a
raw physical-beat floor of **551,232 clocks / 5.51232 ms**. That number
excludes command timing, bridge latency, row conflicts, refresh, display,
codec and processor work. It is not a decode-time prediction.

The V72 controller accepts one transaction at a time. Counting its state
transitions gives an ideal row-hit accept-to-next-accept interval of 15 clocks
for a read and 13 for a write; a closed-row activation adds four, and a
conflicting-row precharge plus activation adds eight. Read sampling and
response retiming are included in the read interval. The 68,904 non-display
commands therefore need **963,480 command-service clocks / 9.63480 ms** under
idealized row hits, no bridge gaps, no refresh and no display. Finite-window
last-response versus next-accept endpoints can differ by a clock. This is a
conditional service-work calculation for the frozen single-outstanding
controller, not a measured validated-decode lower bound. It leaves only about
36,520 clocks before the strict million-clock target even in that relaxation.

The actual delta P0 service counter spans **1,111,713–1,138,963 clocks**
(11.11713–11.38963 ms). It describes existing serialized P0 occupancy; an
optimization could change its command order or interval costs. P0 read service
is a subset of P0 service, and P0 read wait a subset of P0 wait. Wait time can
overlap another client's service, and codec, LCD and HUD progress can overlap
these counters. **No wait, service, read subset or CPU wall time is subtracted
from end-to-end latency**, and no such subtraction is labeled recoverable gain.

## What is calibrated, and what is unknown

The prototype replays all **17** retained V76 baseline/lookahead runs using
their measured strip durations, absolute releases and original deadlines.
Every reconstructed start/end timestamp and deadline-miss count must match.
This checks deadline arithmetic against real controller/model service
evidence; it does not fit a new arbitration model to those runs.

The retained paced dedicated-LCD baseline misses one strip by **308 clocks**;
the separate measured one-strip-early campaign misses zero with **2,470
clocks** minimum slack. P1 paced service misses 90/90 in both schedules.
Release times and deadlines are kept separate. The early-release result is
not imported as an implemented V78 scheduling improvement.

The new DAG scheduler is **uncalibrated**. Available V78 summary counters
do not provide actual per-command acceptance/completion timestamps, per-tile
reference and candidate-ready events, entropy/qmap release times, CPU-service
overlap, or bank/lease transition phases. Numerical proximity of an illustrative
scenario to V78 wall latency would not calibrate these missing dependencies.
Before making a gain claim, capture those events and replay the same decoder,
HUD and display chronology through the proposed policy.

## Bounded scheduler counterfactual

The Python model conserves all canonical/HUD/reference commands. Each tile
must read its four reference blocks, complete one in-order compute job and
drain four candidate-write blocks before its slot is reused. Hidden tiles
skip the reference stage in the static SAFE-map scenarios. Window sizes are
1/2/4/8; every active tile reserves **64 reference plus 64 candidate bytes**,
and the proposed metadata budget is **32 bytes per slot**. Thus the conservative
logical tile-working-storage reservation is 160 × window bytes: 160/320/640/1280.
This excludes existing codec storage, the controller/bridge caches and FIFOs,
LCD storage and implementation packing overhead. It proves neither BRAM fit
nor FPGA timing.

One atomic BL8 request owns the bus until completion, regardless of window
depth. A second serial compute resource can overlap that memory service.
Compute admission and completion are observed at bus scheduling boundaries;
this coarse event quantization is another uncalibrated timing assumption.
`write_first` drains computed candidates before prefetching more references;
`read_first` groups references within the same bounded window. All reference
descriptors are optimistically available at time zero. This removes live
packet, qmap and entropy dependencies rather than inventing their timing.
HUD write/readback service is placed after all canonical writes; actual HUD
preparation and overlap remain unknown.

The synthetic LCD model releases strip i one strip early and retains its
original `(i+1) × 147.403024 us` deadline. Native panel repetitions use absolute
rational timestamps for `541 × 834 × 34.058 ns`, including blanking; period
rounding does not accumulate. LCD receives at most four consecutive BL8
grants while decode/HUD waits. This approximates the V74 bounded-priority
policy; it does not reproduce wrapper acceptance, finite grace, response
backpressure, V78 prefetch/consumer leases or the actual renderer. Completed
strip deadlines and pending strip counts are reported independently. More
than two outstanding fill descriptors or any missed deadline fails the
admission screen for a consuming strip plus two future strips. Passing that
screen is necessary here, and **does not prove live cache residency**. The
existing V77/V78 structured display cache is 29,184 data bytes, excluding
tags, pipelines, line buffers and controller caches.

The model approximates refresh at the first eligible request boundary using
15 clocks and a 750-clock refresh interval, closes all row records, and charges
explicit row costs. Those assumptions and per-request bridge gaps are swept;
they are not hidden fitted constants.

Selected **uncalibrated model completions**, using 64 compute clocks per tile:

| Counterfactual | Model completion | Completed strip misses |
| --- | ---: | ---: |
| Window 1, gap 3, phase 0, write first | 31.9121 ms | 0 |
| Window 2, same assumptions | 26.0313 ms | 0 |
| Window 4, same assumptions | 26.0313 ms | 0 |
| Window 4, gap 0 | 17.9053 ms | 0 |
| Window 4, gap 6 | 33.5452 ms | 0 |
| Window 4, gap 10 | 52.5345 ms | 21 |
| Window 4, half-panel initial LCD phase | 18.5557 ms | 0 |
| Window 4, almost one-panel initial LCD phase | 12.1427 ms | 0 |

No model completion is measured FPGA decode latency, and the differences
between rows are not estimated hardware gains. Zero-compute controls show
that extra outstanding slots do not create bandwidth. The strong sensitivity
to gaps and display phase, and the lack of benefit beyond two slots in one
compute case, argue for a small measured prototype before deeper queues.

## One implementable next RTL experiment

Add a **two-slot generation-tagged reference prefetch window** alongside the
current tile path in a new version. The prefetch address walker advances in
canonical plane/tile order, with the frozen reference bank held immutable.
Each slot carries generation, bank, plane, tile index, four-block progress,
valid/error/abort state and a full 64-byte reference tile. Retain a conservative
64-byte candidate staging reservation per slot plus 32 bytes metadata:
**320 logical bytes total**. Keep at most two admitted tile descriptors, at
most one physical controller request outstanding and the existing four-grant
LCD limit. More slots and arbitrary memory reordering are unnecessary for
this first experiment.

To avoid assuming that future live qmap decisions are already available,
prefetch **all** tiles on delta frames, including hidden ones. Retire an unused
hidden reference only on the matching canonical tile-write completion;
keys bypass reference fetching. This costs an explicit **294 extra tiles /
18,816 bytes / 1,176 read BL8** per delta. It raises idealized non-display
controller work to **981,120 clocks / 9.81120 ms**, again before display,
refresh, rows and codec work. The corresponding two-slot modeled scenario is
26.5189 ms under the illustrative phase/gap/compute assumptions. Traffic
elimination using verified qmap lookahead would be a separate later change.

The receiver must accept a cached reference only on exact generation, bank,
plane and tile identity. A slot remains owned while its read is accepted,
payload is held, or its candidate completion is outstanding. Abort suppresses
new requests, drains the one accepted physical block, invalidates both slots
and suppresses stale replies; a bank lease cannot be released until this
drain completes. The current shared tile adapter is serialized, so a FIFO on
its response alone will not enable lookahead: the new walker/admission path
must issue the next reference independently of the decoder's current request,
and the receiver's single `ref_pending` identity must be adapted deliberately.

Required RTL qualification includes held response payloads, wrong/stale identity,
hidden first/last tiles, plane boundaries, two occupied slots, candidate-write
backpressure, every accepted read-beat abort, reset, original LCD deadlines,
and unchanged actual raster/digest checks. Capture request/response and tile
ready events first; compare identical arrivals and phases before attributing
any wall-time change to prefetch. The Python checks cover command conservation,
finite tile ownership, read→compute→write dependencies, exact serial compute
cost, zero-compute bandwidth controls, per-request gap sensitivity, row hits
and conflicts, refresh invalidation, unaligned-request rejection, and exact
V76 deadline replay. They do not replace those RTL tests.
