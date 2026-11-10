# V125 component timing results

**125 MHz setup still fails.** Fresh V125 routing finishes with WNS **−1.224 ns**, TNS **−2209.865 ns** and **8027 failing setup endpoints**. Against the actual V124 baseline, WNS worsens by 0.054 ns while TNS improves by 317.750 ns and failing endpoints decrease by 1760. The tile-to-tile target improves, but other residuals determine the global result. These measurements do not qualify V125 for hardware integration or a complete-parent clock.

The [native receipt](../../experiments/python-gamebub-v125/native/20261110T065004239267Z/receipt.json) is `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`. The [frozen independent terminal audit](../../experiments/python-gamebub-v125/audit/native-independent.json) passes 1291 integrity checks with zero failed checks/errors; `design_timing_pass` is false. It independently rehashes source/proof/retained/external artifacts and parses timing, clock coverage, routing, methodology and EDIF inventories using host Python 3.14 Zstd support. Integrity PASS is separate from design timing PASS.

| Evidence | SHA256 |
| --- | --- |
| Admission source | `2f65ff770775404071e383890c75549ccb08ec9998993c86f1662cfed65d71eb` |
| Native receipt | `67ac131ffd3aff5365217d5a2f2b362dd4373e5abd5174a0ba8240e5dfada115` |
| Independent terminal audit | `b1765cd1368e0018b0d0f526cf2ff93633cffad20864dc8b74a93a7f3bce80ce` |
| Tile observations | `f5d1ccfbeed2e55920f2e623bd5e28424915af12f20f697b1fc5fd41ed947d08` |
| Candidate tile query | `3322a13720b60eb24d48c7535cc82f264e2d77a34aac2a0b21f463708a6c3950` |
| V124 matched tile query | `71812ab8bcc8952cb10214eeb39a512dd8be53ca80987a84d6ea7b1697d86895` |
| Producer observations | `5a8a3d00f6d3adde3f78fbe1d85e7033fb60be752c83fb1ae4c914c66bb332d5` |

The identical terminal audit is retained at [attempt20261110T072033282453Z](../../experiments/python-gamebub-v125/audit/native-independent-attempts/20261110T072033282453Z.json). The [functional v2 audit](../../experiments/python-gamebub-v125/audit/full-independent-v2.json) remains PASS with SHA `61c343b82cc12604e989380ffe415820e09ad0dfd5cfd71b7ebb91c7e5cf6a75`, and its [read-only review](../../experiments/python-gamebub-v125/audit/functional-v2-review.json) remains SHA `4ba46a73552928e62d22349005f4310d75329fd04fccd36d71b5a4c8d8faca79`. This separately preserved Root prelaunch gate is distinct from the native source-contract proof pins. The original failed auditor, approved single-hunk correction and all passing RTL receipts remain unchanged.

## Global timing and resources

The original Vivado 2026.1 flow, xc7a100tcsg324-1 part, default synthesis, `place_design -directive ExtraNetDelay_high` and `route_design -directive Default` recipe and 8.000 ns component clock remain fixed. The clock is loaded before fresh RTL synthesis. No RTL, constraint, synthesis attribute, placement directive or timing exception was added after the proof freeze. No same-source negative reroute is used.

| Component run | WNS ns | TNS ns | Setup failures |
| --- | ---: | ---: | ---: |
| V121 historical125 | -1.347 | -3248.192 | 9407 |
| V122 historical125 | -1.949 | -4597.575 | 11866 |
| V123 historical125 | -1.086 | -1709.649 | 6724 |
| V124 primary125 | -1.170 | -2527.615 | 9787 |
| V125 candidate125 | -1.224 | -2209.865 | 8027 |

V123 remains historically better than V125: candidate WNS is 0.138ns worse, TNS is 500.216ns more negative and 1303 additional setup endpoints fail. The qualified Source B100 initial/repeat controls remain separate: both have WNS +0.174 ns / TNS 0/no setup failures. Historical B125 and V121–V124125 results remain diagnostics; they do not replace that qualified hardware-integration control.

Hold WHS is +0.052ns with THS0 and zero failures; pulse WPWS is +2.750ns with TPWS0 and zero failures. Setup and hold each examine 103807 endpoints; pulse checks examine 43855. All 73516 routable nets are routed, with zero routing errors. Internal no-clock, multiple-clock, constant-clock, generated-clock, pulse-clock, loop, latch-loop and unconstrained-endpoint counts are zero. External I/O remains unqualified: 1101 inputs lack input delays and 12884 outputs lack output delays. These are retained out-of-context limitations; no guessed external delays or waivers were added.

The worst path is `coefficients/tile_cursor_reg[0]/C` → `coefficients/producer_cell_cache_reg[10]/D`, an unchanged producer cone. Data delay is 9.171ns: 2.204ns logic and 6.967ns routing (75.968% routing), with eight logic levels (three CARRY4 and five LUT6). Same declared family does not guarantee identical physical endpoints between runs.

| Routed resource | V124 | V125 | Delta |
| --- | ---: | ---: | ---: |
| Total LUTs | 33424 | 33431 | +7 |
| Logic LUTs | 33195 | 33202 | +7 |
| FFs | 43494 | 43319 | −175 |
| CARRY4 | 4220 | 4223 | +3 |
| LUTRAMs / SRLs | 137 / 92 | 137 / 92 | 0 / 0 |
| RAMB36 / RAMB18 | 32 / 12 | 32 / 12 | 0 / 0 |
| DSP blocks | 42 | 42 | 0 |
| Control sets, synth / route | 1250 / 1252 | 1250 / 1252 | 0 / 0 |

V125 synthesis reports 33372 total LUTs, 43164 FFs and 4226 CARRY4 cells. Each new scalar (`prepared_tile_hidden`, `prepared_tile_terminal`, `prepared_group_terminal`) maps to exactly one FD in both synthesis and routing. No tile/group verification-owner FF names appear in either EDIF inventory. Whole-admission physical FF totals are 6750 synthesis / 6751 routed versus V124 6728 / 6729: **+22 physical FFs**, despite only three added source payload bits. Whole-design FFs decrease by 175. Those different inventory scopes must not be conflated. Producer-local routed FFs are 585 versus V124 594; scratch rank retains 63 mapped threshold bits and the queue retains 32 prepared-address and 32 issued FFs, with offset 0. Netlist optimization/replication counts are diagnostic; they do not prove semantic narrowing or isolate an RTL cause.

The unchanged V124 producer retains one source KEEP attribute on `logic [1:0] tile_owner_match` (two combinational bits). Admission attributes added/removed are both empty. Observed routed KEEP properties are blank; no KEEP=TRUE or physical-isolation claim follows from the source hint or named-net inventory.

## Matched tile and register-edge observations

Independent read-only review rehashed the candidate query receipt (`3322a137…`), all 115 query artifacts, its native receipt and routed DCP SHA `974937caf0b82cc61722a5e4460d81fae7aca1e035ae43f28042db8e2b85b0b4`. It also checked the V124 query receipt, all 86 artifacts and its unchanged DCP. TSV minima were independently matched to the Slack values in each corresponding path report, and every observation/delta was rebuilt. The comparison contains 115 union families: 77 V124 and 106 V125 returned families, with 70/36 explicit gap records. The same frozen query is used on both checkpoints; these counts include width and absence diagnostics and are not additional timing passes.

| Matched family, ns slack | V124 | V125 | Delta |
| --- | ---: | ---: | ---: |
| Tile → all | -1.170 | -0.464 | +0.706 |
| Tile → tile | -1.170 | +2.447 | +3.617 |
| Tile → coordinates | -1.057 | -0.464 | +0.593 |
| Tile → group_end | +0.558 | +1.899 | +1.341 |
| Tile → state | -0.300 | gap | gap |
| Tile → mode RAM EN/WE | -0.010 | gap | gap |
| Tile → mode RAM data | -0.080 | gap | gap |
| Group_end → all / coordinates | -0.140 | -0.644 | -0.504 |
| Group_end → tile | +0.299 | +4.200 | +3.901 |
| Admission cursor → all | -0.274 | -0.498 | -0.224 |
| Admission plane → all | +0.148 | +0.545 | +0.397 |
| Admission coord_cell → all | -0.185 | +0.111 | +0.296 |

Direct tile→state, tile→mode-RAM EN/WE and tile→mode-RAM data queries return no timed candidate path. These are **query gaps**, not proof that dependencies disappeared or timing passed. Tile→plane and group_end→state/mode-RAM queries also have candidate gaps. Tile→tile improves by 3.617 ns, but tile→coordinates remains−0.464ns and group_end→coordinates worsens to−0.644ns. The admission cursor also remains negative at−0.498ns.

New-register tables distinguish the D capture cone from paths launched by the new register. Here “Q/launch” means the timed launch family selected from that register; Vivado reports its clock pin `/C` as the timing startpoint. The D minimum is the minimum among the declared incoming families actually queried, not an exhaustive all-startpoint claim.

| New scalar | Tile → D | Plane → D | Group_end → D | Worst queried incoming D | Q/launch → all |
| --- | ---: | ---: | ---: | ---: | ---: |
| `prepared_tile_hidden` | -0.191 | +1.813 | +1.675 | -0.191 | +0.182 |
| `prepared_tile_terminal` | +1.235 | +1.357 | +2.580 | +1.235 | +0.360 |
| `prepared_group_terminal` | +0.954 | gap | +1.959 | +0.954 | +0.343 |

The hidden-predicate D path remains−0.191ns (`tile_reg[2]/C`→`prepared_tile_hidden_reg/D`), with 11 logic levels and 8.136 ns data. The corresponding terminal/group-terminal D minima are+1.235/+0.954ns. Group-end input minima are positive (+1.675/+2.580/+1.959ns for hidden/tile-terminal/group-terminal), consistent with measuring the registered predecessor separately from the later tag capture; these observations do not establish universal cone isolation.

| New Q/launch family | State | Tile | Coordinates | Mode RAM EN/WE | Mode RAM data |
| --- | ---: | ---: | ---: | ---: | ---: |
| `prepared_tile_hidden` | +3.043 | +2.490 | +1.448 | +2.566 | +3.103 |
| `prepared_tile_terminal` | +1.743 | +2.050 | +1.007 | +1.320 | +2.726 |
| `prepared_group_terminal` | +3.066 | +3.349 | +2.307 | +2.049 | +3.327 |

Admission tile retains all 32 unique named bits in 33 physical cells; plane retains 2 bits/cells and group_end retains 32 bits/cells. Each scalar has one named bit/cell. No generic full32 contract is replaced with a reachable-coordinate bound.

## Remaining scratch, owner and refill families

| Same-query family, all endpoints | V124 | V125 | Delta |
| --- | ---: | ---: | ---: |
| `emit_bank` | -0.972 | -1.219 | -0.247 |
| `expected_block` | -0.860 | -0.981 | -0.121 |
| `current_child_epoch` | -0.798 | -0.970 | -0.172 |
| `raw_mode` | -1.143 | -0.855 | +0.288 |
| `raw_position` | -1.016 | -0.730 | +0.286 |
| `rank_threshold_mask` | -0.382 | -0.193 | +0.189 |
| `bank_ready` | +0.994 | +1.112 | +0.118 |
| `refill_issued` | +0.455 | +0.624 | +0.169 |
| `refill_prepared_req_addr` | -0.059 | +0.190 | +0.249 |

The near-global emit-bank residual is−1.219ns versus the producer’s global−1.224ns. The refill prepared-address→admission-RAM-enable subset is now+0.190ns, but raw mode, raw position, rank and owner families remain negative. A positive selected subset does not close the component.

## Supplemental producer observations

The [completed producer observations](../../experiments/python-gamebub-v125/producer-observations.json) bind a second read-only comparison on the same unchanged producer RTL. Independent review rehashed both query receipts, 22 artifacts each, both native/DCP pins, 13 returned families and five gap records per checkpoint. Every reported minimum and delta matches its TSV and timing report. No new implementation is performed.

| Producer family, ns slack | V124 | V125 | Delta |
| --- | ---: | ---: | ---: |
| Tile cursor → all | -0.689 | -1.224 | -0.535 |
| Tile cursor → cell cache | -0.511 | -1.224 | -0.713 |
| Tile cursor → tile cursor | +1.340 | +1.665 | +0.325 |
| Tile cursor → state | +1.998 | +1.299 | -0.699 |
| State → all | -0.602 | -0.881 | -0.279 |
| State → cell cache | -0.479 | -0.323 | +0.156 |
| State → state | -0.602 | +0.063 | +0.665 |
| State → tile cursor | -0.386 | -0.389 | -0.003 |
| Plane → all | -0.585 | -0.474 | +0.111 |
| Plane → cell cache | -0.436 | +0.864 | +1.300 |
| Plane → tile cursor | -0.343 | +0.798 | +1.141 |
| Plane → state | +0.507 | +0.092 | -0.415 |
| Cell cache → all | +1.104 | +1.273 | +0.169 |

Producer tile cursor has 13 declared/unique named bits but 36 V124 and 32 V125 physical cells. Cell cache has 11 declared/named/physical cells and plane 2. State is declared 8 bits but maps to five unique named/physical bits in both checkpoints, with indices 5–7 explicitly unmatched. These width differences are recorded gaps requiring interpretation of constants, replication, encoding and renaming; they are not source-contract changes. Cell-cache→cell-cache/tile-cursor/state queries return no timed paths and remain gaps. The producer source is byte-identical between V124 and V125; the changed physical results are not a semantic-delta or isolated-RTL-causality claim.

## Methodology and qualification limits

Fresh route methodology counts are SYNTH-6=28, TIMING-16=76, TIMING-18=1000 and ULMTCS-1=1. V124 has 28/33/1000/1, so large-setup TIMING-16 increases by 43 despite the lower total failing-endpoint count. V123 has only two TIMING-16 records; V122 has 800 and historical B125 has 355 remain diagnostics. Fresh methodology reports determine these counts; cached timing-summary counts are not used for signoff. TIMING-18’s reported count does not replace the explicit 1101/12884 missing external I/O-delay counts. No warning is waived and no constraint is guessed.

The original full functional, actual V97 transport, peer and guarded byte/row parent oracles remain exact to V124, including event/hash cycles and public delta 0; see [functional results](functional-results.md). Their byte/row service and accepted-last-input latency measurements remain abstract fixtures. At an assumed complete-parent 125 MHz, row fast/stalled counts still project to 9.160832/12.425576 ms; the complete-parent 125 MHz clock is not physically qualified. These results establish neither board-level I/O/CDC closure, ESP32 CPU/Wi-Fi/QSPI service, physical memory calibration, sustained distinct-frame hardware 30 fps nor validated end-to-end/hardware decode below 10 ms. Qualified Source B100 remains the hardware-integration control.
