# CU71 display/painter integration status

These are source-bound leaf and controller/display simulation results. Board
routing, live ESP32 transfer, complete CU66 hardware playback and 30 unique
displayed frames/s remain root integration gates.

## Selected interfaces

Use `cu71_painter_strip_burst.sv` for the new RGB backend. Scalar auxiliary
ports now carry reads only. The additional RGB interface is:

| Signal | Direction at painter | Meaning |
|---|---|---|
| rgb_req_valid / ready | out / in | One aligned write burst outstanding |
| rgb_req_addr[23:0] | out | x16 word address, aligned to eight |
| rgb_req_data[127:0] | out | Word i occupies bits16*i+:16 |
| rgb_req_mask[15:0] | out | Active-high disabled bytes; zero for these complete bursts |
| rgb_rsp_valid / ready / error | in / out / in | Actual controller drain completion, not queue acceptance |
| rgb_abort_i / busy / aborted | out / in / in | Cancel joins the explicit memory abort/drain acknowledgment |

On cancellation the painter does not wait for a normal response suppressed by
the memory adapter. It waits until its accepted operation drains and the RGB
busy lease clears. Scalar read aborts continue to consume their normal reply.
Global reset requires the external adapters to be flushed together.

The strip gathers eight synchronous RAM words for each contiguous portrait
column write. Bars write eight zeros per burst. A normal complete frame has
exactly48,000accepted RGB bursts =384,000logical output words, with345,600
canvas pixels. The scalar read contract remains280,320words/frame. The new
backend rejects unaligned RGB bases before emitting memory traffic.

`cu71_scanout_banked.sv` keeps the selected prefetch interface and adds only
an explicit `RGB1_BASE` parameter. It translates the inherited logical slot
bit19 and low19-bit row offset at line admission. Descriptor/lease/token CDC
behavior is unchanged. Use the same generated map as the renderer and memory
bridge. Keep `cu71_scanout_prefetch.sv` as the old-map control.

## Resource and color pipeline repair

The old asynchronous5760word RGB-strip access was not target-fit. The new
BRAM implementations have separate unreset synchronous strip/Y/chroma ports.
Chroma RAMs use two synchronous reads with a write sharing one port during
LOAD. HUD cache storage remains small. State ownership invalidates old data;
configuration or soft reset does not reset bulk memory contents.

The scalar BRAM control passes exact pixels but its initial synthesized
100MHz setup slack is-9.722ns. It is not the timing candidate.

The selected color pipeline uses three additional owned stages per pixel:
bounded chroma sampling, signed products, and scaled RGB, then native clipping.
Interpolated chroma is0..255, centered chroma is signed9-bit-128..127;
coefficients359/454 are positive signed10-bit values, products/sums use19bits,
and scaled RGB uses11signed bits. Rounded horizontal and vertical interpolation
remain separate in the original order. Incremental YUV/strip addresses and
registered narrow HUD offsets avoid long chained DSP control-address paths.

| Candidate | Native synthesis resources | Synthesized100MHz setup / hold | Verdict |
|---|---|---|---|
| Scalar BRAM, `painter-bram-ooc02` |1458LUT,503FF,9RAMB18+4RAMB36,10DSP |-9.722 / +0.246ns | Pixel control only; fails setup |
| Pipeline scalar, `painter-pipe-ooc03` |1322LUT,751FF,9RAMB18+4RAMB36,0DSP |+1.400 / +0.246ns | Leaf gate passes |
| Pipeline RGB burst, `painter-burst-ooc01` |1441LUT,986FF,9RAMB18+4RAMB36,0DSP |+1.397 / +0.246ns | Selected leaf gate passes |

Pulse-width slack is+3.750ns in the passing leaf reports. These are synthesis
estimates on `xc7a100tcsg324-1`, not routed-board timing qualification.

## Executed correctness evidence

- `painter-pipe-raster03`:26complete physical rasters /9,984,000word checks,
  eight actual key/P frames, four synthetic patterns and recovery per seed,
  plus five seeded accepted-read/write abort/error cases.
- `painter-pipe-control03`: independent four-state Icarus dirty-strip discard,
  actual accepted-operation drain and coordinated reset with new source bias.
- `painter-burst-raster02`: the same native full-raster campaign and faults,
  additionally checking exactly48,000accepted RGB packets per normal frame.
  A verification-only adapter exposes all eight words independently to the
  native scoreboard and acknowledges only after their completions. It is not
  the actual SDRAM controller or an RGB throughput benchmark.
- `painter-burst-control02`: four-state dirty data/abort/reset tests and
  unaligned-RGB admission rejection. Bulk RAM remains unreset in the DUT.

The first BRAM attempt exposed a synchronous first-word prefetch error at a
strip transition. Its failed raster and synthesized source remain preserved.
The repaired design primes the first word during strip fill. Early pipeline
compile/lint and negative synthesized timing attempts remain separate.

The old scalar ideal strip cost2,430,489cycles/frame; the three-stage scalar
pipeline costs3,467,289cycles/frame under the same ideal scalar memory model.
The burst verification adapter adds serialization overhead and must not be
used to estimate the new real BL8 backend. Actual system costs must be measured
with the selected memory interface and all concurrent clients.

## Bank placement A/B and an unresolved cadence limit

The old-map qualified-controller/prefetch test with canonical+HUD background
traffic passed full384,000pixel rasters at both declared model corners with
zero underruns. That did not cover concurrent painting into the other RGB slot.

The matched actual-controller full-raster A/B uses distinct per-slot pixels:

| Map / front / background | Black replacement lines of720 | Verdict |
|---|---:|---|
| Old map, RGB0front, RGB1writes +canonical1 |682 | Cadence FAIL |
| RGB1=0x980000, RGB0front, RGB1writes +canonical1 |0 | Selected workload PASS |
| RGB1=0x980000, RGB1front, RGB0writes +canonical2 |656 | Cadence FAIL |

Every line remains exact or entirely black; black lines remain lost content,
not clean presentations. The cross-bank mapping helps one front descriptor but
does not universally solve contention with canonical bank2. No map is silently
promoted to a general release on these results.

The corrected32-line front1 trace shows four clean lines, then accumulating
backlog: line44 completes9ns after its first active pixel. Fill service around
18.6–19.0µs exceeds the18.43µs native line period. The approximate20.5µs initial
lookahead is not a sustainable line-rate budget. See
`banked-newmap-front1-CAN2-trace01`; the original full front1 test's line-fill
timer used the wrong physical base, so its403cycle statistic is invalid while
its pixel and underrun counts remain valid. The follow-up fixes that timer.

Keep these failures visible during full RGB-burst and bank-aware arbitration
integration. The display/painter component gates do not close complete CU66
memory-service, unique-frame cadence or physical performance gates.
