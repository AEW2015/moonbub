# BR88: bounded Rice without adaptive arithmetic feedback

BR88 is an explicit research chunk format for the existing quantized residual
coefficients. It keeps the four DC/AC streams, diagonal coefficient order,
zero-run representation, signed mapping and bounded Rice escape grammar. It
removes the adaptive binary arithmetic interval, probability update and
renormalization layer. There is no transform, quantizer or decoded-pixel change.

This is a new decoder profile. It is not a standard HEVC/AV1 bitstream and is
not silently accepted by the frozen AB38 decoder. The new CS88 frame experiment
can dispatch unchanged AB38 and new BR88 chunks explicitly by chunk magic.

## Actual component results

All **457 native sources / 1,371 whole-plane residual chunks** were decoded from
the frozen AB38 components and re-encoded. The collector confirms exact original
AB38 re-encoding, native BR88 coefficient equality and independent Python BR88
decode parity. It checks **86,444,480 signed coefficient values**. No old work
counters are deleted to simulate a new codec.

| Actual chunk measure | AB38 control | BR88 |
|---|---:|---:|
| Complete chunk bytes across corpus | 4,265,737 | 4,805,106 |
| Adaptive feedback decisions | 37,656,819 | 0 |
| Arithmetic renormalizations | 33,238,189 | 0 |
| Plain bounded-Rice bit reads | — | 37,656,819 |
| Raw-fallback chunks | 0 | 0 |

BR88 costs **539,369 additional chunk bytes, or 12.64%**, on these sources.
Those are complete chunk counts including headers, stream headers, bit padding
and CRC; they are not whole-frame percentage changes. Frame envelopes,
operation/quantizer metadata, directories and HUD must also be counted. The
separate CS88 native-wire campaign makes that complete-packet comparison.

The exact equality between plain Rice bit reads and old feedback decisions
is expected: both consume the same bounded Rice binary decisions before the
old arithmetic compression layer. BR88 removes interval/probability feedback
and renormalization; it does **not** remove bit parsing, coefficient scattering,
run accumulation, memory traffic or inverse-transform work.

The old decision/renormalization counts come from re-encoding the exact frozen
coefficient sequences with the unchanged native AB38 encoder. The resulting
bytes must match the retained original chunks exactly. Native and Python
decoding then independently validate the new encoded coefficients. These
primitive counts are not measured decoder clocks or equivalent unit costs.

## Chunk grammar

The little-endian fixed header is 42 bytes, followed by the data and a four-byte
CRC32 over all preceding bytes:

| Offset | Size | Meaning |
|---|---:|---|
| 0 | 4 | `BR88` |
| 4 | 1 | Version 1 |
| 5 | 1 | Flags: 0 coded, 1 raw |
| 6 | 4 | Number of 8×8 coefficient blocks |
| 10 | 2 | Prediction width, fixed 1 |
| 12 | 2 | Reserved zero |
| 14 | 16 | Four stream byte lengths |
| 30 | 12 | Three AC event counts |
| 42 | variable | Data |
| End − 4 | 4 | CRC32 |

Each coded stream begins with `k0`, `k1` and its four-byte bit length. Bits are
MSB first, and the final byte's unused bits must be zero. DC uses `k0 <= 13`,
`k1 = 255`, a 14-bit escape and independent per-block DC values. AC bands cover
diagonal indices 1–5, 6–20 and 21–63. Each event contains a zero-run Rice symbol
and a nonzero signed-level Rice symbol. Run `k <= 19` escapes to 24 bits; level
`k <= 11` escapes to 12 bits. Counts, positions and coefficient ranges are
checked independently.

A Rice value emits at most 15 zero unary bits. A quotient below 15 also emits
a terminating one followed by `k` low bits. Fifteen zeros instead select the
full escape literal. Thus the largest single symbol consumes **39 bits**
(15 + 24), with no unbounded unary scan. Signed values use the existing mapping;
all coefficients must remain in −2,048 through +2,048. Every declared coded bit
must be consumed; BR88 adds no arithmetic tail or hidden termination bytes.

The encoder chooses Rice parameters by exact coded-bit cost. If the combined
coded stream bodies are at least `128 × blocks` bytes, raw signed little-endian
16-bit coefficients replace them. Raw mode requires the exact stream-length
vector `[128 × blocks, 0, 0, 0]` and all three AC counts zero. The complete chunk is therefore
bounded by **46 + 128 × blocks bytes**. Actual corpus chunks use coded mode,
while synthetic dense one-block vectors exercise raw fallback.

## Python/native checks and retained data

[The selected component report](../../experiments/python-gamebub-v88/entropy/index.json)
binds a unique attempt, source copies, compressed/raw data digests, native
commands/exit code and chunk observations. The loader merges new chunks with
the frozen source frame identities and unchanged qmap/HUD components.

[35 retained grammar checks](../../experiments/python-gamebub-v88/entropy/tests.json)
cover seven synthetic inputs, nine native-corpus fixtures, an explicit maximum
unary escape, and 18 malformed packets rejected by both the Python parser and
native C++ decoder. Cases include lengths, profile/geometry binding, padding,
parameters, AC counts, raw range and CRC errors. A first development test
incorrectly expected a dense 16-block input to choose raw mode; it actually
compresses below raw size. The corrected test uses a dense one-block input and
the failed attempt is retained separately from the selected result.

```sh
python3 scripts/cu66-v88/prototype_entropy.py
python3 experiments/python-gamebub-v88/entropy/test_codec.py
```

These native commands require the existing `gamebub-cu66-v69-build` container,
compiler and shared workspace. The independent Python reader uses the standard
library. Regeneration creates unique attempt directories and updates the
selected index/test reports.

## Application-specific architecture opportunity

The host can compare actual AB38/BR88 bytes for each chunk and choose which
adaptive feedback chains to eliminate within a complete-frame byte budget.
Whole-plane framing has at most three chunks here, so all eight mixed choices
can be enumerated without a selection approximation. A budget policy must
charge the actual frame bytes and preserve the accepted packet for replay.
Eliminated feedback counts are a proxy objective, not a deadline proof.

An FPGA BR88 decoder can investigate a bounded leading-zero detector, bit
reservoir and variable extraction path instead of an adaptive interval
multiply/update loop. It still needs cross-word refill, count/CRC checking,
ordered run accumulation and finite coefficient/output staging. Removing that
feedback may leave more arithmetic resources available for dequantization and
the inverse transform; this prototype proves neither DSP fit nor one-symbol-
per-cycle throughput. The real shared-memory/display bottleneck remains.

Next compare calibrated RTL costs and complete consumer-backpressured decoding
for the mixed choices, then move from an offline feedback-count objective to a
measured byte/decode-deadline policy. The component result alone proves no
sustained hardware 30 fps, complete decoding under 10 ms or HEVC/AV1 superiority.
