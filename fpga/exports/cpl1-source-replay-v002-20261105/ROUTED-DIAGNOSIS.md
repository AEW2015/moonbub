# Fixed-clock routed diagnosis

Evidence is `build/board01/setup-paths.rpt` (30 worst paths), `timing-summary.rpt`, and the immutable source freeze. This is a diagnosis of this exact route, not an exhaustive endpoint-family census. All setup failures are in raw100. No new reroute, exception, I/O relaxation or clock change was used.

| Family / worst actual start → end | Slack | Data delay / levels | Evidence and smallest next isolated experiment |
|---|---:|---|---|
| Gather `column_reg[5]/C` → `held_request_address_reg[16]/D` | −1.618 ns | 11.722 ns = 7.691 logic + 4.031 route; 10 levels, 2 DSP + 3 CARRY4 | `parents/ar03_yuv_line_gather.sv:145` computes `Y_BASE+column*240`; chroma reloads use `col*120` at 97/128. Full mapped path is retained. Test registered/incremental per-plane column bases with unchanged owned request address/identity and native deadline tests; do not simply retime ownership without a reservation. |
| HUD `hud_address5/CLK` → `hud_ram_reg_0_1/ADDRBWRADDR[4]` | −1.618 ns | 10.833 ns = 7.281 logic + 3.552 route; 3 levels, DSP/LUT3/LUT5 | `cp23_key_composite_scanout_local.sv:160` performs ROI-selected `(base_y-origin)*stride+base_x-origin`; line167 consumes synchronous HUD RAM. This is a DSP-output-to-RAM-address path, not a full same-cycle pixel multiplication path. Test a registered ROI-local address stage or incremental row bases with the exact extra base/HUD/hit/coordinate delay; compare all pixels and CRC, including rectangle edges. |
| Identity/cancel/transpose/control `key/epoch_reg[0]_rep__0/C` → `memory/controller/state_reg[2]/D` | −1.594 ns | 11.620 ns = 4.472 logic + 7.148 route; 18 levels, 7 CARRY4 + RAMD32 | Actual netlist runs through `base/raster/...CO`, `hud_stage_fault`, `word_captured`, transpose `cancel_active`, packer address arbitration, controller row-table lookup. Source fanout88 at the epoch register net, downstream source path includes fanout24 and15. This is an identity/fault/control cone; source-level naming alone does not isolate one Boolean cause. Preserve immediate ingress cancel masking and accepted physical-drain obligations in any staged-control experiment. |

An important related path is **epoch → HUD SHA block register CE**, −1.518 ns, 11.329 ns data (3.067 logic / **8.262 route**), 14 levels. Its actual cone includes five CARRY4 equality stages, `outer/base_sha/child_abort` (fanout25), HUD `cancel_children` (13), count-derived control (195), and the block-write enable net (123). It does **not** traverse SHA compression-round arithmetic. The measured evidence favors isolating registered cancellation/owner-validation and a local SHA byte/block-write admission stage before changing SHA rounds. The global-reset→transpose DSP CE path also appears at −1.516 ns, predominantly route (9.020/11.160 ns), so an optimization that fixes only one SHA endpoint cannot establish whole-board timing.

The 30-path sample is already source-bound in `routed-paths.json`; each entry retains the entire actual clock/data/fanout trace. It must not be reported as a complete classification of all 13,015 failing endpoints. More comprehensive endpoint/path-group coverage would be a separate bounded checkpoint-query gate.

## Preserved external and related-clock checks

The exact retained constraints produce these routed groups:

| Group | Setup / hold slack (ns) |
|---|---:|
| Pixel `praw` → LCD forwarded output | +5.313 / +16.633 |
| Core100 → SDRAM forwarded outputs | +0.352 / +2.588 |
| SDRAM forwarded clock → 279° capture | +0.145 / +0.287 |
| 279° capture → core100 | +4.327 / +2.881 |
| Core200 local | +0.113 / +0.045 |

These groups meet their *declared* budgets; they do not repair raw100 setup failure. All 16 SDRAM DQ capture endpoints use the existing previous-beat setup treatment; no hold multicycle was introduced. No combinational or latch loops, missing clocks, multiple clocks or unconstrained internal endpoints are reported. The CDC report still contains bundled-data/enable warnings requiring protocol evidence; it is not a blanket CDC signoff. The 17 no-input-delay ports, partial CS constraint, and forwarded-clock output checks remain explicitly recorded. QSPI external hold/board skew, clock analog behavior, and warm-reset RAM retention remain unqualified.

Next useful development is a separately source-bound address/control staging experiment with whole native + negative lifecycle equivalence and a fresh fixed-clock board implementation. The failed current route remains intact as its A/B baseline. No first-fixture hardware loading is justified by the present timing result.
