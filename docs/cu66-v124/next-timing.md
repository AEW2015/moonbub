# V124 next timing trial — admission tile control

This is a read-only proposal for a future trial, not an implemented or measured
optimization. The final V124 native receipt confirms an 8 ns setup failure, and
the completed read-only candidate checkpoint query reports mixed path-family
tradeoffs. No source, constraint, implementation recipe or selected proof was
changed for this analysis, and no tool job was launched.

## Final routed evidence

The selected admission remains
`fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv`, SHA-256
`54dc87ded7abf37a9dc6757a4dabe62d6530f8127989d0fef2a4fc0f723376cf`.
V124 changes the coefficient owner comparison relative to V123; it does not
change this admission source. V123 and V124 both retain the V123 scratch rank
source and V121 refill queue.

The external report is
`/home/lori/gamebub-build/cu66-v69/v124-owner-125-20261110T044447506815Z-b8c817/results/route-setup-paths.rpt`,
SHA-256 `5568741fc6db8b1568008b4f457e8d34afa2b847590813d6c1b1c59b708e0a49`.
It reports a routed design and an 8 ns `component_clk` requirement. Its first
path is `coefficients/admission/tile_reg[8]/C` to
`coefficients/admission/tile_reg[24]/CE`: slack −1.170 ns, data delay 8.881 ns,
logic 1.448 ns, route 7.433 ns (83.696%), and eight LUT levels
(`LUT2=1 LUT5=2 LUT6=5`). This is a clock-enable path, not the incrementer's
carry path. The displayed clock uncertainty is 0.035 ns and skew −0.049 ns.

| Routed point | Fanout | Following net delay |
| --- | ---: | ---: |
| `tile_reg[8]/Q`, named `mode_store/Q[8]` | 37 | 1.300 ns |
| `mode_store/words_reg_i_152/O` | 2 | 0.645 ns |
| `mode_store/words_reg_i_116/O` | 1 | 0.973 ns |
| `mode_store/words_reg_i_98/O` | 1 | 0.648 ns |
| `mode_store/words_reg_i_50/O`, named `mode_store/tile_reg[11]` | 19 | 1.007 ns |
| `mode_store/words_reg_i_35/O` | 4 | 0.476 ns |
| `coord_cell[10]_i_9/O` | 2 | 0.446 ns |
| `coord_cell[10]_i_4/O` | 2 | 0.834 ns |
| `coord_cell[10]_i_1/O` | 44 | 1.103 ns |

The last net reaches the tile CE. Netlist names under `mode_store` reflect
synthesis sharing and hierarchy; they do not establish a mode-memory readback
dependency. In the RTL the mode store is written from parser control, and its
read output feeds `lookup_mode`, not `tile` (admission lines 413–451). The exact
Boolean decomposition of each LUT requires a netlist/query inspection; this
source review identifies the shared control expressions, not LUT INIT values.

Of the report's 50 selected paths, 33 start at admission tile registers, two at
RAW mode, 12 at context-decoder `emitted_reg[24]`, two at scratch bank epoch and
one at scratch pending tile index. The third path is RAW mode to scratch
`busy_owned_reg/D`, slack −1.143 ns, data 9.088 ns, ten levels including two
`CARRY4`. A tile trial alone would therefore not establish timing closure or
whole-RAW-family closure.

The V123 terminal native receipt is
`experiments/python-gamebub-v123/native/20261110T024415819812Z/receipt.json`,
SHA-256 `5717d2b8d2972931c958276bc86d9ba3e80dcfd7c343f45b49f46305a1200ae2`.
It records WNS −1.086 ns, TNS −1709.649 ns and 6724 setup failures. Its worst
path is scratch `emit_bank_reg/C` to `busy_owned_reg/D`, 9.034 ns data
(2.380 ns logic, 6.654 ns route), 11 levels. Its external setup-path report,
SHA-256 `63dd26f548bffa5327a8182484ce8ec50496514bbe3c4667fea99d8fe13a3c4b`,
contains 36 emit-bank-start paths and no admission-tile-start path in its
selected worst 50. That absence is not a baseline tile-family slack result.
The same unchanged admission can move in a different placement when another
component changes. Do not infer a causal tile regression or owner-lane closure
from the two global worst-path lists alone.

## Source cone and bounded candidate

The relevant selected admission sites are:

- Lines 101–107 retain full 32-bit `tile`/`group_end` and separate reachable
  coordinate state. Lines 138–147 define full-width `hidden(plane,tile)` ranges
  and `tile_count`: 5400 for plane zero, 1350 for every other plane value.
- Lines 346–365 advance the coordinate by the same parser event that advances
  tile. Lines 368–381 independently check reachable coordinates against the
  original full-width calculation.
- Lines 427–443 share hidden/group/terminal decisions with the canonical
  mode-store write enable, address and data.
- Lines 574–583 implement `KEY_TILE`: equality with the plane limit clears
  coordinates and tile; every nonterminal cycle advances tile and coordinates,
  while only visible tiles add a residual block.
- Lines 585–588 compute `group_end` as the literal uint32 `tile+16` minimum
  expression. Lines 595–605 advance after a mixed bit or jump to `group_end`
  after accepting a hidden-only group tag.
- Lines 612–629 implement group equality, hidden/tag-controlled advances,
  mixed-mode entry, malformed-group rejection and plane transition.
- Lines 490–508 give reset/start/abort priority; a valid new parse establishes
  tile/plane and coordinates only at successful `HEADER_CHECK`, lines 564–571.

The proposed next isolated trial is to prepare three scalar predicates on the
existing tile/plane/group-end write edges: `hidden(plane,tile)`,
`tile==tile_count(plane)`, and `tile==group_end`. Keep the 32-bit counters,
coordinate arithmetic, mode-store port, state machine and all public cycles.
Consume the owned prepared scalars consistently in tile/coordinate advancement
and matching canonical mode-write branches, so an old live hidden comparator
does not remain in the tile CE path. Factor the local step event explicitly:
KEY_TILE nonterminal, MODE_BIT with bits available and mixed bit, or GROUP_TILE
nonterminal with hidden/tag-zero/tag-one. Group tag three must retain its
original generic behavior, even when natural packet validation prevents it.

This is a hypothesis about a bounded control cut. It moves successor predicates
to a registered edge; it does not prove that their new input cones or route will
be shorter. Check tile-to-new-predicate D/CE, all new predicate-to-tile/coordinate
D/CE and mode-store EN/data paths, as well as the existing RAW and owner groups.
Do not add KEEP, DONT_TOUCH, placement directives, new clock exceptions or new
public latency as part of this initial trial.

| Original write/predecessor | Key used for next owned predicates |
| --- | --- |
| Successful HEADER_CHECK | New `plane=0,tile=0`; group-end predicate becomes owned when GROUP_BEGIN writes its end |
| KEY_TILE nonterminal | Old plane, literal uint32 `tile+1` |
| KEY_TILE terminal | `tile=0`; plane increments modulo two bits unless old plane is 2, when plane holds and state leaves mode parsing |
| MODE_BIT mixed-bit consume | Old plane, literal uint32 `tile+1`, old group end |
| MODE_BIT accepted hidden-only group | Old plane, exact old `group_end`, without changing its original coordinate delta or mixed-tag checks |
| GROUP_TILE hidden/tag-zero/tag-one step | Old plane, literal uint32 `tile+1`, old group end |
| GROUP_BEGIN | Tile/plane hold; group-end predicate uses the new literal uint32 `tile+16<count ? tile+16 : count`, not old `group_end` |
| GROUP_NEXT terminal, plane other than 2 | Successor modulo-two-bit plane, `tile=0`; new group end is established by the following GROUP_BEGIN |
| GROUP_NEXT terminal plane 2 or nonterminal | Tile/plane hold; no invented update or public state |
| Fetch/byte/load waits and no-step branches | Hold predicates and their ownership; tile/plane/group-end also hold |
| Reset/start/abort | Invalidate ownership with original priority; no broad reset of otherwise unobservable predicate payload |

Owners should be verification-only full-width keys/phase checks where possible.
Production validity must either be established before every consume or explicitly
gate an unobservable cache; it must not add a fallback to the original long
comparison at the same critical consumer. A failed header, malformed group or
cancel must never make stale private payload observable. All first-consume and
hold predecessors need assertions; a single natural-path seed is insufficient.

## Required proof before selecting a trial

Preserve the literal full32 domain independently of reachable coordinate proofs.
Test all four plane encodings, high tile/group-end bits, equality and neighboring
values around 1350/5400 and every hidden interval, and values around uint32
`tile+1`/`tile+16` wrap. Do not substitute `>=` for equality, saturate a counter,
truncate to 13 bits, treat plane three as plane two, or widen a wrapping addition.
The existing full64 chunk sum, full35 header sums and first-error ordering remain
unchanged; include their original tests/assertions rather than deriving a narrower
contract from packet sizes.

Exercise every table predecessor with coherent original state and successor
operands, plus hold cycles and each first consume. If a prepared-domain high-bit
fixture is needed, prime a real predecessor and label the fixture explicitly;
never force a new predicate or disable an original coordinate assertion to make
an arbitrary unreachable coordinate state appear supported. Check generic scalar
predicates separately from the existing reachable coordinate optimization.

On natural packets, pair every public input/output, mode-write tuple, residual
block/active-cell update, state transition, receipt/error and cycle with selected
V124. Include key frames, all group tags, mixed-group first/last bits, all-hidden
and partial-tail groups, all plane boundaries, malformed mixed counts and illegal
tags. Preserve speculative mode writes on the original edge even if a later
group error rejects the packet. In GROUP_TILE, terminal equality and its mixed
count error must precede hidden/tag stepping. In MODE_BIT, missing-byte/error
handling and tag validity must retain their original priority and bit consumption.

Test reset, start and abort individually and overlapping at every predecessor,
consume, fetch response and publication/receipt phase. Original priority is
`reset || start || abort`; start creates a parse only when neither reset nor
abort is asserted. Preserve cancellation of stage requests, stale-response
handling, counters, mode/scale writes and all physical request/debt behavior.
No public event may be delayed or moved between cycles. Payload-only caches need
not receive blanket runtime resets if validity and consumption prove them hidden.

Retain all existing fullfunctional, caller, parent and independent oracles and
assertions. Finite two-state Verilator fixtures corroborate semantics but do not
establish arbitrary four-state/X equivalence or physical reset/CDC behavior.
Only a fresh selected native route under the identical part/8 ns recipe can
measure the new trial. A shorter tile cone would not by itself qualify full
125 MHz, hardware 30 fps or complete validated decode under 10 ms.

## Final terminal and targeted-query binding

The terminal native receipt is
`experiments/python-gamebub-v124/native/20261110T044515396884Z/receipt.json`,
SHA-256 `d5ef0a69df810ed7362521e3b38759d1285ef3df68c99ae4d36264b3976db677`.
Its status is `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`, not timing PASS. Final
WNS is −1.170 ns, TNS −2527.615 ns and setup failures 9787 of 104367 endpoints.
WHS is +0.098 ns with zero hold failures; minimum pulse slack is +2.750 ns with
zero pulse failures. All 73306 routable nets are routed with zero routing errors.
There are zero unconstrained internal endpoints, but 1101 input ports lack input
delay and 12884 output ports lack output delay; board I/O timing is unqualified.
The worst setup tuple matches the first path analyzed above. Relative to V123,
final WNS is 0.084 ns worse, TNS is 817.966 ns more negative and there are 3063
more setup-failing endpoints. These are placement/route results for each complete
composition, not a proof that unchanged admission RTL semantically regressed.

The routed checkpoint is the external build's `results/route.dcp`, 28203745 bytes,
SHA-256 `2ff1d6908e7302b4e94662e24cd4459a42d136b999f80fa20b42971e50cf7711`.
The completed candidate query receipt is
`experiments/python-gamebub-v124/request-inspection/candidate-20261110T051344911535Z/receipt.json`,
SHA-256 `bfc92e415e8c88da60d2aeee330d477c01844eabbe837ec088e18aa5b107a584`.
It binds this exact checkpoint and native receipt, returns
`PASS_READONLY_OBSERVATION`, and records no new implementation or qualification.
The comparative observation artifact is
`experiments/python-gamebub-v124/owner-observations.json`, SHA-256
`47f722ab3008d175816ddce351aea90fabf507d51927d971552654328db0b446`;
its `PASS_OBSERVATION_INTEGRITY` covers 47 requested family comparisons, not a
125 MHz timing pass. The baseline V123 query receipt it binds has SHA-256
`e5c39c0c52587bc1a4c1939daf9f998605fd2cfe32e054e44652e5526b1a02f4`.

| Query family, worst returned slack (ns) | V123 | V124 | V124 minus V123 |
| --- | ---: | ---: | ---: |
| Emit bank, all endpoints | −1.086 | −0.972 | +0.114 |
| Emit bank → scratch busy owner | −1.086 | −0.562 | +0.524 |
| Emit bank → scratch state | −1.011 | −0.972 | +0.039 |
| Current child epoch, all endpoints | −0.154 | −0.798 | −0.644 |
| Expected block, all endpoints | +0.171 | −0.860 | −1.031 |
| RAW mode, all endpoints | −0.891 | −1.143 | −0.252 |
| RAW position, all endpoints | −0.916 | −1.016 | −0.100 |
| Rank threshold mask, all endpoints | +0.159 | −0.382 | −0.541 |
| Admission cursor → admission state | −0.040 | +0.226 | +0.266 |
| Admission cursor, all endpoints | −0.427 | −0.274 | +0.153 |
| Prepared refill address, all endpoints | +0.567 | −0.059 | −0.626 |
| Prepared refill address → admission RAM EN | +0.636 | −0.059 | −0.695 |
| Issued refill cursor → admission RAM EN | +0.959 | +0.455 | −0.504 |

The intended emit-selector/busy-owner path improves locally, while other owner,
RAW, rank and refill families worsen. Even a positive cursor-to-state result
cannot establish all admission-cursor closure: its all-endpoint family still
fails. Likewise issued-to-RAM EN remains positive while the prepared-address EN
family now fails. A next trial must retain these family checks rather than
optimizing the tile CE in isolation.

The query observes exact nets `coefficients/tile_owner_match[0]` and `[1]` within
110 `*tile_owner_match*` net-name matches. Each exact lane net has two reported
pins. Their routed KEEP property is blank, not TRUE. Source RTL contains the
intentional two-bit KEEP attribute, but these observations do not establish that
physical KEEP survived or that two complete independent wide comparator cones
were retained. Inferred net names are not an independent topology proof.

Inventory observes 17 physical emit-bank FF copies for one declared source bit,
and 63 named rank-mask FF bits (indices 1–63) for its declared 64-bit vector.
Do not describe this as 64 retained mask FFs or infer a specific elimination cause
from names alone. Nonempty RAW-mode/RAW-position/rank-mask to producer-state pin
selections return no timed paths; those entries are explicit query gaps, not
elimination or timing-pass results.

The current query does not include an admission-tile source family. Therefore
there is still no like-family V123 tile-to-tile/coordinate/mode-store comparison;
the proposal is grounded in the final global path and source control sites, not
an invented baseline tile-family result. Before implementing or selecting it,
add read-only tile/plane/group-end → tile/coordinate/state D/CE and mode-store
write EN/data groups for both checkpoints, with complete declared/retained
inventory and explicit missing-path reporting. A subsequent new-predicate trial
must also query both sides of each added register. Root's native/query runs are
the only jobs used for this note. This proposal does not select or implement a
new candidate and does not qualify full 125 MHz or a hardware latency target.
