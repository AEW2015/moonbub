# Reports remain native vendor evidence. A missing required report fails.
proc v115_reports {stage} {
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
    # Observe whether the causal local control registers survived mapping.
    # This is a report only: no KEEP/DONT_TOUCH/MAX_FANOUT property is applied.
    set predicates [open [file join $out ${stage}-local-predicates.tsv] w]
    puts $predicates "instance\tprimitive\tlocation\tINIT"
    foreach cell [lsort [get_cells -quiet -hierarchical -filter {NAME =~ *input_prep* || NAME =~ *prepared* || NAME =~ *prep_valid* || NAME =~ *begin_pending* || NAME =~ *plan_valid* || NAME =~ *active_length* || NAME =~ *active_count* || NAME =~ *active_size* || NAME =~ *active_offset* || NAME =~ *active_k* || NAME =~ *descriptor_last_addr* || NAME =~ *replay_word_bits* || NAME =~ *replay_nonzero* || NAME =~ *prefix_window* || NAME =~ *remaining_nonzero* || NAME =~ *load_nonzero* || NAME =~ *prepared_dc_line* || NAME =~ *prepared_raw_line* || NAME =~ *prepared_ac_line* || NAME =~ *admission_credit* || NAME =~ *command_pending* || NAME =~ *owner_open* || NAME =~ *owner_delivered* || NAME =~ *base_kill* || NAME =~ *terminal_valid* || NAME =~ *command_epoch* || NAME =~ *busy_owned* || NAME =~ *fault_pending* || NAME =~ *fault_ack* || NAME =~ *frame_running_owned* || NAME =~ *cache_nonzero_owned* || NAME =~ *accept_pending* || NAME =~ *accept_state* || NAME =~ *result_state* || NAME =~ *geometry* || NAME =~ *phase_input_bad* || NAME =~ *group_visibility* || NAME =~ *local_ac_validation* || NAME =~ *ac_bank_invalid* || NAME =~ *tile_pending* || NAME =~ *tile_event* || NAME =~ *tile_payload* || NAME =~ *header_length* || NAME =~ *header_pair* || NAME =~ *header_total* || NAME =~ *header_expected* || NAME =~ *header_size*}]] {
        set initial UNAVAILABLE
        if {[lsearch -exact [list_property $cell] INIT] >= 0} {set initial [get_property INIT $cell]}
        puts $predicates "$cell\t[get_property REF_NAME $cell]\t[get_property LOC $cell]\t$initial"
    }
    close $predicates
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
    report_high_fanout_nets -timing -load_types -max_nets 50 -file [file join $out ${stage}-high-fanout.rpt]
    report_control_sets -verbose -file [file join $out ${stage}-control-sets.rpt]
    report_design_analysis -complexity -file [file join $out ${stage}-complexity.rpt]
    if {$stage ne "synth"} {
        report_design_analysis -congestion -file [file join $out ${stage}-congestion.rpt]
    }
    set distributed [open [file join $out ${stage}-distributed-ram.tsv] w]
    puts $distributed "instance\tprimitive\tlocation"
    foreach cell [lsort [get_cells -hierarchical -filter {REF_NAME =~ RAM*}]] {
        set kind [get_property REF_NAME $cell]
        if {![string match RAMB* $kind]} {
            puts $distributed "$cell\t$kind\t[get_property LOC $cell]"
        }
    }
    close $distributed
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
