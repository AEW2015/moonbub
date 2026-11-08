if {[llength $argv]!=1} {error "expected isolated build directory"}
set build [file normalize [lindex $argv 0]]
file mkdir [file join $build results]
set_param general.maxThreads 2
open_checkpoint /parent/route.dcp
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "parent part changed"}
set clocks [get_clocks]
if {[llength $clocks]!=1 || [get_property NAME $clocks] ne "component_clk" || abs([get_property PERIOD $clocks]-10.0)>0.0001} {error "parent single 10ns component clock changed"}
set f [open [file join $build results settings.tsv] w]
puts $f "key\tvalue"
foreach {k v} [list tool [version -short] part [get_property PART [current_design]] clock $clocks period_ns [get_property PERIOD $clocks] max_threads [get_param general.maxThreads] physical_directive AggressiveExplore route_directive Default] {puts $f "$k\t$v"}
close $f
write_xdc -force -exclude_physical [file join $build results before-effective-timing.xdc]
report_route_status -file [file join $build results before-route-status.rpt]
# Exactly one diagnostic post-route physical optimization; it reroutes affected nets.
phys_opt_design -directive AggressiveExplore
write_checkpoint -force [file join $build results post-physopt.dcp]
# Use the exact parent report recipe, unchanged.
source [file join $build report.tcl]
v107_reports route
report_route_status -file [file join $build results route-status.rpt]
write_xdc -force -exclude_physical [file join $build results effective-timing.xdc]
write_checkpoint -force [file join $build results route.dcp]
puts V107_SINGLE_POSTROUTE_PHYSOPT_PROBE_FINISHED
