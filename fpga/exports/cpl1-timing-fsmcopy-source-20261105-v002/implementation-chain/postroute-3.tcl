# Physical optimization only; no RTL or timing-constraint edits.
set cp [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
set directive [lindex $argv 2]
set_param general.maxThreads 4
open_checkpoint $cp
if {$directive eq "qspi-state-copy"} {
 set seed [get_cells -hier -regexp {^endpoint/state_reg\[0\]$}]
 set lut [get_cells -hier -regexp {^endpoint/command\[6\]_i_6$}]
 if {[llength $seed]!=1||[llength $lut]!=1||[get_property REF_NAME $seed] ne "FDRE"} {error "Missing exact measured FSM/decoder cells"}
 set oldnet [get_nets -segments -of_objects [get_pins -of_objects $seed -filter {REF_PIN_NAME == Q}]]
 set target {}
 foreach pin [get_pins -of_objects $lut -filter {DIRECTION == IN}] {
  if {[lsearch -exact $oldnet [get_nets -of_objects $pin]]>=0} {lappend target $pin}
 }
 if {[llength $target]!=1} {error "Expected one measured state input on decoder"}
 set init [get_property INIT $seed];set function [dict create]
 foreach pin {D C CE R} {dict set function $pin [get_nets -of_objects [get_pins $seed/$pin]]}
 set loc [get_property LOC $lut]
 if {![regexp {^SLICE_X([0-9]+)Y([0-9]+)$} $loc _ cx cy]} {error "Unexpected decoder location"}
 set f [open [file join $out qspi-state-copy.txt] w]
 puts $f "SOURCE=$seed REF=FDRE INIT=$init FUNCTION=$function ORIGINAL_LUT=$lut LOCATION=$loc REPLACED_INPUT=$target"
 unplace_cell $lut
 create_cell -reference FDRE endpoint/state0_timing_copy
 set copy [get_cells endpoint/state0_timing_copy]
 set_property INIT $init $copy
 set_property DONT_TOUCH TRUE $copy
 foreach pin {D C CE R} {connect_net -hierarchical -net [dict get $function $pin] -objects [get_pins $copy/$pin]}
 create_net endpoint/state0_timing_q
 set n [get_nets endpoint/state0_timing_q]
 connect_net -net $n -objects [get_pins $copy/Q]
 disconnect_net -net [get_nets -of_objects $target] -objects $target
 if {[llength [get_nets -of_objects $target]]} {error "Measured LUT pin not disconnected"}
 connect_net -hierarchical -net $n -objects $target
 if {[get_nets -of_objects $target] ne $n} {error "Measured LUT pin not reconnected"}
 foreach pin {D C CE R} {if {[get_nets -of_objects [get_pins $copy/$pin]] ne [dict get $function $pin]} {error "FSM copy function mismatch at $pin"}}
 if {[get_property INIT $copy] ne $init} {error "FSM copy INIT mismatch"}
 set sites {}
 for {set x [expr {max(0,$cx-6)}]} {$x<=$cx+6} {incr x} {
  for {set y [expr {max(0,$cy-6)}]} {$y<=$cy+6} {incr y} {
   set site [get_sites -quiet SLICE_X${x}Y${y}]
   if {[llength $site]!=1} {continue}
   set occupied [get_cells -quiet -of_objects [get_bels -of_objects $site]]
   if {[llength $occupied]==0} {lappend sites [list [expr {abs($cx-$x)+abs($cy-$y)}] $site]}
  }
 }
 set placed 0
 foreach item [lsort -integer -index 0 $sites] {
  set site [lindex $item 1]
  if {[catch {place_cell [list $lut $site/A6LUT $copy $site/AFF]} why]} {puts $f "REJECT_SITE $site $why";unplace_cell [list $lut $copy];continue}
  set placed 1;break
 }
 if {!$placed} {error "No nearby legal decoder/copy placement"}
 puts $f "COPY=$copy REF=[get_property REF_NAME $copy] INIT=[get_property INIT $copy] LOC=[get_property LOC $copy] BEL=[get_property BEL $copy] LUT_LOC=[get_property LOC $lut] FUNCTION_MATCH=1"
 close $f
 phys_opt_design -routing_opt -critical_pin_opt -path_groups [get_path_groups raw200]
} elseif {$directive eq "qspi-pack"} {
 # No netlist edits: place the complete IRQ-enable bank near its data driver.
 set cells [get_cells -hier -regexp {^endpoint/irq_enable_reg\[[0-3]\]$}]
 if {[llength $cells]!=4} {error "Expected exact four-bit IRQ bank"}
 set pin [get_pins -of_objects [get_cells -hier -regexp {^endpoint/irq_enable_reg\[2\]$}] -filter {REF_PIN_NAME == D}]
 set drivers [get_cells -of_objects [get_pins -leaf -of_objects [get_nets -segments -of_objects $pin] -filter {DIRECTION == OUT}]]
 if {[llength $drivers]!=1} {error "Ambiguous IRQ data driver: $drivers"}
 set loc [get_property LOC $drivers]
 if {![regexp {^SLICE_X([0-9]+)Y([0-9]+)$} $loc _ cx cy]} {error "Unexpected driver location: $loc"}
 set f [open [file join $out qspi-placement.txt] w]
 puts $f "DRIVER=$drivers LOCATION=$loc"
 foreach c $cells {puts $f "BEFORE $c LOC=[get_property LOC $c] BEL=[get_property BEL $c] REF=[get_property REF_NAME $c]"}
 unplace_cell $cells
 set sites {}
 for {set x [expr {max(0,$cx-8)}]} {$x<=$cx+8} {incr x} {
  for {set y [expr {max(0,$cy-8)}]} {$y<=$cy+8} {incr y} {
   set site [get_sites -quiet SLICE_X${x}Y${y}]
   if {[llength $site]!=1} {continue}
   set free 1
   foreach bel {AFF BFF CFF DFF} {if {[llength [get_cells -quiet -of_objects [get_bels $site/$bel]]]!=0} {set free 0}}
   if {$free} {lappend sites [list [expr {abs($cx-$x)+abs($cy-$y)}] $site]}
  }
 }
 set placed 0
 foreach item [lsort -integer -index 0 $sites] {
  set site [lindex $item 1];set pairs {};set i 0
  foreach c [lsort $cells] {lappend pairs $c $site/[lindex {AFF BFF CFF DFF} $i];incr i}
  if {[catch {place_cell $pairs} why]} {puts $f "REJECT_SITE $site $why";unplace_cell $cells;continue}
  set placed 1;break
 }
 if {!$placed} {error "No legal nearby complete IRQ-bank placement"}
 foreach c $cells {puts $f "AFTER $c LOC=[get_property LOC $c] BEL=[get_property BEL $c] REF=[get_property REF_NAME $c]"}
 close $f
 set group [get_path_groups raw200]
 if {[llength $group]!=1} {error "Missing unchanged 200 MHz path group"}
 phys_opt_design -routing_opt -critical_pin_opt -path_groups $group
} else {
 phys_opt_design -directive $directive
}
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
