# Experimental active-cell scan lookahead

**Unselected and unqualified.** The V130 routed worst setup path leads from
`active_index` through the asynchronous 1,350-entry `active_cell` selection
into the `required_cells` update. The isolated
[candidate](../../fpga/experiments/cu66-v130-active-prefetch/cs88_admission_v91i2a.sv)
issues a synchronous read of cell zero on the existing MODE_END edge, then
issues cell `active_index + 1` on each eligible ACTIVE_SCAN edge while counting
the previously read bit. The index-1349 edge does not read 1350; the original
index-1350 terminal transition and external cycle count remain in place.

The payload register is deliberately unreset. Verification-only assertions
track full index and frame epoch, invalidate ownership on reset/start/abort,
and compare each consumed registered bit against the original asynchronous
memory expression. This makes a canceled prefetch unowned. Writes and clearing
of all 1,350 cells are unchanged. The non-synthesis assertion flags any active
scan index above 1,350 rather than assigning meaning to an out-of-range state.

A synchronous read can enable a memory primitive, but actual Series-7 BRAM
inference is **not established**: the two existing conditional write sites may
require Vivado to duplicate logic, use LUT RAM/registers, or infer multiple
ports. Read-address fanout and the incrementer, reset/cancel fanout, utilization,
and all new worst paths require fresh mapped and routed reports. No latency or
clock improvement may be inferred from this source change alone.

The [actual RTL pair test](../../experiments/python-gamebub-v130/active-prefetch/results.json)
passed two seeded runs of 1,633,241 edges each. Each run injects zero, full, and
four seeded random bitmaps into both complete admission instances, checks every
count and terminal cycle across 18,222 directed scan edges, and tests 15
reset/start/abort cases at scan indices 0, 1, 674, 1349 and 1350. Test-only
hierarchical annotations and state injection are absent from the production
candidate and do not establish that every injected state is reachable by a valid
packet. The bench also retains real packet/replay/cancel comparisons, with raw
data buses compared when response-valid as in the speculative-read baseline.

A [separate expected-failure test](../../experiments/python-gamebub-v130/active-prefetch/negative/results.json)
injected index 1351 into both actual RTL instances and observed the candidate's
bounds assertion fire. Its result is not a positive-path PASS. The simulation
binary hash is recorded but the binary remains in the local build directory.
A full-parent canonical/hash/physical-debt regression, independent memory
mapping analysis and a fresh route are still required.

The separate [synthesis-only receipt](../../experiments/python-gamebub-v130/active-prefetch/synth-only/native/20261111T034257038885Z/receipt.json)
completed using the same 8 ns XDC, part, source order and synthesis prefix as
the V130 speculative-read baseline. Its [report comparison](../../experiments/python-gamebub-v130/active-prefetch/synth-only/analysis.json)
found estimated WNS −1.760 ns versus −1.764 ns in the baseline. The worst
synthesized path in both cases is `qbuffer_reg[9][6]` to `cursor_reg[0]/CE`;
these estimates do not establish routed timing. The candidate uses 34,016
slice LUTs and 43,166 registers versus 33,697 and 43,131 respectively; both
have 38 block-RAM tiles and 42 DSPs at synthesis.

The read-only [mapping inventory](../../experiments/python-gamebub-v130/active-prefetch/synth-only/native/20261111T034257038885Z/reports/active-cell-inventory.tsv)
identifies 1,350 `active_cell_reg` entries implemented as FDRE flip-flops, with
no named RAM primitives in the active-cell inventory. The intended bitmap did
not infer block RAM in this synthesis, even though the read was registered.
Those observations do not prove why inference failed. A possible next isolated
experiment is to consolidate the existing conditional mark and clear writers
into one explicitly arbitrated memory-write port while retaining their exact
state, cancel, owner and 1,350-cell semantics, then rerun the actual RTL tests
and inspect the mapped primitive and reports before routing.
