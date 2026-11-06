# V77 cache-backed elastic RGB pipeline

`cu77_yuv_rgb` implements the native CU66 bilinear chroma rounding, Q8 signed
color conversion, clamping, RGB565 packing and opaque HUD replacement. It is a
three-stage elastic pipeline with one accepted pixel per clock when unblocked.
Coordinates and the input error flag remain attached to their pixel. Output
values hold while stalled, and local abort flushes unaccepted pipeline outputs.

Stage 0 captures Y and parity-dependent interpolated signed Cb/Cr. Stage 1
computes signed color values. Stage 2 clamps, packs or substitutes HUD. The
signed extension of Y is explicit so an unsigned arithmetic context cannot
convert negative chroma shifts into logical shifts.

## Cache integration and ownership

`cu77_render_sim` connects the actual `cu77_direct_cache` synchronous word-read
outputs to the converter; expected native sample data does not bypass the RTL
cache. It tracks outstanding accepted pixel requests through both components.
Consume, finish and replacement-descriptor handshakes remain blocked until the
whole pixel pipeline drains. This prevents a cache epoch from being released
while the converter still holds an old pixel. Local abort cancels unaccepted
pixels while the cache separately drains accepted memory words.

The wrapper is a common-core-clock component, not a real pixel-clock CDC,
canonical front/reference bank controller or complete receiver. It emits only
the 345,600 active pixels, in portrait scan order (u outer, v inner); black
border, porch and physical-panel delivery remain separate integration work.

## Native oracle regression

```sh
python3 scripts/cu66-v77/run_render.py
```

The runner first verifies the standalone arithmetic pipeline. A separate C++
mathematical oracle checks corner samples, random sample neighborhoods, all
coordinate parities, HUD replacement, error propagation, backpressure and abort.
The final run accepts 103,631 pixels, emits 103,590 and flushes 41 across 21
abort probes. It verifies 9,997 continuous II=1 cycles.

The integrated bench decodes eight real key/P fixtures from four retained
cohorts using the frozen native decoder, then adds four synthetic patterns and
one recovery frame. Memory planes are independently placed into physical
8×8 tile-major storage; HUD pixels are packed independently. The ideal memory
source delays complete BL8 responses and individual beats, while the actual
cache stores the received words and supplies neighborhood samples. Every
output pixel is compared to the independent native `cu66::render` result.

Three schedules (0, 7701, 7702) verify **39 active frames / 13,478,400 RGB565
words**. They rotate across all three canonical/HUD banks with new descriptor
generations. Every successful frame requires **35,040 read requests, 280,320
received words and 345,600 accepted/emitted pixels**, with no cache misses or
error response. Each delayed schedule additionally aborts a live pixel pipeline
and injects a streamed memory error, followed by an exact recovery frame:
**four integration fault probes** in total. Accepted memory operations drain
before restart, and stale outputs must not survive the new descriptor.

| Ideal memory schedule | Complete active-frame cycles |
|---|---:|
| No injected stalls | 350,870 |
| Seed 7701 | 679,688–681,389 |
| Seed 7702 | 678,846–681,174 |

At the assumed 100-MHz component clock, the no-stall number is 3.50870 ms. It is
**render/cache component work with ideal memory**, not validated FPGA decoding,
real SDRAM throughput, a routed clock or an under-10-ms streaming result. The
old RGB canvas write-back is absent from this component interface, so it is not
an isolated same-operation timing comparison with the old painter.

## Evidence boundaries and provenance

`render/results.json` pins RTL, native source/fixtures, bench and producer, and
retains every build/run command and log hash. The standalone result is separate
in `pixel-results.json`. The initial standalone qualification, before extending
the producer to integrated replay, is preserved as a six-member internally
hashed ZIP in `render/before-cache-integration/`.

Initial unused RGB low-bit lint diagnostics and an initial signed-context color
mismatch are retained as development logs. The qualified RTL packs clamped
5-/6-bit outputs directly and explicitly signs Y; all qualified tests were then
rerun. These diagnostic logs are not passing qualification records.

No result here proves complete compressed-frame decode, source-generation
front/reference leases, pixel-clock delivery, target fit/Fmax/CDC, live ESP32
service, physical 30 fps or strict maximum validated decoding below 10 ms.

## Separate bounded-address variant

The baseline sources and evidence above are preserved. The separate
`cu77_render_bounded_sim` wrapper selects `cu77_direct_cache_bounded`, keeping
the converter, pixel guard and **unchanged `tb_render.cpp`**. Its runner uses a
separate build directory and model prefix; it does not rewrite or substitute
the baseline module.

```sh
python3 scripts/cu66-v77/run_render_bounded.py
python3 scripts/cu66-v77/run_elaboration_bounded.py
python3 fpga/experiments/cu66-v77/elaboration-bounded/compare_mapping.py
```

Native and converted bounded campaigns each pass **39 active frames /
13,478,400 RGB565 words / four integration faults**. Every individual case's
cycle, transfer, output, generation and bank counters equals the baseline.
The cache leaf additionally checks its bounded modulo-three helper exhaustively
and retains its own fault/metadata regression. These are finite checks, not
formal equivalence.

Results are in `render/bounded/results.json` and
`elaboration-bounded/results.json`, with a separately pinned
`elaboration-bounded/comparison.json`. Actual SDRAM/display service and its
address adapter belong to the root integration benchmark, not these ideal
memory tests.
