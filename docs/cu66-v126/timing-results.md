# V126 routed timing and implementation results

**125 MHz setup fails; this candidate is not promoted.** Functional qualification
passes with zero public-cycle change. The existing-edge producer cut improves its
intended data path, but the complete component has worse global timing than V125.
No unchanged-source reroute or positive-repeat claim was made.

## Source and recipe

The only changed origin is the [producer](../../fpga/experiments/cu66-v126-producer/cs88_coefficients_v91k.sv),
SHA-256 `5dec7454e6bfae4f7a9d7f64ecfbef8568665ddaa2dc00d4a76de1167a3c7292`.
All other seventeen V125 origins, the V120 core implementation recipe,
xc7a100tcsg324-1, Vivado 2026.1/build6511674 and the 8 ns clock loaded before
fresh RTL synthesis remain fixed. There are no timing exceptions, guessed I/O
delays, placement-directive changes or prior-checkpoint implementation starts.
Two CPUs and 8 GiB RAM/combined RAM-plus-swap bounded the job.

The [native receipt](../../experiments/python-gamebub-v126/native/20261110T152207460876Z/receipt.json)
binds all commands, source/recipe snapshots, external checkpoint hashes and reports.
Its 1597.263 s host duration is tool runtime, not FPGA decode latency.
The [independent terminal audit](../../experiments/python-gamebub-v126/audit/native-independent.json)
passes 1412 evidence-integrity checks and independently reports `design_timing_pass=false`.

## Global route

| Metric | V125 | V126 | V126 minus V125 |
| --- | ---: | ---: | ---: |
| Setup WNS (ns) | -1.224 | -1.867 | -0.643 |
| Setup TNS (ns) | -2209.865 | -4427.979 | -2218.114 |
| Failing setup endpoints | 8027 | 10868 | 2841 |
| Hold WHS (ns) | 0.052 | 0.088 | 0.036 |
| Failing hold endpoints | 0 | 0 | 0 |
| Pulse WPWS (ns) | 2.750 | 2.750 | 0.000 |
| Failing pulse endpoints | 0 | 0 | 0 |

All 73,846 routable nets are fully routed, with zero routing errors and zero
unconstrained internal endpoints. Board I/O timing remains unqualified: 1,101
input endpoints and 12,884 output endpoints lack delays in this OOC component.
No board clock location or external delays were invented to remove those gaps.

The actual worst routed path is `scratch/tile_overlap_mode_reg` →
`scratch/state_reg[1]_rep__0/D`: 9.864 ns data, comprising 2.769 ns logic and
7.095 ns routing, with 13 logic levels. The path traverses selected metadata,
full-owner comparison, ready return and terminal release/state logic. The
placed command-pending/reset/ready path is a separate observation; it is not
substituted for this routed worst path.

## Matched read-only path observations

Both V125 and V126 checkpoints use the same frozen expanded query, with no
implementation or constraint mutation. The [129-family comparison](../../experiments/python-gamebub-v126/pipeline-observations.json)
retains actual start/end pins, full report hashes and explicit missing-path
and width/replication gaps. The independent [candidate-query review](../../experiments/python-gamebub-v126/audit/candidate-query-review.json)
passes 25 checks of checkpoint/tool/artifact bindings and raw-report minima.
These are worst returned setup slacks within the
named source/target selection, not a replacement for global signoff.

| Selected family | V125 slack (ns) | V126 slack (ns) | Delta (ns) |
| --- | ---: | ---: | ---: |
| Cursor → original cache | -1.224 | 0.246 | 1.470 |
| Cursor → all endpoints | -1.224 | -0.397 | 0.827 |
| Cursor → prepared address D/CE | — | 3.115 | — |
| State → prepared address D/CE (worst is CE) | — | -0.086 | — |
| Plane → prepared address D/CE | — | 0.047 | — |
| Prepared address → prepared cell D/CE | — | 0.256 | — |
| Prepared cell → original cache D/CE | — | 4.802 | — |
| State → prepared cell D/CE | — | 1.449 | — |
| Plane → original cache | 0.864 | -0.486 | -1.350 |
| State → original cache | -0.323 | -0.698 | -0.375 |
| Producer plane → all endpoints | -0.474 | -1.223 | -0.749 |
| Producer state → all endpoints | -0.881 | -1.103 | -0.222 |
| Emit bank → scratch state | -1.219 | -1.813 | -0.594 |
| Admission cursor → all endpoints | -0.498 | -1.020 | -0.522 |
| Admission tile → coordinates | -0.464 | -0.045 | 0.419 |
| Admission group end → coordinates | -0.644 | 0.007 | 0.651 |
| Admission tile → hidden predicate D/CE | -0.191 | 0.086 | 0.277 |
| RAW mode → all endpoints | -0.855 | -1.100 | -0.245 |
| RAW position → all endpoints | -0.730 | -1.012 | -0.282 |
| Refill issued → all endpoints | 0.624 | 0.412 | -0.212 |
| Refill prepared address → all endpoints | 0.190 | 0.225 | 0.035 |

The old cursor-to-cache path gains **1.470 ns**, while the ROM-only successor
stage has +0.256 ns and its outgoing cache transfer +4.802 ns. This confirms
a useful local cut. It does not close all producer control: the new address
CE is −0.086 ns; old plane/cache and state/cache paths remain negative. The
producer-plane all-endpoint worst terminates on scale-store `WEBWE[0]`, and
the producer-state all-endpoint worst reaches ingress bounds preparation.
Unchanged scratch, RAW and admission logic also changes physically; some
families improve while others regress. Missing returned paths are explicit
gaps, never proof of elimination.

## Mapped cost and methodology

| Routed resource | V126 | Delta from V125 |
| --- | ---: | ---: |
| LUT | 33753 | +322 |
| logic_LUT | 33524 | +322 |
| LUTRAM | 137 | +0 |
| SRL | 92 | +0 |
| FF | 43429 | +110 |
| RAMB36 | 32 | +0 |
| RAMB18 | 12 | +0 |
| DSP | 42 | +0 |

Routed control sets are **1252**, unchanged from V125; synthesis has 1,251, one more.
The actual EDIF has **4,227 CARRY4s** after routing (4,230 after synthesis).
All 13 prepared-address and 11 prepared-cell named bits survive. Replication
produces **50 address FFs plus 11 cell FFs** in both synth and route. The
24 logical payload bits therefore represent 61 physical FFs in this build.
Verification-only producer and retained admission owner FFs are absent.
Whole-design FF delta includes other physical optimization/replication and
must not be attributed only to those two new source registers.

Fresh methodology counts are separate from the timing summary’s cached table:

| Rule | V125 fresh | V126 fresh | Description |
| --- | ---: | ---: | --- |
| SYNTH-6 | 28 | 28 | Timing of a RAM block might be sub-optimal |
| TIMING-16 | 76 | 724 | Large setup violation |
| TIMING-18 | 1000 | 1000 | Missing input or output delay |
| ULMTCS-1 | 1 | 1 | Control Sets use limits recommend reduction |

These warnings remain recorded without waivers. TIMING-18’s reported detail
count is not the total missing-delay endpoint count; the explicit check-timing
counts above retain that separate OOC limitation. RAM mapping and control-set
warnings remain future implementation work.

## Latency and next decision

All four actual parent profiles preserve V125’s cycles exactly. Both byte and
row variants, including last-input, first-input and start-to-commit boundaries,
are retained in the [functional report](functional-results.md) and final root
results. The row last-accepted-outer-input counts are 1,145,104 / 1,553,197.
Their 9.160832 / 12.425576 ms values assume a complete-parent 125 MHz clock
which this component study does not qualify. Byte controls project to
29.637640 / 75.873176 ms under the same assumption. These are neither physical
SDRAM service nor measured ESP32 Wi-Fi throughput or displayed frame rates.

At the retained final-input boundary, the stalled row profile needs at least
303,198 cycles removed for strictly below 10 ms at 125 MHz. Queue residence,
first-input processing, physical memory waits and publication boundaries must
remain in their own reported measurements; the timer cannot be moved to hide
work. Sustained hardware 30 fps and validated hardware <10 ms remain open.

V126 completes the bounded producer experiment, not the 125 MHz milestone.
Keep B100 unchanged and V123’s better historical global result as controls.
The [next timing proposal](next-timing.md) addresses the actual mode/owner/ready
return and residual local control, with a separately versioned elastic option
when a cycle-preserving cut cannot isolate the path. No further candidate is
implemented or qualified by that proposal.
