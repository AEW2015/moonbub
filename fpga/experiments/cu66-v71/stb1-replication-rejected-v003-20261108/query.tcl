set_param general.maxThreads 4
set out [file normalize [lindex $argv 0]]
open_checkpoint C:/moon/builds/stb1-v001/placed.dcp
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "wrong part"}
if {[version -short] ne "2025.2"} {error "wrong Vivado"}
proc target_ce {} {
 set ce [get_pins -quiet -hier -filter {NAME == "control_plane/hud_ticket_reg[4]/CE"}]
 if {[llength $ce]!=1} {error "exact semantic CE endpoint missing"}
 set nets [get_nets -quiet -of_objects $ce]
 if {[llength $nets]!=1} {error "CE net ambiguous"}
 set pin [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == OUT}]
 set cell [get_cells -quiet -of_objects $pin]
 if {[llength $pin]!=1 || [llength $cell]!=1 || [get_property REF_NAME $cell] ne "LUT4"} {error "target must have one actual LUT4 driver; no guessing"}
 set loads [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == IN}]
 return [list $ce $nets $pin $cell [get_property REF_NAME $cell] [get_property INIT $cell] [llength $loads]]
}
set target [target_ce]
set f [open [file join $out target-review.tsv] w]
foreach key {endpoint net driver_pin driver_cell driver_ref driver_init leaf_loads} value $target {puts $f "$key\t$value"}
close $f
set driver [lindex $target 3]
report_property $driver -file [file join $out target-driver-properties.rpt]
report_property [lindex $target 1] -file [file join $out target-net-properties.rpt]
report_timing -delay_type max -to [lindex $target 0] -max_paths 8 -file [file join $out target-ce-setup-before.rpt]
report_timing -delay_type max -through [lindex $target 2] -max_paths 12 -file [file join $out target-through-setup-before.rpt]
set f [open [file join $out installed-phys-opt-help.txt] w];puts $f [help phys_opt_design -verbose];close $f
report_clocks -file [file join $out clocks-before.rpt]
report_exceptions -coverage -file [file join $out exceptions-before.rpt]
puts STB1_MARGIN_V003_POSTPLACE_READONLY_COMPLETE
close_design
