# V120 admission header-total equality proposal

This unselected source proposal targets the actual isolated A125 critical cone: `header_packet_total_reg[0]` to `tile_reg[4]/CE`, with slack −1.847 ns, 9.594 ns data delay, three CARRY4s and ten logic levels in route attempt `20261109T193132372767Z`. The separate address and context proposals remain unselected. This proposal makes no routed clock or hardware throughput claim.

## Source and timing cut

The source is [cs88_admission_v91i2a.sv](../../fpga/experiments/cu66-v120-admission-match/cs88_admission_v91i2a.sv), derived from exact V119 admission `23d031d48e3934f1c33ccffcb2c2e707d884daa68ed799cd7ff3c639c6c1496b`. Its reversible [edit recipe](../../fpga/experiments/cu66-v120-admission-match/edit-recipe.json) changes only two source sites:

1. Add one unreset private hardware payload bit, `prepared_header_total_matches`, captured on every existing `HEADER_BYTE` phase edge with the literal full35 equality `header_packet_total == {3'd0,size_bytes}`. Its physical enable has no reset, start, abort, ready, or new owner qualifier.
2. Replace only the total mismatch term at the existing `HEADER_CHECK` error-5 branch with the cached equality bit. All earlier and later error priorities, next states, public values, accepted events and natural public cycles remain unchanged.

The complete total is captured at byte55. Bytes56–127 do not write that total, and `size_bytes` and `receipt_epoch` remain stable during this parse. The final existing `HEADER_BYTE127` edge therefore captures the correct predicate immediately before `HEADER_CHECK`. Earlier or canceled captures are unowned and authorize no work. A new parse recaptures the bit before any live consume; the bit has no reset promise. No buffer, external port, counter, storage capacity or public cycle is added. There is one additional source payload bit; synthesis may optimize or replicate it.

Verification-only ownership state records the final live byte127 edge's complete epoch, full32 stored size and full35 total. Every live `HEADER_CHECK` checks this owner and exact literal predicate identity. All pre-existing RTL assertion blocks remain byte-exact, including the header-sum invariants. The original 35-bit total and all old private fields retain their original writers, reset behavior and values.

The [packaging manifest](../../fpga/experiments/cu66-v120-admission-match/packaging.json) losslessly splits the new source into its admission and two unchanged helper modules, as V119 did. Concatenation reproduces the entire production file byte-for-byte.

## Focused verification contract

The fresh reference body is exact current V119 admission, with only the existing read-only verification adapter. It is not an older admission body. The candidate gets the same adapter plus a public read-only annotation for the new bit. The old probe, whole-module public comparison, original scalar checks, accepted request/response/data ledger, held receipt checks, error priorities, complete independent coordinate/quant/scale/mode Python replays, and all old `require` expressions remain retained.

The literal old legacy fixture is saved separately. Its reversible derived fixture adds only a helper include and two direct-`HEADER_CHECK` preparation call sites. Live direct synthetic CHECK fixtures first clock a genuine `HEADER_BYTE127` in **both** reference and candidate with `byte_value` equal to the fixture's existing `header[127]`. The resulting state is naturally CHECK; the helper does not restore state, error, counters or caches, and never writes the new predicate. Canceled CHECK fixtures need no preparation because they cannot consume it. Sequential byte fixtures and ordinary packet traffic are unchanged.

Each such added preparation edge is counted separately as `fixture_priming_edges`. The old fixture's historical checker-edge totals describe its unchanged original tick calls after priming; they are not asserted to count these new preparation edges. Ordinary packet latency has zero added cycles. This is an explicit fixture precondition extension, not an all-arbitrary-state equivalence claim.

The new focus adds, per seed:

- 67,664 full35 capture contexts, including 65,536 randomized contexts. This is finite sampling, **not exhaustive** over the 2^35 domain. Equal zero-extended full32 sizes, all three upper-bit positions, high32 aliases, sum/carry boundaries, zero, 49,152, over-cap and full32 stored sizes are included.
- Every reset/start/abort combination on the capture edge, followed by real reset and IDLE hold clocks. Raw full35 capture fixtures may hold totals that no coherent header can represent. They reset before CHECK consumption and are explicitly separate from packet validity claims.
- 4,096 coherent header consumes, with actual predecessor capture and all old header-cache assertions enabled. These retain exact full35 sums of four full32 header fields and independent error-4/5/6/7/8 priority checks. No new bit or poststate is forced.
- 36 ordinary malformed packets with full32 declared fields, valid outer CRC when appropriate, header/CRC first-fault priority overlap, and 36 complete clean nonreset retries. These use the unchanged natural packet and physical read-debt oracle. They have their own trace; the original trace is preserved for all four original independent replay oracles.

The prepared raw capture and coherent CHECK domains are reported separately. Neither is mislabeled as a reachable gameplay packet. Stored full32 `size_bytes` values in synthetic tests are not restricted by the ordinary natural-start 49,152-byte admission cap.

## Execution and gates

Preparation-only verification is:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/cu66-v120/admission_match/qualify.py
```

Only Root grants a heavy execution slot:

```sh
python3 scripts/cu66-v120/admission_match/qualify.py --run --root-grant ROOT_V120_ADMISSION_MATCH
```

The runner freshly compiles strict Verilator 5.020 with assertions, warnings fatal, C++ `-Wall -Wextra -Werror`, and no reused candidate. It runs seeds120501/120502 under two CPUs, 8 GiB RAM with equal memory-swap limit, finite watchdogs and the current host RAM/pressure gate. It pins source, verification recipes, old frozen inputs, actual A125 cause, document and all artifacts; failed attempts remain recorded. It does not run Vivado or change clocks, constraints or exceptions.

A focused PASS alone does not select a physical candidate. Root's proposed B composition is isolated range A plus this admission change only. That composition needs fresh full-component, peer, LIVE-parent and native125 qualification. The independent tile-to-active-cell address/fanout paths may remain critical and need their own evidence and separately authorized source repair. A100 hardware handoff qualification remains a separate work item.
