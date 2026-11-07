# V102 native implementation comparisons

All compared builds use native Vivado 2026.1 build 6511674,
`xc7a100tcsg324-1`, the same `cs88_pipeline_v91k` component and public diagnostic
visibility, and the unchanged 10-ns comparison clock loaded before synthesis.
Two Vivado threads and bounded owned containers are used. The V101 control
uses original RTL; each V102 experiment substitutes only its identified
candidate source. Behavioral regression results are recorded separately.

## Observed synthesis results

| Variant | Total LUT | LUT RAM | FF | RAMB36 | DSP | Synthesis WNS (ns) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| V101 original control | 74,340 | 22,286 | 34,985 | 16 | 28 | −16.629 |
| V102 memory only | 50,548 | 3,854 | 34,705 | 32 | 28 | −16.629 |
| V102 predicate only | 71,822 | 22,286 | 35,011 | 16 | 28 | −12.333 |
| V102 combined, synthesis stage | 49,040 | 3,854 | 34,689 | 32 | 28 | −12.181 |

The [V101 native source-bound baseline](../cu66-v101/vendor-rtl-review.md)
failed pre-placement `UTLZ-1` DRC. The
[V102 memory-only attempt](../../experiments/python-gamebub-v102/native/20261107T212049262997Z/receipt.json)
completed synthesis and reporting with exit code 0; it intentionally stopped
before placement. Its
[hierarchical utilization](../../experiments/python-gamebub-v102/native/20261107T212049262997Z/reports/synth-utilization.rpt)
and [timing summary](../../experiments/python-gamebub-v102/native/20261107T212049262997Z/reports/synth-timing-summary.rpt)
are actual native reports, not estimates from source declaration sizes or
part-capacity banners. The separate predicate-only and combined physical results are discussed below.

## Memory-only result

The common registered read-template change reduces whole-component synthesized
LUT use by **23,792 (32.00%)** and LUT RAM by **18,432 (82.71%)**. BRAM use
increases from 16 to 32 RAMB36 blocks. DSP use remains 28. These are measured
component synthesis changes under matched source visibility and target
constraints; they are not physical frame-rate or decode-latency measurements.

Admission moves from **44,040 LUT / 19,956 LUT RAM / zero BRAM** to
**18,892 LUT / 1,524 LUT RAM / 16 RAMB36**. Native messages explicitly identify
`coefficients/admission/memory_reg_*` as Block RAM. Other hierarchy totals also
change during optimization, so the entire top-level delta should not be
attributed solely to a raw bit-count calculation.

The [RAM configuration ledger](../../experiments/python-gamebub-v102/native/20261107T212049262997Z/reports/synth-ram-config.tsv)
records the inferred admission RAMB36E1 objects as TDP, width-one ports,
`WRITE_MODE_A=READ_FIRST`, `WRITE_MODE_B=WRITE_FIRST`, no optional output
register, and `RDADDR_COLLISION_HWCONFIG=DELAYED_WRITE`. Port configuration is
additional inference evidence; it does not replace source collision tests,
a primitive/netlist simulation or eventual hardware verification. No extra
read latency or reset policy was introduced to obtain the result.

The memory-only synthesis DRC report no longer contains the prior `UTLZ-1`
capacity errors. Its reported findings are warnings in CFGBVS/input/DSP pipeline
classes. Actual placement remains a separate gate, not implied by the absence
of a synthesis capacity error.

The old timing cone persists unchanged: the worst reported path still runs
from `reconstruction/plane_reg[1]` to
`reconstruction/count_copy_tiles_reg[0]/CE`, with **49 logic levels** and an
estimated 26.376-ns data path. Synthesis WNS is still −16.629 ns. TNS changes
from −73,220.930 to −74,788.773 ns while the reported timing-endpoint count
changes from 237,608 to 108,350; do not interpret that changed aggregate as an
independent timing win. The separate predicate candidate targets this cone.

## Predicate-only result

The [predicate-only native attempt](../../experiments/python-gamebub-v102/native/20261107T212814813775Z/receipt.json)
synthesizes the isolated exact `safe_hidden` interval substitution. Its
[utilization](../../experiments/python-gamebub-v102/native/20261107T212814813775Z/reports/synth-utilization.rpt)
shows **71,822 LUTs**, a **2,518-LUT (3.39%)** reduction from the V101 control.
Reconstruction decreases from 5,701 to 4,662 LUTs. LUT RAM remains 22,286 and
BRAM remains 16: this independent candidate does not solve the storage fit
blocker.

The [synthesis setup report](../../experiments/python-gamebub-v102/native/20261107T212814813775Z/reports/synth-setup-paths.rpt)
now reports **WNS −12.333 ns**, a **4.296-ns improvement in synthesis slack**
under the unchanged 10-ns target. Timing still fails. The worst reported path
moves from the reconstruction plane-to-counter-enable cone to
`coefficients/admission/tile_reg[2]` →
`coefficients/admission/active_cell_reg[377]/D`: **31 logic levels** including
15 CARRY4 and one DSP48E1, estimated data delay **22.293 ns**. These are unplaced
reports, not a routed speed or FPS gain.

Source inspection identifies the next relevant logic in
[admission `cell_index`](../../fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv#L105):
Y cells use `((t/90)/2)*45+(t%90)/2`, and `residual_tile` uses that result as
the dynamic `active_cell` write index. Unlike the thirteen-bit predicate input,
admission's tile state and this function use **32 bits**. A future width,
precomputed-coordinate or pipeline experiment must prove valid-state/range and
invalid-packet/error semantics, retain metadata/counter/epoch alignment and
accepted-owner drain, and then repeat exact regressions and native reports.
Do not silently truncate this new cone to thirteen bits or remove the counter
endpoint to manufacture timing closure. No further RTL was changed during
this review.

## Combined synthesis and physical implementation

The [combined native attempt](../../experiments/python-gamebub-v102/native/20261107T213234207776Z/receipt.json)
contains both independently qualified source substitutions. Its actual
synthesis uses **49,040 LUTs**, **3,854 LUT RAMs**, **34,689 FFs**, **32 RAMB36**
and **28 DSPs**. Relative to the V101 control that is **25,300 fewer LUTs
(34.03%)** and **18,432 fewer LUT RAMs (82.71%)**. The two individual synthesis
area deltas do not add exactly: global optimization changes across hierarchy.

Combined synthesized WNS is **−12.181 ns**, with TNS **−66,421.344 ns**. The
worst reported path remains in admission's cell-index/active-cell-write cone:
`tile_reg[4]` → `active_cell_reg[561]/D`, 30 logic levels including 15 CARRY4
and one DSP48E1, estimated data delay 22.141 ns. The new memory architecture
and fixed reconstruction predicate have not closed the 10-ns timing target.
Actual placement subsequently completes successfully. Its utilization is
**48,522 LUTs / 2,718 LUT RAMs / 34,795 FFs / 32 RAMB36 / 28 DSPs**. The
placed component passes the former LUT RAM capacity barrier, but its
post-placement setup WNS is **−12.979 ns** and TNS **−247,452.703 ns**. The
worst reported admission tile-to-active-cell path has 31 logic levels and an
estimated 22.926-ns data path. Placement success is resource-fit evidence, not 100-MHz timing closure;
V101 has no placed control for a matched physical speed comparison.

The combined native flow now **completes routing and writes `route.dcp`**.
Its [route status](../../experiments/python-gamebub-v102/native/20261107T213234207776Z/reports/route-status.rpt)
reports **72,867 routable nets, all fully routed, and zero routing errors**.
There are 111,928 logical nets in total; the remainder includes internally
routed, no-load and implicitly routed-port categories. Do not describe every
logical port/net as a qualified board connection.

| Combined stage | Total LUT | LUT RAM | FF | RAMB36 | DSP | Setup WNS (ns) | Hold WHS (ns) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Synthesis | 49,040 | 3,854 | 34,689 | 32 | 28 | −12.181 | +0.196 |
| Placement | 48,522 | 2,718 | 34,795 | 32 | 28 | −12.979 | +0.113 |
| Routing | 48,522 | 2,718 | 34,795 | 32 | 28 | −13.976 | +0.095 |

The [routed setup report](../../experiments/python-gamebub-v102/native/20261107T213234207776Z/reports/route-setup-paths.rpt)
records **WNS −13.976 ns**, TNS **−313,514.625 ns**, with 74,072 failing setup
endpoints out of 108,081 reported endpoints. The hold report has positive
0.095-ns WHS under this OOC analysis. Setup timing remains unclosed.
The route-stage DRC reports 93 warnings (CFGBVS, input/DSP pipelining and
no-routable-load categories), without the former `UTLZ-1` resource errors.

The new worst routed path is
`reconstruction/tile_reg[10]` → `reconstruction/residual_reg[1082]/CE`:
**29 logic levels**, including 14 CARRY4, and a 23.687-ns data path
(8.572-ns logic plus 15.115-ns routing). Source inspection ties this path's
validation context to the unchanged reconstruction
[`quant_cell`](../../fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv#L75)
comparison in `RESIDUAL`: incoming qcell must match the expected plane/tile
mapping before writing the residual lane. This is a different cone from the
removed variable-divisor `safe_hidden` path. Its exact source-level cause and
any candidate timing gain still need an isolated source experiment and native
comparison; a netlist path does not itself prove a proposed rewrite.

A next implementation study should address both quantization-cell sites:
reconstruction's thirteen-bit tile function and admission's **32-bit**
`cell_index`. Consider bounded-width arithmetic only after proving the full
contract, or precomputed/pipelined cell state with explicit plane/tile/epoch
alignment and unchanged invalid-input rejection. Retain qcell validation,
public counters, reference/cancellation drain and byte-exact canonical output.
Do not equate the two input domains or remove validation merely to shorten
the residual write-enable path. No such extra RTL change is part of V102.

## Qualification boundary

The component is not the complete custom decoder/board top. HUD/C2/frame-seal
validation, actual shared-memory/display ownership, transport/CDC and board I/O
requirements remain integration work. Native single-clock OOC CDC reports
skip ports without input-delay contracts. No new delay, false-path blanket,
waiver, reduced packet cap, tied-off public diagnostic or changed part hides
those missing requirements.

The combined router emits `Route 35-198`: external component ports lack
`HD.PARTPIN_LOCS`, so their parent-boundary partial routes and timing are not
accurate/exportable in this OOC build. The log explicitly suppresses further
messages after **100 emitted occurrences**; that is a message limit, not the
total affected-port count. No fictitious boundary locations or board pin
assignments are added to silence it. Native component routing/STA must be read
with this boundary limitation: reported internal register paths are the
assessment scope, while external I/O, parent clock/interface budgets and full
board timing remain unqualified.

The router also emits **`Timing 38-242`**: clock port `clk` lacks
`HD.CLK_SRC`, preventing timing estimation of the actual parent clock-buffer
delay/skew. Thus even the reported routed internal paths retain an abstract
parent-clock limitation. No fabricated clock-buffer location is supplied.
Setup already fails under the present model; do not derive an achieved Fmax
from its slack or treat a positive hold figure as complete board signoff.

A synthesis WNS is an unplaced estimate. Neither it nor the resource savings
is an achieved clock, sustained 30-fps proof, validated complete under-10-ms
decoding result or production-image promotion. Final placement/routing and
all setup/hold/DRC/methodology findings must be reported separately.
