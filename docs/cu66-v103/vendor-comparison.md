# V103 native geometry/control comparison

The control is the frozen V102 combined memory/predicate component at commit
`6d2ca3ae9abe207215d6130cfb0087fd07928917`. Each V103 variant preserves its
memory template, public diagnostic visibility, packet cap and source codec
profile, substituting only the explicitly named geometry function. The
comparison uses native Vivado 2026.1 build 6511674, exact part
`xc7a100tcsg324-1`, a 10-ns clock loaded before synthesis, Default directives
and two Vivado threads. Behavioral parity is measured independently.

## Frozen control and experiment matrix

| Variant | Total LUT | LUT RAM | FF | RAMB36 | DSP | Synthesis WNS (ns) | Stage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| V102 combined control | 49,040 | 3,854 | 34,689 | 32 | 28 | −12.181 | Retained native synthesis |
| V103 reconstruction only | 48,675 | 3,854 | 34,720 | 32 | 28 | −11.596 | Native synthesis completed |
| V103 admission only | 48,800 | 3,854 | 34,694 | 32 | 28 | −14.587 | Native synthesis completed; timing regression |
| V103 combined | 48,283 | 3,854 | 34,682 | 32 | 28 | −14.601 | Native full implementation completed |

The [V102 control reports](../cu66-v102/vendor-comparison.md) retain both
synthesis and physical results. The physical control uses **48,522 LUTs,
2,718 LUT RAMs, 34,795 FFs, 32 RAMB36 and 28 DSPs** after routing. All 72,867
routable nets are fully routed with zero reported routing errors; setup
timing fails with **WNS −13.976 ns**, TNS −313,514.625 ns, and hold WHS
+0.095 ns. The worst reported internal path is reconstruction's tile-to-
residual-enable cone, with 29 logic levels and a 23.687-ns data path.

V103 isolates reconstruction's thirteen-bit tile geometry from admission's
32-bit `cell_index` domain. The [admission candidate](admission-results.md)
uses a full unsigned-32-bit algebraic identity rather than truncating tile
state. Source arithmetic is a hypothesis about technology mapping; measured
native resources and path reports determine whether it helps. No area,
clock, latency or FPS gain is inferred from a shorter source expression.

## Isolated reconstruction synthesis

The [reconstruction-only receipt](../../experiments/python-gamebub-v103/native/20261107T215831292808Z/receipt.json)
records successful synthesis-only completion with actual exit code 0. Its
[hierarchical utilization](../../experiments/python-gamebub-v103/native/20261107T215831292808Z/reports/synth-utilization.rpt)
uses **48,675 LUTs**, **3,854 LUT RAMs**, **34,720 FFs**, **32 RAMB36** and
**28 DSPs**. Relative to the V102 control at the same synthesis stage, total
LUTs decrease by **365 (0.74%)**, while FFs increase by 31. BRAM and DSP
counts are unchanged. The whole-component delta includes global optimization
changes; it is not a count of removed cells within one source function.

The [setup report](../../experiments/python-gamebub-v103/native/20261107T215831292808Z/reports/synth-setup-paths.rpt)
reports **WNS −11.596 ns**, an improvement of **0.585 ns in synthesis slack**
against the unchanged V102 −12.181-ns synthesis control. TNS is
−51,556.223 ns. The 10-ns timing target still fails. The worst reported path
is now admission's `tile_reg[2]` → `active_cell_reg[578]/D`, with **29 logic
levels** (15 CARRY4 and one DSP48E1) and a **21.556-ns estimated data path**.
This unplaced result motivates the independent admission experiment; it does
not establish a routed speed or measured decode-latency gain.

The synthesis DRC report retains **92 reported warnings** in CFGBVS/input/DSP
pipeline categories and no reported resource-fit errors. Placement and route
were intentionally not executed for this isolated synthesis measurement.

## Isolated admission: correct arithmetic, negative timing result

The [admission-only receipt](../../experiments/python-gamebub-v103/native/20261107T220719371412Z/receipt.json)
records successful synthesis-only completion with exit code 0. Its native
[utilization](../../experiments/python-gamebub-v103/native/20261107T220719371412Z/reports/synth-utilization.rpt)
uses **48,800 LUTs**, **3,854 LUT RAMs**, **34,694 FFs**, **32 RAMB36** and
**28 DSPs**. Total LUTs decrease by **240 (0.49%)** relative to V102's
49,040-LUT synthesis control, with five additional FFs. This small area change
does not justify promoting the variant for the streaming timing objective.

The [setup report](../../experiments/python-gamebub-v103/native/20261107T220719371412Z/reports/synth-setup-paths.rpt)
reports **WNS −14.587 ns**, **2.406 ns worse** than the matched V102 synthesis
control. TNS is **−70,388.203 ns**. The worst reported path remains in
admission, `tile_reg[2]` → `active_cell_reg[130]/D`, with **33 logic levels**
(18 CARRY4 and one DSP48E1) and a **24.547-ns estimated data path**.
Logic contributes 14.051 ns and estimated routing 10.496 ns. The algebraic
identity is correct in the focused/full-pipeline parity lanes, but this
combinational technology mapping does not improve the measured synthesis
critical path. No pipeline registers were added; there is no basis to infer
that eliminating a source `%` expression shortens the actual carry/multiply
chain.

Keep this exact failed performance hypothesis and its source/report hashes as
research evidence. A future admission timing experiment should explicitly
register/tag geometry state or prove a reachable-state refinement, then
measure latency, stalls, error behavior and routed timing. The current
admission-only variant is not selected merely for its lower LUT count.

## Physical A/B selection

Two root-owned full implementation runs compare the same frozen reconstruction
source alone against the combined source substitutions. There is no extra
RTL rewrite between the reconstruction synthesis and route runs. Both use
the unchanged target and flow settings. Select the next research handoff
from actual physical results and retain all unsuccessful timing outcomes.

| Routed component | Total LUT | LUT RAM | FF | RAMB36 | DSP | Setup WNS (ns) | Hold WHS (ns) | Routable / fully routed / errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| V102 combined control | 48,522 | 2,718 | 34,795 | 32 | 28 | −13.976 | +0.095 | 72,867 / 72,867 / 0 |
| V103 reconstruction only | 48,179 | 2,718 | 34,775 | 32 | 28 | −14.036 | +0.071 | 72,392 / 72,392 / 0 |
| V103 combined | 47,740 | 2,718 | 34,735 | 32 | 28 | −17.586 | +0.079 | 72,075 / 72,075 / 0 |

The [combined terminal receipt](../../experiments/python-gamebub-v103/native/20261107T221602746856Z/receipt.json)
records full synthesis, placement and route completion with exit code 0 and
a written routed checkpoint. Its
[route-status report](../../experiments/python-gamebub-v103/native/20261107T221602746856Z/reports/route-status.rpt)
counts **72,075 routable nets, all fully routed, zero routing errors**.
Compared with routed V102, it uses **782 fewer LUTs (1.61%)** and 60 fewer
FFs, with unchanged LUT RAM/BRAM/DSP totals. However, routed setup WNS is
**−17.586 ns**, **3.610 ns worse** than V102's −13.976 ns. The
[Design Timing Summary](../../experiments/python-gamebub-v103/native/20261107T221602746856Z/reports/route-timing-summary.rpt)
prints TNS **−340,425.750 ns**, 77,673 failing setup endpoints out of 107,928,
hold WHS **+0.079 ns** and pulse-width slack **+3.750 ns**. The combined
candidate restores neither the target setup timing nor an improvement over
the physical control; area alone is insufficient for next-study selection.

Its [worst routed path](../../experiments/python-gamebub-v103/native/20261107T221602746856Z/reports/route-setup-paths.rpt)
is admission's `tile_reg[5]` → `active_cell_reg[723]/D`, with **33 logic
levels** (18 CARRY4 and one DSP48E1), **27.533-ns data delay** split into
13.450-ns logic and 14.083-ns routing. The route DRC reports 92 warnings,
including CFGBVS, DSP pipelining and `RTSTAT-10` no-routable-load findings;
zero route-status errors do not waive those findings.

The full-run synthesis result is also retained: 48,283 LUTs, 3,854 LUT RAMs,
34,682 FFs, 32 RAMB36, 28 DSPs and WNS −14.601 ns. Whole-top synthesis
deltas from separate candidates are not additive because global optimization
changes across hierarchy. This combined source is not promoted on its lower
area or its correct arithmetic/protocol simulation results.

The [reconstruction-only full-run receipt](../../experiments/python-gamebub-v103/native/20261107T221637235051Z/receipt.json)
also records full synthesis, placement and route completion with exit code 0.
Its synthesis repeats the isolated reconstruction result exactly: 48,675
LUTs, 3,854 LUT RAMs, 34,720 FFs, 32 RAMB36, 28 DSPs and WNS −11.596 ns.
The [routed utilization](../../experiments/python-gamebub-v103/native/20261107T221637235051Z/reports/route-utilization.rpt)
is **48,179 LUTs**, **2,718 LUT RAMs**, **34,775 FFs**, **32 RAMB36** and
**28 DSPs**. The [route-status report](../../experiments/python-gamebub-v103/native/20261107T221637235051Z/reports/route-status.rpt)
counts **72,392 routable nets, all fully routed, zero routing errors**.

This saves **343 routed LUTs (0.71%)** and 20 FFs relative to V102, with
unchanged LUT RAM/BRAM/DSP totals. However, the
[Design Timing Summary](../../experiments/python-gamebub-v103/native/20261107T221637235051Z/reports/route-timing-summary.rpt)
reports **WNS −14.036 ns**, **0.060 ns worse** than V102's −13.976 ns;
TNS is **−312,517.000 ns**, hold WHS **+0.071 ns**, and pulse-width slack
**+3.750 ns**. This one matched physical run does not establish a setup-timing
improvement despite the earlier synthesis-slack gain. No multi-seed placement
robustness or hardware speed claim is made from the 60-ps difference.

The [worst routed reconstruction-only path](../../experiments/python-gamebub-v103/native/20261107T221637235051Z/reports/route-setup-paths.rpt)
is now admission's `tile_reg[5]` → `active_cell_reg[68]/D`, with **31 logic
levels** (16 CARRY4 and one DSP48E1), **23.983-ns data delay** split into
11.283-ns logic and 12.700-ns routing. The route DRC reports 93 warnings,
including the same CFGBVS, DSP-pipelining and no-routable-load classes.
The former reconstruction geometry path is no longer the worst reported
path, but admission still limits the completed component's setup result.

Both physical experiments also retain placement-stage evidence:

| Placed component | Total LUT | LUT RAM | FF | RAMB36 | DSP | Setup WNS (ns) | Hold WHS (ns) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| V102 combined control | 48,522 | 2,718 | 34,795 | 32 | 28 | −12.979 | +0.113 |
| V103 reconstruction only | 48,179 | 2,718 | 34,775 | 32 | 28 | −13.144 | +0.139 |
| V103 combined | 47,740 | 2,718 | 34,735 | 32 | 28 | −16.442 | +0.140 |

Placement's worst paths remain admission tile-to-active-cell writes:
reconstruction-only `tile_reg[3]` → `active_cell_reg[1056]/D` has 30 levels
and a 23.141-ns estimated data path; combined `tile_reg[7]` →
`active_cell_reg[723]/D` has 33 levels and a 26.389-ns estimated data path.
These stages were successfully executed, rather than inferred from synthesis
capacity. Placement timing and final routed timing remain separate measures.

The [recorded source selection](../../experiments/python-gamebub-v103/selection.json)
therefore **retains V102 as the next-study baseline**. The rule requires
completed error-free routing, nonnegative hold/pulse slack, no increase in
LUT/weighted-BRAM/DSP totals, and strictly better routed setup WNS than V102.
Among eligible candidates it prefers highest setup WNS, then lowest LUT
count; otherwise it keeps V102. Neither V103 routed candidate meets that
setup-improvement gate. This retains a reproducible result and rejects a
timing regression rather than promoting a source change for its area alone.

All four V103 native attempts are terminal with exit code 0. The source
substitutions and negative results remain available for future isolated work;
source selection is not production-image promotion or hardware qualification.

## Physical and full-system qualification

Synthesis, placement and route metrics must be compared at matching stages.
Successful routing is distinct from setup/hold closure. OOC component reports
do not supply genuine parent boundary pin locations, parent clock-buffer
placement/skew, or external I/O delays. Any missing `HD.PARTPIN_LOCS`,
`HD.CLK_SRC`, clock/I/O contracts and methodology/DRC findings remain explicit;
no invented constraints, relaxed target or warning waiver closes them.

Both full native logs retain `Route 35-198` for unknown `HD.PARTPIN_LOCS`;
the log suppresses further instances after **100 emitted messages**, which
is not an affected-port count. They also retain `Timing 38-242`: missing
`HD.CLK_SRC` prevents actual parent clock-delay/skew estimation. Thus even
internal routed register timing retains an abstract parent-clock assumption;
the missing boundary/clock information is not supplied by a route-success
marker or by positive hold/pulse slack. Aggregate numbers above use the
Design Timing Summary rows; raw detailed report formatting remains intact.

The component is not the complete custom decoder/board top. HUD/C2/frame-seal
checks, shared-memory/display ownership, transport/CDC and real board timing
remain integration work. Behavioral function parity and component timing
measurements do not establish sustained hardware 30 fps or complete validated
FPGA decoding below 10 ms. No achieved Fmax is derived from negative WNS or
from an abstract OOC parent clock.
