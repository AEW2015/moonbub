# V124 spatial bank owner qualification

This experiment derives only the selected V123 coefficients controller,
`fpga/experiments/cu66-v119-owner/cs88_coefficients_v91k.sv`, SHA-256
`3517bda5016d7c2920e20fbc0767bbb1146e091cea4a5216db9a8b9a6532ee30`.
Its alias remains `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv`.
All other V123 origins remain unchanged, including scratch `12ad7721…`, V122
admission and the V121 refill queue. Interface, packet format, owner capacity,
state/error ordering and the declared public cycle delta (zero) are unchanged.

The V123 125 MHz routed setup report at
`/home/lori/gamebub-build/cu66-v69/v123-rank-125-20261110T024405001928Z-98bc8c/results/route-setup-paths.rpt`
identifies scratch emit-bank to busy-owned as the global worst path: WNS
-1.086 ns, data 9.034 ns, logic 2.380 ns, routing 6.654 ns and 11 levels
including three CARRY4. The reported cone selects a bank epoch/block, compares
those fields in the coefficients parent, returns ready to scratch, and reaches
tile release and final busy deassertion. This proposal moves comparison ahead
of bank selection; a fresh native route must establish its actual effect.

Two combinational `tile_owner_match[1:0]` lanes independently compare each
existing raw bank's full32 epoch and full16 block with the live expected owner.
`child_owner_match` selects one result bit in tile mode. Non-tile mode retains
the original full-width scalar fallback. The common exact predicate is used
consistently by child ready, public valid and the complement that raises
DISPATCH error 67. No bank-ready, child-valid, presumed-current-tag or presumed
block-ordinal assumption qualifies either lane. Invalid and unready-cycle
ready behavior is preserved.

The sole new synthesis attribute is
`(* keep = "true" *) logic [1:0] tile_owner_match;`. Its exact scope is only
the two combinational lane-result bits, to discourage merging comparison back
behind the wide bank mux. It adds no flip-flop, DONT_TOUCH, hierarchy directive,
placement, pblock, clock or timing exception. Native Tcl/XDC remain unchanged.
KEEP does not establish physical lane placement or timing closure; mapped
paths, utilization and routed QoR decide whether the trial helps.

For a one-bit selector, comparing selected epoch/block fields equals selecting
between the two complete equality results for every unsigned32/unsigned16
value. Verification-only assertions check this scalar identity and both lane
results. On every tile-mode clock, including invalid, unready, reset and abort
cycles, they also assert that the raw bank views equal the selected child
epoch/block fields. No existing assertion block is removed or edited.

The producer reset/abort, accepted-start, refill-error and child-error outer
priorities remain literal. A valid bad owner still raises error 67 before
index-63 acceptance. Expected-block increment retains uint16 wrap and the
separate widened terminal count check. Scratch final-case override, same-edge
bank release/publish, busy classification, selected abort epoch, physical debt,
DRAIN, matching/wrong/unsolicited response and error priorities are untouched.
All speculative payload and held-output contracts remain unchanged.

`prepare.py` emits reversible production/module-name/fixture recipes and a
single-module lossless packaging record. Focused verification derives from
every check in `scripts/cu66-v119/owner/producer.py`: the complete readiness,
cache/raw scale storage and nonce/entropy producer pair and independent oracles
remain. The probe adds child-ready equality to its existing complete public,
private/control and raw-cache comparisons. Both producer references use the
selected V123 source contract; all nine actual child RTL sources remain real.

Two generic seeds additionally exercise 393,216 raw-bank boundary wire cases,
65,536 random full-width cases and 8,192 cases spanning all 256 parent state
encodings: 466,944 total. Both banks, high-bit mismatches, opposite-bank poison,
all four raw/tile configurations, both selectors, all bank-ready masks,
child-valid absence, downstream stalls and reset/abort qualification are
covered. New predicates are read and checked, never forced.

Clocked prepared-domain tests add 1,152 DISPATCH contexts crossing eight epoch
boundaries, six full16 block boundaries, good/bad epoch/bad block and all eight
reset/abort/start overlaps. They independently check 192 error-67 cases,
864 cancellations and 16 expected-block wrap cases. Another 336 held edges
poison only the unready opposite bank and check index-62 then index-63 release.
There are 224 prepared response/debt contexts with independent old priority
and state/error/outstanding checks. Prepared synthetic debt is labelled and
retired with a matching response; these contexts are not natural accepted
external memory requests or naturally received packets.

Actual-controller tests use a reversible class/header adapter of the frozen
V91i2b controller bench and all 11 retained packet vectors, with every original
check intact. Two memory profiles give 22 case rows per seed. Both whole
controllers and their real children clock together and compare on every eval.
The independent bench checks all dense coefficients and mapped tuple fields,
packed-memory request/ACK ownership, queue/refill conservation, stable offers,
stalls, held output, accepted-write cancellation/drain, blocked replacement,
late-CRC recovery and one-shot cache behavior. Those natural transactions are
separate from the prepared raw-bank/full-width fixtures.

The planned generic seeds are 124101/124102 and actual-controller seeds
124201/124202. Strict Verilator warnings, assertions and C++
`-std=c++17 -O2 -Wall -Wextra -Werror` remain enabled, with no warning downgrade.
One root-granted container at a time is capped at two CPUs and 8 GiB
memory-plus-swap, with the frozen policy's launch/stop gates and bounded
watchdogs. Every failed attempt, source snapshot, raw log and final receipt is
retained. Inputs and this design note are frozen before execution.

Finite two-state checks do not exhaust every full-width value/control history,
establish four-state X/Z equivalence, formal proof, CDC, timing closure,
throughput, physical memory service or hardware qualification. Full functional
integration and the fixed native experiment remain separate parent-owned gates.
