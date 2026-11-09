# V120 component methodology report

Trial `integrated-125`, fresh RTL, `xc7a100tcsg324-1`, target 8.0 ns.

Default synthesis by omission; Default opt/route and ExtraNetDelay_high placement. No added retiming option or timing exception; normal placer optimizations remain.

Actual clocks, before/after XDC, setup/hold/pulse, methodology, DRC, CDC, high-fanout and primitive mapping reports are retained.

Status: `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`. Result: `{"check_timing": {"constant_clock": 0, "generated_clocks": 0, "latch_loops": 0, "loops": 0, "multiple_clock": 0, "no_clock": 0, "no_input_delay": 1101, "no_output_delay": 12887, "partial_input_delay": 0, "partial_output_delay": 0, "pulse_width_clock": 0, "unconstrained_internal_endpoints": 0}, "clock_target_matches": true, "component_internal_target_pass": false, "routing": {"all_routable_nets_routed": true, "fully_routed_nets": 74080, "reported_net_counts": {"of fully routed nets": 74080, "of implicitly routed ports": 2186, "of internally routed nets": 27942, "of logical nets": 104274, "of nets not needing routing": 30194, "of nets with no loads": 66, "of nets with routing errors": 0, "of routable nets": 74080}, "routable_nets": 74080, "routing_errors": 0, "zero_routing_errors": true}, "target_frequency_MHz": 125.0, "target_period_ns": 8.0, "timing": {"THS_ns": 0.0, "TNS_ns": -3931.934, "TPWS_ns": 0.0, "WHS_ns": 0.082, "WNS_ns": -1.517, "WPWS_ns": 2.75, "hold_failing": 0, "hold_total": 103354, "pulse_failing": 0, "pulse_total": 43842, "setup_failing": 10524, "setup_total": 103354}, "worst_setup_path": {"data_path_delay_ns": 8.99, "destination": "coefficients/admission/memory_reg_0_0/ENBWREN", "logic_levels": 12, "slack_ns": -1.517, "source": "coefficients/refill_overlap_enabled.refill_queue/issued_reg[1]/C"}}`.

This is OOC component evidence. Missing external I/O requirements and full-parent CDC/memory/display integration remain open. No board bitstream or hardware FPS/latency qualification.
