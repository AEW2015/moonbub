# Proposal only. Run against the selected synthesized DY71 netlist before
# accepting first-stage exceptions. Requires required_cells from timing Tcl.
# A timed first-stage functional path is still an unsafe CDC, not a path to cut.
foreach chain {request_sync0 request_sync1 frame_sync done_sync0 done_sync1 valid_sync} {
    set meta [required_cells DY71_${chain}_first [format {system_core/scanout/lcd/%s_reg\[0\]} $chain]]
    set next [required_cells DY71_${chain}_second [format {system_core/scanout/lcd/%s_reg\[1\]} $chain]]
    if {[llength $meta]!=1 || [llength $next]!=1} {
        error "DY71 requires individually reviewed two-stage LCD chain: $chain"
    }
    set q [get_pins -of_objects $meta -filter {REF_PIN_NAME == Q}]
    set expected [get_pins -of_objects $next -filter {REF_PIN_NAME == D}]
    set endpoints [all_fanout -flat -endpoints_only -from $q]
    if {[llength $q]!=1 || [llength $expected]!=1 ||
        [lsort $endpoints] ne [lsort $expected]} {
        error "DY71 LCD first stage has functional or unexpected fanout: $chain -> $endpoints"
    }
}
puts "DY71_LCD_FIRST_STAGES_FEED_ONLY_SECOND_STAGE_D=6"
