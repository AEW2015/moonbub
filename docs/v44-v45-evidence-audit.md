# V44/V45 evidence audit

Audited the V44 block-reader and V45 symmetric-inverse READMEs, results, focused
tests and independent verifier logs. The counts and stated model boundaries agree
with the archived evidence.

## V44 one-block coefficient reader

The study independently replays 3,462 archived AB38 alternatives: 1,731 full
and 1,731 compact. That is 9,177,762 coefficient tiles, all exact against the
full-array decoder. The verifier reports no full coefficient plane staged by the
reader, no encoding during verification, and no target memory or FPS proof. Six
focused tests pass, including `test_raw_late_error_poisoned`.

The 128-byte figure is only the owned 8×8 int16 coefficient output tile. It does
not include the retained compressed input (up to 23,937 bytes in this campaign),
four arithmetic states, 352 logical probability-state bytes, pending events,
Python object/heap cost, transforms, reconstructed frames or transport buffers.
Real archived trials all use arithmetic syntax (`raw_trials: 0`); raw fallback is
covered by directed tests, not by the campaign payload count.

A CRC-valid semantic error can occur after earlier tiles have been returned.
Those tiles are provisional: a caller must stage its reconstructed frame and
publish neither frame nor reference until the complete packet/frame succeeds.
The late raw range-error test checks that the failed iterator is poisoned and
cannot later report success. V44 is a component iterator, not an atomic frame
receiver. The reported 15.50 ms array decode versus 19.21 ms tile decode plus
hash accumulation is asymmetric timing and does not show an iteration speedup.

## V45 symmetric inverse

The study covers 1,731 full-grid planes and 4,673,700 actual dequantized blocks;
all outputs match the frozen Q14 inverse, including both rounding stages. There
are 5,193 scalar tile checks and five focused tests. The block counts reconcile:
3,073,322 zero, 281,230 DC-only and 1,319,148 complex blocks.

With equal zero/DC shortcuts on both sides, the modeled sparse multiply totals
are 275,542,196 direct versus 138,052,328 mirrored: a 49.8979358% logical
multiply reduction. The NumPy vectorized implementation still executes dense
matmuls; the sparse counts model a proposed implementation and are not measured
hardware operations. Mirroring also adds recombination and scheduling work, so
the reduction does not imply proportional cycle or latency savings.

The interval proof retains the full normative input domain: coefficient ×
quantizer is bounded by ±2048×255 = ±522,240 (20 signed bits). The observed
maximum dequantized magnitude of 1,792 is not a basis for narrowing. The
conservative bounds are 36 signed bits for first-pass accumulation, 22 for the
rounded intermediate and 37 for second-pass accumulation. Five focused tests and
independent replay confirm exactness and these bounds. No DSP mapping, resource
fit, memory arbitration, initiation interval, routed clock, frame rate or board
result is established.

## Combined limits

V44 tile delivery and V45 inverse arithmetic remain separate components. Neither
study integrates backpressure, late-error containment and atomic frame
publication with a bounded transform pipeline. The evidence establishes exact
Python-level behavior, logical staging and arithmetic counts for these archived
payloads only; it does not establish a complete receiver or physical performance.
