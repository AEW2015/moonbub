proc unit_reports {variant} {
    global build
    set out [file join $build results]
    report_clocks -file [file join $out ${variant}-clocks.rpt]
    check_timing -verbose -file [file join $out ${variant}-check-timing.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 20 -file [file join $out ${variant}-timing-summary.rpt]
    report_timing -delay_type max -max_paths 50 -path_type full_clock_expanded -file [file join $out ${variant}-setup-paths.rpt]
    report_utilization -file [file join $out ${variant}-utilization.rpt]
    report_utilization -hierarchical -file [file join $out ${variant}-hierarchy.rpt]
    report_high_fanout_nets -timing -load_types -max_nets 50 -file [file join $out ${variant}-high-fanout.rpt]
    report_control_sets -verbose -file [file join $out ${variant}-control-sets.rpt]
    report_exceptions -file [file join $out ${variant}-exceptions.rpt]
    set f [open [file join $out ${variant}-dsp-registers.tsv] w]
    puts $f "instance\tprimitive\tAREG\tBREG\tMREG\tPREG"
    foreach cell [lsort [get_cells -hierarchical -filter {REF_NAME == DSP48E1}]] {
        puts $f "$cell\t[get_property REF_NAME $cell]\t[get_property AREG $cell]\t[get_property BREG $cell]\t[get_property MREG $cell]\t[get_property PREG $cell]"
    }
    close $f
}
