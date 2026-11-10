# Supplemental read-only analysis of an existing routed component checkpoint.
# Usage: vivado ... -source inspect_padding.tcl -tclargs ROUTE_DCP OUTPUT_DIR
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
    if {$from eq "ALL_STARTPOINTS"} {
        emit TIMING_FAMILY $family SOURCE_PIN_COUNT ALL_TIMED_STARTPOINTS
    } else {emit TIMING_FAMILY $family SOURCE_PIN_COUNT [llength $from]}
    if {[llength $from] == 0} {
        gap $family NO_SOURCE_PINS "No -from query executed; empty sources never broaden to all startpoints."
        return
    }
    if {$to ne "ALL_ENDPOINTS" && [llength $to] == 0} {
        gap $family NO_ENDPOINT_PINS "No -to query executed; empty endpoints never broaden to all endpoints."
        return
    }
    if {$from eq "ALL_STARTPOINTS"} {
        emit TIMING_FAMILY $family SOURCE_SCOPE ALL_TIMED_STARTPOINTS
        set paths [get_timing_paths -quiet -to $to -delay_type max -max_paths 15 -nworst 1]
    } elseif {$to eq "ALL_ENDPOINTS"} {
        emit TIMING_FAMILY $family ENDPOINT_SCOPE ALL_TIMED_ENDPOINTS
        set paths [get_timing_paths -quiet -from $from -delay_type max -max_paths 15 -nworst 1]
    } else {
        emit TIMING_FAMILY $family ENDPOINT_PIN_COUNT [llength $to]
        set paths [get_timing_paths -quiet -from $from -to $to -delay_type max -max_paths 15 -nworst 1]
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
    if {$from eq "ALL_STARTPOINTS"} {
        report_timing -to $to -delay_type max -max_paths 15 -nworst 1 \
            -path_type full_clock_expanded -file [file join $out ${family}.rpt]
    } elseif {$to eq "ALL_ENDPOINTS"} {
        report_timing -from $from -delay_type max -max_paths 15 -nworst 1 \
            -path_type full_clock_expanded -file [file join $out ${family}.rpt]
    } else {
        report_timing -from $from -to $to -delay_type max -max_paths 15 -nworst 1 \
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

# Supplemental cache/header-only queries; no broad path family substitution.
# Scalar cache is one source payload bit. Header is 128 bytes, not 128 bits.
proc header_group {} {
    global inventory widths
    set family admission_header
    set cells [get_cells -quiet -hierarchical -filter {NAME =~ *admission/header_reg* && REF_NAME =~ FD*}]
    set indices {};set unknown 0;set span 0
    emit REGISTER_FAMILY $family DECLARED_RTL_WIDTH 1024
    emit REGISTER_FAMILY $family CELL_COUNT [llength $cells]
    foreach cell [lsort $cells] {
        set bit UNKNOWN
        set leaf [lindex [split $cell /] end]
        if {[regexp {header_reg\[([0-9]+)\]\[([0-9]+)\]} $leaf unused byte lane] && $byte<128 && $lane<8} {
            set bit [expr {8*$byte+$lane}];lappend indices $bit
            if {$bit+1>$span} {set span [expr {$bit+1}]}
        } else {
            incr unknown;gap $family UNPARSED_REGISTER_BIT "No exact bounded byte/bit indices in $cell; not counted as a mapped RTL bit"
        }
        set q [get_pins -quiet -of_objects $cell -filter {REF_PIN_NAME == Q}]
        puts $inventory "$family\t$cell\t[get_property REF_NAME $cell]\t[get_property LOC $cell]\t[llength $q]\t1024\t$bit"
    }
    set unique [lsort -integer -unique $indices];set missing {}
    for {set bit 0} {$bit<1024} {incr bit} {if {[lsearch -exact $unique $bit]<0} {lappend missing $bit}}
    puts $widths "$family\t1024\t[llength $cells]\t[llength $unique]\t$span\t$unknown\t[join $unique ,]\t[join $missing ,]"
    flush $inventory;flush $widths
    if {[llength $cells]==0} {gap $family NO_MATCHING_CELLS {No named header FFs; no path-elimination claim};return {}}
    if {[llength $cells]!=1024 || [llength $unique]!=1024} {gap $family DECLARED_PHYSICAL_WIDTH_DIFFERENCE {Declared1024; physical mapping/replication/constant pruning is only observed, not a width-proof}}
    return [get_pins -quiet -of_objects $cells -filter {REF_PIN_NAME == Q}]
}
set cache_cells [get_cells -quiet -hierarchical -filter {NAME =~ *admission/prepared_header_padding_ok_reg* && REF_NAME =~ FD*}]
set cache_q [sequential_group prepared_header_padding_ok *admission/prepared_header_padding_ok_reg* 1]
set cache_d [endpoint_group padding_cache_D $cache_cells {REF_PIN_NAME == D}]
set cache_ce [endpoint_group padding_cache_CE $cache_cells {REF_PIN_NAME == CE}]
set tile_cells [get_cells -quiet -hierarchical -filter {NAME =~ *admission/tile_reg* && REF_NAME =~ FD*}]
set tile_r [endpoint_group admission_tile_R $tile_cells {REF_PIN_NAME == R}]
set header_q [header_group]
set index_q [sequential_group admission_header_index *admission/header_index_reg* 32]
inspect_paths all-inputs-to-padding-cache-D ALL_STARTPOINTS $cache_d
inspect_paths all-inputs-to-padding-cache-CE ALL_STARTPOINTS $cache_ce
inspect_paths padding-cache-Q-all-endpoints $cache_q ALL_ENDPOINTS
inspect_paths padding-cache-Q-to-tile-R $cache_q $tile_r
inspect_paths all-header-Q-all-endpoints $header_q ALL_ENDPOINTS
inspect_paths all-header-Q-to-tile-R $header_q $tile_r
inspect_paths header-index-Q-to-cache-D $index_q $cache_d
inspect_paths header-index-Q-to-cache-CE $index_q $cache_ce

# Named-cache fanout only. Lists are bounded; total counts remain explicit.
set fanout [open [file join $out cache-fanout.tsv] w]
puts $fanout "cell\tQ_pin\tload_pin_count\ttiming_endpoint_count\tlisted_load_pins\tlisted_timing_endpoints"
if {[llength $cache_cells]>16} {gap padding_cache_fanout CELL_CAP {More than16 matching cache FFs; do not expand an ambiguous group}} else {
    foreach cell [lsort $cache_cells] {
        foreach q [get_pins -quiet -of_objects $cell -filter {REF_PIN_NAME == Q}] {
            set nets [get_nets -quiet -of_objects $q]
            set loads [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == IN}]
            set endpoints {}
            if {[catch {all_fanout -flat -endpoints_only $q} endpoints]} {gap $q FANOUT_QUERY_UNAVAILABLE $endpoints;set endpoints {}}
            puts $fanout "$cell\t$q\t[llength $loads]\t[llength $endpoints]\t[join [lrange [lsort $loads] 0 255] ,]\t[join [lrange [lsort $endpoints] 0 255] ,]"
            emit CACHE_FANOUT $q DIRECT_LOAD_COUNT [llength $loads]
            emit CACHE_FANOUT $q TIMING_ENDPOINT_COUNT [llength $endpoints]
            if {[llength $loads]>256 || [llength $endpoints]>256} {gap $q NAMED_FANOUT_LIST_CAP {Counts retained; each printed list capped256}}
        }
    }
}
close $fanout
emit SUMMARY current TARGETED_TIMING_FAMILIES 8
emit SUMMARY current MAX_PATHS_PER_FAMILY 15
emit SUMMARY current QUALIFICATION NONE_READONLY_CHECKPOINT_OBSERVATION
close $path_table
close $inventory
close $widths
close $gaps
close $log
set status [open [file join $out status.txt] w]
puts $status "V128_PADDING_READONLY_INSPECTION_COMPLETE; existing checkpoint only; no new physical trial or positive repeat"
close $status
close_design
exit
