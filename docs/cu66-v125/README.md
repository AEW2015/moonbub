# V125: tile predicates pass function; 125 MHz setup remains open

V125 prepares three admission predicates on existing writer edges. The fresh
functional suite passes with **zero public-cycle delta**, and the previously
worst tile → tile family improves **−1.170 → +2.447 ns**. The complete internal
component route still **fails 125 MHz setup: WNS −1.224 ns, TNS −2,209.865 ns,
8,027 failing endpoints**. It is not promoted or handed off as a qualified
125 MHz design. The broader V125 board-qualification milestone remains open.

| Evidence | V124 control | V125 candidate |
| --- | ---: | ---: |
| Global setup WNS | −1.170 ns | −1.224 ns |
| Global setup TNS | −2,527.615 ns | −2,209.865 ns |
| Setup-failing endpoints | 9,787 | 8,027 |
| Hold WHS / failures | +0.098 ns / 0 | +0.052 ns / 0 |
| Pulse worst slack / failures | +2.750 ns / 0 | +2.750 ns / 0 |
| Matched tile → tile family | −1.170 ns | +2.447 ns |
| Matched tile → coordinate family | −1.057 ns | −0.464 ns |
| Matched producer cursor → cell cache | −0.511 ns | −1.224 ns |
| Matched scratch emit-bank → all endpoints | −0.972 ns | −1.219 ns |

WNS worsens 0.054 ns while TNS improves 317.750 ns and failing endpoints fall
1,760. V123's earlier −1.086 ns WNS / −1,709.649 ns TNS / 6,724 failures remains
better globally than either. No unchanged negative source was rerouted and no
positive-repeat qualification was attempted.

## What changed and how it was checked

Only the admission origin changes relative to the pinned V124 eighteen-file
composition. Three unreset scalar payload FFs hold hidden-tile, tile-terminal
and group-terminal predicates. Full 32-bit keys, two-bit planes, wrapping
arithmetic, exact equality, error priority and speculative writes are preserved.
Tag commit snapshots the already registered group end; GROUP_BEGIN retains its
original literal group-end calculation. No new public cycle, interface, codec syntax,
codec-quality setting, placement directive or synthesis attribute was added.
See the frozen [design](tile-design.md) and [experiment plan](plan.md).

The [focused results](focused-results.md) retain both scalar/generic seeds,
all cancel/state crossings and both actual-controller seeds. Generic fixtures
use real tag-commit predecessor edges without a canonical mode write to prime
the new state; those edges consume a cached tag bit, then the prepared fixture
context is restored. Their extra clocks are counted separately from unchanged
natural public cycles.
The [full functional results](functional-results.md) retain fresh complete
decoder/actual V97 transport, peer and byte/row-parent runs. Ten raw stream sets,
canonical results, terminal dictionaries and public cycles match V124 exactly.
Every original oracle/assertion remains active.

The original independent auditor incorrectly compared the parent's complete
24-source list to the eighteen-file core. Its failure and code are preserved.
A separately derived/reviewed v2 auditor checks the core eighteen and the actual
V124 full stage order (18/18/24), changing only the admission origin. That
auditor-only correction passes; it did not modify or rerun the passing RTL.
The terminal native evidence audit independently passes **1,291 checks**.

Python algebra covers **58,904** full-width predicate/ownership contexts.
A separate optional boundary-update model passes 100,000 seeded transitions
plus explicit boundary, wrap and invalid-owner cases. That optional method is
unimplemented and contributes no measured resource, timing or latency gain.

## Physical result and next experiment

Fresh RTL synthesis/place/route used Vivado 2026.1/build6511674,
`xc7a100tcsg324-1`, `cs88_pipeline_v91k` and the unchanged V120 core recipe.
The 8 ns clock was loaded before synthesis; no timing exceptions, guessed I/O
delays, clock relaxation or checkpoint-started implementation were introduced.
All **73,516** routable nets are routed, with zero routing errors. Hold, pulse
and internal clock coverage pass. External input/output delay omissions remain
1,101/12,884, so this is internal component analysis rather than board signoff.

The new worst path is producer cursor → successor arithmetic → cell-lookup ROM
→ cell-cache D, **9.171 ns data delay**, of which **6.967 ns is routing**.
The matched producer query establishes its prior V124 family value; unchanged
producer RTL is mapped differently after the admission change. This is not an
isolated producer RTL regression. Scratch emit-bank control is only 0.005 ns
behind it. Admission coordinate paths and the new hidden-predicate D input
(−0.191 ns) also remain negative. New predicate Q-source family minima are
positive, but that does not qualify the component.

The [timing report](timing-results.md) retains both sides of the new FFs,
resources, methodology warnings and adverse family changes. The
[next timing proposal](next-timing.md) splits producer successor arithmetic and
ROM lookup across existing owned edges, with exact wrap/ownership/cancel tests;
it separately tracks scratch and admission residuals. It is a proposal, not
another implemented candidate in this version.

## Milestones still open

The row parent remains **1,145,104 / 1,553,197 cycles** from final accepted input
to validated commit. At an assumed complete-parent 125 MHz that is
**9.160832 / 12.425576 ms**. The stalled profile needs at least **303,198** fewer
cycles for strictly below 10 ms; component clock work alone does not save them.
The complete parent is not physically clock-qualified.

The qualified [V120 B100 control](../cu66-v120/handoff.md) and its eighteen
selected files remain unchanged. No board was contacted/programmed, and no
V125 board bitstream or qualified handoff manifest was produced. Full custom
Sunshine/ESP32/FPGA negotiation on one timebase, calibrated Wi-Fi/QSPI/memory
service, sustained hardware 30 distinct fps and validated hardware <10 ms remain
open. Earlier native JPEG seam results remain historical V124 evidence; V125
did not rerun them or transform them into a custom-codec system proof.

Machine-readable [results](../../experiments/python-gamebub-v125/results.json),
[matched tile queries](../../experiments/python-gamebub-v125/tile-observations.json),
[matched producer queries](../../experiments/python-gamebub-v125/producer-observations.json)
and [reproduction instructions](reproduce.md) retain the audit trail. Large
checkpoint files stay outside Git with their hashes recorded. Study jobs used
the two-job cap, two CPUs / 8 GiB RAM and combined RAM-plus-swap per job, finite
timeouts and live pressure gates; unrelated host jobs and protected files were
left alone.
