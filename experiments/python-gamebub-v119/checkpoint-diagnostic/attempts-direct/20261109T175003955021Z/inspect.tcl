# Read-only inspection of one already routed V119 A checkpoint.
# No synth/opt/place/route/phys_opt/constraint/write_checkpoint/bitstream commands.
set_param general.maxThreads 2
set out /output
proc net_segments_or_direct {net} {
    set segments [get_nets -quiet -segments -of_objects $net]
    if {[llength $segments] == 0} {
        emit QUERY_GAP $net EMPTY_SEGMENTS FALLBACK_TO_DIRECT_NET
        return [list $net]
    }
    return $segments
}
file mkdir $out
set log [open [file join $out operands.tsv] w]
puts $log "kind\tobject\tproperty\tvalue"
proc emit {kind object property value} {
    global log
    set clean [string map [list "\t" {\t} "\n" {\n} "\r" {\r}] $value]
    puts $log "$kind\t$object\t$property\t$clean"
    flush $log
}
proc property_or_unavailable {object property} {
    if {[catch {get_property $property $object} value]} {return "UNAVAILABLE:$value"}
    return $value
}
proc dump_pin {pin level} {
    emit PIN $pin REF_PIN_NAME [property_or_unavailable $pin REF_PIN_NAME]
    emit PIN $pin DIRECTION [property_or_unavailable $pin DIRECTION]
    set nets [get_nets -quiet -of_objects $pin]
    emit PIN $pin NETS [join $nets {;}]
    if {[catch {lsort [all_fanin -flat -trace_arcs all -startpoints_only $pin]} starts]} {
        emit PIN $pin STARTPOINTS_UNAVAILABLE $starts
    } else {emit PIN $pin COMPLETE_STARTPOINTS [join $starts {;}]}
    foreach net $nets {
        set segments [net_segments_or_direct $net]
        emit NET $net SEGMENTS [join $segments {;}]
        set drivers [get_pins -quiet -leaf -of_objects $segments -filter {DIRECTION == OUT}]
        emit NET $net DRIVER_PINS [join $drivers {;}]
        if {[llength $drivers] == 0} {emit UNRESOLVED $net NO_DIRECT_LEAF_DRIVERS 1}
        emit NET $net PORTS [join [get_ports -quiet -of_objects $net] {;}]
        foreach driver $drivers {
            set cells [get_cells -quiet -of_objects $driver]
            if {[llength $cells] == 0} {emit UNRESOLVED $driver NO_DRIVER_CELL 1}
            foreach cell $cells {
                set ref [property_or_unavailable $cell REF_NAME]
                emit DRIVER $driver CELL $cell
                emit CELL $cell REF_NAME $ref
                if {[string match LUT* $ref]} {
                    emit CELL $cell INIT [property_or_unavailable $cell INIT]
                    foreach input [lsort [get_pins -quiet -of_objects $cell -filter {DIRECTION == IN}]] {
                        emit LUT_INPUT $input NETS [join [get_nets -quiet -of_objects $input] {;}]
                        if {$level < 2} {dump_pin $input [expr {$level+1}]}
                    }
                }
            }
        }
    }
}
open_checkpoint /input/route.dcp
emit DESIGN current PART [get_property PART [current_design]]
emit DESIGN current INSPECTION_ONLY 1
# Exact matching on full names avoids treating bracketed pin bits as glob syntax.
set carries [get_cells -quiet -hierarchical -filter {REF_NAME == CARRY4}]
set targets [list \
    coefficients/child/packet_decoder/synchronous.ingress/dbg_coef_valid_INST_0_i_11 \
    coefficients/child/packet_decoder/synchronous.ingress/dbg_coef_valid_INST_0_i_4]
set found 0
foreach target $targets {
    set index [lsearch -exact $carries $target]
    if {$index < 0} {emit UNRESOLVED $target TARGET_CARRY_NOT_FOUND 1; continue}
    incr found
    set cell [lindex $carries $index]
    emit CARRY $cell LOC [property_or_unavailable $cell LOC]
    foreach pin [lsort [get_pins -quiet -of_objects $cell]] {
        # Includes all CI,CYINIT,DI[3:0],S[3:0] and all CO/O pins.
        emit CARRY_PIN $pin DIRECTION [property_or_unavailable $pin DIRECTION]
        emit CARRY_PIN $pin NETS [join [get_nets -quiet -of_objects $pin] {;}]
        if {[property_or_unavailable $pin DIRECTION] eq "IN"} {dump_pin $pin 0}
    }
}
set nets [get_nets -quiet -hierarchical]
set named_nets [list \
    {coefficients/admission/mode_store/state_reg[0]_1} \
    coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/base_abort \
    coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/reset_8 \
    coefficients/child/scratch/running_reg_29 \
    coefficients/child/scratch/packet_abort \
    {coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/limit0_2[0]} \
    coefficients/child/scratch/start0 \
    coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/sel_rep__0 \
    coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/parser_in_ready \
    coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/stage_word_ready \
    coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/prepared_request_addr1104_out \
    {coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/prepared_request_addr[15]_i_16_n_0}]
set found_nets 0
foreach target $named_nets {
    set index [lsearch -exact $nets $target]
    if {$index < 0} {emit UNRESOLVED $target TARGET_NET_NOT_FOUND 1; continue}
    incr found_nets
    set net [lindex $nets $index]
    set segments [net_segments_or_direct $net]
    emit CONTROL_NET $net SEGMENTS [join $segments {;}]
    set drivers [get_pins -quiet -leaf -of_objects $segments -filter {DIRECTION == OUT}]
    set loads [get_pins -quiet -leaf -of_objects $segments -filter {DIRECTION == IN}]
    emit CONTROL_NET $net DRIVER_PINS [join $drivers {;}]
    if {[llength $drivers] == 0} {emit UNRESOLVED $net NO_CONTROL_DRIVER 1}
    if {[llength $loads] == 0} {emit UNRESOLVED $net NO_CONTROL_LEAF_LOADS 1}
    emit CONTROL_NET $net ALL_LOAD_PINS [join [lsort $loads] {;}]
    emit CONTROL_NET $net LOAD_PIN_COUNT [llength $loads]
    foreach driver $drivers {dump_pin $driver 0}
}
emit SUMMARY carries FOUND $found
emit SUMMARY cancellation_nets FOUND $found_nets
close $log
set status [open [file join $out status.txt] w]
puts $status "V119_READONLY_DIRECT_CHECKPOINT_DIAGNOSTIC_COMPLETE carries=$found cancellation_nets=$found_nets"
close $status
close_design
exit
