# V92 EC92 contract audit

This is a read-only audit of the proposed V92 E2 wire shape against the V91c
BR88 packet contract and the V92/E2 roadmap. It records specification gaps and
required checks; it does not establish a V92 implementation result.

## Contract fit

The E2 goal is per-context AB38/BR88 choice: four contexts per plane, three
planes, hence at most 12 choices. A four-bit selector byte for each plane can
represent 16 combinations. The stated 4,096 frame combinations follow only if
the frame has three independently selected plane packets and every selector
combination is legal. Define the context-to-bit order (DC, AC0, AC1, AC2), the
AB38/BR88 bit values, and require the unused upper nibble to be zero. Define
whether choices are independent or constrained by a profile.

The proposed offsets are internally non-overlapping if the data starts at byte
44: selectors at 6, reserved byte at 7, block count at 8, predictor field at
12, reserved word at 14, four length words at 16–31, and three AC count words
at 32–43. Explicitly state that these words are little-endian. The singular
block count and four context lengths describe one plane packet; document the
outer frame's plane order, plane packet count, per-plane block geometry, and
how those packet extents are aggregated and CRC-checked. Otherwise “EC92 frame”
can be read as either one plane packet or one three-plane frame.

`pred=1` needs a named meaning and fixed allowed value(s); it must not be
silently treated as an enabled predictor. Likewise define the relation between
RAW flag at byte 5, selector bits, and the noted RAW mask of zero. For RAW, the
contract should state exactly which length is nonzero, whether it includes a
context descriptor, and that all three AC counts are zero. For coded packets,
specify whether each length includes the AB38/BR88-specific descriptor and
terminal/padding bytes. V91c's BR88 lengths include a six-byte descriptor and
the parser validates descriptor parameters, exact bit consumption, zero-event
emptiness, and zero padding; AB38 needs its own equally exact syntax/terminal
rules. A mode selector plus a byte length alone does not define either stream.

## Compatibility and bounds

EC92 must be a new magic/versioned grammar. V91c accepts `BR88`, version 1,
with a 42-byte fixed header, payload at offset 42, and its existing descriptor
layout. It cannot accept EC92 by changing only the magic or by treating the
selector byte as an old field. Keep its receiver explicitly legacy and require
a distinct EC92 parser/adapter for any promoted path.

Define CRC as reflected CRC-32/IEEE (polynomial `0xedb88320`, init/final XOR
`0xffffffff`), stored little-endian in the final four bytes, over bytes
`[0,total_bytes-4)`. Require exact declared length, no trailing data, and CRC
validation before any output is trusted. This matches V91c's CRC convention
while binding the new selector and expanded header.

Treat 49,152 bytes as a complete serialized packet/frame cap including the
44-byte header and four-byte CRC, not payload-only. A single-plane all-RAW
packet is `48 + 128*blocks` bytes; 383 blocks fit at 49,072 bytes, while 384
exceed the cap at 49,200 bytes. This does not prove that three plane packets,
or an outer frame envelope, fit together. Specify whether the cap applies per
plane packet or to the entire complete frame and account for every outer
header, per-plane header, CRC, padding, and ancillary section accordingly.

Length and count validation must use widened arithmetic before sums/products;
reject overflow, truncation, excess declared extents, unsupported flags,
selectors and predictor values, nonzero reserved fields, and inconsistent
counts. Apply resource limits before allocation/ingress. No stream may read
across its declared extent or into the CRC. RAW count/length consistency and
inclusive coefficient range `[-2048, 2048]` should be checked independently.

## Required V92 qualification

- For each context, emit actual AB38 and BR88 alternatives from the same exact
  coefficient input, then verify decoded coefficients match. Cost all bytes
  (EC92/outer framing, context descriptors, payload, padding and CRC); do not
  compare payload-only sizes.
- Compare bounded candidate search with exhaustive enumeration on small cases.
  Reuse coefficient/event preparation across candidates, but measure host time
  and peak memory for all generated alternatives, including discarded ones.
  The “generated once AB+BR per plane” procedure must retain enough per-context
  outputs/costs to select a complete candidate without re-encoding the frame.
- Charge candidate decode work from real AB38 observations: adaptive decisions,
  renormalizations and probability/context setup, plus BR88 bit reads, symbols,
  escapes and parser transitions. Charge all stream/header/CRC bytes and
  metadata checks. Do not infer a win from selector count or byte count alone.
- Have independent Python and native decoders parse serialized EC92 bytes,
  validate all bounds/CRC/terminals, and reproduce exact coefficients and the
  complete canonical pixel, reference, HUD, and seal outputs. Keep Python and
  native parsing independent of the encoder's metadata structures.
- Exercise all 16 selector patterns per plane, mixed AB/BR contexts, zero-event
  contexts, all-RAW and invalid RAW combinations, minimum/maximum extents,
  49,152-byte boundary, bad CRC, malformed lengths/counts, unsupported values,
  truncation/trailing bytes, stream terminal/padding failures, and independent
  plane ordering/bindings. Verify abort, replacement start, reset, and retry
  discard all provisional outputs and preserve accepted state.
- Separate one-plane packet completion from complete-frame completion. Require
  all three planes and outer checks to complete before frame publication; test
  a late failure in the final plane and exact replay after reset/retry.
- Report exact bytes and bounded host preparation (including discarded work),
  decode work/cost assumptions, memory reservation and finite-port costs per
  complete frame. Keep latency conditional on a fully specified integrated
  service model; these audits do not establish actual receiver or hardware
  promotion.

The existing V91c receiver accepts BR88 chunks only. A passing EC92 software
decoder or complete-frame encoder therefore demonstrates E2 grammar and
selection evidence, not promotion into V91 RTL. Promotion requires the roadmap's
receiver adapter and complete-path goldens to be separately implemented and
qualified.

## Basis

- [E2 experiment definition](../literature-review-2026-11-06/experiments.md#e2--finer-entropy-choices-plus-selective-bypass)
- [V92 roadmap gates](../gamebub-v91-v110-development-plan.md#v92v99-codec-host-and-transport-selection)
- [V91c packet grammar and reset semantics](../cu66-v91c/README.md)
