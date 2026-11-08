# V111 component methodology report

Trial `header-125`, fresh RTL, `xc7a100tcsg324-1`, target 8.0 ns.

Default synthesis by omission; Default opt/route and ExtraNetDelay_high placement. No retiming or timing exception added.

Actual clocks, before/after XDC, setup/hold/pulse, methodology, DRC, CDC, high-fanout and primitive mapping reports are retained.

Status: `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`. Result: `{"check_timing": {"constant_clock": 0, "generated_clocks": 0, "latch_loops": 0, "loops": 0, "multiple_clock": 0, "no_clock": 0, "no_input_delay": 1101, "no_output_delay": 12885, "partial_input_delay": 0, "partial_output_delay": 0, "pulse_width_clock": 0, "unconstrained_internal_endpoints": 0}, "clock_target_matches": true, "component_internal_target_pass": false, "routing": {"all_routable_nets_routed": true, "fully_routed_nets": 64170, "reported_net_counts": {"of fully routed nets": 64170, "of implicitly routed ports": 2130, "of internally routed nets": 33106, "of logical nets": 99423, "of nets not needing routing": 35253, "of nets with no loads": 17, "of nets with routing errors": 0, "of routable nets": 64170}, "routable_nets": 64170, "routing_errors": 0, "zero_routing_errors": true}, "target_frequency_MHz": 125.0, "target_period_ns": 8.0, "timing": {"THS_ns": 0.0, "TNS_ns": -47241.035, "TPWS_ns": 0.0, "WHS_ns": 0.096, "WNS_ns": -3.525, "WPWS_ns": 2.75, "hold_failing": 0, "hold_total": 89310, "pulse_failing": 0, "pulse_total": 36127, "setup_failing": 39342, "setup_total": 89310}, "worst_setup_path": {"data_path_delay_ns": 11.401, "destination": "coefficients/child/scratch/state_reg[0]_rep/D", "logic_levels": 12, "slack_ns": -3.525, "source": "coefficients/child/scratch/read_segment_reg[1]/C"}}`.

This is OOC component evidence. Missing external I/O requirements and full-parent CDC/memory/display integration remain open. No board bitstream or hardware FPS/latency qualification.
