set out [file normalize [lindex $argv 0]]
set root [file join $out inputs]
cd $out
set_param general.maxThreads 4
puts "CPL1_BOARD_TOOL [version] PART=xc7a100tcsg324-1"
foreach name {key.cp23.hex quantizers.hex} {if {![file exists [file join $out $name]]} {error "Missing actual working-directory RAM asset: $name"}}
source [file join $root optimized-sources.tcl]
foreach name {lcd_pins_rev4.xdc sdram_pins_rev4.xdc buttons.xdc platform.xdc} {read_xdc [file join $root constraints $name]}
synth_design -top moonshine_top_cpl1 -part xc7a100tcsg324-1
if {[llength [get_clocks clk_50mhz]]!=1 || [get_property PERIOD [get_clocks clk_50mhz]]!=20.0} {error "Missing preserved50MHz input clock"}
write_checkpoint -force [file join $out synthesized.dcp]
report_utilization -hierarchical -file [file join $out synthesized-utilization.rpt]
report_clocks -file [file join $out synthesized-clocks.rpt]
set f [open [file join $out ram-init-inventory.txt] w]
set rom_count 0;set rom_nonzero 0
foreach cell [get_cells -quiet -hier -filter {REF_NAME =~ RAMB*}] {
 set role OTHER_MUTABLE_OR_COMPUTE
 if {[string match diagnostic/loader/rom* $cell]} {set role FIXED_LOADER_ROM;incr rom_count}
 puts $f "CELL $cell REF=[get_property REF_NAME $cell] ROLE=$role"
 foreach prop {READ_WIDTH_A READ_WIDTH_B WRITE_WIDTH_A WRITE_WIDTH_B DOA_REG DOB_REG RAM_MODE} {if {[lsearch -exact [list_property $cell] $prop]>=0} {puts $f "PROPERTY $cell $prop [get_property $prop $cell]"}}
 foreach prop [lsort [list_property $cell]] {
  if {[regexp {^INIT(P)?_[0-9A-F]+$} $prop]} {
   set v [get_property $prop $cell];puts $f "INIT $cell $prop $v"
   if {$role eq "FIXED_LOADER_ROM" && ![regexp {^[0-9]+'h0+$} $v]} {incr rom_nonzero}
  }
 }
 foreach pin [get_pins -quiet -of_objects $cell] {
  set ref [get_property REF_PIN_NAME $pin]
  if {[regexp {^(ADDR|EN|REGCE|RST|WE|CLK)} $ref]} {puts $f "CONTROL $pin NET=[get_nets -quiet -of_objects $pin] STARTS=[all_fanin -flat -startpoints_only -to $pin]"}
  if {[regexp {^(DO|DOP)} $ref]} {puts $f "DATAOUT $pin NET=[get_nets -quiet -of_objects $pin]"}
 }
}
puts $f "LOADER_ROM_CELLS=$rom_count NONZERO_INIT_PROPERTIES=$rom_nonzero EXACT_CONTENT_ORACLE=NOT_YET_PROVEN"
close $f
if {$rom_count==0 || $rom_nonzero==0} {error "Missing/empty mapped loader ROM; resource/timing cannot qualify"}
set q [open [file join $out quantizer-cell-inventory.txt] w]
foreach c [get_cells -quiet -hier -regexp {.*(quant|factor|qfactor).*}] {
 puts $q "CELL $c REF=[get_property REF_NAME $c]"
 if {[lsearch -exact [list_property $c] INIT]>=0} {puts $q "INIT $c [get_property INIT $c]"}
}
close $q
if {[catch {write_verilog -force -mode funcsim -cell [get_cells diagnostic/loader] [file join $out mapped-loader.v]} why]} {
 set ff [open [file join $out loader-export-error.txt] w];puts $ff $why;close $ff
}
set ff [open [file join $out SYNTHESIZED_READY.txt] w];puts $ff "Checkpoint complete; source-bound working-directory assets loaded. Exact mapped INIT review pending; NO BIT.";close $ff
set lf [open [file join $out vivado.log] r];set logtext [read $lf];close $lf
if {[regexp {\[Synth 8-326\]|inferred timing loop} $logtext]} {error "Inferred timing-loop exception is forbidden"}
if {[regexp -nocase {cannot be opened for reading|could not open.*\.hex|cannot open.*\.hex|could not find.*\.hex|data.*truncated} $logtext]} {error "RAM asset load warning forbidden"}
source [file join $root constraints timing-cpl1-reviewed.tcl]
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
report_timing -delay_type max -max_paths 30 -file [file join $out setup-paths.rpt]
report_timing -delay_type min -max_paths 30 -file [file join $out hold-paths.rpt]
report_utilization -hierarchical -file [file join $out utilization.rpt]
report_route_status -file [file join $out route-status.rpt]
report_drc -file [file join $out drc.rpt]
report_cdc -details -file [file join $out cdc.rpt]
report_exceptions -coverage -file [file join $out exceptions.rpt]
report_clock_interaction -file [file join $out clock-interaction.rpt]
report_bus_skew -file [file join $out bus-skew.rpt]
check_timing -verbose -file [file join $out check-timing.rpt]
puts "CPL1_BOARD_ROUTE_REPORTS_COMPLETE_NO_BIT"
