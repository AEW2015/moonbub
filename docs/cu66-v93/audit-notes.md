# V93 EC93 grammar and roadmap audit

This audit checks the proposed V93 E2 extension against the V91–V110 roadmap,
E2 experiment contract, and EC92 framing. It records contract points that need
to be explicit or demonstrated; it is not an implementation or hardware result.

## Roadmap fit

V93 is assigned the arithmetic-prefix/raw-suffix experiment and small-block
Rice/RLGR controls. Its gate is a measured improvement, with finite escapes,
RAW fallback, and all tags, resets, and dependencies charged. The proposed
four homogeneous methods plus a local-context minimum-byte packet are suitable
controls if selection costs complete serialized CS93 bytes and decode work.
Report per-context results as well as full-frame totals. Charge the EC93 header,
HY/SG descriptors, group headers, padding, frame envelope, CRCs, and any
selection/preparation work. A smaller payload alone does not pass the gate.

The E2 review calls for calibration histograms and freezing bypass choices
before held-out testing. Here the rule that all Rice payload suffixes bypass
arithmetic is fixed before data and is not fitted; describe this as a
predetermined mechanism experiment, not a learned or calibrated suffix policy.
If any k, method, grouping, or bypass decision is tuned from corpus results,
freeze that rule on a calibration split before reporting held-out results. The
457-source corpus is related regression material, not independent capture
evidence or generalization proof.

V93 exit remains conditional: retain the control and negative result if the
complete-byte/decode-cost frontier does not improve. CS93 software results do
not implement the mixed V91 RTL receiver or qualify transport, FPGA timing,
30-fps operation, or the under-10-ms complete-frame decode gate. Do not imply
those outcomes or an RLGR-conformance claim.

## EC93 and stream contract

Reusing the 44-byte EC92 header is workable only with an explicit EC93 magic
and version and a new complete-frame CS93 identity. Define byte 6 as four
two-bit selectors in a fixed DC/AC0/AC1/AC2 order (0 AB, 1 BR, 2 HY, 3 SG),
and state that all 256 patterns are legal. Preserve and restate byte order,
reserved fields, block and event counts, per-stream extents, CRC coverage and
storage, exact total-length/trailing-byte rules, and complete-frame cap. The
EC92 parser must reject EC93; do not reinterpret its selector nibble.

For HY, the 10-byte descriptor must define `k0`, `k1`, the little-endian
32-bit arithmetic-prefix bit length, and the little-endian 32-bit raw-suffix
bit length. Define the bit order, arithmetic initialization and exact
termination, zero padding, and how each coded field maps to prefix and suffix
bits. State precisely what the bounded unary prefix represents, how `q=15` is
handled (including any escape), which suffix widths and signed mappings apply,
and how zero-event streams are represented. The bypass decision is fixed by
the grammar, prior to data, and applies to all Rice payload suffix bits. Prove
with bounded arithmetic that both bit extents fit their enclosing stream,
consume exactly, and cannot read into the next stream or CRC. Reset the 88
arithmetic probabilities for every stream and reject nonzero pad bits or
incorrect arithmetic termination.

For SG, define the six-byte outer descriptor as `group_size=32`, reserved zero,
and little-endian group count. Define group order, how group counts derive from
the enclosing DC block count or AC event count, whether empty groups are
allowed, and the exact six-byte per-group `k0`, `k1`, bit-length descriptor.
Each group codes at most 32 values/events with plain bounded Rice and its own
zero-padded extent. For AC, positions must remain strictly increasing and
within the declared band; the position accumulator continues across group
boundaries and resets only at the stream boundary. State exact handling of
the final partial group, zero-event streams, invalid k values, and cumulative
bit/byte overflow. The SG host search must charge actual per-group headers
while choosing the best k; freeze tie-breaking so output is deterministic.

RAW must retain EC92's coefficient ordering, bounds, selector constraints,
and all-RAW fallback semantics under EC93, with complete CS93 length and CRC
accounting. Validate widened length arithmetic before allocation. For every
method reject malformed descriptors, excess or truncated bits, nonzero
padding/reserved fields, invalid escapes, coefficient/range violations,
inconsistent counts, CRC errors, and trailing data before publishing output.

## Evidence required

- Run independent native and Python readers over serialized bytes, not shared
  encoder-side structures. Verify coefficient, canonical pixel, HUD, root,
  seal, reference/replay, and rejection parity through complete CS93 frames.
- Exercise all 256 four-context selector patterns in fixtures, plus mixed
  method streams, empty and partial groups, every k/escape boundary, malformed
  lengths, padding and terminal cases, CRC failures, RAW fallback, truncation,
  and reset/abort/retry paths.
- Collect the four homogeneous packets and local-context minimum-byte packet
  for the same 457-source corpus. Compare complete serialized sizes and
  per-field statistics, context resets, decoder work, and actual host
  preparation cost, including discarded candidates. Keep the CS93 complete
  frame and its root/seal checks as the unit of comparison.
- Keep calibration/held-out treatment explicit. No independent raw captures
  are established by this corpus; no hardware, RTL, transport, or cadence
  qualification follows from these software comparisons.

## Basis

- [V93 roadmap entry and promotion gate](../gamebub-v91-v110-development-plan.md#v92v99-codec-host-and-transport-selection)
- [E2 suffix bypass and held-out requirements](../literature-review-2026-11-06/experiments.md#e2--finer-entropy-choices-plus-selective-bypass)
- [EC92 framing and complete-frame contract](../cu66-v92/README.md)
