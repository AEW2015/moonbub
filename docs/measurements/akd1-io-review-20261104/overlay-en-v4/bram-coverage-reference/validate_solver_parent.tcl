set root [file dirname [file normalize [info script]]]
set_param general.maxThreads 4
open_checkpoint [file join $root .. akd1-compute-cancel-boundary-20261104 build akd1-routed.dcp]
set inventory [open [file join $root evidence parent-all-BRAM-cells.txt] w]
foreach ref {RAMB36E1 RAMB18E1} {
 set cells [lsort [get_cells -quiet -hier -filter "REF_NAME == $ref"]]
 puts $inventory "$ref count=[llength $cells]"
 foreach c $cells {puts $inventory $c}
}
close $inventory
set ::rom_reset_define_only 1
source [file join $root rom_reset_gate.tcl]
unset ::rom_reset_define_only
set reset_q [get_pins -quiet {rst100_reg[3]/Q}]
set en [get_pins -quiet {diagnostic/byte_data_reg_1_0/ENARDEN}]
if {[llength $reset_q]!=1 || [llength $en]!=1} {error "Known-bad reference pins missing"}
set ::RomResetProof::memo [dict create];set ::RomResetProof::known [dict create $reset_q 1]
set value [rom_eval_pin $en]
puts "KNOWN_BAD_PARENT_ROM_EN_RESET=$value"
if {$value!=1} {error "Boolean proof solver did not reproduce known-bad parent EN=1"}
puts "SOLVER_KNOWN_BAD_PARENT_COUNTEREXAMPLE_PASS=1"
close_design
