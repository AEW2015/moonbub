# One bounded physical diagnostic; inherited 10ns clock and all timing scope retained.
if {[llength $argv]!=1} {error "expected owned build directory"}
set build [file normalize [lindex $argv 0]]
file mkdir [file join $build results]
set_param general.maxThreads 2
open_checkpoint /parent/route.dcp
set actual_part [get_property PART [current_design]]
if {$actual_part ne "xc7a100tcsg324-1"} {error "unexpected inherited part: $actual_part"}
proc clock_contract {} {
    set clocks [get_clocks]
    if {[llength $clocks]!=1 || [get_property NAME $clocks] ne "component_clk" ||
        abs([get_property PERIOD $clocks]-10.0)>0.000001} {error "inherited clock contract changed"}
}
clock_contract
set f [open [file join $build results tool-parent.txt] w]
puts $f "version=[version -short]"
puts $f "part=$actual_part"
puts $f "clock=[get_property NAME [get_clocks]] period=[get_property PERIOD [get_clocks]]"
puts $f "strategy=post-route AggressiveExplore; no explicit retiming; no clock/exception edits"
close $f
proc complete_route {path} {
    set f [open $path r];set text [read $f];close $f
    if {![regexp {# of routable nets[. ]+:[ ]+([0-9]+)} $text unused routable] ||
        ![regexp {# of fully routed nets[. ]+:[ ]+([0-9]+)} $text unused routed] ||
        ![regexp {# of nets with routing errors[. ]+:[ ]+([0-9]+)} $text unused errors]} {
        error "cannot establish complete routing from native report"
    }
    return [expr {$routable==$routed && $errors==0}]
}
proc diagnostic_reports {prefix} {
    global build
    set out [file join $build results]
    report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 20 -file [file join $out ${prefix}-timing-summary.rpt]
    report_timing -delay_type max -max_paths 50 -path_type full_clock_expanded -file [file join $out ${prefix}-setup-paths.rpt]
    report_timing -delay_type min -max_paths 50 -path_type full_clock_expanded -file [file join $out ${prefix}-hold-paths.rpt]
    report_pulse_width -file [file join $out ${prefix}-pulse-width.rpt]
    report_route_status -file [file join $out ${prefix}-route-status.rpt]
    report_utilization -file [file join $out ${prefix}-capacity.rpt]
    report_utilization -hierarchical -file [file join $out ${prefix}-utilization.rpt]
    report_high_fanout_nets -timing -load_types -max_nets 50 -file [file join $out ${prefix}-high-fanout.rpt]
    check_timing -verbose -file [file join $out ${prefix}-check-timing.rpt]
    report_drc -file [file join $out ${prefix}-drc.rpt]
    report_methodology -file [file join $out ${prefix}-methodology.rpt]
    report_exceptions -file [file join $out ${prefix}-exceptions.rpt]
    report_clocks -file [file join $out ${prefix}-clocks.rpt]
    report_clock_interaction -file [file join $out ${prefix}-clock-interaction.rpt]
    report_cdc -details -file [file join $out ${prefix}-cdc.rpt]
    write_xdc -force -exclude_physical [file join $out ${prefix}-effective-timing.xdc]
}
diagnostic_reports before
if {![complete_route [file join $build results before-route-status.rpt]]} {error "parent baseline is not completely legally routed"}
puts "V106_POSTROUTE_BASELINE_REPORTS_FINISHED"
phys_opt_design -directive AggressiveExplore
report_route_status -file [file join $build results physical-route-status.rpt]
set route_needed [expr {![complete_route [file join $build results physical-route-status.rpt]]}]
set f [open [file join $build results route-repair.txt] w]
puts $f "route_design_Default_needed=$route_needed"
close $f
if {$route_needed} {route_design -directive Default}
clock_contract
diagnostic_reports after
if {![complete_route [file join $build results after-route-status.rpt]]} {error "postroute probe did not restore complete legal routing"}
write_checkpoint -force [file join $build results postroute.dcp]
puts "V106_POSTROUTE_DIAGNOSTIC_FINISHED; no automatic selection, board or hardware qualification"
