# V106 IDCT operand prefetch

The isolated candidate passes exact clocked comparison against the complete original IDCT. It registers the selected signed 24-bit sample and signed 14-bit basis during the preceding existing IDLE or ACC edge. MUL still produces the identical signed 38-bit product on its original edge. Public ports, FSM scheduling, shortcut behavior, output holding and active-cycle counts remain unchanged.

This targets the measured closure-route path from `k_reg` to `products_reg[3]/A[4]` (WNS −3.952 ns). The candidate has no measured timing result yet; parent native integration determines whether registering the selector improves this cone or exposes another path. The clock remains 10 ns with no exceptions added.

## Edge ownership

- Accepted IDLE prefetch reads the new `in_tile`, rather than the preceding `source_tile` register. Invalid and zero tiles retain immediate output behavior.
- Each FIRST/SECOND ACC edge prefetches the next `k` or group without advancing any public schedule.
- Final FIRST_ACC writes rows 6 and 7 while prefetching the already written intermediate rows 0 and 1 for SECOND_MUL. This avoids same-edge nonblocking-write dependence.
- DC_FIRST_ACC forwards `rounded(current products[0])` to the next operand register. Reading the old `dc_middle` on that edge would be incorrect.
- Reset/abort clears the added operands and live flag with existing priority. Every reachable MUL asserts that prefetched operands match the retained original combinational selector and basis. The live flag/assertions are excluded from synthesis.

## Retained evidence

[Selected focused receipt](../../experiments/python-gamebub-v106/idct/results.json) uses schema `v106-idct-clocked-production-comparison-v1`, selecting attempt `20261108T021455968682Z`. Strict Verilator 5.020 compilation uses assertions, `-Wall`, GCC `-Wall -Wextra -Werror`, j2 and an in-container 300-second watchdog. Both seeds completed in the single retained successful attempt; there were no failed actual RTL attempts.

| Check | Result |
| --- | --- |
| Independent dense two-pass Q14 model | 4,303 golden tiles, PASS |
| Historic fixture reuse | 3,471 tiles, byte-identical original inputs/goldens |
| Additional probes | 512 arbitrary AC, 64 DC, 256 invalid-bound vectors |
| Seed 106401 | 270,128 clock edges; 122,024 multiply edges |
| Seed 106402 | 270,240 clock edges; 122,024 multiply edges |
| Each seed | 4,303 golden tiles + 30 directed replays, 4,333 completed tiles |
| Directed cancellation | Reset, abort, both in each of all 10 states |
| Public active cycles | Zero/invalid 0; DC 4; general 128 |
| Independent offline trace replay | All 540,368 clock edges, PASS |

All public outputs and original state/k/group/products are compared before and after every actual clock edge. The clocked bench independently checks golden output tiles, signed products and active cycles. Random output stalls check payload stability. Busy input wires are deliberately perturbed while the module is not ready to check ignored-input independence; this is a robustness probe rather than a claim that a stalled producer may violate its own valid/hold protocol.

[Independent offline audit](../../experiments/python-gamebub-v106/idct/trace-audit.json) binds the auditor, selected receipt, source snapshots, compressed/raw traces and exact-edit recipe by SHA-256. It separately recomputes all 4,303 vector goldens and replays every product, FSM transition, guard combination and active-cycle count. [Attempt ledger](../../experiments/python-gamebub-v106/idct/attempt-ledger.json) lists all retained focused attempts.

## Frozen production

- Original: `fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv`, SHA-256 `251d4c11d762f6a040c1934d9dca9d80e6187f470a90b7261c63d06d1f3c310c`.
- Candidate: `fpga/experiments/cu66-v106-idct/cu66_idct8x8.sv`, SHA-256 `f972987d80a062b4969c71ac6157e8f17ab9e6b18088bafb77c4030eac78990e`.
- Recipe: `fpga/experiments/cu66-v106-idct/edit-recipe.json`, SHA-256 `817bda21de9a29d3e91a0e6f44e9ec1765c8a02332cce95f7ca80041923b5574`; schema `v106-edit-recipe-v1`, 11 unique literal edits. The complete original body outside those edits is preserved. Test adapters only rename the module and append observation ports/assignments; recovery of both complete production bodies is verified.

This is reachable two-state simulation with an independent integer oracle, not a formal proof over arbitrary internal states or a four-state simulation. It does not establish post-route timing, sustained hardware 30 fps, or validated under-10-ms complete decoding. Parent integration must run complete pipeline regression and the unchanged 100 MHz native flow before performance conclusions.
