# V85 actual residual-only coefficient streams

V85 now **actually re-encodes the original quantized coefficients** for visible
RESIDUAL tiles, instead of estimating a benefit by removing work from an old
trace. Hidden CONST128 tiles are omitted. Visible all-zero coefficient tiles
are COPY only on deltas; every visible tile remains RESIDUAL on keys. Native
pixel quantization and geometry are unchanged.

The new component encoder is a C++ port of the frozen V38 adaptive binary/Rice
encoder. It retains four independent 16-bit arithmetic contexts, shift-only
probability adaptation, bounded coefficient values, minimum-uncoded-Rice-cost
parameter selection, deterministic tie behavior and raw fallback. It resets DC
prediction for **every residual tile** (`blocks_w=1`). Original native streams
may use different full/compact/DC-predictor choices, so comparing only their
sizes would not isolate COPY filtering as the sole cause.

## Correctness and retained components

The original frozen native decoder checks all **457 packets**, canonical plane,
semantic HUD and displayed RGB565 digests. Its 1,371 original coefficient
planes are parsed/scattered into canonical tile order. Python cross-checks
every frame/digest and all 3,701,700 zero-coefficient-mask bits against V82.
Each newly encoded chunk is independently decoded with the **frozen native
AB38 decoder**, then compared against its exact input coefficients.

`experiments/python-gamebub-v85/residual/data.py` exposes `iter_frames()`.
Each record includes:

- Native cohort/ordinal/frame/reference/key identity and original digests.
- Original packed 338-byte quantization map and encoded HUD bytes.
- `canonical_coefficients_sha256`, hashing all 8,100 raster tiles as 64
  signed-16-bit little-endian coefficients each, including implicit zero tiles.
- `zero_mask`, original packet path/lengths, block-size metadata and three
  residual counts.
- `variants`, keyed by `16`, `64`, `256`, `65536`; each value contains three
  ordered plane lists of `{blocks, data}` chunks with actual AB38 bytes.

Scatter order is ascending canonical RESIDUAL tile index within each plane.
There are no chunks for an empty residual plane. The cap `65536` means a whole
native plane; wire framing must represent that value with a sufficiently wide
field or an explicit enum. Frame-envelope, map, chunk-descriptor, transport and
HUD costs are not included in the component table below.

| Residual tiles per reset chunk | AB38 bytes, total | Chunks | Frame median AB38 bytes | Frame maximum AB38 bytes | Largest single chunk |
|---:|---:|---:|---:|---:|---:|
| 16 | 10,979,742 | 85,078 | 23,904 | 65,524 | 454 |
| 64 | 5,990,470 | 21,753 | 12,379 | 36,363 | 1,384 |
| 256 | 4,707,730 | 6,061 | 9,398 | 29,321 | 2,638 |
| Whole plane (`65536`) | 4,265,737 | 1,371 | 8,149 | 27,058 | 23,729 |

All **114,263 generated native chunks** are compressed, and all pass native
decode/input coefficient parity. Reset headers, termination and probability
reinitialization are included in these actual byte lengths. Small chunks are
clearly expensive; the 16-tile case can exceed the old 49,152-byte packet budget
before adding any HUD or outer framing. This is a compatibility observation,
not a claim about the board's physical memory capacity.

The independent retained-data audit checks structure, every chunk's AB38
header/CRC/coverage, native zero masks and recomputed byte totals. Whole-frame
reconstruction, content commitment, protocol identity and timing qualification
remain separate receiver/system checks.

## Matched same-encoder COPY control

A second native executable encodes all visible coefficients and COPY-filtered
coefficients with the **same new encoder and whole-plane `bw=1` rule**. It
checks that its filtered packets are byte-for-byte identical to the retained
whole-plane candidate, providing a matched control independent of original
native dispatch/parameter choices.

| Matched component | AB38 bytes, total | Frame median | Frame maximum |
|---|---:|---:|---:|
| All visible coefficients | 4,618,536 | 9,163 | 27,534 |
| COPY-filtered residuals | 4,265,737 | 8,149 | 27,058 |

Filtering saves **352,799 component bytes (7.64%)**: all 437 deltas improve,
all 20 keys are equal, and none regresses. The paired per-source saving ranges
from 0 to 1,479 bytes, median 803 bytes. The same encoder performs 43,887,028
versus 37,656,819 arithmetic decisions. These are encoding-work observations,
not measured decoder cycles.

The V84 V2 operation maps alone total **384,102 bytes**, more than this isolated
component saving by **31,303 bytes**. The map, frame envelope, HUD and transport
must therefore be included before claiming any whole-stream bitrate advantage.
Residual-only syntax can reduce work while still costing extra total bytes.

## Encoder edge cases and scope

Twenty-two directed native checks cover zero tiles, signed DC extrema, last-AC
extrema, sparse/dense deterministic random coefficients, empty input rejection
and out-of-range rejection. The frozen decoder independently recovers every
valid case. One case selects raw fallback; that path is qualified synthetically,
but absent from the native corpus.

Actual compilation uses the existing `gamebub-cu66-v69-build` container and a
unique `/build/v85-residual-*` path, with `-std=c++17 -O2 -Wall -Wextra -Werror`.
No package/container changes are required. The first compile attempt failed a
misleading-indentation warning in JSON output formatting; its source snapshot
and raw logs are retained. A formatting correction and an additional encoded
HUD SHA check preceded the successful collection. No failed corpus is selected
as the successful result.

Commands, compiler banners, binaries, source archives and native logs remain
under the residual collection/control attempt directories. The component
dataset and original executed sources are immutable after publication. This
work proves component bytes/coefficient parity and a matched coding comparison;
it does not establish a deployed Sunshine/ESP32 codec, physical decoder timing,
FPGA fit, sustained 30 fps or under-10-ms validated decoding.

## Reproduction

Verify retained components without compilation or encoding:

```sh
python3 experiments/python-gamebub-v85/residual/verify.py
```

Original data generation and the matched control use:

```sh
python3 scripts/cu66-v85/collect_residual.py
python3 experiments/python-gamebub-v85/residual/run_control.py
```

Both refuse to overwrite their selected retained result. They are provenance
commands, not instructions to replace a published corpus in place.
