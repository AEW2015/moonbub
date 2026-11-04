# Actual AR03 sparse inverse and conditional stripe service

This study proves a new **bit-exact sparse GENERAL-block inverse** against actual
AR03 vectors, then compares explicitly assumed FPGA service budgets. It also
proves that physical eight-bit YUV reference storage preserves canonical int16
reference tags. The wire format remains AR03; no native firmware, RTL, mapped
memory, DSP fit or physical playback rate is supplied.

The source is the frozen v18 trace fixture: 16 packet decisions, including twelve
native GM/exact decisions from six shared gameplay acquisitions and four partial
flat controls. It is reused precompressed regression footage, not a fresh corpus.
All native coded images retain 720×480 dimensions, with 720×405 active game content.

## Exact arithmetic and application-specific work reduction

`model.inverse()` preserves the frozen two-pass Q14 rounding boundaries. It uses
existing zero/DC shortcuts and, on GENERAL blocks, skips only products whose
coefficient or rounded intermediate is exactly zero. The second pass consumes the
actual first-pass rounded matrix. It does not prune coefficients or approximate
pixels. The working comparison baseline retains the previously implemented
zero/DC shortcuts and performs dense matrix products only on GENERAL blocks;
the dense-all-blocks profile is a diagnostic.

All 97,308 actual blocks, 6,227,712 residual samples, 6,224,472 cropped reconstructed
YUV samples and final display words match frozen outputs. Selected original UI
patches preserve 253,440 RGB565 words. Twelve native decisions contain 97,200
blocks: 46,122 zero, 23,952 DC and 27,126 GENERAL. New GENERAL-block product skipping
reduces their IDCT MAC operations from **27,777,024 to 4,267,808 (84.64%)**, beyond
existing zero/DC bypass. This count excludes dequantization and DC-constant
products, which are reported and charged separately.

The conditional timing model pays source and intermediate index scans, dequant,
two dependent matrix passes, rounding/control overhead and all 64 output stores.
Sparse scanning can cost more than dense execution on dense input; a regression
test demonstrates that edge. Counted MAC savings are not an equal FPGA speedup.

Legal coefficient ±2048 and quantizer ≤255 give a dequantized magnitude bound
522,240. Frozen +8192 biases are included in conservative accumulator bounds.
The declared 32×16 product / 40-bit accumulator slot covers these legal bounds
(20-bit first operand, 22-bit intermediate, 38-bit accumulator bound). The model
lists two 18×18 multiplier primitives per wide slot as an architectural planning
assumption; signed splitting/recombination, additions, rounding, routing and Fmax
are not fitted or synthesized.

## Compact reference storage without changing canonical identity

Reconstructed YUV samples are clipped to 0…255. Every vector is packed to uint8,
unpacked to int16 and compared exactly. Canonical reference hashes are recomputed
from `<HH width,height>` and little-endian int16 Y/Cb/Cr values before and after
packing; all sixteen tags match. UI overlay remains display-only and never enters
these predictors or tags.

The compact profile stores physical reference/reconstruction/color samples as
one byte rather than two. Canonical tag hashing still consumes **two serialized
bytes per sample**; zero-high-byte expansion and SHA-256 service are charged.
Expansion does not invent a second SDRAM read. Actual bank layout, burst packing
and hardware hash implementation remain development work.

## Bounded stripe model and its explicit storage tradeoff

The scheduler uses exact per-block token cursor refills and mode counts from each
packet, grouped in original plane/stripe order. The uniform counterfactual keeps
each plane's total selected bytes and logical bits but spreads them by block count.
The actual burst pattern is retained; it is not repeated-template traffic.

The proposed architecture stages the complete compressed packet externally,
pays four full-packet preflight/CRC passes as an **explicit planning assumption**,
then reads it into a separately counted **49,152-byte local compressed cache**.
The four passes are not a derived count of all frozen parser traversals. Cache
fill reads and local token-read throughput are paid. This cache spends area to
avoid assuming a parallel free SDRAM port for entropy; a smaller refill-cache
with an explicit shared arbiter remains a next experiment.

Two coefficient-stripe buffers permit entropy prefetch while one serial consumer
reads prediction, performs inverse reconstruction and writes YUV. A buffer remains
owned until consumption finishes; the entropy producer stalls rather than
allocating unbounded work. Model dimensions also allow one-buffer controls and up
to four buffers. One reconstruction stripe, inverse scratch/index storage, basis/
quantizer ROM, color lines, palette and two ≤64-bit entropy reservoirs are counted.
The native two-buffer planning footprint is **100,112 bytes**:

| Local storage | Bytes |
| --- | ---: |
| Full compressed cache | 49,152 |
| Two coefficient stripes | 23,040 |
| Reconstruction stripe | 11,520 |
| Inverse/intermediate/accumulator/index scratch | 960 |
| Q14 basis and quantizer ROM | 512 |
| Bilinear chroma, Y and RGB565 color lines | 14,400 |
| Maximum UI palette | 512 |
| Two entropy reservoirs | 16 |

This is not total decoder heap or a BRAM-fit result. Python trace/full-coefficient/
output/oracle arrays, external reference/display banks, parser implementation and
control metadata are outside that bound. The existing v18 functional parser still
materializes full coefficients; this is a prospective incremental architecture.

Reference/reconstruction/tag/color traffic is charged at declared sample width.
Postprocessing pays bilinear/color control, four color-constant products per
pixel, RGB565 packing, full display writes, palette overlay and canonical hash
work. The schedule serializes these stages rather than inventing overlap. It
reserves average bandwidth for 800×480×60 RGB565 scanout. That reservation does
not model the real 480×800 portrait scan order, line deadlines, scaling, rotation
or display-controller timing.

## Retained results

All timings below are deterministic **conditional planning outcomes**, not measured
native or RTL execution. Default assumptions are 100 MHz, four hypothetical wide
multiply slots, 140 MB/s effective aggregate SDRAM, 46.08 MB/s scanout reservation,
20 MB/s QSPI, one source/intermediate index coefficient and output sample per cycle,
80 ns overhead per 64-byte memory burst, and declared 100 MB/s CRC and canonical
SHA-256 service. These figures are uncalibrated.

| Profile | Mean service per native decision (ms) | Native decisions missing 33.33 ms |
| --- | ---: | ---: |
| Existing zero/DC bypass, dense GENERAL, four wide slots | 88.51 | 12/12 |
| New sparse GENERAL, four wide slots | 84.73 | 12/12 |
| New sparse GENERAL, eight wide slots | 82.55 | 12/12 |
| Sparse GENERAL + physical YUV8, four wide slots | 67.63 | 12/12 |
| Sparse GENERAL + YUV8, 240 MB/s memory assumption | 53.45 | 12/12 |

At equal four-slot budgets, paid end-to-end modeled service improves **4.27%**
from new sparse arithmetic; compact physical YUV8 improves a further **20.18%**.
These are matched deterministic model comparisons on identical packets and fixed
assumptions, not independently remeasured Python timings. The large MAC reduction
has a modest whole-chain effect because memory, scans, color and publication work
remain. More DSP slots alone do not solve that bottleneck.

Every native case misses the 33.33 ms budget in this deliberately serial schedule.
That does not establish a physical upper bound or rule out a better fused design.
A frame-ready time is not scanout epoch correctness, and no long-run 30 fps claim
is made. These tests are separate from the packet/frame-grant controller; their
numbers must not be added arithmetically to a different timing model.

Next test a smaller bounded compressed cache with shared memory arbitration,
fused reconstruction/tag/color passes and compact physical banks. Preserve exact
canonical hashes and display-only patches, then qualify mapped SRAM/SDRAM, target
DSP widths, service measurements and portrait line deadlines.

## Reproduce

Using the project environment, from this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python analyze.py --check
```

Twelve tests pass. `benchmark.py` needs NumPy and the retained v18 objects, but not
the original video. `verify.py` checks source/object pins, freshly replays all actual
arithmetic and YUV/display/tag comparisons, and reconciles every conditional
schedule. `analysis.json` is result/analyzer-hash bound. Benchmark wall time is
neither hardware latency nor playback FPS. Source pins conservatively include
ancestry dependencies and retained objects, not exclusively executed code.
