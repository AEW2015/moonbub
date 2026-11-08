proc v107_cdc_reports {stage} {
    global build v107_gray_q v107_gray_c v107_gray_d v107_gray_budget
    set out [file join $build results]
    report_clocks -file [file join $out ${stage}-clocks.rpt]
    report_clock_interaction -file [file join $out ${stage}-clock-interaction.rpt]
    check_timing -verbose -file [file join $out ${stage}-check-timing.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 20 -file [file join $out ${stage}-timing-summary.rpt]
    report_timing -delay_type max -max_paths 30 -path_type full_clock_expanded -file [file join $out ${stage}-setup-paths.rpt]
    report_timing -delay_type min -max_paths 30 -path_type full_clock_expanded -file [file join $out ${stage}-hold-paths.rpt]
    report_utilization -hierarchical -file [file join $out ${stage}-utilization.rpt]
    report_cdc -details -file [file join $out ${stage}-cdc.rpt]
    report_bus_skew -max_paths 4 -file [file join $out ${stage}-bus-skew.rpt]
    report_exceptions -file [file join $out ${stage}-exceptions.rpt]
    report_exceptions -coverage -file [file join $out ${stage}-exception-coverage.rpt]
    report_exceptions -ignored -file [file join $out ${stage}-exceptions-ignored.rpt]
    set method_status [open [file join $out ${stage}-methodology-json-status.txt] w]
    if {[catch {report_methodology -json [file join $out ${stage}-methodology.json]} detail]} {
        puts $method_status "UNAVAILABLE: $detail"
    } else {puts $method_status AVAILABLE}
    close $method_status
    report_methodology -file [file join $out ${stage}-methodology.rpt]
    report_drc -file [file join $out ${stage}-drc.rpt]
    set f [open [file join $out ${stage}-sync-attributes.tsv] w]
    puts $f "instance\tprimitive\tASYNC_REG\tlocation"
    foreach c [lsort [get_cells -hierarchical -filter {ASYNC_REG == TRUE}]] {
        puts $f "$c\t[get_property REF_NAME $c]\t[get_property ASYNC_REG $c]\t[get_property LOC $c]"
    }
    close $f
    set f [open [file join $out ${stage}-ram-recognition.tsv] w]
    set properties {REF_NAME RAM_MODE READ_WIDTH_A READ_WIDTH_B WRITE_WIDTH_A WRITE_WIDTH_B DOA_REG DOB_REG WRITE_MODE_A WRITE_MODE_B}
    puts $f "instance\t[join $properties \t]"
    foreach c [lsort [get_cells -hierarchical -filter {REF_NAME =~ RAM*}]] {
        set row [list $c];set available [list_property $c]
        foreach p $properties {
            if {[lsearch -exact $available $p] >= 0} {lappend row [get_property $p $c]} else {lappend row UNAVAILABLE}
        }
        puts $f [join $row \t]
    }
    close $f
    set proof [open [file join $out ${stage}-gray-applied-proof.tsv] w]
    puts $proof "fifo\tsource\tstart_C\tfirst_D\trequirement_ns\tbudget_ns\texception\tslack_ns\tdatapath_ns"
    set up [get_cells -hierarchical -regexp {^(commands|writes|acks|lines|pixels)/(wup|rup)_reg$}]
    if {[llength $up] != 10} {error "V107 sync prototype lost an independent peer-up notification"}
    set f [open [file join $out ${stage}-independent-up-flags.tsv] w]
    puts $f "cell\tDONT_TOUCH\tprimitive"
    foreach cell [lsort $up] {
        set keep [get_property DONT_TOUCH $cell]
        if {!$keep} {error "V107 sync prototype peer-up DONT_TOUCH missing"}
        puts $f "$cell\t$keep\t[get_property REF_NAME $cell]"
    }
    close $f
    # Per-bundle paths prove the first-stage bounds were not masked.
    foreach fifo {commands writes acks lines pixels} {
        foreach direction {{wgray wgray_meta} {rgray rgray_meta}} {
            lassign $direction source first
            set c $v107_gray_c($fifo,$source);set d $v107_gray_d($fifo,$source)
            if {[llength $c] != 4 || [llength $d] != 4} {error "lost exact mapped Gray endpoints"}
            report_timing -delay_type max -from $c -to $d -max_paths 4 -path_type full_clock_expanded -file [file join $out ${stage}-${fifo}-${source}-first-sync.rpt]
            set paths [get_timing_paths -delay_type max -from $c -to $d -max_paths 4 -nworst 1]
            if {[llength $paths] != 4} {error "V107 Gray timing path coverage is not four bits: $fifo/$source"}
            set found {}
            foreach path $paths {
                set launch [get_property STARTPOINT_PIN $path];set endpoint [get_property ENDPOINT_PIN $path]
                set requirement [get_property REQUIREMENT $path];set exception [get_property EXCEPTION $path]
                set budget $v107_gray_budget($fifo,$source)
                puts $proof "$fifo\t$source\t$launch\t$endpoint\t$requirement\t$budget\t$exception\t[get_property SLACK $path]\t[get_property DATAPATH_DELAY $path]"
                if {[lsearch -exact $c $launch] < 0 || [lsearch -exact $d $endpoint] < 0} {error "V107 unexpected Gray timing path endpoint"}
                if {abs($requirement-$budget) > 0.001 || $exception eq {}} {error "V107 Gray launch bound not applied: $fifo/$source $requirement $budget $exception"}
                lappend found $endpoint
            }
            if {[lsort -unique $found] ne [lsort $d]} {error "V107 Gray first-stage timing coverage incomplete"}
        }
    }
    close $proof
}
