# Prefix native route audit

The V110 prefix native route completed at fixed 10 ns on `xc7a100tcsg324-1` with Vivado 2026.1. Receipt SHA256: `8ea9df6dcf6e42438be10dd41507a1693cf0903fe3a65102d36df57107e02c6b`. Status: `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`. Timing **fails** the 100 MHz component gate: WNS -1.654 ns, TNS -3716.410 ns, and 8,328/89,709 setup endpoints fail. Hold slack is +0.086 ns with zero failures; pulse slack is +3.750 ns with zero failures. All 66,412 routable nets routed with zero errors.

Worst routed path: `coefficients/child/scratch/read_segment_reg[1]/C` → `coefficients/child/scratch/cursors_reg[1][29]/R`, 11.140 ns across 14 logic levels. 14 logic levels; route delay is 7.901 ns (70.926% of data delay). The critical path includes a fanout-106 net with 0.785 ns delay, then cursor logic nets with fanout 33/32 and 0.301/0.922 ns delays. The old Rice `cached_remaining[5]` quotient path does not appear in the routed top-50 setup report.

I checked dispatch, preflight and policy pins; 18 source snapshots; all recipe copies; the parent clock/checkpoint; and 98 local retained files plus 72 external run artifacts. The effective XDC keeps `component_clk` at 10 ns and adds no false-path, multicycle, clock-group or I/O-delay exceptions.

Across the five new V110 native routes, this prefix composition has the best WNS at -1.654 ns; all five remain negative and none has a clean positive repeat.

This is an OOC component result. Full-parent timing, board I/O, hardware 30 fps, and complete validated decode below 10 ms remain open. Machine-readable audit: [`prefix-native-final.json`](../../experiments/python-gamebub-v110/audit/prefix-native-final.json).
