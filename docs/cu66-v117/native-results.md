# V117 terminal native results: timing remains open

All five predeclared initial measurements completed from fresh RTL on
`xc7a100tcsg324-1`, Vivado 2026.1, with clock constraints loaded before synthesis.
No source/clock pair was rerouted to search for a pass. There were three source
compositions, three 125 MHz trials, two 100 MHz controls and zero repeats.

| Composition | Target | Routed WNS | TNS | Setup failures | Hold/pulse/routing |
| --- | ---: | ---: | ---: | ---: | --- |
| A | 125 MHz | -1.925 ns | -9909.251 ns | 19,863/98,882 | zero failures/errors |
| B | 125 MHz | -2.202 ns | -11052.357 ns | 20,904/101,991 | zero failures/errors |
| C | 125 MHz | -1.679 ns | -7430.129 ns | 17,428/102,793 | zero failures/errors |
| B | 100 MHz | -0.100 ns | -1.510 ns | 20/100,455 | zero failures/errors |
| C | 100 MHz | -0.317 ns | -37.943 ns | 324/102,268 | zero failures/errors |

B100 is closest, but −0.100 ns and 20 failing setup endpoints are still a failure.
Neither 100 MHz nor 125 MHz is qualified. A positive fresh repeat requires an
actual positive initial result; none was eligible. The primary 125 MHz target
remains open. C125 improves aggregate WNS by 0.523 ns versus B125, but does not
close timing. Direct registered canonical enables and removal of the named
wide residual insertion carry are observed structural changes; they do not
guarantee shorter routed nets.

The five receipts bind source snapshots, exact images/tools/recipes, actual
clocks, effective XDC, methodology, DRC, CDC, setup/hold/pulse, fanout, primitive
mapping and routing reports. Every terminal has a separate independent audit.
The unchanged OOC clock constraints intentionally do not invent external I/O
requirements. No full-parent memory/CDC/display timing or board qualification
is claimed.

## Functional outcome

Final C passes all focused suites, 44 decoder profiles/42 directed checks,
24 transport profiles with 4 abort/reset retries, 28 peer canonical retries,
and four guarded parent profiles. Complete C event bytes and cycle records
match B exactly; valid canonical bytes also match the frozen independent V113
goldens. Parent canonical/HUD/root/seal and physical ACK/debt checks remain.

For keyframe `actual_001`, fast-row validated completion is 1,126,533 cycles, down 289,916 cycles (20.47%)
from V116C/A. At an assumed common 125 MHz clock this is 9.012264 ms; at 100 MHz it
is 11.265330 ms. Stalled row is 1,553,878 cycles (12.431024/15.538780 ms respectively).
These are finite-memory-model normalizations; no tested clock is qualified.
Sustained distinct-frame hardware 30 fps and hardware-validated under 10 ms remain
open. See [parent performance](parent-performance.md).

## Evidence index

- [A125 receipt](../../experiments/python-gamebub-v117/read-study/native/20261109T113046956485Z/receipt.json)
- [B125 receipt](../../experiments/python-gamebub-v117/throughput-study/native/20261109T121229166037Z/receipt.json)
- [C125 receipt](../../experiments/python-gamebub-v117/repair-study/native/20261109T132139123840Z/receipt.json)
- [B100 receipt](../../experiments/python-gamebub-v117/throughput-study/native/20261109T135052237312Z/receipt.json)
- [C100 receipt](../../experiments/python-gamebub-v117/repair-study/native/20261109T132645224285Z/receipt.json)

- [Collected source-bound results](../../experiments/python-gamebub-v117/results.json)
- [Retained failure index](../../experiments/python-gamebub-v117/orchestration/attempt-notes.json)
- [Actual C mapping and limitations](final-c-mapping.md)
- [Future timing hypotheses](next-timing-steps.md)
- [Reproduction](reproduce.md)
- [Hardware handoff scope](handoff.md)
