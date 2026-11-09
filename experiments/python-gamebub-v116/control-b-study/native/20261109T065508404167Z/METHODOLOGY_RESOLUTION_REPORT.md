# V116 component methodology report

Trial `integrated-125`, fresh RTL, `xc7a100tcsg324-1`, target 8.0 ns.

Default synthesis by omission; Default opt/route and ExtraNetDelay_high placement. No added retiming option or timing exception; normal placer optimizations remain.

Actual clocks, before/after XDC, setup/hold/pulse, methodology, DRC, CDC, high-fanout and primitive mapping reports are retained.

Status: `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`. Result: `{"check_timing": {"constant_clock": 0, "generated_clocks": 0, "latch_loops": 0, "loops": 0, "multiple_clock": 0, "no_clock": 0, "no_input_delay": 1101, "no_output_delay": 12884, "partial_input_delay": 0, "partial_output_delay": 0, "pulse_width_clock": 0, "unconstrained_internal_endpoints": 0}, "clock_target_matches": true, "component_internal_target_pass": false, "routing": {"all_routable_nets_routed": true, "fully_routed_nets": 72474, "reported_net_counts": {"of fully routed nets": 72474, "of implicitly routed ports": 2166, "of internally routed nets": 30468, "of logical nets": 105209, "of nets not needing routing": 32735, "of nets with no loads": 101, "of nets with routing errors": 0, "of routable nets": 72474}, "routable_nets": 72474, "routing_errors": 0, "zero_routing_errors": true}, "target_frequency_MHz": 125.0, "target_period_ns": 8.0, "timing": {"THS_ns": 0.0, "TNS_ns": -16550.705, "TPWS_ns": 0.0, "WHS_ns": 0.093, "WNS_ns": -2.238, "WPWS_ns": 2.75, "hold_failing": 0, "hold_total": 98770, "pulse_failing": 0, "pulse_total": 42059, "setup_failing": 26346, "setup_total": 98770}, "worst_setup_path": {"data_path_delay_ns": 9.725, "destination": "coefficients/child/scratch/pending_record_reg[19]/R", "logic_levels": 11, "slack_ns": -2.238, "source": "coefficients/child/packet_decoder/synchronous.ingress/raw_mode_reg/C"}}`.

This is OOC component evidence. Missing external I/O requirements and full-parent CDC/memory/display integration remain open. No board bitstream or hardware FPS/latency qualification.
