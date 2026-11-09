# V115 component methodology report

Trial `integrated-100`, fresh RTL, `xc7a100tcsg324-1`, target 10.0 ns.

Default synthesis by omission; Default opt/route and ExtraNetDelay_high placement. No added retiming option or timing exception; normal placer optimizations remain.

Actual clocks, before/after XDC, setup/hold/pulse, methodology, DRC, CDC, high-fanout and primitive mapping reports are retained.

Status: `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`. Result: `{"check_timing": {"constant_clock": 0, "generated_clocks": 0, "latch_loops": 0, "loops": 0, "multiple_clock": 0, "no_clock": 0, "no_input_delay": 1101, "no_output_delay": 12887, "partial_input_delay": 0, "partial_output_delay": 0, "pulse_width_clock": 0, "unconstrained_internal_endpoints": 0}, "clock_target_matches": true, "component_internal_target_pass": false, "routing": {"all_routable_nets_routed": true, "fully_routed_nets": 73053, "reported_net_counts": {"of fully routed nets": 73053, "of implicitly routed ports": 2172, "of internally routed nets": 30419, "of logical nets": 105745, "of nets not needing routing": 32692, "of nets with no loads": 101, "of nets with routing errors": 0, "of routable nets": 73053}, "routable_nets": 73053, "routing_errors": 0, "zero_routing_errors": true}, "target_frequency_MHz": 100.0, "target_period_ns": 10.0, "timing": {"THS_ns": 0.0, "TNS_ns": -224.175, "TPWS_ns": 0.0, "WHS_ns": 0.098, "WNS_ns": -0.777, "WPWS_ns": 3.75, "hold_failing": 0, "hold_total": 98145, "pulse_failing": 0, "pulse_total": 41830, "setup_failing": 1077, "setup_total": 98145}, "worst_setup_path": {"data_path_delay_ns": 10.488, "destination": "coefficients/producer_cell_cache_reg[5]/CE", "logic_levels": 12, "slack_ns": -0.777, "source": "owner_sequence_reg[0]/C"}}`.

This is OOC component evidence. Missing external I/O requirements and full-parent CDC/memory/display integration remain open. No board bitstream or hardware FPS/latency qualification.
