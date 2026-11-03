# Reproducible standalone Rev4.1 build. No existing projects or sources mutated.
set here [file dirname [file normalize [info script]]]
set root [file dirname $here]
set out [file join $root build]
file mkdir $out
set_param general.maxThreads 4
read_verilog -sv [glob [file join $root rtl *.sv]]
read_verilog [glob [file join $root vendor core_jpeg src_v *.v]]
read_xdc [file join $root evidence lcd_pins_rev4.xdc]
read_xdc [file join $root evidence sdram_pins_rev4.xdc]
read_xdc [file join $root evidence button_pins_rev4.xdc]
read_xdc [file join $here platform.xdc]
synth_design -top moonshine_top -part xc7a100tcsg324-1
write_checkpoint -force [file join $out synthesized.dcp]
source [file join $here timing.tcl]
opt_design
place_design
phys_opt_design
route_design
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing_summary.rpt]
report_route_status -file [file join $out route_status.rpt]
report_utilization -file [file join $out utilization.rpt]
report_drc -file [file join $out drc.rpt]
report_cdc -details -file [file join $out cdc.rpt]
report_clock_interaction -file [file join $out clock_interaction.rpt]
check_timing -verbose -file [file join $out check_timing.rpt]
write_checkpoint -force [file join $out moonshine_routed.dcp]
set setup [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set hold [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
set drcs [get_drc_violations -quiet -filter {SEVERITY == Error}]
puts "MOONSHINE_ROUTED_SETUP=$setup HOLD=$hold DRC_ERRORS=[llength $drcs]"
if {$setup<=0 || $hold<=0 || [llength $drcs]!=0} {error "Routed gate incomplete; inspect saved checkpoint/reports"}
write_bitstream -force [file join $out moonshine-rev4.1.bit]
puts "MOONSHINE_BITSTREAM_READY=1"
