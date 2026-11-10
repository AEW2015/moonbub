# V122 admission bounds preparation

This candidate derives only from the admission selected in the frozen V121
composition: `cu66-v120-admission-match/cs88_admission_v91i2a.sv`, SHA-256
`275071538fd2de34246bad17ddbeb170f356e8f41e6162969b7a97ab3f45ef3f`.
The V121 request queue remains unchanged. No other datapath is modified.

The V121 full-parent 125 MHz routed report at
`experiments/python-gamebub-v121/native/20261109T234502249779Z/reports/route-setup-paths.rpt`
reports the worst path from admission `cursor_reg[1]/C` to
`state_reg[0]_rep/D`: WNS -1.347 ns, data delay 9.232 ns, 14 logic levels,
eight CARRY4 cells. The original chunk-length decision includes
`{32'd0,cursor}+4+{32'd0,word_value}>{32'd0,residual_end}`. This experiment
separates the arithmetic from the state decode using phases already occupied by
the fourth byte of each word. A new route is required to establish its effect.

The preparation schedule is fixed before focused execution:

| Existing edge | New private payload |
| --- | --- |
| WORD_BYTE, index 2 | full64 zero-extended cursor + 4; separate uint32 cursor + 12 |
| FETCH_REQ, index 3, return CHUNK_LENGTH | full64 cursor base + zero-extended first three word bytes |
| FETCH_WAIT, index 3, return CHUNK_LENGTH | full64 partial sum + final synchronous RAM byte |
| WORD_BYTE, index 3 | complete length-invalid predicate or number-outside predicate |
| CHUNK_LENGTH / CHUNK_NUMBER | consume prepared bit on the original edge |

The full64 maximum sum is `0x200000002`; it is never truncated to uint32.
The number predicate intentionally retains the original uint32 `cursor+12`
wrap. Existing cursor updates retain uint32 wrap independently. PLANE_BEGIN's
literal `cursor+4` guard is unchanged in this narrow experiment. Number mismatch
error 12, empty plane handling, bound error 13, descriptor writes, chunk-length
capture even on rejection, and all state/fetch/counter edges retain their order.
There is no fallback combinational length sum in the production consume branch.

There are 226 new source payload bits: three full64 sums, one uint32 sum and
two predicates. Synthesis may remove constant upper bits. Payload has no reset;
canceled or unrelated captures are unowned and cannot authorize work. Additional
verification-only valid, phase and owner fields reset on reset/start/abort and
bind cursor, residual end, epoch, plane, return state and selected length limit.
Every actual consume checks the original literal predicate and full64 sum.
Every pre-existing assertion block remains byte-exact.

`prepare.py` emits a reversible edit recipe, verification derivations and
lossless production packaging hashes. The pair compares every original public
output on low, high and falling edges. All V120 packet, coordinate, quant,
scale, mode, header and first-fault oracles remain. Existing synthetic chunk
fixtures are extended with coherent real predecessor clocks: one RX-port write
at a safe backing address, followed by the actual final-word load phases. They
never force a new predicate or restore state, errors or counters. Their added
clocks are reported as prepared-domain fixture clocks and are not natural
packet latency.

Two seeds each retain the original 25,344 chunk-boundary cases and 294
cancellations, the inherited natural packets and malformed-header retries, and
add 16,384 independent random full32 cursor/word/end cases. These deliberately
include full64 high-word aliases, exact ends, uint32 wraps, wrapped selected
limits and overlapping first faults. Another 56 cases cancel each new phase
for both continuations under all seven reset/start/abort combinations and retry.
Strict Verilator warnings and all RTL assertions remain enabled. Independent
Python coordinate/quant/scale/mode replays remain mandatory.

The declared natural public cycle delta is zero. Focused finite simulation
establishes its tested contract only; full-parent functional integration and
routed timing remain separate gates. This document and all focused source
inputs are frozen for each attempt; later evidence belongs in new receipts.
