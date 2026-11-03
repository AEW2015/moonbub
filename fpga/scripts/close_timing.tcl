# Post-route physical closure from the exact source-bound v3 routed checkpoint.
set here [file dirname [file normalize [info script]]]
set root [file dirname $here]
set out [file join $root build-final]
set_param general.maxThreads 4
open_checkpoint [file join $root attempts v3-routed moonshine_routed.dcp]
phys_opt_design -directive AggressiveExplore
route_design -directive Explore -tns_cleanup
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing_summary.rpt]
report_clocks -file [file join $out clocks.rpt]
report_timing -from [get_ports {sdram_dq[*]}] -delay_type max -max_paths 16 -file [file join $out sdram_input_setup.rpt]
report_timing -from [get_ports {sdram_dq[*]}] -delay_type min -max_paths 16 -file [file join $out sdram_input_hold.rpt]
report_timing -delay_type max -max_paths 20 -file [file join $out setup_paths.rpt]
report_timing -delay_type min -max_paths 20 -file [file join $out hold_paths.rpt]
report_route_status -file [file join $out route_status.rpt]
report_utilization -file [file join $out utilization.rpt]
report_drc -file [file join $out drc.rpt]
report_cdc -details -file [file join $out cdc.rpt]
report_exceptions -file [file join $out exceptions.rpt]
report_bus_skew -file [file join $out bus_skew.rpt]
report_clock_interaction -file [file join $out clock_interaction.rpt]
check_timing -verbose -file [file join $out check_timing.rpt]
write_checkpoint -force [file join $out moonshine_routed.dcp]
set setup [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set hold [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
set drcs [get_drc_violations -quiet -filter {SEVERITY == Error}]
puts "MOONSHINE_ROUTED_SETUP=$setup HOLD=$hold DRC_ERRORS=[llength $drcs]"
set status [open [file join $out gate.txt] w]
puts $status "setup_wns=$setup\nhold_whs=$hold\ndrc_errors=[llength $drcs]"
close $status
if {$setup<=0 || $hold<=0 || [llength $drcs]!=0} {error "Routed gate incomplete; inspect saved checkpoint/reports"}
write_bitstream -force [file join $out moonshine-rev4.1.bit]
puts "MOONSHINE_BITSTREAM_READY=1"
