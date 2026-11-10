# V125 next timing trial — producer successor cell preparation

This is a read-only proposal, not an implementation. The completed native route
and matched tile/producer queries confirm that global 125 MHz setup timing still
fails. The measured producer cone motivates the bounded next trial below; it is
not a selected or measured new implementation. No RTL, frozen proof, recipe or
constraint was edited, and no tool job was launched for this analysis.

## Observed routed cone

The report is
`/home/lori/gamebub-build/cu66-v69/v125-tile-125-20261110T064925972833Z-38f26d/results/route-setup-paths.rpt`,
SHA-256 `66da5f53f252ab2fca1131cf08933a1c68e78b740b9efd1cfd7954d99ff54d5c`.
It identifies a routed design at the unchanged 8 ns `component_clk` requirement.
The first path is `coefficients/tile_cursor_reg[0]/C` to
`coefficients/producer_cell_cache_reg[10]/D`: slack −1.224 ns, 9.171 ns data,
2.204 ns logic and 6.967 ns route (75.968%). Its eight levels contain three
`CARRY4` and five `LUT6`; uncertainty is 0.035 ns and clock skew −0.049 ns.

| Point in first data path | Fanout | Following routed net |
| --- | ---: | ---: |
| `tile_cursor_reg[0]/Q`, named `t[0]` | 7 | 1.209 ns |
| `g0_b0_i_3/CO[3]` | 1 | 0 ns |
| `g0_b0_i_1/CO[3]` | 1 | 0 ns |
| `g0_b0_i_2/O[2]`, named `sel[4]` | 504 | 1.673 ns |
| `g0_b3__9/O` | 2 | 1.160 ns |
| `producer_cell_cache[10]_i_17/O` | 1 | 0.613 ns |
| `producer_cell_cache[10]_i_10/O` | 1 | 1.326 ns |
| `producer_cell_cache[10]_i_4/O` | 1 | 0.986 ns |
| `producer_cell_cache[10]_i_2/O` | 1 | 0 ns |

The carry chain is consistent with the 13-bit successor addition before the
quant-cell truth table. The address bit with fanout 504 and the long lookup/output
routes make this more than a short counter increment. Exact LUT INIT/topology
attribution requires the checkpoint query; source and net names alone do not
identify every mux arm.

The second path is scratch `emit_bank_reg/C` to `state_reg[0]_rep/D`, slack
−1.219 ns, 9.166 ns data and 13 levels. Of the selected worst 50 paths, two
start at producer tile cursor and 48 at scratch emit bank. A producer-only win
would leave a nearly equal failing scratch family to address. The report's
absence of admission tile starts does not establish that the admission tile or
new predicate-D families closed; the matched data below retains failures.

V124's global report, SHA-256
`5568741fc6db8b1568008b4f457e8d34afa2b847590813d6c1b1c59b708e0a49`,
had no producer tile-cursor source in its selected worst 50. That is not a
like-family V124 producer slack. These are different full placements, with an
unchanged producer source, so the new global worst is not proof of a semantic
producer regression caused by V125.

## Actual selected source and chronology

The producer remains
`fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv`, SHA-256
`963b46c3449d3a31e5ae85763f0681c6e68156c8d8c2c4c330d834ed2554fb53`.
The relevant sites in that exact source are:

- Lines 141–144 declare plane2, tile cursor13 and producer cell cache11.
- Lines 196–199 define tile bounds and `quant_cell`. The Y function is a
  64-bank truth table selected by tile bits `[12:7]`, with bit tables indexed
  by `[6:1]` (lines 200–1048); every nonzero plane returns tile `[10:0]`.
- Lines 1105–1106 bind admission lookup tile/cell, and line 1115 asserts the
  coefficient lookup request in MAP_REQ only below the plane's tile bound.
- MAP_REQ (1259–1262) rejects out-of-range tile with error67 or enters MAP_WAIT.
  MAP_WAIT (1263–1266) captures mapped cell/scale for residual mode2; every other
  returned mode advances tile and writes `quant_cell(plane,tile_cursor+13'd1)`.
- DISPATCH (1268–1273) rejects a bad child owner first. Only an accepted index63
  coefficient advances expected block; only a nonterminal block also advances
  tile and evaluates the same successor-cell expression.
- NEXT_PLANE (1277–1279) changes plane while keeping tile and recomputes its
  current cell with `quant_cell(plane+2'd1,tile_cursor)`. PREP_PLANE subsequently
  clears tile/cell only for a nonempty plane (1236–1241). Empty planes therefore
  require the intermediate current-cell invariant too.
- Reset/abort (1203–1207), accepted start (1210–1214) and nonempty PREP_PLANE
  establish the original zero tile/cell tuple. Queue error precedes child error,
  which precedes the state case (1220–1224).
- The original assertion at 1287–1288 checks
  `producer_cell_cache==quant_cell(plane,tile_cursor)` on every non-reset,
  non-abort edge, including failure and intermediate plane states. It is not
  limited to reachable visible tiles or to lookup consumers.

## Bounded next hypothesis

Separate successor-address addition from the lookup ROM across existing edges.
Keep every public state/cycle and the original current cell cache. Add an owned
13-bit `prepared_successor_tile` and an owned 11-bit `prepared_successor_cell`
(24 proposed source payload bits, not a physical inventory claim):

1. On the original tile writers, prepare the address for the next current key.
   A tile-clear writer prepares 1. When current tile advances from t to uint13
   t+1, prepare uint13 t+2, so after the edge the prepared address equals the
   new current tile plus one. A plane-only change holds that address or
   recaptures the same full13 value; it revokes the prior plane's cell owner.
2. On the existing MAP_REQ edge, register
   `quant_cell(plane,prepared_successor_tile)`. The original admission lookup
   occurs on this edge; the already-registered successor address has no add
   feeding the new ROM stage. MAP_WAIT can consume the cell on its original
   next edge even when the lookup returns at the earliest supported cycle.
3. On MAP_WAIT skip and nonterminal DISPATCH index63 acceptance, write the
   original `producer_cell_cache` from the prepared successor cell, update tile
   on its original edge, and prepare the following successor address in parallel.
   Keep the snapshot owned across a mode2 MAP_WAIT and any DISPATCH stall.

This adds a register boundary inside the private preparation cone, not a public
pipeline stage. It splits increment→ROM into increment→address FF, address FF→ROM
cell FF, and cell FF→original cache. It is a hypothesis, not a claim that the
high-fanout ROM-only route will meet 8 ns. New CE/control paths and both sides
of each new register must be queried; merely moving the same full add+ROM cone
to a differently named FF would not establish a cut.

Keep NEXT_PLANE's direct current-cell update unless a separately proved existing
predecessor can prepare that exact intermediate value. Its source has no +1
adder on the tile input, and dropping it because PREP_PLANE often clears tile
would violate the original all-cycle assertion, especially across empty planes.
No full13 domain narrowing, ROM/table approximation, new state, KEEP/DONT_TOUCH,
placement directive or timing exception belongs to the initial trial.

| Original situation | Required ownership/action |
| --- | --- |
| Reset/abort or accepted start | Original public/current-cache initialization; invalidate new ownership |
| PREP_PLANE nonempty | Original tile0/cell0 plus prepared successor1 before any MAP_REQ |
| PREP_PLANE empty | Preserve original held tile/current cell; no invented lookup |
| MAP_REQ valid lookup | Successor address must belong to full plane/tile/frame key; capture ROM result before MAP_WAIT consume |
| MAP_REQ error67 | Original bound error wins; speculative unowned payload must not authorize consumption |
| MAP_WAIT no response | Hold current tuple and prepared ownership |
| MAP_WAIT mode2 | Capture old current mapped tile/cell/scale exactly; preserve successor cell across DISPATCH |
| MAP_WAIT other mode | Consume owned next cell and advance both 13-bit address relations on this edge |
| DISPATCH held/not-last | Hold preparation; never publish or release a coefficient early |
| DISPATCH bad owner/error | Original error67/queue/child priority; preparation cannot enable a transfer |
| DISPATCH accepted index63, terminal block | Original WAIT_DONE edge, no tile advance |
| DISPATCH accepted index63, nonterminal | Consume next cell and update successor address for the new tile |
| NEXT_PLANE | Preserve exact modulo-two-bit plane transition and current-cache recompute for old held tile; revoke old-plane successor-cell ownership |

The source add is 13-bit at the function argument and tile assignment. At tile
8191, successor wraps to0; a t+2 preparation must become1 after that advance.
Do not widen it to full32 or assume tile<5400 to simplify the function. Preserve
all four plane encodings: plane3 uses the original chroma mapping and its generic
NEXT_PLANE transition wraps to0. Keep full32 epoch and full16 block-owner checks;
the current 32-bit `expected_block+1 == selected_blocks` comparison must not be
replaced with a wrapped16 comparison. All original full32/full35/full64 semantics
in the unchanged children remain part of the inherited proof.

## Required proof and decision gate

Use verification-only complete owners for frame epoch, full plane/current tile,
prepared successor address and lookup phase, with validity revocation on every
reset/abort/accepted-start/new-plane path. A raw start rejected by start_ready
only increments blocked_starts in the original source; it must not revoke the
ongoing frame's preparation or change its transfer chronology. Confirm whether current child epoch is needed
to distinguish a reused plane/key at a child transition. Check every writer,
first consume, wait, overwrite, earliest response and repeated DISPATCH hold.
New unobservable payload may remain unreset, but it must never supply a fallback
or a stale cell after a cancel/retry. Preserve original current-cache reset and
private value comparisons; do not weaken the existing assertion to valid cycles.

Retain the V119/V124 producer cache/nonce/owner/lane oracles and assertions,
including their full32 nonce and full16/full32 bank comparisons on invalid and
unready cycles. Add finite full13×all-plane scalar/address/ROM fixtures against
an independent integer/table oracle, especially t8190/8191/0, row/pair/bank
boundaries and high bits. Prepared fixtures must clock actual new writer stages,
never force new payload/owner predicates, and label extra primer clocks honestly.
Keep unreachable scalar domains separate from claims of natural packet flow.

Fresh actual-controller and full parent pairs must match selected V125 on every
public/private current value, coefficient/lookup/memory tuple, request/ack/debt,
cycle and first fault. Include both refill modes, zero/empty planes, mode skips,
mode2 stalls, foreign/matching cancellation, accepted-start rejection, earliest
lookup response, concurrent reconstruction lookup, final block/nonce wrap,
queued/pending refill abort, child error and all response overlaps. Keep state
priority and immediate logical cancellation; do not gate readiness on assumed
child-valid/bank-ready conditions. Finite two-state/Python algebra is additional
evidence, not a formal proof or physical reset/CDC qualification.

The completed matched producer query below covers cursor→current-cell and
all-endpoint families together with plane/state/current-cell groups. Keep those
groups, admission tile/coordinate/mode groups, every new V125 predicate-D family
and RAW/owner/rank/refill groups when measuring a future candidate. The optional
admission hidden-boundary variant now has a measured residual D-path target
(−0.191 ns), but that local evidence does not outweigh the much worse producer
and scratch paths or select a combined multi-origin trial. A shorter producer
cone alone cannot close global timing with the near-equal scratch family failing.

## Final native and query evidence

The terminal native receipt is
`experiments/python-gamebub-v125/native/20261110T065004239267Z/receipt.json`,
SHA-256 `67ac131ffd3aff5365217d5a2f2b362dd4373e5abd5174a0ba8240e5dfada115`.
Its status is `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`, with
`component_internal_target_pass=false`. Final WNS is −1.224 ns, TNS
−2209.865 ns and setup failures 8027 of 103807 endpoints. WHS is +0.052 ns
with zero hold failures; minimum pulse slack is +2.750 ns with zero pulse
failures. All 73516 routable nets are routed, with zero routing errors and zero
unconstrained internal endpoints. External I/O remains unqualified: 1101 inputs
lack input delay and 12884 outputs lack output delay.

Relative to final V124, WNS worsens by 0.054 ns, TNS improves by 317.750 ns and
setup-failing endpoints decrease by 1760. This mixed result is not overall
125 MHz closure. The producer source is byte-identical across these two complete
compositions; changed mapping/placement/routing results do not establish a
producer RTL regression or a uniquely identified physical cause.

The exact external V125 `results/route.dcp` is 28412507 bytes, SHA-256
`974937caf0b82cc61722a5e4460d81fae7aca1e035ae43f28042db8e2b85b0b4`.
The candidate tile query receipt is
`experiments/python-gamebub-v125/request-inspection/candidate-20261110T072031933927Z/receipt.json`,
SHA-256 `3322a13720b60eb24d48c7535cc82f264e2d77a34aac2a0b21f463708a6c3950`.
It binds this native receipt/checkpoint and reports `PASS_READONLY_OBSERVATION`,
not implementation or qualification. The 115-family matched summary is
`experiments/python-gamebub-v125/tile-observations.json`, SHA-256
`f5d1ccfbeed2e55920f2e623bd5e28424915af12f20f697b1fc5fd41ed947d08`.

| Matched V124→V125 tile-family worst slack (ns) | V124 | V125 |
| --- | ---: | ---: |
| Admission tile, all endpoints | −1.170 | −0.464 |
| Admission tile → admission tile | −1.170 | +2.447 |
| Admission tile → coordinates | −1.057 | −0.464 |
| Group end → coordinates | −0.140 | −0.644 |
| Scratch emit bank, all endpoints | −0.972 | −1.219 |
| Admission cursor, all endpoints | −0.274 | −0.498 |

The selected tile→tile family becomes positive, while tile→coordinate and
all-tile endpoint families still fail and group-end→coordinate worsens. Each of
the three prepared predicates has one observed physical FF. Their Q-start
all-endpoint worst slacks are hidden +0.182 ns, tile-terminal +0.360 ns and
group-terminal +0.343 ns. On the input side, tile→prepared-hidden D fails at
−0.191 ns (8.136 ns data, 11 levels); tile→prepared-tile-terminal is +1.235 ns
and tile→prepared-group-terminal +0.954 ns. Thus the outgoing register cuts
have local positive results but their complete input/other-coordinate cones are
not closed. Direct tile→state and mode-RAM EN/data selections return no timed
path, which is an explicit query gap rather than a positive slack or an
elimination proof. No verification owner FFs are observed in synthesis.

The supplemental 13-family matched producer summary is
`experiments/python-gamebub-v125/producer-observations.json`, SHA-256
`5a8a3d00f6d3adde3f78fbe1d85e7033fb60be752c83fb1ae4c914c66bb332d5`.
Its exact baseline query is
`experiments/python-gamebub-v125/producer-inspection/baseline-v124-20261110T072544067468Z/receipt.json`,
SHA-256 `c72357291c58d0cf98f1b13d52c76ea8e10547e673be85bd3e89787ab17b321b`;
its candidate query is
`experiments/python-gamebub-v125/producer-inspection/candidate-20261110T072630347562Z/receipt.json`,
SHA-256 `dd4d2f9774e25f6bdaa474923830734240d96cc6667fe508c44115938c8a6c3d`.
Both are read-only checkpoint observations. The summary's observation-integrity
PASS establishes report binding/comparison, not timing qualification.

| Matched producer worst slack (ns) | V124 | V125 |
| --- | ---: | ---: |
| Tile cursor, all endpoints | −0.689 | −1.224 |
| Tile cursor → current cell cache | −0.511 | −1.224 |
| Tile cursor → tile cursor | +1.340 | +1.665 |
| Tile cursor → producer state | +1.998 | +1.299 |
| Producer state → current cell cache | −0.479 | −0.323 |
| Producer state, all endpoints | −0.602 | −0.881 |
| Producer plane → current cell cache | −0.436 | +0.864 |
| Current cell cache, all endpoints | +1.104 | +1.273 |

These data specifically support targeting the cursor→successor-ROM→cache
input cone, while retaining state/control measurements because state→cache
also fails. In V125 the query inventories all 13 unique cursor bits in 32
physical FF cells, 11 current-cache FFs and two plane FFs. Producer state is
source-declared8 bits but five named/mapped bits are observed; this is an
explicit inventory difference, not permission to narrow the source state type.
Current-cache→cache/tile/state selections have nonempty pin sets but no timed
paths; keep those gaps explicit. Replicas and absent names are not domain or
constant-value proofs.

A future trial must retain the exact source/derivation and new-stage owner
proofs described above, then route afresh under the same 8 ns part/recipe and
query each new D/CE/Q family. This note proposes that bounded trial only; it
implements nothing and claims no global timing, hardware 30fps or complete
validated-decode-under10ms qualification.
