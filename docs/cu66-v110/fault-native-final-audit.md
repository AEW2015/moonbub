# Fault native route audit

The V110 fault native route completed at fixed 10 ns on `xc7a100tcsg324-1` with Vivado 2026.1. Receipt SHA256: `176929cfd3d73950f3a07d2a7605cf577dac59bd0de6f98e17288e1948fcda15`. Status: `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`. Timing **fails** the 100 MHz component gate: WNS -2.578 ns, TNS -8838.627 ns, and 13,862/87,829 setup endpoints fail. Hold slack is +0.086 ns with zero failures; pulse slack is +3.750 ns with zero failures. All 65,293 routable nets routed with zero errors.

Worst routed path: `coefficients/child/scratch/read_segment_reg[1]/C` → `coefficients/child/scratch/state_reg[3]/D`, 12.463 ns across 15 logic levels. 15 logic levels; route delay is 9.453 ns (75.849% of data delay). A combinational path net with fanout 135 adds 1.267 ns; the `read_segment` source net has fanout 29 and adds 0.681 ns.

I checked dispatch, preflight and policy pins; 18 source snapshots; all recipe copies; the parent clock/checkpoint; and 98 local retained files plus 72 external run artifacts. The effective XDC keeps `component_clk` at 10 ns and adds no false-path, multicycle, clock-group or I/O-delay exceptions.

This is an OOC component result. Full-parent timing, board I/O, hardware 30 fps, and complete validated decode below 10 ms remain open. Machine-readable audit: [`fault-native-final.json`](../../experiments/python-gamebub-v110/audit/fault-native-final.json).
