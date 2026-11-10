# V127 routed timing and implementation results

**125 MHz setup still fails; no promotion.** Comparing complete owners before
mode selection improves global timing and the old mode/owner path, with unchanged
functional streams and public cycles. It does not close the complete component.
One fresh implementation was performed; the unchanged negative source was not
rerouted and no positive repeat is claimed.

## Fixed source and implementation

Exactly scratch, child pipeline and producer change from the frozen V126
18-origin composition; the other 15 origins and the original source order remain
unchanged. The new source exposes 32-bit epoch/16-bit block scalar views, compares bank0,
bank1 and scalar keys before selecting a Boolean match, and adds no production
register, reset, synthesis attribute, public top port, wire format or public cycle.
The retained V126 successor pipeline still has 24 logical payload bits.

Vivado 2026.1/build6511674 targets xc7a100tcsg324-1 with the byte-identical V120
run/report scripts, 8 ns loaded before fresh RTL synthesis, synthesis Default,
opt Default, place ExtraNetDelay_high and route Default. There is no separate
phys-opt pass, prior-checkpoint implementation start, timing exception, invented
I/O delay or constraint relaxation. Vivado's internal placement optimizations
remain part of the fixed place command. The job used two CPUs and 8 GiB combined
RAM plus swap with finite watchdogs and RAM/pressure monitoring.

The [native receipt](../../experiments/python-gamebub-v127/native/20261110T190637913699Z/receipt.json)
has SHA-256 `47ca8bedc398933be0b70b79f94d1a93ecb9672e94c06139dbf0886d86d9557e` and records 1570.267 s host runtime;
that runtime is not FPGA decode latency. Its immutable external routed checkpoint
is 28,394,147 bytes, SHA-256
`ad16aff87b1830ebefe7777726b54ad37a88a82568a7e77f17b979069fa47533`.
The [independent terminal audit](../../experiments/python-gamebub-v127/audit/native-independent.json)
passes **1530 evidence-integrity checks**, with `design_timing_pass=false`.
Source and recipe snapshots remain exact. The [prelaunch review](../../experiments/python-gamebub-v127/audit/native-preflight-review.json)
passes 17 checks after complete functional qualification.

## Global routed result

| Metric | V126 | V127 | V127 minus V126 |
| --- | ---: | ---: | ---: |
| Setup WNS (ns) | -1.867 | -1.193 | +0.674 |
| Setup TNS (ns) | -4427.979 | -1762.554 | +2665.425 |
| Failing setup endpoints | 10868 | 6980 | -3888.000 |
| Hold WHS (ns) | 0.088 | 0.075 | -0.013 |
| Failing hold endpoints | 0 | 0 | +0.000 |
| Pulse WPWS (ns) | 2.75 | 2.75 | +0.000 |
| Failing pulse endpoints | 0 | 0 | +0.000 |

Global WNS improves by 0.674 ns, absolute TNS falls 60.20%, and setup failures
fall by 3,888. V123's historical −1.086 ns global WNS remains better than
V127's −1.193 ns; it is also a failed 125 MHz composition. No version is promoted
from this relative improvement.

All 73,814 routable nets are routed, with zero routing errors and zero
unconstrained internal endpoints. Hold and pulse failures remain zero. This is
out-of-context component evidence: 1,101 input and 12,884 output endpoints lack
I/O delays, so board I/O and the complete parent clock remain unqualified.

The new worst route starts at ingress `raw_mode_reg/C` and ends at
`scratch/state_reg[3]_rep__0/D`: **9.140 ns data = 2.529 ns logic + 6.611 ns route**,
11 logic levels (3 CARRY4, 6 LUT6, one LUT5 and one LUT3). Its first data net has
fanout 100 and 1.504 ns delay. The path traverses selected context metadata,
validation and scratch control. Cell labels alone do not identify the precise
arithmetic operation in each carry chain.

The second returned global path is admission `header_reg[124][0]/C` →
`tile_reg[15]/R`, at **−1.165 ns**, with 8.652 ns data = 1.572 ns logic +
7.080 ns route and nine LUT levels. This is a synchronous reset/control endpoint;
fixing only the RAW path cannot establish global closure.
See the [actual setup report](../../experiments/python-gamebub-v127/native/20261110T190637913699Z/reports/route-setup-paths.rpt)
and the source-grounded [next timing proposal](next-timing.md).

## Matched read-only families

The same frozen query opens immutable V126 and V127 routed checkpoints without
implementation or constraint mutation. The [145-family comparison](../../experiments/python-gamebub-v127/pipeline-observations.json)
retains actual pins, worst returned paths, artifact hashes and all missing-path
or width gaps. These are minima within the declared query selections, which can
have different physical endpoints across implementations.

| Selected family slack (ns) | V126 | V127 | Delta |
| --- | ---: | ---: | ---: |
| Tile-overlap mode → all endpoints | -1.867 | +0.451 | +2.318 |
| Tile-overlap mode → scratch state | -1.867 | +0.986 | +2.853 |
| Scratch RAW mode → all endpoints | -1.457 | +0.127 | +1.584 |
| Emit bank → all endpoints | -1.813 | -0.562 | +1.251 |
| Emit bank → scratch state | -1.813 | -0.367 | +1.446 |
| Scalar epoch → all endpoints | -1.751 | -0.671 | +1.080 |
| Scalar block → all endpoints | -1.380 | -0.234 | +1.146 |
| Ingress RAW mode → all endpoints | -1.100 | -1.193 | -0.093 |
| Ingress RAW position → all endpoints | -1.012 | -0.719 | +0.293 |
| Producer cursor → original cache | +0.246 | -0.489 | -0.735 |
| Prepared address → ROM cell | +0.256 | -0.111 | -0.367 |
| Prepared ROM cell → original cache | +4.802 | +3.814 | -0.988 |
| Producer state → prepared address | -0.086 | +0.150 | +0.236 |
| Producer plane → all endpoints | -1.223 | -0.920 | +0.303 |
| Producer state → all endpoints | -1.103 | -0.757 | +0.346 |
| Admission cursor → all endpoints | -1.020 | -0.675 | +0.345 |
| Admission tile → coordinates | -0.045 | -0.421 | -0.376 |
| Admission group end → coordinates | +0.007 | -0.268 | -0.275 |
| Tile → prepared hidden-predicate D/CE | +0.086 | -0.644 | -0.730 |

The intended mode path improves strongly: tile-mode → all endpoints gains
2.318 ns and tile-mode → scratch state gains 2.853 ns. Emit-bank and scalar-key
families improve but several remain negative. Ingress RAW mode is a different
origin from scratch RAW mode and now determines global WNS.

Adverse changes remain material: cursor→cache and address→ROM now fail; the
hidden-predicate D/CE, tile/group-end coordinate and producer-plane families also
need closure. A positive address-stage enable no longer means the whole producer
pipeline passes. All unchanged origins can move physically after a source change.

Named owner nets do not prove complete physical lane isolation. V126/V127 have
78/110 `*tile_owner_match*` nets, exceeding the query's 32-net bound, so their
fan-in queries are explicitly unexecuted. Candidate scalar-owner has one named
intermediate whose raw fan-in lists 16 output-block and 16 expected-block
startpoints; that is only part of a full owner comparison. Candidate selected
child-owner has no matched named net. Raw `inspection.tsv` retains the fan-in rows;
the comparison's filtered owner-net list does not include that row kind. There
is no source-width narrowing or complete 48-bit lane-isolation claim. Absent
paths are gaps, never evidence that a dependency was removed.

## Mapped cost and methodology

| Routed resource | V127 | Delta from V126 |
| --- | ---: | ---: |
| LUT | 33576 | -177 |
| logic_LUT | 33347 | -177 |
| LUTRAM | 137 | +0 |
| SRL | 92 | +0 |
| FF | 43594 | +165 |
| RAMB36 | 32 | +0 |
| RAMB18 | 12 | +0 |
| DSP | 42 | +0 |
| CARRY4 | 4227 | +0 |
| Control sets | 1253 | +1 |

No logical source register was added, but physical optimization/replication
changes FF count by 165. The existing prepared address still has 13 unique bits
in 50 physical FFs; prepared cell has 11 in 11. Verification-only owner FFs remain
absent. Source declarations and named physical widths retain their distinct scopes.

Fresh methodology reports contain 28 SYNTH-6, 55 TIMING-16, 1000 TIMING-18 and
one ULMTCS-1 item. V126 had 724 TIMING-16 items; fewer reported items do not waive
the remaining warnings, missing I/O constraints or 6,980 failing setup endpoints.
Cached methodology rows remain separate from fresh reports in the audit.

## Qualification and remaining goals

[Full functional qualification](functional-results.md) passes with six focused
seed runs and ten complete raw stream sets, zero public-cycle change, and all
original key, debt, cancellation, hash/HUD/seal and first-error oracles retained.
The finite Python owner model is a separate algebra check, not sequential or
physical proof. Native timing remains failed, so no fresh positive-repeat gate
is satisfied, no qualified board bitstream is generated and B100 remains intact.

The row fixtures retain 1,145,104 / 1,553,197 cycles, projecting to9.160832 /
12.425576 ms only if the entire parent is qualified at 125 MHz. Strictly under 10 ms
still needs at least 303,198 fewer stalled cycles. Complete-parent routing,
calibrated ESP32 CPU/Wi-Fi/QSPI and physical SDRAM service, custom endpoint
negotiation, sustained 720×480 at 30 distinct displayed frames/s and validated
hardware decode under 10 ms remain open.
