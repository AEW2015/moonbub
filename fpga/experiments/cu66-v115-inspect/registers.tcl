# Read-only examination of a completed route, not a new implementation trial.
if {[llength $argv] != 3} {error "expected routed checkpoint, output directory and period"}
set checkpoint [lindex $argv 0]
set out [lindex $argv 1]
set period [lindex $argv 2]
set_param general.maxThreads 2
open_checkpoint $checkpoint
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "wrong part"}
# HDL top is verified from dcp.xml in the exact receipt-hashed checkpoint by
# the host runner; an opened checkpoint design NAME is a session alias.
set opened_design_name [get_property NAME [current_design]]
if {[version -short] ne "2026.1" || ![string match *6511674* [version]]} {error "tool changed"}
set clocks [get_clocks]
if {[llength $clocks]!=1 || [get_property NAME $clocks] ne "component_clk" || abs([get_property PERIOD $clocks]-$period)>0.0001} {error "clock differs from routed receipt"}
set f [open [file join $out settings.tsv] w]
puts $f "opened_design_name\t$opened_design_name"
puts $f "part\t[get_property PART [current_design]]"
puts $f "tool\t[version -short]"
foreach c [get_clocks] {puts $f "clock\t[get_property NAME $c]\t[get_property PERIOD $c]\t[get_property WAVEFORM $c]"}
close $f
set f [open [file join $out registers.tsv] w]
puts $f "name\tref_name\tlocation"
foreach cell [lsort [get_cells -quiet -hierarchical -filter {NAME =~ *base_kill* || NAME =~ *next_address_at_request* || NAME =~ *prepared_request*}]] {
    puts $f "$cell\t[get_property REF_NAME $cell]\t[get_property LOC $cell]"
}
close $f
set f [open [file join $out bounds-fanin.tsv] w]
puts $f "destination\tstartpoint\tcell_type"
set targets [get_pins -quiet -hierarchical -filter {NAME =~ *prepared_request_in_bounds_reg*/D || NAME =~ *prepared_request_in_bounds_reg*/CE}]
if {![llength $targets]} {error "bounds endpoint absent"}
foreach target [lsort $targets] {
    foreach pin [lsort [all_fanin -flat -startpoints_only -to $target]] {
        set cell [get_cells -quiet -of_objects $pin]
        set kind "PORT"
        if {[llength $cell]} {set kind [get_property REF_NAME $cell]}
        puts $f "$target\t$pin\t$kind"
    }
}
close $f
puts "V115_READ_ONLY_REGISTER_INSPECTION_COMPLETE"
close_design
