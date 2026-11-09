# V115 initial native terminal audit

The two frozen initial native component runs both completed place and route, but both **fail their internal setup target**. Their non-setup checks are clean: zero hold failures, zero pulse-width failures, zero routing errors, all routable nets routed, and zero unconstrained internal endpoints. This is not a timing signoff or board qualification. The audit pins the existing receipts, snapshots, route reports, and cards in [initial-native-terminal.json](../../experiments/python-gamebub-v115/audit/initial-native-terminal.json); it did not rerun either flow.

| Target | Setup result | Worst routed path | Other gate counts |
| --- | --- | --- | --- |
| 100 MHz / 10 ns | WNS −0.645 ns; 481 / 98,027 setup endpoints fail | `synchronous.ingress/fetch_bytes_reg[27][0]/C` → `synchronous.ingress/state_reg[0]/D` | Hold 0 / 98,027; pulse 0 / 41,134; routing errors 0 |
| 125 MHz / 8 ns | WNS −2.688 ns; 33,790 / 97,932 setup endpoints fail | `scratch/read_band_reg[0]/C` → `scratch/tile_reg[1][62][0]/R` | Hold 0 / 97,932; pulse 0 / 41,187; routing errors 0 |

Both runs loaded the period constraint before synthesis, used `synth_design -top cs88_pipeline_v91k -part xc7a100tcsg324-1 -mode out_of_context -flatten_hierarchy rebuilt`, the default synthesis/place/route directives, and no checkpoint. Their identical frozen input snapshots contain the same 18 source-origin aliases and SHA-256 pins. The flow and constraints matched the reviewed V115 recipe. Each used the same content-addressed tool image, 2 CPUs, 8 GiB memory and swap limits, and a 3,600-second timeout. The sampled full PSI average was zero; peak combined memory usage remained below 0.60.

Neither run contacted hardware or generated a bitstream. `check_timing` reports no missing clocks and no unconstrained internal endpoints, while 1,101 input endpoints and roughly 12.9k output endpoints have no I/O delay. Both status values remain `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`; setup failure keeps the targets open. The routed top-50 setup-path reports contain no `owner_sequence` endpoint, which supports the refined ingress and scratch focus recorded in [native-refined-draft.md](native-refined-draft.md).
