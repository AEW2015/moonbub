# V003 physical CE replication result

**FAIL timing; do not select.** The passing V001/V028 image is preserved. This isolated post-place experiment completed normally and produced all reports, but positive hold/pulse and complete routing do not overcome negative setup slack.

| Gate | Final V003 |
|---|---:|
| Setup WNS / TNS | -0.197 / -9.204 ns |
| Failing setup endpoints | 105 |
| Hold WHS / THS | +0.021 / 0 ns |
| Pulse WPWS / TPWS | +2.000 / 0 ns |
| Routed / routable nets | 56,569 / 56,569 |
| Routing errors | 0 |
| DRC | 230 warnings; no errors |
| CDC | Two inherited CDC-1 critical paths; unresolved by this experiment |
| Internal unconstrained endpoints / missing clocks / loops | 0 / 0 / 0 |
| Tool exit / report completion | 0 / complete |

Final worst path is control_plane/command_state_reg[2]_rep ? system_core/receiver/bank_generation_reg[2][29]/CE: 9.939 ns data, 12 logic levels, 73.799% routing. This differs from V001's +0.005 ns HUD-generation-to-ticket CE path. The targeted ticket CE is not represented in the saved worst-50 report, so its final slack is unknown here; do not infer a measured endpoint gain merely because the worst family changed.

The exact post-place CE query found control_plane/E[0], driven by LUT4 hud_bank[1]_i_1, INIT0001, 324 loads. Forced replication was accepted in this stage and created seven LUT4 replicas. Original plus replica fanouts were 3,12,8,12,25,235,21,8 (sum324). The largest branch remained235. Baseline-identical full route, AggressiveExplore and cleanup then ran. The resulting whole design regressed despite that local fanout reduction.

Intermediate values are retained, not final qualifications: post-place targeted CE -0.381 ns; post-replication global estimate -0.889 ns; first routed result -0.634 ns. Physopt and cleanup improved to the final -0.197 ns, which still fails. The separate V002 post-route option rejection was a tool-stage limitation, not this experiment's final timing result.

All79 V001 source inputs and the baseline placed/routed checkpoints were rechecked unchanged. No RTL/XDC/clock/pin/exception edit, BIT generation, hardware or new reset was used. The candidate checkpoints are retained for replay, while V001 remains selected. Runtime was2676.094 seconds (44.6 minutes). Full source/command/report/checkpoint hashes are in result.json.
