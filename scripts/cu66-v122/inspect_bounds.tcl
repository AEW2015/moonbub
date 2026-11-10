# Supplemental read-only analysis of an existing routed component checkpoint.
# Usage: vivado ... -source inspect_bounds.tcl -tclargs ROUTE_DCP OUTPUT_DIR
# No implementation command, setting, constraint or checkpoint write is used.
if {[llength $argv] != 2} {error "expected existing ROUTE_DCP and separate OUTPUT_DIRECTORY"}
set checkpoint [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
if {![file isfile $checkpoint]} {error "checkpoint does not exist: $checkpoint"}
file mkdir $out
if {[file exists [file join $out status.txt]]} {error "inspection output already has status.txt; use a fresh directory"}

set log [open [file join $out inspection.tsv] w]
puts $log "kind\tobject\tproperty\tvalue"
set gaps [open [file join $out query-gaps.tsv] w]
puts $gaps "family\tstatus\tdetail"
set inventory [open [file join $out register-inventory.tsv] w]
puts $inventory "family\tinstance\tprimitive\tlocation\tQ_pin_count\tdeclared_width\tparsed_bit_index"
set widths [open [file join $out register-width-summary.tsv] w]
puts $widths "family\tdeclared_width\tphysical_cell_count\tunique_named_bit_count\tmax_named_index_plus_one\tunparsed_cell_count\tobserved_named_indices\tunmatched_declared_indices"
set path_table [open [file join $out targeted-paths.tsv] w]
puts $path_table "family\tindex\tstartpoint\tendpoint\tslack_ns\tdata_path_ns\tlogic_levels"

proc emit {kind object property value} {
    global log
    set clean [string map [list "\t" {\t} "\n" {\n} "\r" {\r}] $value]
    puts $log "$kind\t$object\t$property\t$clean"
    flush $log
}

proc gap {family status detail} {
    global gaps
    set clean [string map [list "\t" {\t} "\n" {\n} "\r" {\r}] $detail]
    puts $gaps "$family\t$status\t$clean"
    flush $gaps
    emit QUERY_GAP $family $status $detail
}

proc sequential_group {family pattern declared_width} {
    global inventory widths
    set cells [get_cells -quiet -hierarchical -filter "NAME =~ $pattern && REF_NAME =~ FD*"]
    emit REGISTER_FAMILY $family PATTERN $pattern
    emit REGISTER_FAMILY $family DECLARED_RTL_WIDTH $declared_width
    emit REGISTER_FAMILY $family CELL_COUNT [llength $cells]
    set indices {};set unknown 0;set span 0
    foreach cell [lsort $cells] {
        set q [get_pins -quiet -of_objects $cell -filter {REF_PIN_NAME == Q}]
        set leaf [lindex [split $cell /] end]
        set bit UNKNOWN
        if {[regexp {\[([0-9]+)\]} $leaf unused parsed]} {
            set bit $parsed
            lappend indices $bit
            if {$bit+1>$span} {set span [expr {$bit+1}]}
        } elseif {$declared_width==1} {
            set bit 0;lappend indices 0;set span 1
        } else {
            incr unknown
            gap $family UNPARSED_REGISTER_BIT "Exact name $cell has no bracketed index; not counted as an observed RTL bit."
        }
        puts $inventory "$family\t$cell\t[get_property REF_NAME $cell]\t[get_property LOC $cell]\t[llength $q]\t$declared_width\t$bit"
    }
    set unique [lsort -integer -unique $indices]
    set missing {}
    for {set bit 0} {$bit<$declared_width} {incr bit} {
        if {[lsearch -exact $unique $bit]<0} {lappend missing $bit}
    }
    puts $widths "$family\t$declared_width\t[llength $cells]\t[llength $unique]\t$span\t$unknown\t[join $unique ,]\t[join $missing ,]"
    flush $inventory;flush $widths
    emit REGISTER_FAMILY $family UNIQUE_NAMED_BIT_COUNT [llength $unique]
    emit REGISTER_FAMILY $family OBSERVED_NAMED_INDICES $unique
    emit REGISTER_FAMILY $family UNMATCHED_DECLARED_INDICES $missing
    if {[llength $cells] == 0} {
        gap $family NO_MATCHING_CELLS "Pattern $pattern; absence is not proof of path elimination or bit-width narrowing."
        return {}
    }
    if {[llength $unique]!=$declared_width||[llength $cells]!=$declared_width} {
        gap $family DECLARED_PHYSICAL_WIDTH_DIFFERENCE "Declared width $declared_width, physical cells [llength $cells], unique named indices [llength $unique]; inspect constants, replicas, renaming and synthesis before interpreting."
    }
    set pins [get_pins -quiet -of_objects $cells -filter {REF_PIN_NAME == Q}]
    emit REGISTER_FAMILY $family Q_PIN_COUNT [llength $pins]
    if {[llength $pins] == 0} {gap $family NO_MATCHING_Q_PINS "Sequential cells matched but no Q pins matched."}
    return $pins
}

proc endpoint_group {family cells pin_filter} {
    emit ENDPOINT_FAMILY $family CELL_COUNT [llength $cells]
    emit ENDPOINT_FAMILY $family PIN_FILTER $pin_filter
    if {[llength $cells] == 0} {
        gap $family NO_MATCHING_CELLS "Endpoint cell selection empty; no timing query was substituted."
        return {}
    }
    set pins [get_pins -quiet -of_objects $cells -filter $pin_filter]
    emit ENDPOINT_FAMILY $family PIN_COUNT [llength $pins]
    foreach pin [lsort $pins] {emit ENDPOINT_PIN $family NAME $pin}
    if {[llength $pins] == 0} {gap $family NO_MATCHING_ENDPOINT_PINS "Cells matched but endpoint pin filter was empty."}
    return $pins
}

proc inspect_paths {family from to} {
    global out path_table
    emit TIMING_FAMILY $family SOURCE_PIN_COUNT [llength $from]
    if {[llength $from] == 0} {
        gap $family NO_SOURCE_PINS "No -from query executed; empty sources never broaden to all startpoints."
        return
    }
    if {$to ne "ALL_ENDPOINTS" && [llength $to] == 0} {
        gap $family NO_ENDPOINT_PINS "No -to query executed; empty endpoints never broaden to all endpoints."
        return
    }
    if {$to eq "ALL_ENDPOINTS"} {
        emit TIMING_FAMILY $family ENDPOINT_SCOPE ALL_TIMED_ENDPOINTS
        set paths [get_timing_paths -quiet -from $from -delay_type max -max_paths 50 -nworst 1]
    } else {
        emit TIMING_FAMILY $family ENDPOINT_PIN_COUNT [llength $to]
        set paths [get_timing_paths -quiet -from $from -to $to -delay_type max -max_paths 50 -nworst 1]
    }
    emit TIMING_FAMILY $family PATH_COUNT [llength $paths]
    if {[llength $paths] == 0} {
        gap $family NO_TIMED_PATHS "Nonempty selected pins have no returned max-delay paths; no elimination or timing-pass claim."
        return
    }
    set index 0
    foreach path $paths {
        incr index
        puts $path_table "$family\t$index\t[get_property STARTPOINT_PIN $path]\t[get_property ENDPOINT_PIN $path]\t[get_property SLACK $path]\t[get_property DATAPATH_DELAY $path]\t[get_property LOGIC_LEVELS $path]"
    }
    if {$to eq "ALL_ENDPOINTS"} {
        report_timing -from $from -delay_type max -max_paths 50 -nworst 1 \
            -path_type full_clock_expanded -file [file join $out ${family}.rpt]
    } else {
        report_timing -from $from -to $to -delay_type max -max_paths 50 -nworst 1 \
            -path_type full_clock_expanded -file [file join $out ${family}.rpt]
    }
    flush $path_table
}

open_checkpoint $checkpoint
emit DESIGN current CHECKPOINT $checkpoint
emit DESIGN current TOOL [version]
emit DESIGN current INSPECTION_ONLY 1
set part [get_property PART [current_design]]
emit DESIGN current PART $part
if {$part ne "xc7a100tcsg324-1"} {error "unexpected checkpoint part: $part"}
set clocks [get_clocks -quiet]
emit DESIGN current CLOCK_COUNT [llength $clocks]
if {[llength $clocks] != 1} {error "expected exactly one existing component clock"}
set clock_name [get_property NAME $clocks]
set period [get_property PERIOD $clocks]
set wave [get_property WAVEFORM $clocks]
emit CLOCK $clock_name PERIOD_NS $period
emit CLOCK $clock_name WAVEFORM $wave
if {$clock_name ne "component_clk" || abs($period-8.0)>0.0001} {error "expected existing component_clk at 8 ns"}
if {[llength $wave] != 2 || abs([lindex $wave 0])>0.0001 || abs([lindex $wave 1]-4.0)>0.0001} {
    error "expected existing 0/4 ns component clock waveform"
}
emit DESIGN current PART_AND_EXISTING_CLOCK_VALIDATED 1
report_clocks -file [file join $out checkpoint-clocks.rpt]
report_route_status -file [file join $out checkpoint-route-status.rpt]

# Declared widths are source declarations, not claims about retained hardware.
set admission_sources [dict create]
set admission_targets [dict create]
foreach {family pattern declared_width} {
    admission_cursor *admission/cursor_reg* 32
    admission_word_acc *admission/word_acc_reg* 24
    bounds_cursor_base *admission/bounds_cursor_base_reg* 64
    bounds_word_base *admission/bounds_word_base_reg* 64
    bounds_length_total *admission/bounds_length_total_reg* 64
    bounds_number_plus12 *admission/bounds_number_plus12_reg* 32
    prepared_number_outside *admission/prepared_number_outside_reg* 1
    prepared_length_invalid *admission/prepared_length_invalid_reg* 1
} {
    dict set admission_sources $family [sequential_group $family $pattern $declared_width]
    # The old cursor is a source only. New payload and old word accumulator
    # endpoints expose both recurrence and successive preparation stages.
    if {$family ne "admission_cursor"} {
        set cells [get_cells -quiet -hierarchical -filter "NAME =~ $pattern && REF_NAME =~ FD*"]
        dict set admission_targets $family [endpoint_group ${family}_data_enable $cells \
            {REF_PIN_NAME == D || REF_PIN_NAME == CE}]
    }
}
set state_cells [get_cells -quiet -hierarchical -filter {NAME =~ *admission/state_reg* && REF_NAME == FDRE}]
dict set admission_targets admission_state [endpoint_group admission_state $state_cells \
    {REF_PIN_NAME == D || REF_PIN_NAME == CE}]

# Deliberate cross product: every selected source is checked against each
# selected stage, including CE and shared state decode; unreachable pairs are
# explicit NO_TIMED_PATHS gaps. No empty selection broadens a timing query.
dict for {family pins} $admission_sources {
    inspect_paths ${family}-all-endpoints $pins ALL_ENDPOINTS
    dict for {target endpoints} $admission_targets {
        inspect_paths ${family}-to-${target} $pins $endpoints
    }
}

# Separate unchanged V121 refill-request observation. Keep the B125 packet RAM
# family and enumerate both physical enables; unrelated lookup RAMs excluded.
set ram_cells [get_cells -quiet -hierarchical -filter {NAME =~ *admission/memory_reg* && REF_NAME =~ RAMB*}]
foreach cell [lsort $ram_cells] {
    emit PACKET_RAM $cell REF_NAME [get_property REF_NAME $cell]
    emit PACKET_RAM $cell LOC [get_property LOC $cell]
}
set ram_enable [endpoint_group refill_admission_ram_enable $ram_cells \
    {REF_PIN_NAME == ENARDEN || REF_PIN_NAME == ENBWREN}]
foreach {family pattern declared_width} {
    refill_prepared_req_addr *refill_queue/prepared_req_addr_reg* 32
    refill_issued *refill_queue/issued_reg* 32
    refill_offset *refill_queue/offset_reg* 32
} {
    set pins [sequential_group $family $pattern $declared_width]
    inspect_paths ${family}-all-endpoints $pins ALL_ENDPOINTS
    inspect_paths ${family}-to-admission_ram_enable $pins $ram_enable
}
emit SUMMARY current QUALIFICATION NONE_READONLY_CHECKPOINT_OBSERVATION
close $path_table
close $inventory
close $widths
close $gaps
close $log
set status [open [file join $out status.txt] w]
puts $status "V122_BOUNDS_READONLY_INSPECTION_COMPLETE; existing checkpoint only; no new physical trial or positive repeat"
close $status
close_design
exit
