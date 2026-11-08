# V113 component methodology report

Trial `spatial-125`, fresh RTL, `xc7a100tcsg324-1`, target 8.0 ns.

Default synthesis by omission; Default opt/route and ExtraNetDelay_high placement. No retiming or timing exception added.

Actual clocks, before/after XDC, setup/hold/pulse, methodology, DRC, CDC, high-fanout and primitive mapping reports are retained.

Status: `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`. Result: `{"check_timing": {"constant_clock": 0, "generated_clocks": 0, "latch_loops": 0, "loops": 0, "multiple_clock": 0, "no_clock": 0, "no_input_delay": 1101, "no_output_delay": 12887, "partial_input_delay": 0, "partial_output_delay": 0, "pulse_width_clock": 0, "unconstrained_internal_endpoints": 0}, "clock_target_matches": true, "component_internal_target_pass": false, "routing": {"all_routable_nets_routed": true, "fully_routed_nets": 68598, "reported_net_counts": {"of fully routed nets": 68598, "of implicitly routed ports": 2135, "of internally routed nets": 35237, "of logical nets": 106071, "of nets not needing routing": 37473, "of nets with no loads": 101, "of nets with routing errors": 0, "of routable nets": 68598}, "routable_nets": 68598, "routing_errors": 0, "zero_routing_errors": true}, "target_frequency_MHz": 125.0, "target_period_ns": 8.0, "timing": {"THS_ns": 0.0, "TNS_ns": -48746.754, "TPWS_ns": 0.0, "WHS_ns": 0.109, "WNS_ns": -3.303, "WPWS_ns": 2.75, "hold_failing": 0, "hold_total": 96321, "pulse_failing": 0, "pulse_total": 39906, "setup_failing": 44277, "setup_total": 96321}, "worst_setup_path": {"data_path_delay_ns": 11.013, "destination": "coefficients/child/packet_decoder/synchronous.ingress/prepared_request_addr_reg[16]/CE", "logic_levels": 11, "slack_ns": -3.303, "source": "transform/accept_state_reg[0]/C"}}`.

This is OOC component evidence. Missing external I/O requirements and full-parent CDC/memory/display integration remain open. No board bitstream or hardware FPS/latency qualification.
