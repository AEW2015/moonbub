# Template for an elaborated/mapped v107_cdc_fabric hierarchy. This file does
# NOT create clocks or declare any clocks unrelated. Call after real parent
# clocks exist. Missing/multiple endpoint/clock matches are fatal.
proc v107_gray_bundle {fifo source first_sync bits {launch_period {}}} {
    set src [get_cells -hierarchical -regexp [format {^%s/%s_reg\[[0-9]+\]$} $fifo $source]]
    set dst [get_cells -hierarchical -regexp [format {^%s/%s_reg\[[0-9]+\]$} $fifo $first_sync]]
    if {[llength $src] != $bits || [llength $dst] != $bits} {
        error "V107 Gray endpoint mismatch: $fifo/$source -> $first_sync"
    }
    set q [get_pins -of_objects $src -filter {REF_PIN_NAME == Q}]
    set d [get_pins -of_objects $dst -filter {REF_PIN_NAME == D}]
    set c [get_pins -of_objects $src -filter {REF_PIN_NAME == C}]
    set clocks [get_clocks -of_objects $c]
    if {[llength $clocks] != 1} { error "V107 requires one known launch clock: $fifo/$source" }
    set actual_period [get_property PERIOD $clocks]
    set budget $actual_period
    if {$launch_period ne {}} {
        if {$launch_period <= 0 || $launch_period > $actual_period} { error "V107 supplied Gray bound exceeds actual source period" }
        set budget $launch_period
    }
    if {$budget <= 0} { error "V107 invalid launch-clock period" }
    # Bound all source Gray bits to the FIRST synchronizer D pins by one
    # launch period; a faster next transition must not overtake this bundle.
    # ASYNC_REG places first/second synchronizers; normal destination timing
    # remains active on first->second. Never hide these with clock_groups.
    set_max_delay -datapath_only $budget -from $q -to $d
    set_bus_skew $budget -from $q -to $d
}
proc v107_constrain_fifo {fifo {write_period {}} {read_period {}}} {
    v107_gray_bundle $fifo wgray wgray_meta 4 $write_period
    v107_gray_bundle $fifo rgray rgray_meta 4 $read_period
    # Peer-up single-bit synchronizers: exception only at first stage D.
    foreach pair {{wup wup_sync 0} {rup rup_sync 0}} {
        lassign $pair source target bit
        set src [get_cells -hierarchical -regexp [format {^%s/%s_reg$} $fifo $source]]
        set dst [get_cells -hierarchical -regexp [format {^%s/%s_reg\[%s\]$} $fifo $target $bit]]
        if {[llength $src] != 1 || [llength $dst] != 1} { error "V107 peer-up endpoint mismatch: $fifo/$source" }
        set_false_path -from [get_pins -of_objects $src -filter {REF_PIN_NAME == Q}] -to [get_pins -of_objects $dst -filter {REF_PIN_NAME == D}]
    }
}
# Example only after actual hierarchy/clock discovery:
# foreach channel {commands writes acks lines pixels} {
#     v107_constrain_fifo "actual_parent/experimental_fabric/$channel"
# }
# Required review: report_cdc -details, report_exceptions -coverage,
# report_bus_skew, report_timing through each Gray first-stage D, and check
# report_methodology. Reset recovery/removal and RAM recognition are separate.
