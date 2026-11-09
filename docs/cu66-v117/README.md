# V117: owned read validation and overlapping decode stages

Branch: `study/gamebub-v117-read-validation-throughput-20261109`.
Base: published V116 commit `971279616a3025426f5d21a56a24cf2cefc50374`.
Status: all final C focused, decoder/transport, peer and guarded-parent
regressions passed. C matches B's event bytes and cycle counts exactly. The
fast-memory row-write test of keyframe `actual_001` takes 1,126,533 cycles versus 1,416,449 before (20.47% fewer):
conditionally 9.01 ms at 125 MHz or 11.27 ms at 100 MHz. The stalled row takes
1,553,878 cycles. These are model results, not hardware measurements.

Final C routed setup fails at both targets: −1.679 ns at 125 MHz and −0.317 ns
at 100 MHz. Hold, pulse and routing checks pass. The final B100 control also misses setup: −0.100 ns with20 failing endpoints.
All five planned measurements are complete; none qualifies for a fresh positive
repeat. No achieved clock or hardware milestone is claimed.
Original failures, diagnostic replays and parser/compiler repairs remain
preserved in source-bound receipts.

V117 keeps the 720×480 codec packet format, reconstructed YUV420 samples and transport format
unchanged. It has two independent acceptance gates: routed decoder-body timing,
and measured validated-parent cycle latency. Hardware frame rate and physical
parent timing remain separate.

## Baseline and target

V116 C completed Artix-7 routing at 125 MHz but failed setup: WNS −1.847 ns,
TNS −7365.672 ns and 16,725 failing endpoints. Hold, pulse and routing checks
passed. Its worst path was scratch read-address selection through AC legality
and error control to `busy_owned/D`, with 75.424% of data delay in routing.

The selected V116 parent simulation takes 1,416,449 cycles from its last
accepted outer byte to validated commit under fast abstract memory service;
stalled service takes 1,844,338 cycles. Strictly below 10 ms at an actually
achieved 125 MHz requires fewer than 1,250,000 cycles, so the fast model needs
at least 166,450 cycles saved. A 100 MHz result would instead need fewer than
1,000,000 cycles; a lower clock is not substituted into the primary target.

## Implementation sequence

1. **A, selected AC tuple.** Capture the complete selected word/position and
   ownership on existing cache-hit/fill edges; validate the registered tuple in
   AC_EXTRACT. Keep exact public cycles, raw views, error priority and physical
   debt. In particular, do not delay the ownership/busy error transition to
   shorten its path. Qualify strict generic and actual-caller old/new pairs,
   then fresh body, transport and peer tests before component routing. The
   parent test is a separate required gate and may run alongside component
   routing within the same two-job limit; a component measurement alone does
   not qualify the application.
2. **B, coupled throughput.** Pipeline inverse capture, registered validation
   and commit with complete owned tuples and a separately reserved accepted
   frontier. Use exactly two reconstruction tile owners with separate fill and
   ordered emission frontiers, real costed storage/ports and one arithmetic
   engine. Both changes are needed: V116's inverse II=2 and serialized
   64-input/64-output reconstruction are coupled limits. Declare changed
   scheduling, retain the frozen original checkers and independently verify
   arithmetic, ordering, metadata, first-fault priority, cancellation, reference
   leases and every accepted physical response. Then integrate A+B and rerun
   full/peer/transport checks before routing that exact composition, and the
   required parent checks before selecting it for application handoff.
3. **Only if required, C.** A further source change must address an actual
   remaining routed cause, retain fresh proofs and fit the predeclared budget.
   No unchanged-source reroute or implementation-strategy search is allowed.

A failed experiment remains evidence. A source candidate is not selected from
a clean compile, partial run or provisional receipt. All runs require an
explicit terminal verdict and source/recipe/artifact bindings. Throughput tests
must not omit cycles or weaken old functional checks to obtain a faster model.

## Fixed execution policy

The [master policy](../../experiments/python-gamebub-v117/study-policy.json)
was frozen before any build: at most five initial source/clock measurements
(three at 125 MHz and two at 100 MHz), three actual source compositions, and
at most one successful fresh repeat per clock. Prefer the final successful
125 MHz candidate. No negative repeat, timing exception, invented I/O delay,
retiming, fanout attribute, KEEP/DONT_TOUCH or method search is permitted.
Positive component qualification requires its actual routed checks and a fresh
identical-source/recipe/image repeat.

Root dispatches every heavy job, at most two globally. Each gets two CPUs,
8 GiB memory, no extra swap and one compiler job. Available RAM and PSI are the
main gates, with combined RAM/swap use secondary. Source, recipe and proof
inputs remain frozen while consumed by a job. Builds use the existing strict
Verilator 5.020 image and Vivado 2026.1 Artix-7 image; the unavailable Vivado MCP
connection is recorded in [environment.json](../../experiments/python-gamebub-v117/environment.json).

All V116 and older sources, goldens, receipts and checkers remain immutable.
The unrelated untracked marker-recovery work is outside this study. No hardware
contact, flash programming, Sunshine restart, protocol revision or ESP32
firmware deployment is part of V117.

## Required evidence before handoff

Keep focused old/new or semantic proofs, exact canonical/HUD byte checks,
qcache/owner/ACK/hash/drain/retry checks, source-bound full and peer executions,
finite memory/transport models, actual parent completion fences, mapped reset
and enable structure, routed path details and explicit remaining violations.
Keep failures and source snapshots; publish only the V117 source/evidence scope.

An OOC decoder-body pass does not qualify the row join, SHA, physical SDRAM,
ESP32 execution, transport/CDC, display or board I/O. A one-keyframe/retry test
does not prove sustained distinct-frame 30 fps. Conditional cycle-to-time
normalizations do not establish hardware-validated decoding under 10 ms.

Baseline and intermediate snapshots are recorded in [inventory.md](inventory.md).
Component design notes are frozen proof inputs and can retain their original
pre-execution status; terminal receipts and the results below are authoritative.

Terminal measurements and remaining gates are in [native-results.md](native-results.md).
Future architectural work is recorded in [next-timing-steps.md](next-timing-steps.md).
