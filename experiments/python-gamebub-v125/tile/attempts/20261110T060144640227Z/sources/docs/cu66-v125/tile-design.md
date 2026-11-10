# V125 registered admission tile predicates

Status: prepared and frozen for Root review before execution. The matched
read-only baseline queries passed; production RTL and reversible fixtures are
prepared. No V125 compile, simulation or native route has run at this freeze.
The selected focused receipt, when present, determines executed status.

## Measured cause and selected source

The matched V123/V124 query summary is
`experiments/python-gamebub-v125/tile-baselines.json`, SHA-256
`9d32b7f6a72f2fe466202ebc49cc503482493ec6083561d48e5d1e7796a43087`.
Its observation-integrity PASS covers 77 query families, not timing closure.
V123→V124 worst slacks are tile/all −0.498→−1.170 ns, tile→tile
−0.101→−1.170 ns, tile→coordinates +0.022→−1.057 ns, tile→state
+0.396→−0.300 ns, mode EN +0.457→−0.010 ns and mode data
+0.313→−0.080 ns. V124 retains 32 distinct tile-bit indices in 33 physical
FF cells, two plane bits and 32 group-end bits. The final V124 global path is
tile[8]→tile[24]/CE, eight LUT levels and 8.881 ns data, mostly routing.
V124 still fails 125 MHz; other failing RAW/owner/refill paths remain relevant.
See the evidence and limitations in `docs/cu66-v124/next-timing.md`.

The only production derivative is
`fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv`, SHA-256
`2f65ff770775404071e383890c75549ccb08ec9998993c86f1662cfed65d71eb`,
reversibly derived from selected V122 admission
`fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv`, SHA-256
`54dc87ded7abf37a9dc6757a4dabe62d6530f8127989d0fef2a4fc0f723376cf`.
Integration baseline is complete selected V124. Its producer owner lanes and
intentional two-bit KEEP attribute, V123 rank scratch, V121 refill queue and
all other origins remain frozen. V125 adds no KEEP, DONT_TOUCH, placement,
hierarchy, timing directive or constraint.

## Literal scalar and ownership contract

Three unreset production scalar payload FFs replace the corresponding live
consumer comparisons:

| Exact name | Owned equation |
| --- | --- |
| `prepared_tile_hidden` | Original full32 `hidden(plane,tile)` |
| `prepared_tile_terminal` | `tile==tile_count(plane)` |
| `prepared_group_terminal` | `tile==group_end` |

Tile/group-end counters stay unsigned 32-bit; plane stays two bits, including
encoding 3. Tile count remains 5400 for plane zero and 1350 for every other
encoding. Preserve equality rather than >=, high bits, modulo-two-bit plane
advance and literal uint32 additions/minimum. The original GROUP_BEGIN
`tile+16<tile_count(plane)?tile+16:tile_count(plane)` remains byte-identical.
Full35 header and full64 chunk-bound semantics remain unchanged. There is no
combinational fallback to the old comparison at a cache consumer.

No production ports, keys, valid bits, state encodings or public cycles are
added. Under `ifndef SYNTHESIS`, complete-key owners are
`tile_pred_owner_{valid,epoch,plane,tile}` and
`group_pred_owner_{valid,epoch,plane,tile,end}`. At actual consumes they check
full key ownership and compare each prepared bit to the original expression.
All original assertion blocks remain unchanged. Only owner validity resets;
private payload and otherwise unobservable keys need no blanket reset.

| Real original edge | Preparation and following ownership |
| --- | --- |
| Successful HEADER_CHECK | Tile key plane0/tile0; group owner invalid |
| KEY_TILE nonterminal | Tile key old plane, uint32 tile+1; group owner invalid |
| KEY_TILE terminal | Tile0 and original successor plane, retaining plane2 exit behavior; group owner invalid |
| GROUP_BEGIN | Original new end write; invalidate group owner only; all three payload bits hold |
| MODE_BIT completed tag | Atomic three-scalar snapshot of current plane/tile/already-registered end |
| Accepted hidden-only tag jump | Last-assignment override snapshots plane/group_end/group_end |
| MODE_BIT mixed consume | Snapshot old plane, uint32 tile+1, old group end |
| GROUP_TILE hidden/tag0/tag1 step | Snapshot old plane, uint32 tile+1, old group end |
| GROUP_NEXT plane clear | Tile0 and original next plane; group owner invalid |
| Other noncancel edges | Payload/owner hold, except the stated group invalidation |
| Reset/start/abort overlap | Original priority; invalidate both verification owners; payload holds |

The tag-commit boundary has a real architectural purpose: GROUP_BEGIN has
already registered group_end, so group equality does not add a tile→plus16/min
→new predicate-D cone. Sampling hidden/plane-terminal again at that same real
commit is an intentional atomic tuple ownership choice. It is not a test-only
writer, added state or added cycle. Rejected tags retain original error priority;
their private snapshot is unobservable in FAILED. Accepted hidden-only jump
uses the actual successor, respecting task/NBA last-assignment priority.

KEY_TILE consumes tile terminal then hidden; GROUP_TILE consumes group equality
first, then hidden and original tag branches; GROUP_NEXT consumes tile terminal.
Canonical mode writes use these same bits on the original edge. MODE_BIT tag
commit consumes none of them. A plane-clear snapshot is naturally superseded
by tag commit before a cache consumer, so its zero first-consume count is honest;
its overwrite is explicitly recorded. GROUP_BEGIN invalidation is not a payload
writer. Do not invent a first consume for either case.

## Frozen focused proof structure

Focused selector: `experiments/python-gamebub-v125/tile/results.json`.
Attempt schema: `v125-tile-existing-edge-predicates-focused-v1`.
Generic/scalar seeds: 125501, 125502. Actual-controller seeds: 125601, 125602.
The light preparation scripts never invoke older preparation entry points or a
compiler. Production recipe and packaging reconstruct the complete source;
verification recipe reconstructs every adapter and exact scalar extraction,
pins unchanged copies and newly authored C++/header inputs, and verifies that
no inherited require body or assertion block was removed.

The runner snapshots all source/recipe/design/driver inputs before execution,
including `edit-recipe.json`, `verification-recipe.json`, `packaging.json` and
baseline V122 source. Four full admission adapters losslessly share the original
scale/mode helper fragments. Selected source hashes and all compile-fragment,
binary, trace/log/resource and terminal/failed receipt hashes remain retained.

1. **Extracted registered scalar probe.** Exact production hidden/count functions,
   register/tasks and terminal successor call expressions are copied losslessly.
   Independent C++ interval/equality/uint32 oracles cover all four planes, every
   low13 value, boundary/high-bit aliases and 65536 random full32 cases. Literal
   terminal calls test plane3 wrap and plane2 no-write behavior without clocking
   unreachable original coordinate states. Per seed: 8309 tile-domain values,
   232652 boundary cases, 298188 total cases, 596376 hold edges, 2087316 cancel
   cases, eight terminal transitions and 5665589 actual clock edges. The raw
   `uint32_plus16_wrap_cases` counts wrap-domain inputs; it is not a claim that
   this probe recomputes the unchanged GROUP_BEGIN minimum.
2. **Actual admission pair.** Selected V122 versus V125 uses the entire inherited
   V122 bounds/header/V119 owner/legacy chain with its original packet, error,
   coordinate, quant, mode/scale RAM, request/response and receipt oracles. New
   monitors independently check owned scalar keys at first/held consumes,
   successor values, holds and cancel priority. The directed campaign has
   411 prepared contexts, 852 semantic clocks plus 411 real primer clocks,
   1263 total clocks, 189 cancellation cases, 19 first-followup consumes,
   three malformed contexts and two speculative-mode-write checks. Real
   GROUP_NEXT→GROUP_BEGIN→tag-commit sequences check old versus newly registered
   end and plane change. Original state/guard fixtures cover every one of the
   33 states with all seven nonempty reset/start/abort overlaps.
3. **Actual controller pair.** Two complete selected V124 producer instances
   differ only in their selected admission source. All other children stay at
   V124 origins. The inherited whole-producer pair/controller bench retains
   all public/private/scale comparisons, 11 vectors, 22 cases/two configurations,
   original coefficient tuples, memory request/acknowledgement and physical
   debt, held data, row/output, cancellation, late CRC and publication checks.
   No new key primer is used for this natural caller path.

The retained mode fixture still has 158228 semantic cases and 158230 original
clock edges. A non-consuming real tag-commit primer establishes the candidate
key before an old forced consume context. It never writes new flags or owners
from C++, never writes mode RAM or advances coordinates, and reuses the original
fixture's already-forced old key/context. Primer clocks increment real counters
and are explicitly additional prepared-domain clocks. The old semantic checks
remain; raw clock_edges/mode_prepared_edges increase truthfully by measured
primer counts. This is not natural packet chronology or extra natural coverage.

The raw `v125_retained_mode_ledger` reports semantic cases, original clocks,
primer clocks and their sum. `v125_tile_campaign` reports the directed counts
above. `v125_tile_verdict` reports nine writer categories in order header,
key-step, key-terminal, tag-commit, hidden-jump, mixed-step, group-step,
plane-clear, group-begin; natural/prepared writers, first consumes and overwritten
snapshots are separate. Categories 0–6 require first consumes; plane-clear
requires observed overwrite. Its 33×8 cancel-state matrix records every original
state/overlap. All new-predicate/owner forces, removed checks and added natural
public cycles must be zero. Monitored prepared clocks equal 158228 plus total
primer clocks plus 852; monitored total equals natural plus prepared clocks.
Other inherited generic loops retain their own clock ledgers rather than being
silently folded into this new monitor's denominator.

Retained floors include 40585 scale edges, 738933 header edges, 348673
quant/prepared edges, V119 mode-bound 540 cases, V116 chunk-bound 25344 cases
with 294 cancellations, V120 full35 67664 cases (65536 random, 4096 owned
consumes, 36 natural packets and 36 nonreset retries), and V122 full32-bound
16384 cases with 56 cancellations. Keep the full64 overflow/high32 and separate
uint32 number-wrap fixtures and unchanged independent replay checks. The scalar
extraction is finite algebra evidence, not a substitute for those old oracles.

## Execution and limits

Only an explicit Root grant may launch the frozen runner. Strict Verilator
assertions/warnings and C++ `-Wall -Wextra -Werror` remain enabled, without a
global fatal downgrade. Caps are two CPUs and 8 GiB RAM-plus-swap, no extra swap;
launch requires available RAM≥8 GiB, full PSI<1 and combined use<0.85, with
retained pressure-stop thresholds and finite watchdogs. No Vivado job is part
of focused qualification. Failed attempts must be retained before any repair.

Finite two-state fixtures and separate independent Python algebra do not prove
arbitrary four-state/X behavior, physical CDC/reset, timing or hardware service.
Prepared high32/plane3 scalar cases are explicitly not natural packets and do
not disable the V105 coordinate assertions. A new native route under unchanged
part/8 ns constraints must measure both sides of the added registers and all
prior tile/RAW/owner/rank/refill families. No 125 MHz, hardware30fps or complete
validated decode under10ms claim follows from this focused proof.
