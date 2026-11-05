# V73 hardware-development handoff

V73 makes strip memory banking explicit and replaces scalar reference assembly
with wide row reads and an eight-line cache. The matched P transaction falls
from **148.51433 ms to 129.16555 ms (13.03% less modeled time)** with exact output
and zero LCD underruns. The strip maps to **eight RAMB18E1 cells instead of 24
RAMB36E1 cells** in the stated unplaced 7-series flow. **30 fps, validated target
decoding under 10 ms and exact-device implementation remain open.**

Baseline: v72 commit `41d070476c074e8caa1ccabe7ae745ba61707717`. All frozen
v69/v70/v71/v72 files remain unchanged. CU66 packet syntax, 720×480 coded image,
exact decoded quality, Sunshine/ESP32 wire protocols, masked write semantics,
LCD timing and presentation ownership are unchanged. No hardware was programmed.

## Implemented changes

- `cu73_painter_burst` has eight explicit 720×16 row-lane banks, with one selected
  bank written per produced pixel and one synchronous read per bank when
  gathering an eight-word portrait burst. Logical strip capacity remains
  11,520 bytes. Native case timing and transaction counters match v72 exactly.
- `cu73_tile_memory` issues **eight four-word reference-row requests per tile**,
  replacing 32 scalar requests. It selects the correct 64-bit half of the
  returned aligned 128-bit line using the actual row address; chroma pitch 180
  words alternates halves. Identity-qualified 512-bit tile completion follows
  all eight rows. Writes still use the qualified v72 half-row bursts.
- `cu73_word_bridge` provides a held full-line P0 response and eight fully
  associative reference cache lines with round-robin replacement. Both clients'
  writes invalidate all matching physical tags before service. The controller,
  LCD elastic buffer, four-grant bound and finite request-gap grace are retained.
- `P0_CACHE_LINES=1` is a qualified control configuration, allowing the row API
  benefit to be separated from the additional cache locality. Both supported
  settings pass strict native lint and exact full-system comparison.
- Nine read-only profiling outputs separate P0/P1 hits/misses, row admissions,
  wait/service and reference-read-only wait/service. They do not affect flow.
  These are prototype top-level outputs, not an installed hardware MMIO ABI.

The frozen v72 controller/model, v70 receiver/qmap/base/commit owner and v71 LCD
path remain in use. Accepted references come from prior RTL-written SDRAM;
native expected pixels are confined to scoreboards.

## Results and scope

| Check | Result |
| --- | --- |
| Memory adapters | **40/40 executions**: 28 traffic/reset, four masked cache-alias, eight wide-row capacity/corner/backend tests |
| Wide-row probes | Each run checks 68 assertions / 42 wide reads, held full-line snapshots, replacement, half selection, alias invalidation and reset; both one/eight-line settings |
| Modeled LCD deadline | Worst tested line **15.94 µs**, within **18.425378 µs**, including request gaps and same-bank backslot conflicts |
| Native painter | **39 rasters / 14,976,000 exact RGB565 words**, ten fault probes and 30 invalid-start probes |
| Translated painter | The same 39 cases pass after pinned sv2v lowering, with exactly matching native cycles/counters |
| Key/P integration | Both cache settings produce exact canonical/HUD/RGB data and complete source rasters, with **zero LCD underruns** |
| Four-frame history | IDs 0–3 use actual prior stored references; exact output, four complete distinct source presentations, **zero underruns** |
| Integrated guards | Two headers, two completed HUD words, seven denied writes, two abort drains, premature HUD completion rejected, zero partial acceptances |
| Python trace | 8,100 synthetic raster-order tiles confirm row addresses, halves and cache traffic; not the actual CU66 P-request set or cycle timing |
| Frontend/mapping | Both painters pass pinned sv2v → Yosys structure/memory checks and unplaced `synth_xilinx -family xc7` mapping |
| Exact-device OOC | Vivado 2025.2 exits 2 with `UNAVAILABLE_EXACT_PART`; synthesis and implementation did not start |

Timing values use the unchanged model inputs: 100 MHz memory, 279-degree read
sampling, 34.058 ns pixel period and approximately 65.0755 Hz panel refresh.
They are not achieved device clocks or electrical timing measurements.

| Matched P-frame result | V72 scalar/cache1 | V73 rows/cache1 | V73 rows/cache8 |
| --- | ---: | ---: | ---: |
| Full transaction through COMMIT ACK | 148.51433 ms | 140.69137 ms | **129.16555 ms** |
| Complete-packet to modeled ready | 77.76904 ms | 70.09588 ms | **58.20614 ms** |
| Reference API requests | 249,792 inferred scalar calls | 62,448 row calls | 62,448 row calls |
| Reference read commands | Not separately instrumented | 62,448 | **31,528** |
| Reference wire bytes | Not separately instrumented | 999,168 | **504,448** |
| Useful reference bytes | Same unchanged tile work | 499,584 | 499,584 |
| Reference wait clocks | Not separately instrumented | 1,974,577 | 1,622,313 |
| Reference service clocks | Not separately instrumented | 1,381,880 | 748,774 |

The wide-row/cache1 control saves 5.27% transaction time versus v72. Eight cache
lines save a further 8.19% versus that control; the combined reduction is 13.03%.
The cache change removes **49.51% of measured reference read commands** in this
P input. V72 scalar-call count is inferred from the unchanged 7,806 reference
tiles and frozen 32-word/tile adapter, not presented as a new V72 instrumented
counter. Cache-hit ratios have different request denominators across scalar and
row APIs and must not be compared directly.

The matched key transaction remains **59.72594 ms**, with no reference reads.
P-frame RGB composition is 70.95872 ms versus v72's 70.74460 ms: different
LCD/refresh phases change contention. Banking changes memory implementation,
not painter arithmetic or native case cycles. Raw total read counts from runs
of different durations are not normalized bandwidth comparisons.

The four-frame transactions are **59.72594, 129.16555, 130.82141 and 128.42881 ms**.
Their modeled packet-to-ready portion spans **22.94679–58.20614 ms**. The run
checks 21,943 clean complete lines and 10,532,946 observed pixels. Its 27 complete
raster refreshes comprise 9/8/9/1 refreshes of four source IDs; repeated panel
refreshes are not new game frames. Trailing partial rasters are excluded from
complete counts. The separate pair and control replay are repeated coverage.

Native HUD preparation/readback/tag code executes, but processor execution does
not advance model time. Packet staging and typed sidebands substitute for live
transport. Consequently the model portion is not the fully charged on-target
validated-decoding interval. The runs are decoder-paced, not fixed 30-fps input
campaigns, and do not close either target milestone.

## Memory implementation evidence

The strip has the same 92,160 logical data bits in both versions. After
`memory_dff`/`memory_share`, v72 has one 5,760×16 memory with eight synchronous
read ports; v73 has eight 720×16 memories with one synchronous read and one write
port each. Unplaced family mapping yields:

| Painter resource | V72 | V73 |
| --- | ---: | ---: |
| Strip RAMB36E1 | 24 | 0 |
| Strip RAMB18E1 | 0 | 8 |
| Strip allocation, 18K equivalents | 48 | **8** |
| Other RAMB18E1 (Y row) | 1 | 1 |
| Painter DSP48E1 | 11 | 11 |
| Painter FDRE | 791 | 901 |

The strip allocation is **83.33% lower in this family-mapped, unplaced flow**.
No full-system fit, device-fit percentage, Fmax, CDC, pad timing or physical RAM
behavior follows from these counts. The 11 DSPs describe the painter, not the
whole decoder. Translated RTL simulation is not mapped-netlist or post-route
functional/timing simulation. See [elaboration.md](elaboration.md) for exact
commands, pinned frontend identity, generated-only lint exceptions and limits.

The Python all-tile trace separately predicts 64,800→32,640 reference bursts
and 518,400→261,120 physical x16 read beats, with unchanged 518,400 useful bytes.
Wire bytes are 1,036,800→522,240 and overfetch 518,400→3,840 bytes. This synthetic
trace differs from the CU66 P input's 7,806 reference tiles; it supports the
locality hypothesis without pretending to be frame-rate or latency evidence.

## Reproduce and integrate

Use the existing tool containers with the checkout mounted at the same absolute
path. The frontend binary must match the SHA in [elaboration.md](elaboration.md);
set `SV2V_PATH` to its container path if required. Native simulations retain
full strict lint. Build jobs remain one each under the shared 4-CPU/4-GiB limit.

```sh
python3 scripts/cu66-v73/verify_baseline.py
python3 scripts/cu66-v73/reference_traffic.py
python3 scripts/cu66-v73/run_memory.py
python3 scripts/cu66-v73/run_painter.py
python3 scripts/cu66-v73/run_elaboration.py
python3 fpga/experiments/cu66-v73/system/run_control.py
python3 scripts/cu66-v73/run_system.py --frames 2 --strip
python3 scripts/cu66-v73/run_system.py --frames 2 --strip --p0-cache-lines 1
python3 scripts/cu66-v73/run_history.py --frames 4 --strip
python3 scripts/cu66-v73/compare_system.py
python3 scripts/cu66-v73/verify_evidence.py
python3 scripts/cu66-v73/bundle_manifest.py
```

Regenerate comparison, audit and bundle records after producer reruns. Never
rerun old-version producers into frozen paths. `system/sources.json` lists the
integrated sources; hardware top is `cu73_system`, `USE_STRIP=1`,
`P0_CACHE_LINES=8`, with no `SIMULATION` and the simulation wrapper/model excluded.
The staged `build/ooc_system.tcl` retains the exact device and declared clocks.
`build/status.json` pins 21 hardware sources, includes, tool identity and logs;
the unavailable-part preflight is not an implementation PASS.

Preserve actual drained-boundary presentation ACKs and candidate/reference/front
leases. Retain the held full-line P0 response until accepted, even during abort.

Profiling counters are 32-bit modulo values. Current runs use per-frame deltas
well below wrap; long campaigns require overflow-safe software accumulation or
wider/snapshotted counters. Service includes held responses; wait counts only
an asserted unaccepted request. Do not add asynchronous phase counters as if
they were a complete critical-path decomposition. Live MMIO snapshots and clock
synchronization still need board integration.

`system/before-cache-index-widths/` preserves 43 source/log entries in a hashed
ZIP. Default-eight behavior passed, but strict cache1 lint exposed index widths
sized only for eight lines. Parameter-dependent casts fix that configuration;
both settings were requalified without warning suppression. Other development
logs are not substituted for the qualified producer records.

## Next implementation priorities

1. Profile and prototype tile-major canonical storage with four full BL8 writes
   and reads per 64-byte tile, versus eight masked row writes. It can reduce
   write commands and scalar/row arbitration, but painter/scanout access costs
   must be measured before selecting the layout. Preserve canonical hash order.
2. Evaluate a direct-YUV display path with bounded strip/line caches, bilinear
   conversion and the same exact HUD. Removing RGB copy traffic must still pay
   conversion, prefetch, memory and scanout costs and preserve front leases.
3. Evaluate independent cache-hit replies and safe decode/paint overlap only
   with explicit ordering, pending-write fences, accepted-operation drains and
   measured queue tails. The current response ownership remains conservative.
4. Qualify retained 457-frame histories through the changed memory path, then
   the predefined 1,800-distinct-source arrival campaign. Close exact-device
   synthesis/placement/routing/CDC and live ESP32/processor service before the
   ten-minute physical 30-fps claim. Retain throughput before closing strict
   observed maximum validated decoding below 10 ms. Short benches and unplaced
   painter mapping satisfy neither gate.
