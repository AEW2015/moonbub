# Strict actual-netlist Boolean proof. Unknown sequential outputs stay unknown;
# a LUT is constant only if every assignment to unknown inputs agrees.
namespace eval RomResetProof {variable memo;variable known}
proc rom_eval_pin {pin} {
 variable ::RomResetProof::memo
 variable ::RomResetProof::known
 # Preserve typed scalar pins as well as singleton Vivado collections.
 if {[dict exists $known $pin]} {return [dict get $known $pin]}
 if {[dict exists $memo $pin]} {return [dict get $memo $pin]}
 dict set memo $pin -1
 set nets [get_nets -quiet -segments -of_objects $pin]
 # Actual typed net properties, never spelling such as <const0>.
 if {[llength $nets]>0} {
  set types [get_property TYPE $nets]
  set unique_types [lsort -unique $types]
  if {$unique_types eq "GROUND"} {dict set memo $pin 0;return 0}
  if {$unique_types eq "POWER"} {dict set memo $pin 1;return 1}
 }
 set drivers [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == OUT}]
 # Keep Vivado pin objects typed; sorting/string conversion is unnecessary.
 if {[llength $drivers]!=1} {return -1}
 set output [lindex $drivers 0]
 if {[dict exists $known $output]} {set value [dict get $known $output];dict set memo $pin $value;return $value}
 set cell [get_cells -quiet -of_objects $output]
 if {[llength $cell]!=1} {return -1}
 set ref [get_property REF_NAME $cell]
 if {$ref eq "GND"} {dict set memo $pin 0;return 0}
 if {$ref eq "VCC"} {dict set memo $pin 1;return 1}
 if {![regexp {^LUT([1-6])$} $ref unused n]} {return -1}
 set init [get_property INIT $cell]
 if {![regexp {^[0-9]+'h([0-9a-fA-F]+)$} $init unused hex]} {error "Unrecognized actual LUT INIT: $cell $init"}
 set truth [expr "0x$hex"]
 set inputs {}
 for {set i 0} {$i<$n} {incr i} {
  set ip [get_pins -quiet -of_objects $cell -filter "REF_PIN_NAME == I$i"]
  if {[llength $ip]!=1} {error "Missing actual LUT input: $cell I$i"}
  lappend inputs [rom_eval_pin $ip]
 }
 set answer -1
 for {set assignment 0} {$assignment<(1<<$n)} {incr assignment} {
  set possible 1
  for {set i 0} {$i<$n} {incr i} {
   set v [lindex $inputs $i]
   if {$v!=-1 && (($assignment>>$i)&1)!=$v} {set possible 0;break}
  }
  if {!$possible} {continue}
  set bit [expr {($truth>>$assignment)&1}]
  if {$answer==-1} {set answer $bit} elseif {$answer!=$bit} {dict set memo $pin -1;return -1}
 }
 dict set memo $pin $answer
 return $answer
}
if {[info exists ::rom_reset_define_only] && $::rom_reset_define_only} {return}
set roms [get_cells -quiet -hier -filter {REF_NAME =~ RAMB* && NAME =~ diagnostic/* && NAME !~ diagnostic/compute/*}]
if {[llength $roms]==0} {error "No actual fixture ROM blocks found"}
set fence [get_cells -quiet -hier -regexp {rst100_reg\[3\]}]
if {[llength $fence]!=1} {error "Missing/ambiguous initialized reset fence"}
set fence_init [get_property INIT $fence]
if {$fence_init ne "1'b1"} {error "Reset fence not initialized asserted: $fence_init"}
if {[get_property REF_NAME $fence] ne "FDPE"} {error "Reset fence no longer async-preset FDPE"}
set fence_q [get_pins -quiet -of_objects $fence -filter {REF_PIN_NAME == Q}]
if {[llength $fence_q]!=1} {error "Missing actual reset fence Q"}
set fence_pre [get_pins -quiet -of_objects $fence -filter {REF_PIN_NAME == PRE}]
set pll_lock [get_pins -quiet service_pll/LOCKED]
if {[llength $fence_pre]!=1 || [llength $pll_lock]!=1} {error "Missing actual reset/PLL-lock objects"}
set ::RomResetProof::memo [dict create];set ::RomResetProof::known [dict create $pll_lock 0]
if {[rom_eval_pin $fence_pre]!=1} {error "Reset preset not proven asserted when service PLL unlocked"}
set proof [open [file join $out rom-reset-proof.txt] w]
puts $proof "reset_fence=$fence_q INIT=$fence_init\nROM_blocks=[llength $roms]\nmethod=actual_LUT_INIT_all_unknown_assignments\nunknown_sequential_outputs=unconstrained\npreLOCK_fence=asserted_from_INIT_and_async_lock_reset"
puts $proof "PLL_unlocked_preset_proof=1 PRE=$fence_pre LOCK=$pll_lock"
foreach ram $roms {
 puts $proof "ROM $ram REF_NAME=[get_property REF_NAME $ram]"
 set enable_pins [get_pins -quiet -of_objects $ram -filter {REF_PIN_NAME =~ EN*}]
 set reset_write_pins [get_pins -quiet -of_objects $ram -filter {REF_PIN_NAME =~ RST* || REF_PIN_NAME =~ WE*}]
 if {[llength $enable_pins]==0 || [llength $reset_write_pins]==0} {error "Incomplete actual ROM control inventory: $ram"}
 foreach pin $reset_write_pins {
  set ::RomResetProof::memo [dict create];set ::RomResetProof::known [dict create]
  set result [rom_eval_pin $pin]
  puts $proof "$pin unconditional=$result net=[get_nets -quiet -of_objects $pin]"
  flush $proof
  if {$result!=0} {error "ROM reset/write input not tied inactive: $pin result=$result"}
 }
 foreach pin $enable_pins {
  set ::RomResetProof::memo [dict create];set ::RomResetProof::known [dict create $fence_q 1]
  set result [rom_eval_pin $pin]
  puts $proof "$pin reset_asserted=$result net=[get_nets -quiet -of_objects $pin]"
  puts $proof "fanin_startpoints=[all_fanin -flat -startpoints_only -to $pin]"
  flush $proof
  if {$result!=0} {error "ROM enable not proven low for all states under reset: $pin result=$result"}
 }
}
puts $proof "ALL_ROM_EN_LOW_RESET_AND_RESET_WRITE_PINS_INACTIVE_PASS=1"
close $proof
puts "ALL_ROM_EN_LOW_RESET_AND_RESET_WRITE_PINS_INACTIVE_PASS=1"
