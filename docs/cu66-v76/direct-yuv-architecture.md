# Direct-YUV architecture prototype and bounded lookahead

This is a proposed hardware organization with an executable Python address,
cache-liveness and pixel model. The V76 service benchmark separately measures
real frozen controller transactions. Neither component is a new RTL display
renderer or proof of safe hardware presentation.

## Structured banks instead of a large associative LRU

The independent service trace uses a software 720-line YUV LRU and a separate
192-line HUD LRU, each line holding eight x16 words. A literal 720-way lookup or
software LRU update is not the intended FPGA implementation. Fixed geometry
allows smaller tag/control structures with the same tested miss sets.

At coded column `u0` in steps of eight, a native physical strip covers
`u=u0..u0+7`, `v=0..479`, mapped to physical `y=u+40`, `x=v`.

| Storage | One-strip organization | Data bytes |
|---|---|---:|
| Y | One 8-column tile column × 480 rows | 3,840 |
| Cb | Two tagged 8-column tile columns × 240 rows | 3,840 |
| Cr | Two tagged 8-column tile columns × 240 rows | 3,840 |
| HUD | Two packed BL8 columns × 24 rows for each of four rectangles | 3,072 |
| Total | | **14,592** |

Chroma needs a right interpolation halo. Each plane uses two column slots,
indexed by global chroma tile-column parity, with explicit global-column tags.
The column needed by consecutive strips remains live while the next is loaded.
Y uses tile-row and word-within-tile indexing inside its current column bank.
Each HUD rectangle uses its own packed-word column slots; its source address is
`HUD_base + patch_offset + row*rectangle_width + block_column*8`.

A structured prefetch loads each required physical BL8 once, in the tested
per-strip order. Across the 90 strips it issues exactly **32,400 YUV bursts plus
2,640 HUD bursts = 35,040 bursts / 560,640 bytes**, matching the independent
LRU trace's complete per-strip miss sets. The HU data is not treated as a
contiguous logical byte charge per strip: the rectangles at coded x=22 cause
packed-block misalignment, and retained columns matter.

## Two live strips and a real overwrite hazard

A next-strip fill may load strip `i+1` while strip `i` remains live.
This requires storage and ownership for both;
starting requests early without that storage is unsafe.

Two Y column slots cost 7,680 bytes. Chroma still needs two slots per plane:
the union of the required chroma columns for two adjacent strips spans at most
two tile columns. HUD is different. Since a rectangle can start at x=22,
two adjacent physical strips can span **three** packed BL8 columns in that
rectangle. Two HUD slots may overwrite pixels still needed by the current strip.

The model deliberately tests that unsafe two-HUD-column variant. It detects a
live HUD-column mismatch when current strip u=24..31 still needs packed column
0 but prefetch of u=32..39 has replaced it with column 2. A three-slot ring,
with explicit global-column tags, retains all three required columns.

| Storage | Current + next strip | Data bytes |
|---|---|---:|
| Y | Two column slots | 7,680 |
| Cb + Cr | Two column slots per plane | 7,680 |
| HUD | Three BL8-column slots per rectangle | 4,608 |
| Total | | **19,968** |

This is **5,376 additional bytes** versus the one-strip model. Tag/control,
response staging, pixel pipelines, output line/CDC buffers and implementation
padding are additional. Data bytes do not predict BRAM primitives or target fit.
A slot-ring counter can implement the three HUD slots; the Python modulo
expression is not a requirement for a hardware divider or associative LRU.

## The passing early schedule requires three live strips

The benchmark's original request release is `R_i=i*P`, with cache-ready
deadline `D_i=(i+1)*P`, where `P=147.403024 µs`. To consume whole cached strips,
start consuming strip `i` at `D_i`, after one initial period of prefill. Its
pixels remain live through `D_i+P`. Thus even the original service schedule
can fill one strip while consuming the previous one.

The separately passing early schedule moves request release to
`R_i=max(0,i-1)*P` while **retaining `D_i`**. It can hold a current consuming
strip, the next ready strip, and an additional strip being filled. A two-live
strip proof does not justify that schedule. Three adjacent Y columns and three
chroma columns per plane may be live together; misaligned HUD rectangles may
span four packed block columns.

| Storage | Current + next ready + filling strip | Data bytes |
|---|---|---:|
| Y | Three column slots | 11,520 |
| Cb + Cr | Three column slots per plane | 11,520 |
| HUD | Four BL8-column slots per rectangle | 6,144 |
| Total | | **29,184** |

The corrected model checks that configuration with the same physical miss sets
and all active pixels. Separate negative probes retaining only two Y slots,
two chroma slots, or three HUD slots each expose an overwritten live column.
The earlier 19,968-byte model remains useful for **two** live strips; it is not
the memory budget for the passing early-service schedule. The correction is a
consumer-timeline/liveness issue, not a change to measured SDRAM deadlines.

The 29,184-byte budget is 9,216 bytes above the two-live model, with hardware
padding, pipeline staging, tags and output buffers still additional. The initial
prefill window and subsequent source-generation transitions must be implemented
and measured; the service bench has no pixel consumer enforcing those times.

## Model evidence

```sh
python3 scripts/cu66-v76/structured_cache.py
```

Each of the one-, two- and three-live-strip configurations checks **345,600 active RGB565
pixels** from deterministic synthetic YUV and opaque HUD data. Cache fills
decode physical tile-major/packed HUD addresses independently; pixel queries
use logical sample coordinates, exact parity-dependent bilinear rounding and
fixed-point color equations. The mathematical reference bypasses caches.
The models verify all required sample tags and values after any lookahead fill,
then compare complete per-strip request sets with the independent service trace.

The expected-hazard probes must fail their liveness lookups in the undersized
configurations. Their rejection is a negative self-check, not a passing hardware
configuration. Result sources and trace hashes are in
`fpga/experiments/cu66-v76/structured/results.json`.

The checks cover one immutable synthetic source, active pixels and finite
geometry. They do not implement cycle timing, HDL cache ports, fixed-width RTL
arithmetic, a DDR-to-cache data mover, black-border delivery, a display clock
crossing or real source-generation changes. The existing phase replay retains
its separate actual-RTL/native-oracle full portrait checks.

## RTL integration gates

1. Build a streamed cache fill path with explicit write addresses and valid
   tags only after accepted data drains. A 128-bit reply unpacked serially for
   eight extra clocks has a different budget from a controller stream that
   writes one received word per clock; measure the actual implementation.
2. Schedule cache reads and writes on real BRAM ports. Register full words
   before byte selection as in V75. Exploit fixed-u scan rows and reuse of
   neighboring chroma rows, rather than assuming four unconstrained RAM reads
   per pixel. Pipeline color arithmetic for native pixel delivery and measure
   fill/compute overlap under stalls.
3. Keep current/next strip tags live until consumption completes. Compare the
   hardware miss addresses, tags, all pixels and deadlines against this model.
   Requalify the cache budget if the lookahead depth changes.
4. Bind caches to bank, generation and source ID. A new descriptor must not
   reuse old-generation data. Drain old-front accepted reads and honor the
   qualified vblank switch before releasing its canonical bank. The old RGB
   flow could release a canonical bank after copying it; direct scanout cannot
   inherit that assumption.
5. Test actual source switches, stale/late responses, aborts, pending
   descriptors, reference/front sharing and memory errors. Service-only
   deadline success and Python liveness checks do not close these gates.
