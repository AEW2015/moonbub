# CU66 V74: tile-major memory and tile-aware painter

V74 reduces the matched predicted-frame transaction from **129.16555 to
92.38045 ms (28.48%)** in the checked SDRAM command model. The key frame improves
from 59.72594 to 45.43165 ms. Four chronological sources produce exact canonical
planes and portrait RGB565 output with **zero LCD underruns**. These are
simulation measurements at an assumed 100-MHz memory clock, not board results.
The 30-fps and strict maximum validated-decode-under-10-ms milestones remain open.

## What changes

Canonical allocation bases, capacities, plane offsets, CU66 packet syntax,
8×8 tile identity, canonical hash order, HUD semantics and presentation ownership
remain unchanged. Within each canonical plane, tiles are now physically
contiguous: `plane_base + tile_index*32 + word_in_tile`, counting x16 words.
Each tile uses four full BL8 writes/reads instead of V73's eight half-row
requests. This layout requires the V74 tile adapter and V74 painter together;
an older raster-addressed painter cannot consume this memory layout.

The painter prefetches eight Y rows and retains rolling four-row chroma quads,
then performs the existing exact bilinear conversion, HUD overlay, portrait
transpose and black borders. Its auxiliary reads now return a held 128-bit
snapshot. There is one outstanding auxiliary transaction, and the arbiter
captures its read/write-burst qualifiers and routes its held response to its
owner. Scalar processor HUD transfers and their generation/permission guards
remain in place. See [memory](memory.md) and [painter](display.md).

## Integrated measurements

The frozen V73 comparison uses the same source packets, model clocks, native
oracle, frozen V72 controller/model and V71 scanout. This is a comparison of
the complete V74 change, including both layout and painter; it does not isolate
a single optimization. Packet-complete staging is immutable bench input.
`validated` ends at the actual validated-ready event; `composition` ends at
RGB-ready. Native processor HUD execution is outside simulated clock time.
The bench's first-correct-pixel timestamp can include matching black border
pixels; it is not a first-game-image or input-to-photon latency measurement.

| Same source | V73 transaction | V74 transaction | V73 validated interval | V74 validated interval | V74 composition |
|---|---:|---:|---:|---:|---:|
| Key, frame 0 | 59.72594 ms | 45.43165 ms | 22.94679 ms | 15.80350 ms | 29.62812 ms |
| Predicted, frame 1 | 129.16555 ms | 92.38045 ms | 58.20614 ms | 36.84403 ms | 55.53573 ms |

Four-frame history transaction times are **45.43165, 92.38045, 92.22263,
92.21534 ms**. The validated interval spans **15.80350–36.91419 ms**. Every
transaction exceeds the 33.333-ms new-frame budget, so this iteration does not
satisfy 30 fps even within the model. Display refreshes of an unchanged front
are counted separately: four distinct sources, 20 complete repeated rasters
(6/6/6/2), 16,183 clean lines and 7,767,868 observed pixels. Repeated refreshes
are not new streamed frames. The lost processor COMMIT acknowledgment is retried
without a second global commit.

Even an ideal zero-cost replacement for composition would leave the measured
36.91419-ms validated tail above the 33.333-ms new-frame budget. Direct-YUV
scanout alone therefore cannot close 30 fps on this evidence. The validated
path needs independent improvement, and the strict under-10-ms target requires
more than a 3.69-fold reduction of this observed modeled tail at the same
assumed clock. This ratio is a budget comparison, not a proposed achievable
frequency increase or a target-hardware latency prediction.

The C++ oracle reconstructs logical raster planes from **actual tile-major
SDRAM contents** using an independent coordinate formula, then checks all bytes
and the canonical tag. Predicted references come from previous RTL-produced
SDRAM contents; the oracle never feeds golden reference pixels into the decoder.
Every portrait framebuffer word is checked independently, and live LCD checks
retain generation, pixel-order and complete-raster checks.

| Per complete frame | V73 | V74 |
|---|---:|---:|
| Canonical write commands | 64,800 | 32,400 |
| Canonical physical x16 write beats | 518,400 | 259,200 |
| Total write commands, including RGB/HUD | 133,920 | 101,520 |
| Total physical write beats | 1,071,360 | 812,160 |
| Active x16 word updates | 664,320 | 664,320 |
| Painter input API calls | 280,320 scalar | 35,040 BL8 |
| Painter useful input words | 280,320 | 280,320 |
| Painter output commands / words | 48,000 / 384,000 | 48,000 / 384,000 |

Total write beats fall **24.19%**, while exact active updates stay unchanged.
The matched P frame requests 7,806 reference tiles: 62,448 four-word V73 calls
become 31,224 eight-word V74 calls. V74 fetches exactly 499,584 useful/wire bytes;
V73 fetches 504,448 wire bytes for that same useful payload. Thus most of this
iteration's gain is request/write efficiency, not a large compression reduction.
The legacy `p0_row_reads` counter has different useful-word width in V74;
compare byte totals rather than treating the counters as equivalent rows.
Background LCD/refresh traffic also changes with transaction duration/phase;
raw total read/ACT/PRE counts are not normalized measurements.

## Verification and implementation cost

Native and pinned-sv2v-converted painter simulations each pass **39 rasters,
14,976,000 compared RGB words, 16 fault probes and 30 invalid starts**. All
converted case counters and cycle totals match native SV. The memory regression
uses both Icarus and Verilator, real controller commands, response stalls,
physical aliases, reset, malformed requests and accepted-operation abort drains;
all **44 cases pass**, with a worst observed LCD line of **1,673 clocks**
against the 1,842-clock component-test deadline. Details are in
[memory.md](memory.md).
The integrated control smoke additionally checks seven denied writes, two
partial abort drains and early HUD-drain rejection.

The data-cache footprint grows from 13,696 to **23,056 bytes**. Unplaced XC7
family mapping reports 11 DSP48E1, eight RAMB18E1 and **2,304 RAM64M** for the
painter, versus 384 RAM64M previously. This larger distributed-RAM allocation
is a material implementation cost. Neither cell totals nor generic mapping
establish full-system fit. [Frontend/mapping evidence](elaboration.md) includes
tool identities, source hashes, generated-only lint exceptions and limitations.

The exact `xc7a100tcsg324-1` Vivado preflight returns
**UNAVAILABLE_EXACT_PART**, before RTL synthesis or implementation. There is no
new bitstream, routed clock, timing/CDC signoff or physical performance result.

## Reproduce and integrate

Run from this research checkout with the existing tool containers and mounted
paths. Each build uses one job under the shared container limits. Preserve all
V69–V73 paths and evidence. Only new V74 paths are writable producer outputs.

```sh
python3 scripts/cu66-v74/verify_baseline.py
python3 scripts/cu66-v74/run_memory.py
python3 scripts/cu66-v74/run_painter.py
python3 scripts/cu66-v74/run_elaboration.py
python3 fpga/experiments/cu66-v74/system/run_control.py
python3 scripts/cu66-v74/run_system.py --frames 2 --strip
python3 scripts/cu66-v74/run_history.py --frames 4 --strip
python3 scripts/cu66-v74/compare_system.py
python3 scripts/cu66-v74/verify_evidence.py
python3 scripts/cu66-v74/bundle_manifest.py
```

The direct-YUV traffic study is separate Python-only evidence; see
[direct-yuv.md](direct-yuv.md) for reproduction and assumptions. It is **not**
an integrated display bypass or a new scanout RTL implementation.

`system/sources.json` lists the exact integrated sources. Hardware top is
`cu74_system`, `USE_STRIP=1`, `P0_CACHE_LINES=8`; exclude `_sim.sv` and
`_model.sv` and remove `SIMULATION` for hardware. `USE_STRIP=0` is rejected
because the retired scalar painter addresses raster layout. The staged
`build/ooc_system.tcl` uses the 20 hardware sources and declared clock assumptions.

The host encoder and ESP32 packet forwarder need no new codec syntax for this
experiment. Hardware integration must explicitly pair the tile-major memory
and painter capabilities with its bitstream/software build identity. Do not
silently use a V73 raster debug reader or painter against a V74 canonical bank;
update diagnostic readback addressing and reject mismatched layout capabilities.
This study does not implement such runtime capability negotiation or flash
firmware. Counter snapshots remain 32-bit modulo counters; use overflow-safe
accumulation and proper clock-domain snapshots in longer target campaigns.

## Next implementation work

1. Register full 16-bit input-cache reads before byte selection and make the
   chroma cache port schedule BRAM-friendly. Re-run exact native/converted
   raster, fault and mapping tests; quantify cycle costs and resource reduction.
2. Build a real direct-YUV display prototype only after the strip-cache service
   budget is met. Use separate rolling chroma retention and overlap prefetch
   with conversion. Measure real controller row/refresh/turnaround interference,
   not only aggregate bandwidth. Preserve bilinear rounding and the same HUD.
3. Bind direct scanout to a canonical bank plus generation/frame descriptor;
   retain the old front lease until accepted reads drain and a qualified vblank
   switches ownership. Invalidate cache tags on generation/layout changes. Add
   abort, pending descriptor, old-front drain and stale-response tests before
   removing RGB buffers. Do not acknowledge painting success without an actual
   verified replacement display path.
4. Add guarded full-BL8 processor HUD upload/readback as a separate ablation.
   Uploading 21,120 words in 2,640 full bursts could remove 18,480 write
   commands and 147,840 masked physical beats per frame from the current path;
   these are arithmetic projections, not measured results. Keep generation/frame
   checks, contiguous address/count validation, payload immutability, readback hash
   order, all-beat drain and rejection of premature HUD-drain claims. Compare
   actual controller cycles, CPU service and abort/fault behavior.
5. Profile independent cache-hit responses and safe decode/compose phase overlap.
   Preserve pending-write fences, accepted-operation drains, reference/front
   ownership and exactly-once processor commit reconciliation. Measure queue tails.
6. Extend the changed full-system path to the retained 457-frame histories and
   the predefined 1,800-distinct-source fixed-arrival campaign. Missing a deadline,
   dropping a required source, repeating a source or any underrun must fail
   qualification, not be hidden by counting panel refreshes.
7. Close exact-device fit/route/CDC and live ESP32 Wi-Fi/QSPI plus processor HUD
   service. Then require ten minutes of physical distinct-source 30-fps operation;
   retain that gate while pursuing a strict observed maximum validated target
   decode below 10 ms, including stalls and recovery paths. Average or kernel-only
   times do not close either milestone.
