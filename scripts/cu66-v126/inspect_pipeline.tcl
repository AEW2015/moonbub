# Supplemental read-only analysis of an existing routed component checkpoint.
# Usage: vivado ... -source inspect_pipeline.tcl -tclargs ROUTE_DCP OUTPUT_DIR
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

proc sequential_group {family pattern declared_width {bank_filter ALL}} {
    global inventory widths
    set cells [get_cells -quiet -hierarchical -filter "NAME =~ $pattern && REF_NAME =~ FD*"]
    if {$bank_filter ne "ALL"} {
        set selected {}
        foreach cell $cells {
            set leaf [lindex [split $cell /] end]
            if {[regexp {bank_(epoch|block)_reg\[([01])\]\[([0-9]+)\]} $leaf unused field bank bit]} {
                if {$bank eq $bank_filter} {lappend selected $cell}
            } else {gap $family UNPARSED_BANK_CELL $cell}
        }
        set cells $selected
    }
    emit REGISTER_FAMILY $family PATTERN $pattern
    emit REGISTER_FAMILY $family DECLARED_RTL_WIDTH $declared_width
    emit REGISTER_FAMILY $family CELL_COUNT [llength $cells]
    set indices {};set unknown 0;set span 0
    foreach cell [lsort $cells] {
        set q [get_pins -quiet -of_objects $cell -filter {REF_PIN_NAME == Q}]
        set leaf [lindex [split $cell /] end]
        set bit UNKNOWN
        if {$bank_filter ne "ALL" && [regexp {bank_(epoch|block)_reg\[([01])\]\[([0-9]+)\]} $leaf unused field bank parsed]} {
            set bit $parsed;lappend indices $bit
            if {$bit+1>$span} {set span [expr {$bit+1}]}
        } elseif {[regexp {\[([0-9]+)\]} $leaf unused parsed]} {
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

# Bank-owner sources and return endpoints; two-dimensional banks are selected
# and indexed independently so bank index is never confused with bit index.
set sources [dict create]
foreach {family pattern width} {
    emit_bank *scratch/emit_bank_reg* 1
    bank_ready *scratch/bank_ready_reg* 2
    current_child_epoch *coefficients/current_child_epoch_reg* 32
    expected_block *coefficients/expected_block_reg* 16
    raw_mode *synchronous.ingress/raw_mode_reg* 1
    raw_position *synchronous.ingress/raw_position_reg* 32
    rank_threshold_mask *scratch/rank_threshold_mask_reg* 64
} {dict set sources $family [sequential_group $family $pattern $width]}
foreach bank {0 1} {
    dict set sources bank_epoch${bank} [sequential_group bank_epoch${bank} *scratch/bank_epoch_reg* 32 $bank]
    dict set sources bank_block${bank} [sequential_group bank_block${bank} *scratch/bank_block_reg* 16 $bank]
}
set targets [dict create]
foreach {family pattern} {
    scratch_busy_owned *scratch/busy_owned_reg*
    scratch_state *scratch/state_reg*
    producer_state *coefficients/state_reg*
} {
    set cells [get_cells -quiet -hierarchical -filter "NAME =~ $pattern && REF_NAME =~ FD*"]
    dict set targets $family [endpoint_group ${family}_D_CE_R_S $cells \
        {REF_PIN_NAME == D || REF_PIN_NAME == CE || REF_PIN_NAME == R || REF_PIN_NAME == S}]
}
dict for {family pins} $sources {
    inspect_paths ${family}-all-endpoints $pins ALL_ENDPOINTS
    dict for {target endpoints} $targets {inspect_paths ${family}-to-${target} $pins $endpoints}
}
# Combinational lane nets may be optimized or renamed; absence is an explicit
# observation gap, not evidence for an unmeasured mapped topology.
foreach pattern {*tile_owner_match* *child_owner_match*} {
    set nets [get_nets -quiet -hierarchical -filter "NAME =~ $pattern"]
    emit OWNER_LANE_NET_GROUP $pattern NET_COUNT [llength $nets]
    if {[llength $nets]==0} {gap $pattern NO_MATCHED_LANE_NETS {No topology claim from absent name}}
    foreach net [lsort $nets] {
        emit OWNER_LANE_NET $net KEEP [get_property KEEP $net]
        emit OWNER_LANE_NET $net PIN_COUNT [llength [get_pins -quiet -of_objects $net]]
    }
}
set cells [get_cells -quiet -hierarchical -filter {NAME =~ *admission/state_reg* && REF_NAME =~ FD*}]
set ends [endpoint_group admission_state $cells {REF_PIN_NAME == D || REF_PIN_NAME == CE || REF_PIN_NAME == R || REF_PIN_NAME == S}]
set pins [sequential_group admission_cursor *admission/cursor_reg* 32]
inspect_paths admission_cursor-all-endpoints $pins ALL_ENDPOINTS
inspect_paths admission_cursor-to-admission_state $pins $ends
set ram [get_cells -quiet -hierarchical -filter {NAME =~ *admission/memory_reg* && REF_NAME =~ RAMB*}]
set ends [endpoint_group admission_ram_enable $ram {REF_PIN_NAME == ENARDEN || REF_PIN_NAME == ENBWREN}]
foreach {family pattern width} {
    refill_prepared_req_addr *refill_queue/prepared_req_addr_reg* 32
    refill_issued *refill_queue/issued_reg* 32
} {
    set pins [sequential_group $family $pattern $width]
    inspect_paths ${family}-all-endpoints $pins ALL_ENDPOINTS
    inspect_paths ${family}-to-admission_ram_enable $pins $ends
}
# Retained V125 admission predicate sources and local consumers. New scalar sources may
# be absent in the two baseline checkpoints; preserve that gap explicitly.
set tile_sources [dict create]
foreach {family pattern width} {
    admission_tile *admission/tile_reg* 32
    admission_plane *admission/plane_reg* 2
    admission_group_end *admission/group_end_reg* 32
    admission_group_tag *admission/group_tag_reg* 2
    admission_coord_cell *admission/coord_cell_reg* 11
    prepared_tile_hidden *admission/prepared_tile_hidden_reg* 1
    prepared_tile_terminal *admission/prepared_tile_terminal_reg* 1
    prepared_group_terminal *admission/prepared_group_terminal_reg* 1
} {dict set tile_sources $family [sequential_group $family $pattern $width]}
set tile_targets [dict create]
foreach {family pattern} {
    admission_tile *admission/tile_reg*
    admission_plane *admission/plane_reg*
    admission_group_end *admission/group_end_reg*
    admission_coordinate *admission/coord_*_reg*
    admission_state *admission/state_reg*
    prepared_tile_hidden *admission/prepared_tile_hidden_reg*
    prepared_tile_terminal *admission/prepared_tile_terminal_reg*
    prepared_group_terminal *admission/prepared_group_terminal_reg*
} {
    set cells [get_cells -quiet -hierarchical -filter "NAME =~ $pattern && REF_NAME =~ FD*"]
    dict set tile_targets $family [endpoint_group ${family}_D_CE $cells \
        {REF_PIN_NAME == D || REF_PIN_NAME == CE}]
}
set mode_rams [get_cells -quiet -hierarchical -filter {NAME =~ *admission/mode_store/* && REF_NAME =~ RAMB*}]
dict set tile_targets mode_RAM_EN_WE [endpoint_group mode_RAM_EN_WE $mode_rams \
    {REF_PIN_NAME =~ EN* || REF_PIN_NAME =~ WE*}]
dict set tile_targets mode_RAM_data [endpoint_group mode_RAM_data $mode_rams \
    {REF_PIN_NAME =~ DI*}]
dict for {family pins} $tile_sources {
    inspect_paths ${family}-all-endpoints $pins ALL_ENDPOINTS
    dict for {target endpoints} $tile_targets {inspect_paths ${family}-to-${target} $pins $endpoints}
}
# V126 producer pipeline families, including both new register boundaries.
# Actual source widths: cursor13/cache11/plane2/state8/successor13/cell11.
set producer_sources [dict create]
foreach {family pattern width} {
    producer_tile_cursor *coefficients/tile_cursor_reg* 13
    producer_cell_cache *coefficients/producer_cell_cache_reg* 11
    producer_plane *coefficients/plane_reg* 2
    producer_state *coefficients/state_reg* 8
    prepared_successor_tile *coefficients/prepared_successor_tile_reg* 13
    prepared_successor_cell *coefficients/prepared_successor_cell_reg* 11
} {dict set producer_sources $family [sequential_group $family $pattern $width]}
set producer_targets [dict create]
foreach {family pattern} {
    producer_cell_cache *coefficients/producer_cell_cache_reg*
    producer_tile_cursor *coefficients/tile_cursor_reg*
    producer_state *coefficients/state_reg*
    prepared_successor_tile *coefficients/prepared_successor_tile_reg*
    prepared_successor_cell *coefficients/prepared_successor_cell_reg*
} {
    set cells [get_cells -quiet -hierarchical -filter "NAME =~ $pattern && REF_NAME =~ FD*"]
    dict set producer_targets $family [endpoint_group ${family}_D_CE $cells \
        {REF_PIN_NAME == D || REF_PIN_NAME == CE}]
}
dict for {family pins} $producer_sources {
    inspect_paths ${family}-all-endpoints $pins ALL_ENDPOINTS
    dict for {target endpoints} $producer_targets {inspect_paths ${family}-to-${target} $pins $endpoints}
}
emit SUMMARY current QUALIFICATION NONE_READONLY_CHECKPOINT_OBSERVATION
close $path_table
close $inventory
close $widths
close $gaps
close $log
set status [open [file join $out status.txt] w]
puts $status "V126_PIPELINE_READONLY_INSPECTION_COMPLETE; existing checkpoint only; no new physical trial or positive repeat"
close $status
close_design
exit
