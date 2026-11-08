set build [file normalize [lindex $argv 0]]
file mkdir [file join $build results]
set_param general.maxThreads 2
open_checkpoint /parent/route.dcp
report_clocks -file [file join $build results clocks.rpt]
set f [open [file join $build results endpoints.tsv] w]
puts $f "kind\tcell\tprimitive\tclock\tperiod"
foreach kind {mode scale} {
 set c [get_cells -hierarchical -regexp [format {^coefficients/admission/lookup_%s_reg\[[01]\]$} $kind]]
 if {[llength $c] != 2} {error "exact two lookup endpoint registers missing: $kind"}
 set d [get_pins -of_objects $c -filter {REF_PIN_NAME == D}]
 if {[llength $d] != 2} {error "exact two D pins missing: $kind"}
 foreach cell $c {
  set clock [get_clocks -of_objects [get_pins -of_objects $cell -filter {REF_PIN_NAME == C}]]
  if {[llength $clock] != 1 || abs([get_property PERIOD $clock]-10)>0.001} {error "original10ns lookup clock changed"}
  puts $f "$kind\t$cell\t[get_property REF_NAME $cell]\t$clock\t[get_property PERIOD $clock]"
 }
 report_timing -delay_type max -to $d -max_paths 10 -path_type full_clock_expanded -file [file join $build results lookup-${kind}-routed.rpt]
 set q [open [file join $build results lookup-${kind}-paths.tsv] w]
 puts $q "source\tendpoint\tslack\tdatapath\tlogic_levels"
 foreach path [get_timing_paths -delay_type max -to $d -max_paths 10] {
  puts $q "[get_property STARTPOINT_PIN $path]\t[get_property ENDPOINT_PIN $path]\t[get_property SLACK $path]\t[get_property DATAPATH_DELAY $path]\t[get_property LOGIC_LEVELS $path]"
 }
 close $q
}
close $f
puts V107_READONLY_LOOKUP_PROBE_COMPLETE
