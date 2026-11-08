# V109 existing-edge scratch prefetch arithmetic

The isolated candidate targets the qualified V108 composite's second-worst routed setup family: output_block[2] to scratch state, −2.008 ns slack and 11.953 ns data delay with five CARRY4s. It adds no cycle, memory owner, interface or timing constraint. It does not target the global-fault/Rice path.

The only production substitution is the historical native alias `fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv`. Its actual V108 origin is `fpga/experiments/cu66-v108-capacity/packed_scratch_v91g2.sv`, SHA-256 `5c4e6fc665c81920a2f907bb87d34e78f0eac22a114f75633a1f1dc2ddd33676`; the V109 body is `fpga/experiments/cu66-v109-prefetch/packed_scratch_v91g2.sv`, SHA-256 `742726be34e0560b72f3cd0026edcd9be44bffbede5200a179edd483c24fca34`. The other seventeen qualified origins remain unchanged for this isolated hypothesis.

At DC_FETCH/RAW_FETCH, the candidate captures the original full-width next-value address and next-block/value range predicates. At AC_CHECK, it captures each sparse band's original starts+cursors*4 address and cursors<count predicate. Only the final aligned eighteen-bit address is stored, after the original thirty-two-bit arithmetic. No truncation of counts, starts, cursor arithmetic or range comparisons is introduced.

Every successful sparse AC_EXTRACT increments its cursor and returns to AC_CHECK. AC_CHECK does not modify any cursor, and every path entering EMIT passes through it. The final AC_CHECK edge therefore captures all current cursors before EMIT can launch. DC_FETCH precedes extraction; output block/index cannot change until the later EMIT/RAW_EXTRACT acceptance. RAW_FETCH occurs for every raw scalar, including transitions between blocks. Read misses may insert request/wait edges without changing these operands. Stalled dense output leaves the operands fixed. These are existing-edge deadlines, with no stale-cache assumption.

Cache tags/validity, outstanding ownership, error/cancellation, prefetch_offer and response completion remain live on the original launch edge. First-DC-then-band priority, concurrent dense acceptance, prefetch drain transitions, foreground/background cache refill behavior, accepted request immutability and malformed-record checks remain in their original code. New simulation assertions compare every captured term with the full original expression whenever its consuming state is active. All old assertions remain.

`edit-recipe.json` stores exact before/after text and verifies both forward reconstruction and reverse reconstruction. `verification/adapters.json` binds complete-body adapters to their source hashes. The scratch bench and accepted-write hazard oracle are byte-identical to the existing V106 fixtures; the paired four-body bench and probe are byte-identical to the existing V108 fixtures. The scratch observation wrapper adds coherent V108 prefix/threshold/capacity inputs without changing those old test drivers. Both variants use the complete qualified V108 body, with only the candidate's scratch body changed.

Prepared reproduction commands:

```sh
python3 scripts/cu66-v109/prefetch/prepare.py
python3 scripts/cu66-v109/prefetch/verification.py
python3 scripts/cu66-v109/prefetch/qualify.py
python3 scripts/cu66-v109/prefetch/qualify.py --run
```

The explicit run uses Verilator assertions and strict warnings, C++ `-Wall -Wextra -Werror`, uniform `-O1`, two seeds and both synchronous staging modes for the four-body suite. Docker is limited to 8 GiB including swap, two CPUs and one build job; memory pressure stops the run. Full canonical/native qualification belongs to the integrating root agent. No timing or hardware success is claimed here.

Focused qualification completed with actual RTL execution: **PASS**, two scratch seeds and four complete-body runs (two seeds in each staging mode). The four-body runs checked 31855149 public cycles and 18007552 independent golden dense values. Each scratch seed retained 72 complete transactions, 128 corrupted-memory response cases, four accepted-read ownership cases and nine historical accepted-write hazard checks; all four cache banks and sixteen byte offsets were covered. No Verilator warning occurred in any strict compile.

The [selected receipt](../../experiments/python-gamebub-v109/prefetch/attempts/20261108T105800922404Z/results.json) has SHA-256 `609e3701a43a39d982522945a498804a7982c309e9e7a90e213f3fb2dee16482`; [current selection](../../experiments/python-gamebub-v109/prefetch/results.json) records `status: PASS`, `actual_RTL_run: true` and the frozen source hashes. This is focused qualification, not native timing closure.

Coverage note: the inherited scratch full-transaction block sizes are 1, 3 and 8. Its sparse cases do not cross DC-cache line boundary block 7→8; new assertions do compare the exact cached address/range expressions at every consumer edge. A separate follow-up bank experiment has been asked to add 9/17-block and live begin-input cases. No universal formal-equivalence claim is made from these finite traces.
