# Supplemental read-only analysis of an existing routed component checkpoint.
# Usage: vivado ... -source inspect_request.tcl -tclargs ROUTE_DCP OUTPUT_DIR
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
puts $inventory "family\tinstance\tprimitive\tlocation\tQ_pin_count"
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

proc sequential_group {family pattern} {
    global inventory
    set cells [get_cells -quiet -hierarchical -filter "NAME =~ $pattern && REF_NAME =~ FD*"]
    emit REGISTER_FAMILY $family PATTERN $pattern
    emit REGISTER_FAMILY $family CELL_COUNT [llength $cells]
    if {[llength $cells] == 0} {
        gap $family NO_MATCHING_CELLS "Pattern $pattern; absence is not proof of path elimination."
        return {}
    }
    foreach cell [lsort $cells] {
        set q [get_pins -quiet -of_objects $cell -filter {REF_PIN_NAME == Q}]
        puts $inventory "$family\t$cell\t[get_property REF_NAME $cell]\t[get_property LOC $cell]\t[llength $q]"
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

set sources [dict create]
foreach {family pattern} {
    prepared_req_addr *refill_queue/prepared_req_addr_reg*
    issued *refill_queue/issued_reg*
    offset *refill_queue/offset_reg*
} {
    dict set sources $family [sequential_group $family $pattern]
}

# Retain the exact packet-RAM family of the B125 ENBWREN destination, while
# enumerating both physical ports; unrelated admission lookup RAMs are excluded.
set ram_cells [get_cells -quiet -hierarchical -filter {NAME =~ *admission/memory_reg* && REF_NAME =~ RAMB*}]
foreach cell [lsort $ram_cells] {
    emit PACKET_RAM $cell REF_NAME [get_property REF_NAME $cell]
    emit PACKET_RAM $cell LOC [get_property LOC $cell]
}
set targets [dict create]
dict set targets admission_ram_enable [endpoint_group admission_ram_enable $ram_cells \
    {REF_PIN_NAME == ENARDEN || REF_PIN_NAME == ENBWREN}]
dict set targets admission_ram_address [endpoint_group admission_ram_address $ram_cells \
    {REF_PIN_NAME =~ ADDR*}]

set cursor_cells [get_cells -quiet -hierarchical -filter {NAME =~ *refill_queue/prepared_req_addr_reg* && REF_NAME =~ FD*}]
dict set targets cursor_update [endpoint_group cursor_update $cursor_cells {REF_PIN_NAME == D || REF_PIN_NAME == CE}]
set request_cells [get_cells -quiet -hierarchical -filter {REF_NAME =~ FD* && (NAME =~ *refill_queue/pending_reg* || NAME =~ *refill_queue/pending_addr_reg* || NAME =~ *refill_queue/pending_last_reg* || NAME =~ *refill_queue/issued_reg*)}]
dict set targets queue_request_state [endpoint_group queue_request_state $request_cells {REF_PIN_NAME == D || REF_PIN_NAME == CE}]
set response_cells [get_cells -quiet -hierarchical -filter {REF_NAME =~ FD* && (NAME =~ *admission/ram_addr_reg* || NAME =~ *admission/ram_epoch_reg* || NAME =~ *admission/replay_rsp_valid_reg*)}]
dict set targets admission_response_owner [endpoint_group admission_response_owner $response_cells {REF_PIN_NAME == D || REF_PIN_NAME == CE}]

dict for {family pins} $sources {
    inspect_paths ${family}-all-endpoints $pins ALL_ENDPOINTS
    dict for {target endpoints} $targets {
        inspect_paths ${family}-to-${target} $pins $endpoints
    }
}
emit SUMMARY current QUALIFICATION NONE_READONLY_CHECKPOINT_OBSERVATION
close $path_table
close $inventory
close $gaps
close $log
set status [open [file join $out status.txt] w]
puts $status "V121_REQUEST_READONLY_INSPECTION_COMPLETE; existing checkpoint only; no new physical trial or positive repeat"
close $status
close_design
exit
