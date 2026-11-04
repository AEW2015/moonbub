set here [file dirname [file normalize [info script]]]
set_param general.maxThreads 4
open_checkpoint C:/Users/lavat/codex/moonbub/fpga/candidates/akd1-compute-cancel-boundary-20261104/build/akd1-routed.dcp
set ::rom_reset_define_only 1
source [file join $here solver-definition.tcl]
unset ::rom_reset_define_only
set f [open [file join $here overlay-enable.txt] w]
set reset_q [get_pins -quiet {rstpixel_reg[3]/Q}]
set reset_cell [get_cells -quiet -of_objects $reset_q]
if {[llength $reset_q]!=1 || [get_property INIT $reset_cell] ne "1'b1"} {error "Missing asserted-INIT pixel reset"}
puts $f "RESET=$reset_q REF=[get_property REF_NAME $reset_cell] INIT=[get_property INIT $reset_cell]"
set ro [get_pins -quiet {diagnostic/byte_data_reg_1_0/ENARDEN}]
set core_reset [get_pins -quiet {rst100_reg[3]/Q}]
set ::RomResetProof::memo [dict create]
set ::RomResetProof::known [dict create $core_reset 1]
set validation [rom_eval_pin $ro]
puts $f "KNOWN_BAD_HIGH_ROM_RESET_EN=$validation"
if {$validation!=1} {error "Copied solver did not reproduce known-bad direct ROM enable"}
set rams {}
foreach cell [get_cells -hier -filter {REF_NAME == RAMB36E1}] {
 if {[string match overlay/* [get_property NAME $cell]]} {lappend rams $cell}
}
if {[llength $rams]!=44} {error "Expected44 overlay RAMs, got[llength $rams]"}
set enables [get_pins -of_objects $rams -filter {REF_PIN_NAME == ENBWREN}]
if {[llength $enables]!=44} {error "Expected44 overlay ENBWREN pins"}
puts $f "RAM_COUNT=[llength $rams] ENABLE_COUNT=[llength $enables]"
set starts [all_fanin -flat -startpoints_only -to $enables]
set start_cells [lsort -unique [get_cells -quiet -of_objects $starts]]
puts $f "STARTPOINTS=$starts"
set init_known [dict create $reset_q 1]
foreach cell $start_cells {
 set ref [get_property REF_NAME $cell]
 if {![regexp {^FD} $ref]} {puts $f "NON_FF_START=$cell REF=$ref";continue}
 set init [get_property INIT $cell]
 set q [get_pins -quiet -of_objects $cell -filter {REF_PIN_NAME == Q}]
 puts $f "FF_INIT $cell REF=$ref INIT=$init Q=$q"
 if {[llength $q]==1 && [regexp {^1'b([01])$} $init unused v]} {dict set init_known $q $v}
}
set cells [all_fanin -flat -only_cells -to $enables]
puts $f "CONE_CELL_COUNT=[llength $cells]"
foreach cell $cells {
 set ref [get_property REF_NAME $cell]
 if {![regexp {^LUT[1-6]$} $ref]} {continue}
 puts $f "LUT $cell REF=$ref INIT=[get_property INIT $cell]"
 foreach ip [get_pins -quiet -of_objects $cell -filter {DIRECTION == IN}] {
  set nets [get_nets -quiet -segments -of_objects $ip]
  puts $f " INPUT=$ip DRIVER=[get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == OUT}] NETS=$nets"
 }
}
set ::RomResetProof::memo [dict create]
set ::RomResetProof::known [dict create $reset_q 1]
foreach pin $enables {
 set nets [get_nets -quiet -segments -of_objects $pin]
 puts $f "ENABLE_RESET_ONLY $pin value=[rom_eval_pin $pin] DRIVER=[get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == OUT}]"
 flush $f
}
set ::RomResetProof::memo [dict create]
set ::RomResetProof::known $init_known
foreach pin $enables {
 puts $f "ENABLE_FRESH_INIT $pin value=[rom_eval_pin $pin]"
 flush $f
}
puts $f "METHOD=LUT_truth_tables_all_unknown_assignments; -1 means unknown, never PASS"
puts $f "OVERLAY_READ_ONLY_QUERY_COMPLETE=1"
close $f
puts "OVERLAY_READ_ONLY_QUERY_COMPLETE=1"
close_design
exit
