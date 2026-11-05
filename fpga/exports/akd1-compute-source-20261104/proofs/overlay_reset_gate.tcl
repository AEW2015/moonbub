# Same direct LUT enumeration used for the selected image, exact new netlist.
namespace eval ::Akd1ExportOverlay {
 set akd1Reset [get_pins -quiet {rstpixel_reg[3]/Q}]
 set akd1ResetCell [get_cells -quiet -of_objects $akd1Reset]
 if {[llength $akd1Reset]!=1 || [get_property REF_NAME $akd1ResetCell] ne "FDPE" || [get_property INIT $akd1ResetCell] ne "1'b1"} {error "Missing initialized overlay reset fence"}
 set akd1Rams [get_cells -quiet -hier -filter {REF_NAME == RAMB36E1 && NAME =~ overlay/*}]
 if {[llength $akd1Rams]!=44} {error "Expected44 overlay RAM blocks"}
 set akd1Record [open [file join $::akd1Out overlay-reset-proof.txt] w]
 puts $akd1Record "reset=$akd1Reset INIT=1'b1 blocks=44 method=direct_actual_LUT_all_reset1_assignments"
 foreach akd1Ram $akd1Rams {
  set akd1En [get_pins -quiet -of_objects $akd1Ram -filter {REF_PIN_NAME == ENBWREN}]
  set akd1Drivers [get_pins -quiet -leaf -of_objects [get_nets -quiet -segments -of_objects $akd1En] -filter {DIRECTION == OUT}]
  if {[llength $akd1En]!=1 || [llength $akd1Drivers]!=1} {error "Missing/ambiguous overlay enable driver"}
  set akd1Lut [get_cells -quiet -of_objects $akd1Drivers]
  if {[get_property REF_NAME $akd1Lut] ne "LUT4"} {error "Overlay enable not expected directLUT4"}
  set akd1Init [get_property INIT $akd1Lut]
  if {![regexp {^16'h([0-9a-fA-F]+)$} $akd1Init akd1Unused akd1Hex]} {error "Unknown overlay LUT4 INIT format"}
  set akd1Truth [expr "0x$akd1Hex"]
  set akd1I0 [get_pins -quiet -of_objects $akd1Lut -filter {REF_PIN_NAME == I0}]
  set akd1I0Drivers [get_pins -quiet -leaf -of_objects [get_nets -quiet -segments -of_objects $akd1I0] -filter {DIRECTION == OUT}]
  if {[get_property NAME $akd1I0Drivers] ne [get_property NAME $akd1Reset]} {error "Overlay LUT I0 is not actual resetQ"}
  for {set akd1Assignment 1} {$akd1Assignment<16} {incr akd1Assignment 2} {
   if {($akd1Truth>>$akd1Assignment)&1} {error "Overlay ENB not reset-low for every address assignment"}
  }
  puts $akd1Record "RAM=$akd1Ram EN=$akd1En DRIVER=$akd1Drivers INIT=$akd1Init RESET_INPUT=$akd1I0 RESET_DRIVER=$akd1I0Drivers all8_reset1_entries=0"
 }
 puts $akd1Record "ALL44_OVERLAY_RESET_LOW_PASS=1"
 close $akd1Record
 puts "ALL44_OVERLAY_RESET_LOW_PASS=1"
}
