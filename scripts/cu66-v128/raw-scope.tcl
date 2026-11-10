# Read-only V128 supplement; inserted before the existing query closes files.
set raw_sources [dict create]
foreach {family pattern width} {
    ingress_raw_epoch *synchronous.ingress/context_epoch_reg* 32
    context_active_epoch *synchronous.ingress/context_decoder/context_epoch_reg* 32
    context_output_epoch *synchronous.ingress/context_decoder/out_epoch_reg* 32
} {dict set raw_sources $family [sequential_group $family $pattern $width]}
dict for {family pins} $raw_sources {
    inspect_paths ${family}-all-endpoints $pins ALL_ENDPOINTS
    dict for {target endpoints} $targets {inspect_paths ${family}-to-${target} $pins $endpoints}
}
# Exact baseline cells and input drivers; candidate absence is a recorded gap.
set traced [dict create]
proc trace_cell {cell depth} {
    global traced
    set name [get_property NAME $cell]
    if {[dict exists $traced $name]} {return}
    if {[dict size $traced]>=128} {gap RAW_CRITICAL_TRACE CELL_CAP "128 unique cells; remaining trace not expanded";return}
    dict set traced $name 1
    set ref [get_property REF_NAME $cell]
    emit RAW_TRACE_CELL $name REF_NAME $ref
    emit RAW_TRACE_CELL $name LOC [get_property LOC $cell]
    if {[string match LUT* $ref]} {emit RAW_TRACE_CELL $name INIT [get_property INIT $cell]}
    foreach pin [lsort [get_pins -quiet -of_objects $cell -filter {DIRECTION == IN}]] {
        if {[get_property REF_PIN_NAME $pin] in {C CLK R CE}} {continue}
        set nets [get_nets -quiet -of_objects $pin]
        set drivers [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == OUT}]
        emit RAW_TRACE_PIN [get_property NAME $pin] NETS $nets
        emit RAW_TRACE_PIN [get_property NAME $pin] DRIVERS $drivers
        if {$depth>0} {
            foreach driver $drivers {
                foreach parent [get_cells -quiet -of_objects $driver] {
                    if {[string match LUT* [get_property REF_NAME $parent]] || [get_property REF_NAME $parent] eq "CARRY4"} {trace_cell $parent [expr {$depth-1}]}
                }
            }
        }
    }
    foreach pin [get_pins -quiet -of_objects $cell -filter {DIRECTION == OUT}] {
        set starts [all_fanin -flat -startpoints_only $pin]
        emit RAW_TRACE_FANIN [get_property NAME $pin] STARTPOINT_COUNT [llength $starts]
        if {[llength $starts]<=256} {emit RAW_TRACE_FANIN [get_property NAME $pin] STARTPOINTS [lsort $starts]} else {
            gap [get_property NAME $pin] STARTPOINT_CAP "More than256 timing startpoints; names not recorded"
        }
    }
}
foreach name {
    {coefficients/child/packet_decoder/synchronous.ingress/context_decoder/dbg_coef_epoch[4]_INST_0}
    {coefficients/child/packet_decoder/synchronous.ingress/context_decoder/error_reg[0]_i_9}
    {coefficients/child/packet_decoder/synchronous.ingress/context_decoder/error_reg[0]_i_5}
    {coefficients/child/packet_decoder/synchronous.ingress/context_decoder/error_reg[0]_i_4}
    {coefficients/child/packet_decoder/synchronous.ingress/context_decoder/state[4]_i_40}
    {coefficients/child/scratch/state[3]_rep__0_i_1__0}
    {coefficients/admission/tile[31]_i_1}
} {
    set cells [get_cells -quiet -hierarchical -filter [format {NAME == "%s"} $name]]
    if {[llength $cells]!=1} {gap $name EXACT_TRACE_CELL_ABSENT_OR_AMBIGUOUS "Expected1 exact cell, got[llength $cells]";continue}
    trace_cell [lindex $cells 0] 2
}
emit RAW_TRACE_SUMMARY current UNIQUE_CELLS [dict size $traced]
