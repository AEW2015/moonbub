# V117 component methodology report

Trial `integrated-125`, fresh RTL, `xc7a100tcsg324-1`, target 8.0 ns.

Default synthesis by omission; Default opt/route and ExtraNetDelay_high placement. No added retiming option or timing exception; normal placer optimizations remain.

Actual clocks, before/after XDC, setup/hold/pulse, methodology, DRC, CDC, high-fanout and primitive mapping reports are retained.

Status: `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`. Result: `{"check_timing": {"constant_clock": 0, "generated_clocks": 0, "latch_loops": 0, "loops": 0, "multiple_clock": 0, "no_clock": 0, "no_input_delay": 1101, "no_output_delay": 12884, "partial_input_delay": 0, "partial_output_delay": 0, "pulse_width_clock": 0, "unconstrained_internal_endpoints": 0}, "clock_target_matches": true, "component_internal_target_pass": false, "routing": {"all_routable_nets_routed": true, "fully_routed_nets": 73346, "reported_net_counts": {"of fully routed nets": 73346, "of implicitly routed ports": 2166, "of internally routed nets": 31054, "of logical nets": 106667, "of nets not needing routing": 33321, "of nets with no loads": 101, "of nets with routing errors": 0, "of routable nets": 73346}, "routable_nets": 73346, "routing_errors": 0, "zero_routing_errors": true}, "target_frequency_MHz": 125.0, "target_period_ns": 8.0, "timing": {"THS_ns": 0.0, "TNS_ns": -9909.251, "TPWS_ns": 0.0, "WHS_ns": 0.099, "WNS_ns": -1.925, "WPWS_ns": 2.75, "hold_failing": 0, "hold_total": 98882, "pulse_failing": 0, "pulse_total": 42164, "setup_failing": 19863, "setup_total": 98882}, "worst_setup_path": {"data_path_delay_ns": 9.636, "destination": "coefficients/child/packet_decoder/synchronous.ingress/offsets_reg[0][0]/CE", "logic_levels": 16, "slack_ns": -1.925, "source": "coefficients/child/packet_decoder/synchronous.ingress/size_bytes_reg[1]/C"}}`.

This is OOC component evidence. Missing external I/O requirements and full-parent CDC/memory/display integration remain open. No board bitstream or hardware FPS/latency qualification.
