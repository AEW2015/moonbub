# V107 IDCT private source-payload reset/CE removal

The isolated candidate changes only the private 1,280-bit `source_tile` storage. It removes its reset assignment and accepted-input assignment from the main process, then captures `in_tile` in a separate clocked process whenever `state==IDLE`. State, public outputs, errors, active-cycle counts, operands, accumulators, intermediate storage and every original assertion remain unchanged. No public port or cycle is added.

## Exact baseline and source recipe

The actual selected baseline is [V106 IDCT-area](../../fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv), SHA-256 `1ed49416dae06b727544ad1d2f96440f553cd99e5324dc895a0af5edbca5cc32`. Native snapshots copy those bytes under the canonical alias `fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv`. The unoverridden historical source at that alias hashes `251d4c11d762f6a040c1934d9dca9d80e6187f470a90b7261c63d06d1f3c310c` and is a different implementation. The selected `1ed49416…` baseline already contains operand prefetch and the area repair; this experiment adds neither. [baseline-origin.json](../../fpga/experiments/cu66-v107-idct-reset/baseline-origin.json) binds the source origin and an immutable elastic-native snapshot containing identical bytes.

The [three-edit recipe](../../fpga/experiments/cu66-v107-idct-reset/edit-recipe.json) reproduces candidate SHA-256 `2495e1d5461771cd2d09ce8770ea7818f4f38703bf035bbed4049cdd4226d44f` from that baseline. Removing the added observation ports and assignments from the verification adapters recovers both complete production bodies exactly.

## Overwrite before every read

On an accepted IDLE edge, both modules capture the same complete `in_tile` before leaving IDLE. The initial operand prefetch explicitly reads external `in_tile`, rather than the previously stored `source_tile`. The new register holds in every non-IDLE state, so later first-pass reads retain the accepted tile despite arbitrary changes to external data, ID or valid. Second-pass reads use intermediate storage; all original operand-live assertions remain enabled.

Zero and input-range-error shortcuts enter `OUTPUT_TILE` without math and still capture the same accepted private tile. Public result, error, ID and active-cycle behavior remain original. Held outputs and all owned source bits stay stable.

Original state/output/error resets still dominate reset and abort. On an IDLE cancellation edge the candidate may capture arbitrary unowned input; during an active cancellation it holds the old private payload instead of clearing it. State returns to IDLE, where no math consumer can use that old payload. A fresh accepted input overwrites the entire register before any subsequent math read. The proof therefore includes immediate retry, reset/abort combined with `in_valid`, and input changes while reset is held. It does not rely on payload power-up contents.

Deleting only the reset assignment inside the original reset/else process would leave reset-derived hold/enable logic. The separate IDLE capture instead removes reset, abort and input handshake signals from the explicit payload CE equation. Capturing unowned IDLE data can change switching activity; no power reduction is claimed.

## Focused actual RTL qualification

The V106 paired bench retains every original public/observation comparison and signed product/timing assertion. Only the newly added source observation is compared old/new when owned, since private unowned contents intentionally differ. A separate accepted-source oracle checks all 40 words before and after every owned edge, bound to the actual input handshake.

The independent dense integer two-pass Q14 model revalidates all 3,471 historical golden tiles and adds 512 arbitrary AC, 64 DC and 256 invalid-domain tiles: 4,303 total. It uses all eight basis positions and independent rounding after each pass, importing no production RTL or helper. [model.json](../../experiments/python-gamebub-v107/idct-reset/model.json) records the vector identities.

Both actual RTL seeds, 107801 and 107802, passed: 541,947 paired clock edges; 8,606 independent golden tile executions plus 60 directed cancellation cases; 1,045,124 owned-source checks; and 2,048 idle-noise edges. All ten FSM states were visited and targeted by reset, abort and both together. Independent signed-product replay passed all 244,048 multiplication edges. Held results, zero and invalid inputs, and arbitrary external changes during active states are included. The original two-million-edge global watchdog and per-tile operation watchdog remain enabled.

The historical Verilator backend used `-Wall --assert` and C++ `-Wall -Wextra -Werror`, with no warning suppression. The frozen [focused receipt](../../experiments/python-gamebub-v107/idct-reset/attempts/20261108T053836654669Z/results.json), SHA-256 `52d5584f81736b48c40ae166412e38ff4e9165948670b37bf1427eb1cc52a291`, includes source snapshots, commands, binary hash and traces. [audit.json](../../experiments/python-gamebub-v107/idct-reset/audit.json) rechecks all 15 source hashes and 23 artifacts. Production source and focused runner/bench are frozen after this PASS. This is reachable-state, two-state clocked testing, not formal arbitrary-state or four-state proof.

## Isolated native mapping

Sequential unit synthesis completed after simulation, within the shared two-heavy-job limit: exit 0 in 154.1 seconds. It compares the exact baseline and candidate on `xc7a100tcsg324-1`, with the same synthetic 10 ns clock, and checks all 1,280 source-register reset and CE cones. Actual `all_fanin` startpoints are classified by object `CLASS==port`, with the baseline reset and handshake ports serving as positive controls. Empty `get_ports -of_objects` output alone is not accepted as proof. The [native receipt](../../experiments/python-gamebub-v107/idct-reset/native/20261108T054142782352Z/receipt.json), SHA-256 `aefaa1a6075673e72ced3e21c3e42dbc2f248bd0bc8196d600ca7a450b828387`, passed these checks for every source bit:

| Measured source-register property | Baseline | Candidate |
| --- | --- | --- |
| FDRE cells | 1,280 | 1,280 |
| Reset pins driven directly by GND | 0 | 1,280 |
| Input ports reaching reset | `abort_frame rst` | none |
| Input ports reaching CE | `abort_frame in_valid rst` | none |
| CE has state-register startpoints | yes | yes |

The candidate retains a local state-controlled CE; the CE pin and its 1,280 loads do not disappear. This measurement proves removal of global input/reset dependencies from that payload control cone. Register startpoints are reported exactly as returned by `all_fanin` (state-register clock pins in this Vivado query), rather than mislabeled as Q pins.

The complete OOC mapping changed total LUTs 8,835→8,822, FFs 5,159→5,165 and unique control sets 22→11; DSP blocks stayed 17. Reset-pin endpoints reached from either reset or abort changed 3,604→2,321. Input-valid flat endpoints changed 3,704→2,431. These whole-netlist deltas include synthesis replication/optimization; the per-bit source TSV is the precise 1,280-bit reset/CE proof. [native-summary.json](../../experiments/python-gamebub-v107/idct-reset/native-summary.json) pins all results and rechecks 20 native artifacts.

The synthetic unit-clock report is not parent timing qualification: it has no routed delays, `HD.CLK_SRC` is unset, and external I/O timing is unconstrained. Synthesis retained the unused `dc_middle` and RAM-to-register inference warnings; no critical warnings or errors occurred. The constant-GND reset queries also produce expected no-fanin warnings, retained in the log. No warning suppression command was added.

[reset-fanout-plan.md](reset-fanout-plan.md) records the older full-top route's 1,313-register CE/SR group and 6,035-load reset/control net that motivated this experiment. Those measurements do not establish the new candidate's parent timing. Full canonical composition and fixed-10-ns routed closure remain separate gates; no hardware frequency or frame-rate claim is made.
