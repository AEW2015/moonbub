set out [file normalize [lindex $argv 0]]
set src [file join $out inputs]
set_param general.maxThreads 2
create_project sdr1 [file join $out project] -part xc7a100tcsg324-1
set_property target_language Verilog [current_project]
foreach name {top.sv engine.sv controller.sv endpoint.sv} {add_files [file join $src $name]}
foreach name {lcd_pins_rev4.xdc sdram_pins_rev4.xdc buttons.xdc platform.xdc} {add_files -fileset constrs_1 [file join $src constraints $name]}
create_ip -name vio -vendor xilinx.com -library ip -module_name sdr1_vio
set config [list CONFIG.C_NUM_PROBE_IN {9} CONFIG.C_NUM_PROBE_OUT {1} CONFIG.C_PROBE_OUT0_WIDTH {1}]
foreach i {0 1 2 6 7 8} {lappend config CONFIG.C_PROBE_IN${i}_WIDTH {32}}
foreach i {3 4 5} {lappend config CONFIG.C_PROBE_IN${i}_WIDTH {128}}
set_property -dict $config [get_ips sdr1_vio]
generate_target all [get_ips sdr1_vio]
set_property top sdr1_top [current_fileset]
launch_runs synth_1 -jobs 2
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis did not complete"}
open_run synth_1
source [file join $out memory-timing.tcl]
write_checkpoint [file join $out constrained.dcp]
opt_design
place_design
phys_opt_design
route_design
write_checkpoint [file join $out routed.dcp]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing-summary.rpt]
report_route_status -file [file join $out route-status.rpt]
report_timing -delay_type max -max_paths 20 -file [file join $out setup.rpt]
report_timing -delay_type min -max_paths 20 -file [file join $out hold.rpt]
check_timing -verbose -file [file join $out check-timing.rpt]
report_drc -no_waivers -file [file join $out drc.rpt]
report_cdc -details -file [file join $out cdc.rpt]
report_utilization -file [file join $out utilization.rpt]
puts "SDR1_ROUTED_REPORTS_ONLY_NO_IMAGE_NO_HARDWARE"
close_design
close_project
