# Reports remain native vendor evidence. A missing required report fails.
proc v102_reports {stage} {
    global build
    set out [file join $build results]
    report_clocks -file [file join $out ${stage}-clocks.rpt]
    report_clock_interaction -file [file join $out ${stage}-clock-interaction.rpt]
    check_timing -verbose -file [file join $out ${stage}-check-timing.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 20 -file [file join $out ${stage}-timing-summary.rpt]
    report_timing -delay_type max -max_paths 50 -path_type full_clock_expanded -file [file join $out ${stage}-setup-paths.rpt]
    report_timing -delay_type min -max_paths 50 -path_type full_clock_expanded -file [file join $out ${stage}-hold-paths.rpt]
    report_utilization -hierarchical -file [file join $out ${stage}-utilization.rpt]
    report_utilization -file [file join $out ${stage}-capacity.rpt]
    set dsp_file [open [file join $out ${stage}-dsp-registers.tsv] w]
    puts $dsp_file "instance\tprimitive\tAREG\tBREG\tMREG\tPREG"
    foreach cell [lsort [get_cells -hierarchical -filter {REF_NAME == DSP48E1}]] {
        puts $dsp_file "$cell\t[get_property REF_NAME $cell]\t[get_property AREG $cell]\t[get_property BREG $cell]\t[get_property MREG $cell]\t[get_property PREG $cell]"
    }
    close $dsp_file
    set ram_file [open [file join $out ${stage}-ram-config.tsv] w]
    set ram_properties {REF_NAME RAM_MODE READ_WIDTH_A READ_WIDTH_B WRITE_WIDTH_A WRITE_WIDTH_B WRITE_MODE_A WRITE_MODE_B DOA_REG DOB_REG RDADDR_COLLISION_HWCONFIG}
    puts $ram_file "instance\t[join $ram_properties \t]"
    foreach cell [lsort [get_cells -hierarchical -filter {REF_NAME =~ RAMB*}]] {
        set row [list $cell]
        set available [list_property $cell]
        foreach property $ram_properties {
            if {[lsearch -exact $available $property] >= 0} {
                lappend row [get_property $property $cell]
            } else {lappend row UNAVAILABLE}
        }
        puts $ram_file [join $row \t]
    }
    close $ram_file
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
