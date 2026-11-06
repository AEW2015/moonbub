# Post-route candidate image generation only. Never opens a hardware target.
set cp [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
file mkdir $out
set_param general.maxThreads 4
open_checkpoint $cp
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "Wrong board part"}
set copy [get_cells -quiet -hier -regexp {^endpoint/state0_timing_copy$}]
if {[llength $copy]} {
 set source [get_cells -hier -regexp {^endpoint/state_reg\[0\]$}]
 if {[llength $source]!=1||[llength $copy]!=1||[get_property REF_NAME $source] ne "FDRE"||[get_property REF_NAME $copy] ne "FDRE"} {error "Unexpected state-copy primitive"}
 foreach p {D C CE R} {
  if {[get_nets -of_objects [get_pins $source/$p]] ne [get_nets -of_objects [get_pins $copy/$p]]} {error "State-copy sequential input differs at $p"}
 }
 foreach p {INIT IS_C_INVERTED IS_D_INVERTED IS_R_INVERTED} {
  if {[lsearch -exact [list_property $source] $p]>=0 && [get_property $p $source] ne [get_property $p $copy]} {error "State-copy primitive parameter differs at $p"}
 }
 set f [open [file join $out state-copy-function-proof.txt] w]
 puts $f "FDRE source and copy have identical D/C/CE/R nets, INIT and available inversion parameters. No timing exception was added. Equal reset/initial state and equal synchronous inputs imply equal logical output on every clock."
 close $f
}
foreach type {max min} {
 set p [get_timing_paths -delay_type $type -max_paths 1]
 if {[llength $p]!=1 || [get_property SLACK $p]<=0} {error "Nonpositive routed $type slack"}
}
foreach c [get_drc_checks] {
 if {[lsearch -exact [list_property $c] MAX_MESSAGES]>=0} {set_property MAX_MESSAGES 100000 $c}
}
report_drc -no_waivers -file [file join $out drc-uncapped.rpt]
set f [open [file join $out drc-native-inventory.txt] w]
set errors 0
foreach v [get_drc_violations] {
 set severity [get_property SEVERITY $v]
 puts $f "$v SEVERITY=$severity"
 if {$severity eq "Error"} {incr errors}
}
close $f
if {$errors>0} {error "DRC errors prevent candidate bitstream"}
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out final-timing-summary.rpt]
report_route_status -file [file join $out final-route-status.rpt]
write_bitstream -force [file join $out moonbub-cpl1-timing-rev4.1.bit]
puts "TIMING_CANDIDATE_BITSTREAM_WRITTEN_NO_HARDWARE"
close_design
