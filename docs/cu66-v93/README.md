# V93: arithmetic-prefix bypass and small-group Rice

This is the next isolated research step after [V92](../cu66-v92/README.md).
The target remains exact intended 720×480 video, followed by hardware 30 fps
and complete validated FPGA decoding below 10 ms. These software experiments
change entropy representation, retaining coefficients, quantizers, temporal
references, semantic HUD, RGB565 output, content roots and frame seals.

## Candidate methods

| Method | Coder | State and cost |
|---|---|---|
| 0 / AB | Frozen AB38 arithmetic-coded bounded Rice | Arithmetic prefix and payload bits; 88 probabilities reset per stream |
| 1 / BR | Frozen BR88 plain bounded Rice | Plain prefix and payload bits; no arithmetic feedback |
| 2 / HY | Arithmetic unary prefix, plain Rice payload suffix | Separate bounded arithmetic and plain extents; arithmetic prefix state resets per stream |
| 3 / SG | Plain Rice with parameters chosen per 32 values/events | Actual group headers charged; parameter choice belongs on the host |

HY bypasses **every** Rice payload suffix according to a rule fixed before the
experiment. Its descriptive suffix-position histograms do not select or fit
that rule. This is a mechanism experiment, not a learned/calibrated held-out
suffix policy. SG is a small-block Rice control, not an implementation of RLGR
or a claim of RLGR conformance. Its fixed 32-event grouping is also frozen
before observation. These methods are custom syntax, not HEVC CABAC or AV1.

## EC93 chunk grammar

EC93 keeps the 44-byte EC92 header and trailing little-endian CRC-32/IEEE,
with explicit magic **EC93**, version 1. Offsets remain:

| Offset | Bytes | Meaning |
|---|---:|---|
| 0 | 4 | `EC93` |
| 4 | 1 | Version 1 |
| 5 | 1 | 0 coded, 1 RAW |
| 6 | 1 | Four two-bit selectors; method for context `c` is `(selector >> (2*c)) & 3` |
| 7 | 1 | Reserved zero |
| 8 | 4 | Block count, 1–65,536 |
| 12 | 2 | Predictor width 1; DC prediction resets per block |
| 14 | 2 | Reserved zero |
| 16 | 16 | Four stream lengths, including descriptors and byte padding |
| 32 | 12 | Three AC event counts |
| 44 | variable | Streams, or RAW coefficients |
| final 4 | 4 | CRC over every preceding chunk byte |

All chunk multibyte fields are little-endian. All **256** selector patterns
are valid; EC92's upper-nibble restriction does not apply. Context order is DC,
then diagonal-zigzag AC ranges `[1,6)`, `[6,21)` and `[21,64)`. Methods share
the frozen signed mapping, Rice unary limit 15, and DC/run/level escape widths
14/24/12. DC `k0≤13`, `k1=255`; AC run `k0≤19`, level `k1≤11`. Bits are
MSB-first; final byte padding is zero. Coefficients remain in `[-2048,2048]`.
AC events have nonzero levels and strictly increasing band-local positions.

AB and BR retain their six-byte descriptors: `k0`, `k1`, 32-bit bit length,
then coded bytes. AB terminates exactly as frozen; BR consumes exactly its
declared bits. Every arithmetic stream resets its 88 probabilities and 16-bit
state; initialization and renormalizations remain separate measured counts.

HY has a ten-byte descriptor: `k0`, `k1`, 32-bit arithmetic-prefix bit length,
32-bit plain-suffix bit length. It then stores the separately byte-padded prefix
extent followed by the separately padded suffix extent. For unsigned Rice
value `v`, `q=v>>k`: encode up to 15 zero unary decisions arithmetically; if
`q<15`, encode the terminating one arithmetically and place the low `k` payload
bits in the plain extent. At `q≥15`, omit the terminating one and put the full
escape-width value in the plain extent. Arithmetic unary contexts are `q`
for DC/run and `48+q` for level. Prefix and suffix consumption must both end
exactly; prefix termination includes the frozen two zero bits. A zero-event
HY stream still has arithmetic initialization/termination and zero suffix bits.

SG starts with six bytes: group-size byte 32, reserved byte zero and a 32-bit
group count. The count is exactly `ceil(events/32)`, using the block count for
DC and the header event count for AC. Each group has its own six-byte
`k0,k1,bit_length` descriptor and zero-padded plain Rice extent. A group holds
at most 32 DC values or 32 interleaved run/level pairs. Its final partial group
codes the exact remainder. The AC position accumulator **continues across
groups** and resets only at the context boundary. Zero AC events mean zero
groups. The host minimizes bounded Rice bit cost per group with deterministic
lowest-k ties; group headers are fixed for that grouping and fully counted.

RAW requires selector zero, lengths `[128×blocks,0,0,0]`, zero AC counts and
signed little-endian 16-bit block/raster coefficients, without descriptors.
Coded payload must be strictly smaller than `128×blocks`; otherwise assembly
uses RAW. As in V92, if either frozen encoder has discarded its coded streams
for RAW, the prototype conservatively emits RAW for all choices. The production
sender still needs an admitted frame-level fallback/split policy for future
content; current-corpus fits are not worst-case evidence.

## Complete frame comparison and limits

CS93/version 1 explicitly changes the frame profile. It retains the CS88/CS92
big-endian 128-byte envelope, mode map, QM87, plane directories, HUD and outer
CRC. Native reconstruction decodes EC93 directly and commits accepted state
only after content/HUD/seal checks. Legacy CS92 receivers reject CS93.

The normal receiver enforces the **49,152-byte complete-frame cap**. A separate
binary compiled with `CS93_RESEARCH` permits 2 MiB solely to reconstruct and
measure homogeneous BR/HY/SG controls that might exceed the target. Every such
frame reports target-cap fit independently. Diagnostic acceptance never means
hardware admission or cap qualification. Selected byte-min/work policies and
the frozen V92 controls run through the normal bounded receiver.

The host prepares four method alternatives once per context and assembles
homogeneous and mixed packets from those actual bytes. It does not re-encode
all `4^12` frame choices. Minimum bytes is separable and exact for the retained
coded corpus. Work selection uses a deterministic **128-state beam**, with at
most 512 proposals per context and 6,144 per complete 12-context search. It
keeps low-byte and low-work Pareto extremes and charges descriptors/padding.
This search is approximate; no global-optimum claim is made. The frozen V92
controls and exact byte-min candidate are explicit feasible anchors.

Work policies minimize adaptive decisions, then renormalizations, plain bit
reads, complete bytes and selector. Group headers and arithmetic initializations
are also counted but are not calibrated cycle weights. Thus a winning work
count is not a measured decoder speedup. Memory/display contention, parser
setup, ports, transport and routed clocks still require integrated costing.

## Reproduction

Use Python 3 and the existing strict GCC 13.3 C++17 container
`gamebub-cu66-v69-build`, from the repository root:

```sh
python3 scripts/cu66-v93/test_python.py
python3 scripts/cu66-v93/test_selection.py
python3 scripts/cu66-v93/collect_contexts.py
python3 scripts/cu66-v93/run_wire.py
python3 scripts/cu66-v93/test_wire.py
python3 scripts/cu66-v93/summarize.py
python3 scripts/cu66-v93/bundle_manifest.py
```

Finite watchdogs, strict compilation, source snapshots/pins, actual packet
archives, malformed/recovery inputs, observed counters and retained attempts
make the study reviewable. Candidate preparation includes discarded methods,
assemblies and hashes; independent verification is timed separately. Host
measurements exclude live capture/DCT and do not measure ESP32 or FPGA timing.

See [results](results.md) and the [independent audit](audit-notes.md).
The corpus remains one related precompressed walkthrough family in four reset
histories. It does not establish independent raw capture coverage or held-out
generalization. V91l and V92d integration remain open. Any V93 research winner
needs an implemented mixed-method RTL path and complete physical service
qualification before promotion; hardware 30 fps and validated under-10-ms
decoding remain unproven.
