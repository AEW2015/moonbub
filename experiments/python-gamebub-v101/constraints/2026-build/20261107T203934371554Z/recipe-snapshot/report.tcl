# Reports remain native vendor evidence. A missing required report fails.
proc v101_reports {stage} {
    global build
    set out [file join $build results]
    report_clocks -file [file join $out ${stage}-clocks.rpt]
    report_clock_interaction -file [file join $out ${stage}-clock-interaction.rpt]
    check_timing -verbose -file [file join $out ${stage}-check-timing.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 20 -file [file join $out ${stage}-timing-summary.rpt]
    report_timing -delay_type max -max_paths 50 -path_type full_clock_expanded -file [file join $out ${stage}-setup-paths.rpt]
    report_timing -delay_type min -max_paths 50 -path_type full_clock_expanded -file [file join $out ${stage}-hold-paths.rpt]
    report_utilization -hierarchical -file [file join $out ${stage}-utilization.rpt]
    report_drc -file [file join $out ${stage}-drc.rpt]
    report_methodology -file [file join $out ${stage}-methodology.rpt]
    report_cdc -details -file [file join $out ${stage}-cdc.rpt]
    report_exceptions -file [file join $out ${stage}-exceptions.rpt]
    # JSON methodology is optional/version-specific; preserve explicit failure.
    set json_status [open [file join $out ${stage}-methodology-json-status.txt] w]
    if {[catch {report_methodology -json [file join $out ${stage}-methodology.json]} detail]} {
        puts $json_status "UNAVAILABLE: $detail"
    } else {puts $json_status "AVAILABLE"}
    close $json_status
}
