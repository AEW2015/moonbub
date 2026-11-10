# V126 producer successor address and ROM stages

Status: prepared for Root review/freeze; no V126 compile, simulation or native
implementation has run at this document's input freeze. Executed status belongs
to the subsequently selected attempt receipt. This is a cycle-preserving trial
from [the V125 measured proposal](../cu66-v125/next-timing.md) and
[the V126–V130 plan](../gamebub-v126-v130-timing-streaming-plan.md).

## Selected source and architecture

The sole changed production alias is
`fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv`, selecting
`fpga/experiments/cu66-v126-producer/cs88_coefficients_v91k.sv`. Baseline producer
is frozen V124/V125 source
`fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv`, SHA-256
`963b46c3449d3a31e5ae85763f0681c6e68156c8d8c2c4c330d834ed2554fb53`.
Prepared candidate SHA-256 is
`5dec7454e6bfae4f7a9d7f64ecfbef8568665ddaa2dc00d4a76de1167a3c7292`.
All other 17 selected V125 origins remain byte-identical, including V125 admission,
V123 scratch and V121 refill queue. The inherited V124 two-bit owner-lane KEEP
attribute remains unchanged; this trial adds no attribute, placement directive,
constraint, public port/state/cycle or clock exception.

V125's producer cursor→current cell cache path fails at −1.224 ns, with three
CARRY4, five LUT6 and an intermediate ROM-select net of fanout504. The source
evaluates `quant_cell(plane,tile_cursor+13'd1)` on the same edge as advancing
the current tile. V126 separates address addition from ROM evaluation:

| Original edge | New private work | Original behavior retained |
| --- | --- | --- |
| Nonempty PREP_PLANE | `prepared_successor_tile<=1` | Tile/current cell clear to0 |
| MAP_REQ | `prepared_successor_cell<=quant_cell(plane,prepared_successor_tile)` | Original lookup/bounds/state transition |
| MAP_WAIT skip | Address becomes wrapped old tile+2; current cache copies prepared cell | Original tile+1, MAP_REQ edge |
| DISPATCH accepted index63, nonterminal block | Same parallel address preparation and cell copy | Original block/tile/state update |
| MAP_WAIT mode2 | Hold successor stages | Map original current tile/cell/scale |
| NEXT_PLANE | Revoke verification ownership; payload can hold | Original direct current-cell recompute for held tile and next plane |
| Empty plane, waits, stalls, terminal block | No invented pipeline work | Original current-cache/geometry and state behavior |

`prepared_successor_tile[12:0]` and `prepared_successor_cell[10:0]` add24 logical
payload bits, not a claim of24 retained physical FFs. Both payloads are unreset.
The address helper receives literal uint13 successor/current and old-tile+2
expressions. The ROM-only register uses the already registered address on the
existing MAP_REQ edge. A mode2 reply may arrive on the very next MAP_WAIT edge;
the successor is ready and remains owned through a held child coefficient.
No combinational fallback recomputes add+ROM at the old cache consumer.

Keep all13 tile bits and all four plane encodings. Tile8191 advances to0, so
old-tile+2 becomes1; wrapping occurs before the function lookup. The exact Y
truth table covers all8192 inputs and its 11-bit return truncation, including
integer cell values above2047. Nonzero planes retain tile[10:0]. The existing
`producer_cell_cache==quant_cell(plane,tile_cursor)` assertion remains literal
and active on every original non-reset/non-abort edge, including FAILED and
intermediate empty-plane states. NEXT_PLANE's original direct cache update
therefore stays intact rather than assuming PREP will later clear it.

## Priority and complete ownership

Verification-only keys under `ifndef SYNTHESIS` are:

- `address_owner_{valid,frame,plane,tile}`: frame32, plane2 and current tile13.
  Address geometry is established before allocation and deliberately has no
  child-epoch dependency.
- `cell_owner_{valid,frame,child_epoch,plane,tile,address}`: full frame32/current
  allocated child32, plane2 and both13-bit geometry keys, captured at MAP_REQ.

There are no new production validity/key registers. Assertions require complete
address ownership before a valid MAP_REQ and complete address/cell ownership
before the original skip/nonterminal cache consume. They follow the exact old
priority: reset/abort, accepted start, queue error when REFILL_OVERLAP is enabled,
child error while owned, then state-specific behavior. DISPATCH bad-owner error67
precedes any new consume check. Original full32 epoch, full16 block, full17 block
limit, nonce, physical request/debt and all first-fault checks remain unchanged.

Only accepted_start revokes the previous frame; a raw start rejected by
start_ready continues its current operation and increments the original blocked
counter. Cell ownership includes the child epoch after ALLOCATE. Waits/holds
retain that exact tuple. Original reset/current-cache values remain observable
and unchanged; only new owner validity resets. The phase-local ROM payload may
sample an old MAP_REQ even on cancellation, but its owner is invalidated and it
cannot affect an output/current-cache consume. Cancel tests check that sampling
rule rather than falsely requiring unreset ROM payload to hold.

## Reversible proof inputs

`scripts/cu66-v126/producer/prepare.py` generates the source edit recipe and
single-module lossless packaging. `prepare_verification.py` derives baseline
and candidate whole-producer adapters, retains every old assertion/need/require
body, copies unchanged checks and extracts exact production functions/tasks/
register/ROM/call fragments into a scalar wrapper. Neither script invokes an
old preparer, compiler or simulator. Old/pinned files are read-only.

The focused selector is `experiments/python-gamebub-v126/producer/results.json`,
with schema `v126-producer-existing-edge-successor-focused-v1`. Planned seeds
are126501/126502 for scalar/generic and126601/126602 for caller. Two fresh strict
models serve three modes: `producer_scalar_probe` and `ready_probe` (shared by
generic and caller). Ready instances differ only in selected producer; other
V125 children and admission packaging stay frozen. The focused ready model uses
the retained default REFILL_OVERLAP=1; its monitor reads the actual elaborated
parameter through a verification-only output, preserving the production queue
fault guard rather than assuming it for future configurations.

### Extracted full13 scalar domain

Exact production quant_cell, address task, register declarations, ROM writer and
advance/PREP/NEXT call expressions are copied losslessly. Independent C++ integer
math checks all8192 tiles × all4 planes (32768 cases), plus65536 random cases.
Expected per seed:98304 cases,1190177 clocks,294912 hold edges and1120 cancellation
contexts (4planes ×8 boundary keys ×5 stages ×7 nonempty reset/abort/accepted-start
overlaps). The clock ledger is98304×12 + initial1 +1120×9 +224×2. Positive counters
require 13-bit successor wrap, +2 wrap, plane3, Y return truncation and canceled
ROM samples that actually change value.

The scalar wrapper bootstraps arbitrary keys by loading only old geometry, then
clocks the actual address task and ROM writer. It never forces new payload/key
bits. This isolated register/table domain is not the original state machine,
request bounds, allocation or physical-debt chronology. Its capture body tests
full13 algebra independently of controller request eligibility. Whole-producer
tests below cover actual bounded control; no coordinate/original oracle is
disabled to claim unreachable keys as natural packets.

### Whole-producer generic tests

Retain the complete V119 cache/nonce and V124 owner-lane focus:2048 prepared cache
counter cases,9216 nonce/entropy cases and250000 full32 random nonce cases;
466944 owner wire cases including65536 random/8192 state cases;1152 clock cases,
192 error67,864 cancel,16 terminal-block wraps,336 held-output edges and224
response/owner contexts. Existing oracles/check bodies and their original raw
clock counts remain intact. New observers add no clocks to those tests. Their
ledger covers instrumented tick_owner calls, not the separate legacy cache
Driver clock denominator.

The new prepared campaign uses actual PREP and MAP_REQ writers, actual synchronous
mode/scale RAM responses and bounded producer planes0–2. It has534 prepared
contexts,1428 primer clocks (phases510/486/432),3664 total monitored campaign
clocks and2236 nonprimer clocks. Primer rows record original state transitions
3→4,9→10 and10→11. Prepared control skips allocation/refill and initializes old RAM
and child lease fields; it does not claim a complete natural packet. No cursor
is restored under an old new-stage owner after PREP. The full13/plane3 domain
belongs to the extracted scalar proof.

| New campaign check | Count |
| --- | ---: |
| Earliest lookup modes0/1/2/3 plus reconstruction arbitration |24 |
| Consecutive actual skip advances |555 |
| Held child edges with poisoned opposite bank/blocked raw start |21 |
| Nonterminal full16 wrap/advance cases |96 |
| Reset/abort cases at nonterminal acceptance |288 |
| Bad epoch/block owner priority |48 |
| Stage reset/abort/blocked-start overlaps |72 |
| Deliberately unowned malformed MAP_REQ error67 |9 |
| Empty-plane intermediate current-cell cases |3 |
| Actual accepted-start/epoch65 cases |3 |

The skip walk crosses pair/row and ROM-bank boundaries, reaching odd Y tile185.
Its held mode2 current cell is47 and the nonterminal successor at186 must be48,
so copying the current value cannot pass. The malformed high-tile contexts start
with invalid owners after reset and consume nothing; they test original error67,
not an owned out-of-bounds walk. Accepted-start fixtures assert both physical
outstanding bits are zero, mem_req_ready=0 and no response before clearing only
logical synthetic leases; they never erase accepted debt. Actual physical debt
remains independently tested by the retained natural caller.

New monitor types are `v126_successor_generic_monitor` and
`v126_successor_caller_monitor`; they report phase events, actual monitored
clocks, captures/consumes, earliest responses, held owners, raw versus accepted
starts and all-cycle current-cache checks. Generic monitored clocks are275333:
271669 retained instrumented calls plus3664 new campaign clocks. Hardcoded primer
trace files are retained separately for each seed, with sequential actual edge
IDs; no first-seed trace is overwritten or relabeled as natural traffic.

### Actual caller

The unchanged whole-producer/controller checker runs11 vectors,22 cases/two
memory profiles and12 original directed checks per seed. It retains all mapped
coefficient/current-cell/scale values, public/private cycles, requests/ACKs,
physical debt, held payload, cache/nonce, cancellation, late CRC and retry checks.
Natural callbacks observe both geometry stages without adding or skipping a
clock. Caller tests use no new fixture primer. Source/compiled fragments,
binaries, raw logs/traces, resources and distinct terminal/failed receipts are
pinned; independent auditors bind raw original and new verdicts separately.

## Execution and limits

Only Root can grant the first heavy run after source/bench/design/runner freeze.
Use strict --assert/-Wall and C++ -Wall/-Wextra/-Werror, no global fatal downgrade,
two CPUs and8GiB RAM-plus-swap, no extra swap, finite watchdogs and the frozen
host RAM/PSI/combined-use launch/stop gates. No Vivado job is part of this focus.
Retain every failed attempt before any ordinary fixture/tool repair.

Finite two-state source pairs and additional independent Python algebra are not
formal four-state, physical CDC/reset, timing or hardware evidence. Extra
prepared primer clocks are measured explicitly, while natural/public cycles
must exactly match selected V125. A fresh fixed-recipe route must query both new
register boundaries and every prior negative family. The near-equal scratch
emit-bank path and residual admission/RAW/refill failures remain open; neither
this design nor a focused PASS qualifies125MHz, sustained30fps or under10ms.
