# V119 frozen baseline and qualification gates

This audit pins V119 to `d310e4d77fdb0d12b46640202b5b5f1648987a8f` (`study/gamebub-v119-owned-validation-timing-20261109`). The V118 handoff selects `integrated-study`; its source order is 17 RTL read aliases plus the `cu66-v69/inverse` include directory, whose selected `.svh` file makes 18 source files. Each alias, origin and digest is recorded in [baseline.json](../../experiments/python-gamebub-v119/audit/baseline.json). All 18 origin files currently match the V118 source hashes and selected native source map.

## Frozen component timing

The V118 component is the out-of-context `cs88_pipeline_v91k` for `xc7a100tcsg324-1`, using Vivado 2026.1, `SYNTHESIS`, and fixed 10 ns / 8 ns clock constraints loaded before synthesis. The final routed receipts show:

| Trial | WNS | TNS | Setup failures | Hold / pulse failures | Routing errors | Internal unconstrained endpoints |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 125 MHz, 8 ns | −1.499 ns | −4,570.194 ns | 12,667 / 103,125 | 0 / 0 | 0 | 0 |
| 100 MHz, 10 ns | +0.061 ns | 0 | 0 / 102,478 | 0 / 0 | 0 | 0 |
| 100 MHz fresh identical-source repeat | +0.061 ns | 0 | 0 / 102,478 | 0 / 0 | 0 | 0 |

The fresh repeat refers to the first 100 MHz receipt by digest and repeats its source, tool image and recipe. Thus the internal component clock is qualified at 100 MHz; 125 MHz is not. This says nothing about full-parent timing, external I/O, or a hardware clock. The 125 MHz raw-mode/input-validation path is worst (14 logic levels, 3 CARRY4, 9.496 ns data delay). Independent admission/producer, admission mode, scratch return-state, admission scan/header and reconstruction-reference families also appear in retained paths. See [V118 mapping evidence](../cu66-v118/native-mapping-next.md) and [input chronology proposal](../cu66-v118/input-validation-proposal.md).

## Parent-model baseline

The source-bound `actual_001` LIVE fixture measures last accepted outer byte through validated parent commit, not whole-fixture elapsed time. These cycles use a finite abstract service model. Conditional milliseconds assume a clock and are not hardware measurements.

| Profile | Cycles | Conditional at 125 MHz | Conditional at 100 MHz | Baseline C cycles | Savings vs C |
| --- | ---: | ---: | ---: | ---: | ---: |
| Byte, fast | 3,704,705 | 29.638 ms | 37.047 ms | 4,166,111 | 461,406 |
| Byte, stalled | 9,484,147 | 75.873 ms | 94.841 ms | 9,873,327 | 389,180 |
| Row, fast | 1,145,104 | 9.161 ms | 11.451 ms | 1,416,449 | 271,345 |
| Row, stalled | 1,553,197 | 12.426 ms | 15.532 ms | 1,844,338 | 291,141 |

The fast row case only falls below 10 ms under the *conditional* 125 MHz conversion. Full-parent routing, hardware-validated decode under 10 ms, sustained distinct-frame hardware 30 fps and production Sunshine/ESP32 endpoint integration are all open. These are modeled RTL cycles and distinct qualification targets, not claims about FPGA or system performance.

## V119 source qualification gates

Apply the gates for the source changes actually selected; a passing local proof cannot be substituted for an omitted integration proof.

1. **Accepted coefficient timing/chronology:** capture the full untruncated tuple and immutable expected context on eligible INGEST; validate and commit only on its owned APPEND. Explicitly ledger accepted, validated, committed, discarded and physically outstanding owners. Preserve reset/cancel/wrong-tag priority, older coefficient fault priority, no revoked assembler publication, and exactly-once drain of accepted physical writes. Cover all phase encodings, range/order endpoints, simultaneous events and response cases. Declare and count any new edge.
2. **Admission ownership:** for the selected producer/admission changes, test all eight nonzero-plane masks and entropy combinations; prove nonce overflow equivalence to the original 64-bit expression at boundaries and random values, retaining entropy-before-overflow precedence and monotonic child epochs. If using the existing mode extent, prove its same-owner identity and preserve 32-bit wrap, cursor, trailing-bit and malformed-input behavior. Do not map a flattened path to a guessed source predicate without bounded fan-in evidence.
3. **Residual/reference ownership:** if cutting response-tag logic from residual word enables, prove phase non-overlap, all 64 words, payload zero semantics in COPY/reset/mode changes, commit ordering, invalid tuple/cancel behavior, and preservation of every physical reference descriptor through reset/start/cancel until its matching response. Simulation reachability is bounded evidence, not an all-trace proof.
4. **Integrated functional proofs:** retain strict focused oracles, all 18 source bindings, full independent canonical goldens, exact transport and LIVE byte/row publication/hash/ACK/fault/retry/debt checks. Compare ordered accepted and committed events and bytes; report added edges and measured cycles. Do not claim old-cycle equivalence when the validation point moves.
5. **Physical timing:** only after functional qualification, use fixed correct constraints and a fresh routed 125 MHz trial; report setup, hold, pulse, internal endpoint coverage and routing plus all surviving timing families. A positive clock qualification requires an identical-source/tool/recipe fresh positive repeat. Full-parent timing and real memory/CDC/display/ESP32 hardware measurements remain later gates.

## Preserved workspace evidence

At audit time the only pre-existing untracked path was `fpga/experiments/throughput30/burst/marker-recovery/`. Its two SystemVerilog files were left untouched. Their SHA256 and nanosecond mtimes are preserved in `baseline.json` so a later audit can confirm continuity. No builds, Git mutations, old-file edits or native trials were run for this baseline capture.
