# Resume an immutable synthesis checkpoint; no synthesis, clock edits or timing cuts.
if {[llength $argv] != 1} {error "expected prepared build directory"}
set build [file normalize [lindex $argv 0]]
file mkdir [file join $build results]
set_param general.maxThreads 2
open_checkpoint /parent/synth.dcp
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "wrong inherited part"}
proc check_clock {} {
    set clocks [get_clocks]
    if {[llength $clocks] != 1 || [get_property NAME $clocks] ne "component_clk" ||
        abs([get_property PERIOD $clocks] - 10.0) > 0.000001} {error "inherited 10ns clock changed"}
}
check_clock
set f [open [file join $build results tool-parent.txt] w]
puts $f "version=[version -short]"
puts $f "part=[get_property PART [current_design]]"
puts $f "clock=[get_property NAME [get_clocks]] period=[get_property PERIOD [get_clocks]]"
puts $f "flow=resume synthesis checkpoint; Default opt/place/route"
close $f
write_xdc -force -exclude_physical [file join $build results before-effective-timing.xdc]
source [file join $build report.tcl]
opt_design -directive Default
place_design -directive Default
v106_reports place
route_design -directive Default
v106_reports route
check_clock
write_checkpoint -force [file join $build results route.dcp]
report_route_status -file [file join $build results route-status.rpt]
write_xdc -force -exclude_physical [file join $build results after-effective-timing.xdc]
puts "V107_COMPONENT_ROUTE_FINISHED; no hardware or board qualification"
