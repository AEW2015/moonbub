# Physical optimization only; no RTL or timing-constraint edits.
set cp [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
set directive [lindex $argv 2]
set_param general.maxThreads 4
open_checkpoint $cp
phys_opt_design -directive $directive
route_design -directive Explore -tns_cleanup
write_checkpoint -force [file join $out routed.dcp]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing-summary.rpt]
report_timing -delay_type max -max_paths 30 -file [file join $out setup-paths.rpt]
report_timing -delay_type min -max_paths 30 -file [file join $out hold-paths.rpt]
report_route_status -file [file join $out route-status.rpt]
report_utilization -hierarchical -file [file join $out utilization.rpt]
report_drc -file [file join $out drc.rpt]
report_cdc -details -file [file join $out cdc.rpt]
report_exceptions -coverage -file [file join $out exceptions.rpt]
report_clock_interaction -file [file join $out clock-interaction.rpt]
report_bus_skew -file [file join $out bus-skew.rpt]
check_timing -verbose -file [file join $out check-timing.rpt]
puts "POSTROUTE_CLEANUP_COMPLETE_NO_BIT_NO_CONSTRAINT_CHANGES"
close_design
