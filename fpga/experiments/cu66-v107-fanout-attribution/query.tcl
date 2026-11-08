if {[llength $argv]!=1} {error "expected output build"}
set build [file normalize [lindex $argv 0]]
file mkdir [file join $build results]
set_param general.maxThreads 2
open_checkpoint /parent/route.dcp
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "unexpected checkpoint part"}
set clocks [get_clocks]
if {[llength $clocks]!=1 || abs([get_property PERIOD $clocks]-10.0)>0.0001} {error "expected unchanged single 10ns clock"}
report_clocks -file [file join $build results clocks.rpt]
proc csvrow {f values} {
 set row {}
 foreach v $values {lappend row "\"[string map [list \" \"\"] $v]\""}
 puts $f [join $row ,]
}
set f [open [file join $build results settings.csv] w]
csvrow $f {tool part clock period_ns max_threads}
csvrow $f [list [version -short] [get_property PART [current_design]] $clocks [get_property PERIOD $clocks] [get_param general.maxThreads]]
close $f
set index 0
foreach name {coefficients/child/scratch/cancelled transform/inverse/reset_0 coefficient_boundary/running14_out} {
 set net [get_nets -quiet $name]
 if {[llength $net]!=1} {error "exact target net missing or ambiguous: $name"}
 set pins [get_pins -leaf -of_objects $net]
 set loads [filter $pins {DIRECTION == IN}]
 set drivers [filter $pins {DIRECTION == OUT}]
 if {[llength $loads]==0 || [llength $drivers]==0} {error "empty actual loads/drivers for $name"}
 set f [open [file join $build results net${index}-pins.csv] w]
 csvrow $f {net direction pin ref_pin cell primitive parent LOC BEL}
 foreach pin [lsort -dictionary $pins] {
  set cell [get_cells -quiet -of_objects $pin]
  if {[llength $cell]!=1} {error "non-leaf pin or missing primitive: $pin"}
  csvrow $f [list $name [get_property DIRECTION $pin] $pin [get_property REF_PIN_NAME $pin] $cell [get_property REF_NAME $cell] [file dirname $cell] [get_property LOC $cell] [get_property BEL $cell]]
 }
 close $f
 set f [open [file join $build results net${index}-counts.csv] w]
 csvrow $f {net loads drivers}
 csvrow $f [list $name [llength $loads] [llength $drivers]]
 close $f
 report_timing -through $net -delay_type max -max_paths 3 -path_type full_clock_expanded -file [file join $build results net${index}-setup.rpt]
 report_timing -through $net -delay_type min -max_paths 3 -path_type full_clock_expanded -file [file join $build results net${index}-hold.rpt]
 incr index
}
puts V107_READONLY_FANOUT_ATTRIBUTION_COMPLETE
