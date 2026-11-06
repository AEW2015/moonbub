set_param general.maxThreads 4
set out [file normalize [lindex $argv 0]]
open_checkpoint {C:/mb70/fpga/experiments/cu66-v71/board/implementation01/synthesized.dcp}
source [file join $out corrected-timing.tcl]
write_checkpoint -force [file join $out constrained.dcp]
check_timing -verbose -file [file join $out check-timing-postsynth.rpt]
opt_design
place_design
phys_opt_design
route_design
phys_opt_design -directive AggressiveExplore
route_design -directive Explore -tns_cleanup
write_checkpoint -force [file join $out routed.dcp]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing-summary.rpt]
report_timing -delay_type max -max_paths 40 -file [file join $out setup-paths.rpt]
report_timing -delay_type min -max_paths 40 -file [file join $out hold-paths.rpt]
report_utilization -hierarchical -file [file join $out utilization.rpt]
report_route_status -file [file join $out route-status.rpt]
report_drc -file [file join $out drc.rpt]
report_cdc -details -file [file join $out cdc.rpt]
report_exceptions -coverage -file [file join $out exceptions.rpt]
report_clock_interaction -file [file join $out clock-interaction.rpt]
report_bus_skew -file [file join $out bus-skew.rpt]
check_timing -verbose -file [file join $out check-timing.rpt]
puts "CU71_BOARD_REPORTS_COMPLETE_NO_BIT_OR_HARDWARE"
