set here [file dirname [file normalize [info script]]]
set root [file dirname $here]
set out [file join $root build-final]
file mkdir $out
set_param general.maxThreads 4
set rtl [glob [file join $root rtl *.sv]]
set jpeg [glob [file join $root vendor core_jpeg src_v *.v]]
read_verilog -sv $rtl
read_verilog $jpeg
read_xdc [file join $root evidence lcd_pins_rev4.xdc]
read_xdc [file join $root evidence sdram_pins_rev4.xdc]
read_xdc [file join $here buttons.xdc]
read_xdc [file join $here platform.xdc]
synth_design -top moonshine_top -part xc7a100tcsg324-1
write_checkpoint -force [file join $out synthesized.dcp]
source [file join $here timing-reviewed.tcl]
opt_design
place_design
phys_opt_design
route_design
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing_summary.rpt]
report_clocks -file [file join $out clocks.rpt]
report_timing -from [get_ports {sdram_dq[*]}] -delay_type max -max_paths 16 -file [file join $out sdram_input_setup.rpt]
report_timing -from [get_ports {sdram_dq[*]}] -delay_type min -max_paths 16 -file [file join $out sdram_input_hold.rpt]
report_timing -to [get_ports {sdram_a[*] sdram_bs[*] sdram_dq[*] sdram_we_n sdram_ldqm sdram_udqm sdram_cas_n sdram_ras_n sdram_cke[*] sdram_cs_n[*]}] -delay_type max -max_paths 64 -file [file join $out sdram_output_setup.rpt]
report_timing -to [get_ports {sdram_a[*] sdram_bs[*] sdram_dq[*] sdram_we_n sdram_ldqm sdram_udqm sdram_cas_n sdram_ras_n sdram_cke[*] sdram_cs_n[*]}] -delay_type min -max_paths 64 -file [file join $out sdram_output_hold.rpt]
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
