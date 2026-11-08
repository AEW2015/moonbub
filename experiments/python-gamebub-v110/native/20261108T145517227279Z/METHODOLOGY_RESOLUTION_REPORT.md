# V110 methodology resolution report

Trial `v110-fault-initial`, mode `rtl`; part `xc7a100tcsg324-1`.
Directives: `{'opt': 'Default', 'phys_opt': None, 'phys_opt_stage': None, 'place': 'ExtraNetDelay_high', 'route': 'Default'}`. Status: `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`.

## Clock and constraints

The component target remains 100 MHz / 10.000 ns. No clock, I/O, false/multicycle or waiver change was made.

| Aspect | Constraint | Period | Waveform | Clock Definition Object |
| --- | --- | --- | --- | --- |
| Before | `create_clock -name component_clk -period 10.000 [get_ports clk]` | 10.000 ns | {0.000 5.000} | component_clk |
| After | `create_clock -name component_clk -period 10.000 [get_ports clk]` | 10.000 ns | {0.000 5.000} | component_clk |

Source: `component.xdc` in this build; actual before/after effective constraints and native clock reports are retained in `results/`. No constraint diff is applicable because constraints were not modified.

## Actual native findings

| Rule | Severity | Listed checks | Resolution/scope |
| --- | --- | ---: | --- |
|SYNTH-6|Warning|39|RAM output-register finding: inspect the actual endpoint/latency contract; no blind output-register insertion.|
|TIMING-16|Warning|1000|Operational control/architecture; setup must pass the fixed clock. No waiver.|
|TIMING-18|Warning|1000|OOC boundary lacks board I/O contracts. Full-parent constraints remain required; no invented delays.|
|ULMTCS-1|Warning|1|Control-set locality/ownership work remains; do not remove functional resets.|

Listed methodology entries are not the count of failing setup endpoints; the native timing summary below is authoritative. Raw methodology/DRC, I/O, CDC, high-fanout, control-set and local-predicate mapping reports remain available.

Measured timing: {"THS_ns": 0.0, "TNS_ns": -8838.627, "TPWS_ns": 0.0, "WHS_ns": 0.086, "WNS_ns": -2.578, "WPWS_ns": 3.75, "hold_failing": 0, "hold_total": 87829, "pulse_failing": 0, "pulse_total": 35906, "setup_failing": 13862, "setup_total": 87829}

Internal component 100 MHz: False.
Setup remains unresolved; positive hold/pulse alone is insufficient.

## Waivers and remaining actions

No waivers were created. Board clocks/I/O/CDC, finite memory/display/reference/HUD/hash service, calibrated validated publication, hardware 30 fps and complete validated decode below 10 ms remain open. This OOC run does not generate a board bitstream or prove hardware performance.
