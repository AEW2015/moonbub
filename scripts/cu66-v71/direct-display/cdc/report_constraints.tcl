set_param general.maxThreads 2
open_checkpoint {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/direct-pipe-ooc01/synthesized.dcp}
source {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/direct_cdc_candidate.tcl}
set out {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/constraint-report01}
file mkdir $out
set f [open $out/selected-objects.txt w]
dict for {key value} $direct_cdc_objects {puts $f "$key $value"}
puts $f "pattern_first_D_net [get_nets -of_objects [get_pins -of_objects [direct_exact_reg {lcd/pattern_sync_reg[0]}] -filter {REF_PIN_NAME == D}]]"
puts $f "pattern_first_startpoints [all_fanin -flat -startpoints_only -to [get_pins -of_objects [direct_exact_reg {lcd/pattern_sync_reg[0]}] -filter {REF_PIN_NAME == D}]]"
close $f
report_timing_summary -delay_type min_max -file $out/timing-summary.rpt
report_exceptions -coverage -file $out/exceptions.rpt
report_cdc -details -file $out/cdc.rpt
report_bus_skew -file $out/bus-skew.rpt
report_timing -from [get_clocks mem_clk] -to [get_clocks mem_clk] -max_paths 10 -file $out/memory-paths.rpt
report_timing -from [get_clocks pixel_clk] -to [get_clocks pixel_clk] -max_paths 10 -file $out/pixel-paths.rpt
report_timing -from [direct_pins [direct_bit_regs lcd/request_line0_reg 10] Q] -to [direct_pins [direct_bit_regs lcd/captured_line_reg 10] D] -max_paths 10 -file $out/request-payload.rpt
report_timing -from [direct_pins [direct_exact_reg lcd/completed_bad0_reg] Q] -to [direct_pins [direct_exact_reg lcd/loaded0_reg] D] -max_paths 10 -file $out/done-payload.rpt
write_xdc -force $out/applied-leaf-only.xdc
puts "DIRECT_CDC_CONSTRAINT_REPORT_COMPLETE_NOT_BOARD_SIGNOFF"
