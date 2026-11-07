# V92: actual per-context arithmetic/Rice choices

This isolated research branch implements the V92 E2 experiment from the
[V91–V110 roadmap](../gamebub-v91-v110-development-plan.md). It retains the
720×480 picture, quantizers, intended coefficients, temporal references,
semantic HUD and publication commitments. The candidate changes entropy
representation only. V91l remains partial; this study does not close its
integration gates.

Each plane has four independent entropy streams: DC, then zigzag AC indices
`[1,6)`, `[6,21)` and `[21,64)`. EC92 can choose frozen AB38 adaptive arithmetic
coding or BR88 plain bounded Rice separately for each stream. Three planes
therefore expose 12 selector bits and 4,096 combinations. No HEVC CABAC or AV1
bitstream compatibility is implied.

## Grammar and compatibility

An EC92 chunk encodes one sequence of 8×8 residual blocks, not a complete frame.
All multibyte EC92 fields below are little-endian.

| Offset | Bytes | Meaning |
|---|---:|---|
| 0 | 4 | ASCII `EC92` |
| 4 | 1 | Version 1 |
| 5 | 1 | 0 coded, 1 RAW; all other values rejected |
| 6 | 1 | Bits 0–3 select DC/AC0/AC1/AC2; 0 AB38, 1 BR88; upper nibble zero |
| 7 | 1 | Reserved zero |
| 8 | 4 | Block count, 1–65,536, matching the enclosing directory |
| 12 | 2 | Predictor width 1: each block's DC starts from zero |
| 14 | 2 | Reserved zero |
| 16 | 16 | Four stream byte lengths |
| 32 | 12 | Three AC event counts |
| 44 | variable | Four streams in selector order, or RAW coefficients |
| final 4 | 4 | CRC-32/IEEE over all preceding chunk bytes |

A coded stream length includes its six-byte descriptor: Rice parameter `k0`,
parameter `k1`, and a 32-bit bit length, followed by MSB-first coded bits and
zero low-bit byte padding. DC uses `k0≤13`, `k1=255`; AC uses run `k0≤19` and
level `k1≤11`. Run/level mapping, bounded unary prefix 15 and escape widths
14/24/12 are unchanged. DC has exactly one value per block. AC uses the declared
event count and strictly increasing positions confined to its band.
Coefficients remain within `[-2048,2048]`.

Every stream starts fresh. AB38 uses the frozen 88 probability contexts,
16-bit arithmetic state initialization and exact two-zero-bit termination.
BR88 consumes exactly its declared bits. A zero-event BR88 AC stream can have
zero bits; an AB38 stream still has its arithmetic initialization/termination.
Neither coder may read through another stream or into the CRC.

Coded stream bytes together must be strictly fewer than `128×blocks`; equality
or overflow uses RAW. RAW requires selector zero, lengths
`[128×blocks,0,0,0]`, zero AC counts and little-endian signed 16-bit coefficients
in block/raster order, without stream descriptors. Chunk size is at most
`48+128×blocks`. The prototype conservatively uses RAW for every choice if
either frozen whole-plane encoder has already discarded its candidate streams
for RAW; it does not invent unavailable alternatives. This limitation is tested
and does not occur in the retained gameplay corpus.

Complete frames use explicit **CS92/version 1**, preserving CS88's 128-byte
big-endian frame envelope, mode map, QM87 quantizers, three plane directories,
HUD, canonical root, frame seal and final big-endian CRC. Each plane directory
binds an EC92 chunk's block count and byte length. The implemented study uses
one chunk per plane. The complete CS92 frame, including every component and CRC,
must fit **49,152 bytes**. This is a negotiated research profile limit, not a
measured FPGA RAM ceiling. A small RAW chunk fitting its own bound does not
establish that a complete frame fits. Oversized future content needs a real
sender fallback or split profile before product promotion.

The new native receiver directly decodes EC92 and validates the reconstructed
picture/HUD/root/seal before atomic state commit. It does not repack chunks into
legacy packets. Legacy CS88 receivers reject CS92. The existing V91 RTL
admission/BR88 path remains unchanged and cannot accept this profile.

## Bounded selection and host accounting

The host encodes AB38 and BR88 once per plane and retains four stream candidates
from each result. It assembles 16 actual EC92 chunks from those streams. It never
performs 4,096 complete frame encodes. Native decoding verifies every assembled
chunk, with independently counted arithmetic decisions/renormalizations and
plain bit reads. The standalone Python reader imports neither encoder nor
native decoder.

The frame selector uses an exact Pareto search over byte count and the
lexicographic objective `(AB decisions, AB renormalizations, BR bits, mask)`.
After each plane it discards dominated states. Its hard combination bound is
`16+256+4096=4368` proposals and at most 4,096 simultaneous proposals. An
independent exhaustive enumeration checks each selected result. This objective
is a reproducible work policy, not a prediction of FPGA completion latency.
An all-Rice choice still performs real bit reads and parser work.

Policies compare minimum bytes, minimum adaptive work under 5% and 15% complete
byte allowances, and a matched whole-plane-only control under the same 15%
allowance. Each allowance is relative to the frozen CS88 all-AB38 complete frame,
and every choice also respects 49,152 bytes. Thus the extra six header bytes per
complete frame are charged, not hidden in the denominator.

Native generation timing includes frozen coefficient extraction, both encodes,
all 16 candidate assemblies and hashes, including discarded candidates. Native
all-candidate verification and Python/archive wall time are separate. The
experimental AB38 encoder also performs internal parity verification, which is
included rather than subtracted. These are Linux host timings, not ESP32 or FPGA
cycle measurements, live Sunshine throughput or a routed-clock estimate.

## Reproduction and evidence

Run from the repository root with Python 3 and the existing
`gamebub-cu66-v69-build` container (strict GCC 13.3 C++17 build):

```sh
python3 scripts/cu66-v92/test_python.py
python3 scripts/cu66-v92/test_selection.py
python3 scripts/cu66-v92/collect_contexts.py
timeout 1200 python3 scripts/cu66-v92/run_wire.py
timeout 180 python3 scripts/cu66-v92/test_wire.py
python3 scripts/cu66-v92/summarize.py
```

Attempts retain source snapshots/pins, actual serialized bytes, commands and
observed results. The selected component archive and complete frame archive are
hash-bound and compressed. Failed attempts remain available with their causes.
See [results](results.md) and [the independent contract audit](audit-notes.md).

## Promotion gates

V92a/b establish the grammar and real alternative bytes. V92c software evidence
requires independent coefficient decoding, complete native frame parity,
malformed/recovery tests and actual host preparation accounting. V92d remains
open until selection includes integrated physical memory/latency costs and a
promoted mixed-context RTL receiver is implemented and qualified. Current
operation counts do not account for all arithmetic-core setup, ports, shared
SDRAM/display contention, transport or physical clock cost.

Next compare the measured entropy frontier against the retained V91 memory
service bottleneck before choosing an RTL adapter. Keep BR88 as the supported
control, then test any proposed arithmetic/context adapter against complete
source-backed frames, rollback, finite cadence and shared memory. Broader raw
captures and matched-quality HEVC/AV1 comparisons remain V98 work. Sustained
hardware 30 fps and complete validated decoding below 10 ms remain unproven.
