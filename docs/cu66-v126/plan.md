# V126: separate producer successor arithmetic and lookup

This is the first bounded experiment in the
[V126–V130 plan](../gamebub-v126-v130-timing-streaming-plan.md). V125's complete
component setup fails at 125 MHz: WNS −1.224 ns / TNS −2,209.865 ns / 8,027
endpoints. Its producer cursor → cell cache path contains successor arithmetic
followed by the lookup truth table; the detailed data delay is 9.171 ns,
including 6.967 ns routing. Scratch emit-bank control is nearly equal at
−1.219 ns, and admission/control families also remain negative.

## Source and behavior contract

Change only the producer alias relative to V125's eighteen-file composition.
Keep the prepared admission predicates, scratch rank, queue repair, owner lanes
and every other selected source frozen. Qualified V120 B100 and its original
eighteen files remain unchanged; retain V123's better historical global result
as a control rather than assuming accumulated changes always improve timing.

Add 13-bit `prepared_successor_tile` and 11-bit `prepared_successor_cell` payloads.
Prepare the successor address on original tile writers; capture the ROM result
from that registered address on MAP_REQ; consume it at the original MAP_WAIT
skip or nonterminal DISPATCH completion. Keep the original current-cell cache
and its all-cycle assertion, including NEXT_PLANE and empty-plane intermediates.
No public stage/cycle, syntax, rounding, quality, port or packet change is intended.

Retain full thirteen-bit wrap and all four planes, accepted versus rejected
start semantics, full owner keys, nonce/error priority and accepted response
debts. Verification-only ownership/validity must show every consumption is
initialized and correctly keyed. New payloads may remain unreset only while
unowned values cannot affect outputs; no production fallback or width narrowing
is permitted. The [frozen V125 source chronology and proposal](../cu66-v125/next-timing.md)
defines the initial hypothesis; source and tests must verify it before native use.

## Verification and physical gates

Prepare reversible source, fixture and runner derivations before execution.
Retain every inherited oracle/assertion and all natural public-cycle comparisons.
Generic prepared fixtures may use actual writer edges but must count those
extra clocks separately; never force the new payload/owner bits. Include full
13-bit scalar/table equivalence, all planes, wrap, earliest response, holds,
overwrite, cancellation and stale-owner cases, plus real caller seed pairs.

After focused PASS, run fresh full decoder/actual V97 transport, peer and
byte/row-parent pairs. All ten raw stream sets must match V125, with the
eighteen-core-file source order and the parent's full twenty-four-file order
retained. The independent functional audit directly gates the new native
launcher and preflight auditor, including its exact index digest and 4/2/4
stream counts. Compilation must retain strict Verilator assertions and warning
flags, plus strict host compiler warnings. Failed attempts remain preserved.

Use the established standalone Verilator 5.020 backend and pinned simulation
image. Vivado MCP Tcl startup failed once with `Transport closed`; the existing
CLI/Docker fallback remains Vivado 2026.1/build6511674 with its pinned image,
xc7a100tcsg324-1 part and unchanged V120 core Tcl/XDC. Load 8 ns before fresh RTL
synthesis. Keep default synthesis, placement `ExtraNetDelay_high`, routing
`Default`, and no separate physical optimization. No checkpoint starts
implementation, clock relaxation, guessed I/O delay, timing exception or waiver.

Before and after implementation, use the same bounded read-only checkpoint
query for the V125 reference and V126 candidate. Keep all old admission, owner,
RAW, rank and queue families; add producer cursor/cache/plane/state plus both
new registers' D/CE/Q groups and explicit declared/physical-width inventory.
Missing registers/paths are gaps, not timing passes. Rehash the checkpoint
before and after observation; do not write it or change constraints.

Require global setup/hold/pulse/coverage/routing PASS, then a separate fresh
same-source/tool/core-recipe repeat before 125 MHz qualification. A shorter
producer cone alone does not pass this gate. Do not reroute an unchanged negative
source. A second source composition, if justified by measured failure, needs
its own complete source-bound proofs before implementation.

## Budgets and limits

At most two heavy study jobs, each two CPUs, compiler j1, 8 GiB RAM and 8 GiB
combined RAM-plus-swap, with finite watchdogs. Launch with available RAM ≥8 GiB,
full PSI avg10 <1 and combined used fraction <0.85; stop at available <4 GiB,
full PSI ≥5 twice, or combined fraction ≥0.90. Account for other observed host
jobs. Do not change swap or stop unrelated jobs. Protected marker files must
retain SHA, byte size and mtime.

Cycle-preserving V126 does not remove the retained row parent's 303,198-cycle
stalled gap to strict <10 ms at an assumed complete-parent 125 MHz. Its
1,145,104 / 1,553,197 cycles still project to 9.160832 / 12.425576 ms until
actual new measurements establish otherwise. Complete-parent timing, calibrated
ESP32 Wi-Fi/QSPI/memory service, custom endpoint negotiation and hardware
30 fps / <10 ms remain separate open gates. No board access/programming is part
of this experiment.
