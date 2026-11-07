# V104 native control and DSP register-mapping comparison

The retained source control is the V102 memory/predicate component selected
by V103, recorded at provenance baseline
`1d0a702a758787522723ac52ff44a1bf220c39d1`. Every candidate keeps the frozen
720×480 codec/profile, 49,152-byte cap, public ports and diagnostic visibility.
The comparison uses native Vivado 2026.1 build 6511674,
`xc7a100tcsg324-1`, Default directives, two threads and the unchanged 10-ns
component clock loaded before synthesis. No retiming switch, clock exception,
DRC waiver, DSP attribute or changed output visibility supplies a shortcut.
Behavioral parity and source provenance are measured separately.

## Frozen component control

The [V102 implementation](../cu66-v102/vendor-comparison.md) is the native
control, not either of the V103 variants whose routed timing regressed.
Synthesis uses **49,040 LUTs, 3,854 LUT RAMs, 34,689 FFs, 32 RAMB36 and
28 DSPs**, with WNS **−12.181 ns**. Its routed implementation uses
**48,522 LUTs, 2,718 LUT RAMs, 34,795 FFs, 32 RAMB36 and 28 DSPs**, with
WNS **−13.976 ns**, TNS **−313,514.625 ns**, hold WHS **+0.095 ns**, and
pulse-width slack **+3.750 ns**. All **72,867 routable nets** are fully routed
with zero reported routing errors. These are OOC component results, not a
qualified board clock or hardware performance measurement.

## Native synthesis matrix

| Component source | Total LUT | LUT RAM | FF | RAMB36 | DSP | Setup WNS (ns) | Native stage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Retained V102 control | 49,040 | 3,854 | 34,689 | 32 | 28 | −12.181 | Published synthesis |
| V104 DSP only | 48,933 | 3,854 | 34,720 | 32 | 29 | −11.837 | Synthesis-only completed |
| V104 cached control only | 48,103 | 3,854 | 34,672 | 32 | 28 | −12.095 | Full implementation completed |
| V104 combined | 49,421 | 3,854 | 34,715 | 32 | 29 | −11.624 | Full implementation completed |

The variants are independent source substitutions. The DSP experiment
changes the [dequantizer product register placement](dsp-results.md), preserving
all public cycles and partial packed outputs. The control experiment changes
[geometry state](control-results.md), preserving the selected sequential
contract. The combined source contains both substitutions. Whole-top resource
deltas need not add across isolated candidates because Vivado optimizes
across hierarchy; do not sum source-level arithmetic counts to predict them.

## DSP48E1 register evidence

The [retained baseline register ledger](../../experiments/python-gamebub-v102/native/20261107T213234207776Z/reports/route-dsp-registers.tsv)
contains 28 actual DSP48E1 instances. Eight are under `transform/dequant` and
have `AREG=BREG=MREG=PREG=0`. The sixteen under `transform/inverse` already
use fifteen `MREG=1` and one `PREG=1` product paths. Three context/ingress/
scratch instances use `AREG=1`; the remaining admission instance is not
registered. Thus the baseline already uses DSP pipelines in the inverse
transform; the dequantizer experiment targets its separate eight unregistered
multipliers.

The [DSP-only native receipt](../../experiments/python-gamebub-v104/native/20261107T224846078746Z/receipt.json)
records successful synthesis-only completion with exit code 0. The
[actual DSP48E1 register ledger](../../experiments/python-gamebub-v104/native/20261107T224846078746Z/reports/synth-dsp-registers.tsv)
verifies **all eight** `transform/dequant/products_reg[0..7]` instances with
`PREG=1`, `AREG=BREG=MREG=0`. The native transcript also reports absorption
of those product registers into their DSPs. This is an observed inference
result, obtained without a DSP attribute; the source/clocked proofs establish
public latency separately. The original dequantizer's eight multipliers had
all four register properties zero.

| Native hierarchy | V102 DSP count/configuration | V104 DSP-only count/configuration |
| --- | --- | --- |
| `transform/dequant` | 8; all AREG/BREG/MREG/PREG=0 | 8; all PREG=1, AREG/BREG/MREG=0 |
| `transform/inverse` | 16; 15 MREG=1 and one PREG=1 | 17; all MREG=1, PREG=0 |
| Coefficient/admission/context/scratch | 4; three AREG=1, one unregistered | 4; same register configurations |
| Whole component | 28 DSPs | 29 DSPs |

The additional whole-component DSP is in the **inverse-transform hierarchy**,
not an extra dequantizer lane. Its RTL source is unchanged. Global synthesis
changes its primitive decomposition from the baseline sixteen DSPs to
seventeen; do not describe the whole-top DSP delta as a newly added local
multiply. Aggregate enabled-register counts change from AREG=3/MREG=15/PREG=1
to AREG=3/MREG=17/PREG=8, with BREG=0 in both builds.

The [hierarchical utilization](../../experiments/python-gamebub-v104/native/20261107T224846078746Z/reports/synth-utilization.rpt)
shows dequantizer leaf LUTs **3,483→3,785** (+302), FFs **2,351→2,349** (−2)
and unchanged **eight DSPs**. Whole-component synthesis instead changes
49,040→**48,933 LUTs** (−107, 0.22%), 34,689→**34,720 FFs** (+31), and
28→**29 DSPs** (+1), with the same 3,854 LUT RAMs and 32 RAMB36. Leaf and
global deltas are deliberately reported separately; they are not additive
source-level resource predictions. Product-register absorption does not
imply zero surrounding mux/control cost or a lower total DSP count.

The [setup report](../../experiments/python-gamebub-v104/native/20261107T224846078746Z/reports/synth-setup-paths.rpt)
reports WNS **−11.837 ns**, a **0.344-ns improvement in synthesis slack**
relative to V102's −12.181 ns. The target still fails. Its worst path remains
admission `tile_reg[2]` → `active_cell_reg[959]/D`, with **30 logic levels**
(15 CARRY4 and one DSP48E1), **21.797-ns estimated data delay**, split into
11.651-ns logic and 10.146-ns estimated routing. The top-level path is not
one of the newly registered dequantizer multipliers.

The [Design Timing Summary](../../experiments/python-gamebub-v104/native/20261107T224846078746Z/reports/synth-timing-summary.rpt)
prints TNS **−66,750.688 ns**, hold WHS **+0.196 ns** and pulse-width slack
**+3.750 ns**. Its reported setup-endpoint count is 108,346, so aggregate TNS
is not interpreted independently of the changed endpoints. The synthesis DRC
reports **87 warnings**: one CFGBVS, 53 DPIP-1, 21 DPOP-1 and 12 DPOP-2;
no reported resource-fit error. Remaining pipelining warnings are retained.
This isolated job intentionally stops before placement, so it establishes
neither a routed timing gain nor an achieved clock/FPS/complete latency.

The [native capacity table](../../experiments/python-gamebub-v104/native/20261107T224846078746Z/reports/synth-capacity.rpt)
retains the actual part limits: 63,400 slice LUTs, 19,000 memory-capable LUTs,
126,800 FFs, 135 BRAM36 equivalents and 240 DSPs. DSP-only synthesis leaves
14,467 total LUTs, 15,146 memory-capable LUTs, 92,080 FFs, 103 BRAM36
equivalents and 211 DSPs nominally unused. LUT and memory-LUT capacities
overlap and are not additive. This is component synthesis headroom; it does not guarantee placement, board I/O closure or sufficient
resources/ports for the missing whole decoder/display/transport integration.

## Cached-control synthesis

The closed synthesis stage of the [control-only native run](../../experiments/python-gamebub-v104/native/20261107T225623415653Z/receipt.json)
uses **48,103 LUTs**, **3,854 LUT RAMs**, **34,672 FFs**, **32 RAMB36** and
**28 DSPs**. Relative to retained V102 synthesis, that is **937 fewer LUTs
(1.91%)** and 17 fewer FFs, with unchanged RAM/DSP totals. The source cache
replaces the reconstruction geometry path; no dequantizer product prefetch
is present in this isolated variant.

The synthesis DSP ledger matches the baseline hierarchy/configurations:
eight dequantizer DSPs with AREG/BREG/MREG/PREG=0, sixteen inverse-transform
DSPs with fifteen MREG=1 and one PREG=1, and four coefficient-side DSPs with
three AREG=1. A PREG-absorption result must not be attributed to control-only
merely because that result was observed in the independent DSP candidate.

The [setup report](../../experiments/python-gamebub-v104/native/20261107T225623415653Z/reports/synth-setup-paths.rpt)
records WNS **−12.095 ns**, **0.086 ns better in synthesis slack** than the
−12.181-ns synthesis control. TNS is **−48,392.605 ns**. The worst reported
path remains admission `tile_reg[2]` → `active_cell_reg[624]/D`, with **30
logic levels** (15 CARRY4 and one DSP48E1) and a **22.055-ns estimated data
path** (11.651-ns logic plus 10.404-ns estimated routing). The 100-MHz target
still fails; these are unplaced results rather than a routed speed gain.
The synthesis DRC reports **92 warnings** (one CFGBVS, 51 DPIP-1, 27 DPOP-1,
13 DPOP-2), retaining the existing categories and no reported fit error.

## Combined synthesis

The closed synthesis stage of the [combined native run](../../experiments/python-gamebub-v104/native/20261107T230358177941Z/receipt.json)
uses **49,421 LUTs**, **3,854 LUT RAMs**, **34,715 FFs**, **32 RAMB36** and
**29 DSPs**. Against retained V102 synthesis, that is **381 additional LUTs
(0.78%)**, 26 additional FFs and one additional DSP, with unchanged RAM totals.
These costs differ from the sums of the isolated results; the complete native
top is measured rather than predicted by adding leaf/source deltas.

The [DSP register ledger](../../experiments/python-gamebub-v104/native/20261107T230358177941Z/reports/synth-dsp-registers.tsv)
again verifies eight dequantizer DSPs with `PREG=1` and AREG/BREG/MREG=0.
The unchanged inverse transform maps to seventeen DSPs with MREG=1/PREG=0,
and the coefficient subtree retains its four baseline DSPs/configurations.
This combined source preserves the register-absorption feature and the cached
control, with their independent behavioral parity already checked separately.

The [setup report](../../experiments/python-gamebub-v104/native/20261107T230358177941Z/reports/synth-setup-paths.rpt)
reports WNS **−11.624 ns**, **0.557 ns better in synthesis slack** than V102,
and TNS **−48,482.098 ns**. The worst reported path is admission
`tile_reg[4]` → `active_cell_reg[203]/D`, **29 logic levels** (15 CARRY4 and
one DSP48E1), **21.584-ns estimated data delay** (11.527-ns logic plus
10.057-ns estimated routing). The 10-ns target remains unmet; the final routed comparison below
does not demonstrate a setup improvement over V102.

## Physical A/B matrix

| Routed component source | Total LUT | LUT RAM | FF | RAMB36 | DSP | Setup WNS (ns) | Hold WHS (ns) | Routable / fully routed / errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Retained V102 control | 48,522 | 2,718 | 34,795 | 32 | 28 | −13.976 | +0.095 | 72,867 / 72,867 / 0 |
| V104 cached control only | 47,588 | 2,718 | 34,730 | 32 | 28 | −14.750 | +0.067 | 71,894 / 71,894 / 0 |
| V104 combined | 48,868 | 2,728 | 34,766 | 32 | 29 | −13.978 | +0.098 | 73,363 / 73,363 / 0 |

The [control-only terminal receipt](../../experiments/python-gamebub-v104/native/20261107T225623415653Z/receipt.json)
records successful synthesis, placement and route completion with exit code 0.
Its [route-status report](../../experiments/python-gamebub-v104/native/20261107T225623415653Z/reports/route-status.rpt)
counts **71,894 routable nets, all fully routed, zero routing errors**.
The [routed utilization](../../experiments/python-gamebub-v104/native/20261107T225623415653Z/reports/route-utilization.rpt)
uses **47,588 LUTs**, **2,718 LUT RAMs**, **34,730 FFs**, **32 RAMB36** and
**28 DSPs**. That is **934 fewer LUTs (1.92%)** and 65 fewer FFs than routed
V102, with unchanged RAM/DSP totals.

However, its [Design Timing Summary](../../experiments/python-gamebub-v104/native/20261107T225623415653Z/reports/route-timing-summary.rpt)
reports WNS **−14.750 ns**, **0.774 ns worse** than V102's −13.976 ns.
TNS is **−268,076.219 ns**, with 71,291 failing setup endpoints out of
107,932, hold WHS **+0.067 ns** and pulse-width slack **+3.750 ns**.
The smaller registered-control source does not demonstrate a routed setup
improvement in this run. That observation is not a multi-seed robustness or
hardware-latency measurement.

Its [worst routed path](../../experiments/python-gamebub-v104/native/20261107T225623415653Z/reports/route-setup-paths.rpt)
remains admission `tile_reg[2]` → `active_cell_reg[451]/D`, with **30 logic
levels**, including 16 CARRY4 and one DSP48E1, **24.747-ns data delay**
(11.455-ns logic plus 13.292-ns routing). Dequantizer and inverse-transform
DSP register counts/configurations stay identical to V102 through synthesis,
placement and route in this control-only source. Its route DRC reports **93
warnings**: one CFGBVS, 51 DPIP-1, 27 DPOP-1, 13 DPOP-2 and one RTSTAT-10.

Placement also completed and is recorded separately:

| Placed source | Total LUT | LUT RAM | FF | RAMB36 | DSP | Setup WNS (ns) | Hold WHS (ns) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Retained V102 control | 48,522 | 2,718 | 34,795 | 32 | 28 | −12.979 | +0.113 |
| V104 cached control only | 47,588 | 2,718 | 34,730 | 32 | 28 | −13.629 | +0.129 |
| V104 combined | 48,868 | 2,728 | 34,766 | 32 | 29 | −13.206 | +0.113 |

Control-only placement's worst path is admission `tile_reg[0]_rep` →
`active_cell_reg[261]/D`, 31 levels including 16 CARRY4 and one DSP48E1,
23.576-ns estimated data delay (11.741-ns logic plus 11.835-ns estimated
routing). Its placed setup slack is 0.650 ns worse than V102's matched place
stage. Compare each candidate at matching stages; zero routing errors do not
close timing or waive methodology findings. Final selection must use recorded
physical criteria, rather than product-register count or source expression
length. The final combined outcome follows below.

Combined placement's worst path is admission `tile_reg[2]` →
`active_cell_reg[705]/D`, 31 levels including 17 CARRY4 and one DSP48E1,
23.153-ns estimated data delay (11.413-ns logic plus 11.740-ns estimated
routing). Its placed WNS is 0.227 ns worse than V102's place stage. The eight
dequantizer PREG=1 configurations and seventeen inverse-transform MREG=1
configurations persist in the placement ledger; its placement DRC reports
87 warnings in the same CFGBVS/DPIP/DPOP categories as DSP-only synthesis.

## Combined route and next-study decision

The [combined terminal receipt](../../experiments/python-gamebub-v104/native/20261107T230358177941Z/receipt.json)
records successful full implementation with exit code 0. Its
[route-status report](../../experiments/python-gamebub-v104/native/20261107T230358177941Z/reports/route-status.rpt)
counts **73,363 routable nets, all fully routed, zero routing errors**.
The [routed utilization](../../experiments/python-gamebub-v104/native/20261107T230358177941Z/reports/route-utilization.rpt)
uses **48,868 LUTs**, **2,728 LUT RAMs**, **34,766 FFs**, **32 RAMB36** and
**29 DSPs**. Relative to routed V102, this adds **346 LUTs (0.71%)**,
ten LUT RAMs and one DSP, with 29 fewer FFs and unchanged BRAM. The exact
part capacity is sufficient for this component; extra pipeline state is not
rejected merely because it costs resources, and those costs are retained.

The [Design Timing Summary](../../experiments/python-gamebub-v104/native/20261107T230358177941Z/reports/route-timing-summary.rpt)
reports WNS **−13.978 ns**, TNS **−258,181.734 ns**, 67,859 failing setup
endpoints out of 108,457, hold WHS **+0.098 ns**, and pulse-width slack
**+3.750 ns**. Its WNS is **0.002 ns (2 ps) below** V102's −13.976 ns at
the reports' printed precision. Treat this as essentially tied in this
single physical comparison, not evidence of a robust regression or speedup.
No multi-seed implementation or hardware timing measurement was performed.
It does not meet the predeclared strict routed-slack-improvement gate or the
100-MHz target.

The [worst routed path](../../experiments/python-gamebub-v104/native/20261107T230358177941Z/reports/route-setup-paths.rpt)
is admission `tile_reg[5]` → `active_cell_reg[747]/D`, **29 logic levels**
(15 CARRY4 and one DSP48E1), with **23.925-ns data delay** (11.497-ns logic
plus 12.428-ns routing). Admission's original geometry/active-cell write
logic still limits the reported path. The route DRC reports **88 warnings**:
one CFGBVS, 53 DPIP-1, 21 DPOP-1, 12 DPOP-2 and one RTSTAT-10. None is
silently waived by the zero-routing-error result.

The [routed DSP ledger](../../experiments/python-gamebub-v104/native/20261107T230358177941Z/reports/route-dsp-registers.tsv)
confirms that all eight dequantizer DSPs retain `PREG=1`, with
AREG/BREG/MREG=0, through the entire implementation. The inverse subtree
retains seventeen MREG=1/PREG=0 instances, and coefficient-side configurations
remain unchanged. Thus **DSP product-register absorption is demonstrated**
without added public cycles, while a whole-component routed timing gain is
not demonstrated. Those are separate results.

The [recorded selection](../../experiments/python-gamebub-v104/selection.json)
therefore **retains V102** as the next-study source baseline. V104's
predeclared rule allows extra resource cost when the exact target fits; it
requires completed error-free routing, no unclocked/unconstrained internal
endpoints, nonnegative hold/pulse slack, exact workload-cycle parity and
strictly better routed setup WNS. It prefers highest WNS, then lower LUT/DSP
use. Neither routed V104 candidate satisfies the setup-improvement condition.
This is a research source choice, not production-image or hardware promotion.

All three native attempts are terminal with exit code 0: DSP-only synthesis,
control-only full implementation and combined full implementation. The
registered products, cached geometry, their exact parity evidence and the
negative/near-tied physical outcomes remain reproducible experiments. Future
timing work should address the measured admission cone with explicit
state/owner proofs, rather than infer a global speedup from local register
absorption or fewer arithmetic expressions.

## Qualification boundary

All measurements describe the single-clock `cs88_pipeline_v91k` component,
not the complete decoder/board top. Actual HUD/C2/frame-seal checks,
shared-memory/display ownership, transport/CDC and board clock/I/O contracts
remain separate integration work. OOC boundary pin locations and parent
clock-buffer location/skew are not supplied by this component flow. Missing
`HD.PARTPIN_LOCS`, `HD.CLK_SRC` and real I/O delays remain explicit obligations;
no invented location, false path or warning waiver closes them.

Both full native logs retain `Route 35-198` for missing `HD.PARTPIN_LOCS`.
Each explicitly suppresses further messages after **100 emitted occurrences**;
this is a message cap, not a total affected-port count. Both also retain
`Timing 38-242`: absent `HD.CLK_SRC` prevents estimation of the actual parent
clock-buffer delay/skew. Even internal register-path STA therefore retains
an abstract parent-clock assumption. Design Timing Summary rows supply the
aggregate values above, while detailed native reports are retained unchanged.

Native DRC/methodology reports may be enumeration-limited and OOC checks do
not cover every parent connection. Keep reported warnings and counts as
observed evidence, not proof that every possible issue was exhaustively
checked. A route-success marker does not qualify board timing, complete
validated decoder latency, sustained hardware 30 fps or under-10-ms hardware
decoding. No achieved Fmax is derived from negative slack or abstract parent
clock assumptions. Native jobs retain their inputs, actual exit status,
reports and external checkpoint hashes independently of these conclusions.
