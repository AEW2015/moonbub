# V94: bounded byte-rANS and a real RTL symbol kernel

This is a **partial V94 research checkpoint**, following
[V92](../cu66-v92/README.md) and [V93](../cu66-v93/README.md). It implements
table-inclusive byte-rANS with two/four interleaved states and frequency
precision 8/9/10. It also implements and simulates a standalone RTL category
decoder. It does not implement tANS, trained fixed models, acknowledged model
caching, or the complete mixed-codec FPGA frame path. Those V94 gates remain
open, together with V91l/V92d integration and both hardware milestones.

The representation-only lane retains the intended 720×480 coefficients,
quantizers, reference pixels, semantic HUD, RGB565, content roots and seals.
See [measured results](results.md), the [resource audit](audit-notes.md), and
the [RTL boundary](../../fpga/experiments/cu66-v94-rans/README.md).

## EC94 wire contract

EC94 retains the 44-byte EC92/EC93 header and trailing little-endian
CRC-32/IEEE. Its magic is `EC94`, version 1. Offsets remain:

| Offset | Bytes | Meaning |
|---|---:|---|
| 0 | 4 | `EC94` |
| 4 | 1 | Version 1 |
| 5 | 1 | 0 coded, 1 RAW |
| 6 | 1 | Four two-bit methods, context `c` in bits `2*c+1:2*c` |
| 7 | 1 | Reserved zero |
| 8 | 4 | Block count, 1–65,536 |
| 12 | 2 | Predictor width 1: DC prediction resets per block |
| 14 | 2 | Reserved zero |
| 16 | 16 | Four stream byte lengths |
| 32 | 12 | Three AC event counts |
| 44 | variable | Streams, or RAW coefficients |
| final 4 | 4 | CRC over all preceding chunk bytes |

All multibyte chunk fields are little-endian. Context order is DC, followed
by diagonal-zigzag AC bands `[1,6)`, `[6,21)`, `[21,64)`. Methods 0/1 are
unchanged AB38/BR88 streams; methods 2/3 are two/four-state byte-rANS. Every
selector pattern is legal. V93's HY/SG method numbers do not carry into this
new profile. Streams reset independently; RAW requires selector zero,
`[128×blocks,0,0,0]` lengths and zero AC counts. Signed 16-bit RAW coefficients
remain in block/raster order and within `[-2048,2048]`. Coded payload must be
strictly smaller than RAW. The conservative frozen-encoder RAW fallback is
retained and tested.

Each rANS stream has a 20-byte descriptor:

| Stream offset | Bytes | Meaning |
|---|---:|---|
| 0 | 1 | Rice `k0` |
| 1 | 1 | Rice `k1`; DC requires 255 |
| 2 | 1 | Precision `S`, exactly 8, 9 or 10 |
| 3 | 1 | Table mode, exactly 0 for inline tables |
| 4 | 4 | Model identity: CRC-32 of the exact inline frequency bytes |
| 8 | 4 | ANS byte count, including initial state words |
| 12 | 4 | Plain literal bit count |
| 16 | 4 | Category-symbol count |

After the descriptor come one DC model or two AC models, each containing
16 unsigned 16-bit frequencies. Each model sums exactly to `M=2^S`.
Zero-frequency categories are allowed but cannot be coded. The identity is a
checksum of the complete inline model block, not a cache lookup or a second
CRC field. There is no persistent model state: table mode 1 and every other
unsupported mode reject. Recovery uses a fresh valid inline packet bound to
the actual accepted frame history; no cache acknowledgment protocol is claimed.

Next come `N` initial 32-bit state words followed by renormalization bytes,
together occupying the ANS byte extent. Last is the separately zero-padded,
MSB-first literal extent. Symbol count is exactly the block count for DC or
twice the AC event count for interleaved run/level fields. DC has one model;
AC alternates run model 0 and level model 1. Field `i` uses state `i mod N`.

Each unsigned Rice field `v` emits category `q=min(v>>k,15)`. For `q<15`,
the literal is the low `k` bits; category 15 uses the full bounded escape:
14 bits DC, 24 bits run, 12 bits level. DC/run/level mapping, parameter bounds
and AC position coverage remain unchanged from the frozen controls.

## ANS state and models

The lower state bound is `L=2^23`. Every initial state is in `[L,2^31)`.
For slot `x mod M`, find category interval `[cdf[q],cdf[q]+freq[q])`, then:

```text
x_next = freq[q] * (x >> S) + slot - cdf[q]
while x_next < L:
    x_next = 256*x_next + next_byte
```

At precision 8/9/10, at most two bytes are required. Exact ANS and literal
consumption, zero padding and final state `L` for **every** lane are mandatory,
including lanes unused by a short/empty stream. Encoder division and reverse
ordering remain on the host. This arithmetic follows the pinned
[byte-rANS reference](https://github.com/rygorous/ryg_rans/blob/c9d162d996fd600315af9ae8eb89d832576cb32d/rans_byte.h);
the framing and bounded Rice-category adaptation are independently implemented
research syntax, not FSE/tANS bitstream compatibility.

Per-chunk normalization gives one frequency to each observed category and
distributes the remaining mass proportionally, using largest remainders and
lower-category ties. An empty model is uniform. Tables are not trained on the
evaluation corpus and then cached: every table is transmitted and charged.
The initial comparison freezes the BR-optimal Rice parameters to isolate the
coder change. A separate rate-aware Rice-parameter experiment, when reported,
keeps this baseline frozen and counts its search and discarded candidates.

## Complete frame and host accounting

CS94/version 1 explicitly changes the frame profile. It preserves the
128-byte envelope, mode/QM87 metadata, directories, HUD, outer CRC and content
commitments. Native receivers decode EC94 directly; legacy CS93 rejects it.
Normal complete-frame admission is **49,152 bytes**. A separate 2-MiB diagnostic
receiver reconstructs homogeneous controls to report their real oversized
cases. Diagnostic acceptance never qualifies target admission.

The baseline prepares AB, BR and six rANS variants once per plane, retaining
their actual context bytes. It emits eight homogeneous choices and the local
minimum-byte choice. The complete-frame byte-min policy is separable and exact
for the retained coded corpus; it does not encode all `8^12` combinations.
Tables, descriptors, states, padding, CRCs and discarded preparation are
included. Native timings include source coefficient extraction and the frozen
AB encoder's internal verification; independent all-candidate verification and
Python/archive wall time are recorded separately. No host timing is an ESP32
or FPGA instruction/cycle measurement.

All 457 sources remain one related precompressed walkthrough family in four
reset histories. This is regression and mechanism evidence, not independent
raw-capture coverage or held-out game generalization. Audio, input, real
transport, DMA and memory/display contention are not modeled by this host run.

## Reproduction

Use Python 3 and the existing `gamebub-cu66-v69-build` container with GCC 13.3
and standalone Verilator 5.020. From the repository root:

```sh
python3 scripts/cu66-v94/test_python.py
python3 scripts/cu66-v94/collect_contexts.py
python3 scripts/cu66-v94/run_wire.py
python3 scripts/cu66-v94/test_wire.py
python3 scripts/cu66-v94/export_rtl_vectors.py
python3 scripts/cu66-v94/optimize_rice.py
python3 scripts/cu66-v94/run_optimized_wire.py
python3 scripts/cu66-v94/export_optimized_rtl.py
python3 scripts/cu66-v94/run_rtl.py --vectors-index experiments/python-gamebub-v94/optimized-rtl-vectors/index.json
python3 scripts/cu66-v94/audit_rtl.py
python3 scripts/cu66-v94/run_fast_rtl.py
python3 scripts/cu66-v94/audit_fast_rtl.py
python3 scripts/cu66-v94/summarize.py
python3 scripts/cu66-v94/bundle_manifest.py
```

Each campaign has finite watchdogs, source snapshots/hashes, actual byte
archives, strict compiler logs and explicit verdicts. Failed/exploratory
attempts remain distinct. The RTL experiment is standalone behavioral
simulation with no vendor primitive libraries or Vivado integration claim.
Routed 7-series mapping/placement/timing remains the V100–V110 phase.

The rate-aware follow-up searches all legal k values for each DC/run/level
model, scoring normalized category entropy plus literal bits. It then emits
actual streams and retains the frozen rANS alternative whenever it is smaller.
The grammar is unchanged. The corpus result is only eleven fewer complete
bytes than the earlier local minimum; no default-codec promotion follows.

A separate [no-refill bypass RTL variant](../../fpga/experiments/cu66-v94-rans-fast/README.md)
reduces matched component clocks by 21.67% while preserving all outputs. The
extra normalization check shares the multiply/update path, so routed clock and
full-path latency remain unqualified. The staged implementation is retained.
