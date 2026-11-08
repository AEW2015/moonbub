# Separate candidate after retained original endpoint-count failure and
# retained Q-pin segmentation/invalid-startpoint failure.
# MSB Gray/bin flops and equivalent per-domain up flops can merge in synthesis.
# Derive the ACTUAL sequential Q that drives each exact first-stage D.
# Never broaden to all registers of a clock, or to an entire clock group.
proc v107_one_driver {destination} {
    set nets [get_nets -segments -of_objects $destination]
    set driver [get_pins -leaf -of_objects $nets -filter {DIRECTION == OUT}]
    if {[llength $driver] != 1} {error "V107 expected one actual first-stage driver: $destination -> $driver"}
    set c [get_cells -of_objects $driver]
    if {[llength $c] != 1 || ![get_property IS_SEQUENTIAL $c] || [get_property REF_PIN_NAME $driver] ne "Q"} {
        error "V107 first-stage driver must be one sequential Q: $destination -> $driver"
    }
    return $driver
}
proc v107_gray_bundle {fifo source first_sync bits {launch_period {}}} {
    global v107_gray_q v107_gray_c v107_gray_d v107_endpoint_log
    set targets [get_cells -hierarchical -regexp [format {^%s/%s_reg\[[0-9]+\]$} $fifo $first_sync]]
    if {[llength $targets] != $bits} {error "V107 exact Gray first-stage count mismatch: $fifo/$first_sync"}
    set q {};set d {};set actual_clocks {}
    for {set bit 0} {$bit < $bits} {incr bit} {
        set cell [get_cells -hierarchical -regexp [format {^%s/%s_reg\[%s\]$} $fifo $first_sync $bit]]
        if {[llength $cell] != 1} {error "V107 missing Gray bit: $fifo/$first_sync/$bit"}
        set pin [get_pins -of_objects $cell -filter {REF_PIN_NAME == D}]
        set driver [v107_one_driver $pin];set launch [get_cells -of_objects $driver]
        set expected [format {^%s/%s_reg\[%s\]$} $fifo $source $bit]
        set binary [string map {gray bin} $source]
        set msb_alias [format {^%s/%s_reg\[%s\]$} $fifo $binary $bit]
        if {![regexp $expected $launch] && !($bit == $bits-1 && [regexp $msb_alias $launch])} {
            error "V107 unexpected Gray bit driver: $pin <- $driver"
        }
        set clk [get_clocks -of_objects [get_pins -of_objects $launch -filter {REF_PIN_NAME == C}]]
        if {[llength $clk] != 1} {error "V107 missing/ambiguous Gray source clock"}
        lappend q $driver;lappend d $pin;lappend actual_clocks $clk
        puts $v107_endpoint_log "GRAY\t$fifo\t$source\t$bit\t$driver\t$pin\t$clk"
    }
    set actual_clocks [lsort -unique $actual_clocks]
    if {[llength $actual_clocks] != 1} {error "V107 Gray bundle has multiple source clocks"}
    set period [get_property PERIOD $actual_clocks];set budget $period
    if {$launch_period ne {}} {
        if {$launch_period <= 0 || $launch_period > $period} {error "V107 Gray bound exceeds source period"}
        set budget $launch_period
    }
    if {$budget <= 0 || [llength [lsort -unique $q]] != $bits} {error "V107 invalid Gray sources/budget"}
    # Valid sequential clock-pin startpoints retain the C->Q timing arcs.
    # Raw Q pins would segment paths (UG903); never use them as -from.
    set c [get_pins -of_objects [get_cells -of_objects $q] -filter {REF_PIN_NAME == C}]
    if {[llength $c] != $bits} {error "V107 missing exact Gray launch C pins"}
    set_max_delay -datapath_only $budget -from $c -to $d
    set_bus_skew $budget -from $c -to $d
    set v107_gray_c($fifo,$source) $c
    set v107_gray_q($fifo,$source) $q;set v107_gray_d($fifo,$source) $d
}
proc v107_constrain_fifo {fifo {write_period {}} {read_period {}}} {
    global v107_endpoint_log
    v107_gray_bundle $fifo wgray wgray_meta 4 $write_period
    v107_gray_bundle $fifo rgray rgray_meta 4 $read_period
    foreach pair {{wup wup_sync wgray} {rup rup_sync rgray}} {
        lassign $pair source target reference
        set dst [get_cells -hierarchical -regexp [format {^%s/%s_reg\[0\]$} $fifo $target]]
        if {[llength $dst] != 1} {error "V107 exact peer-up first-stage mismatch"}
        set d [get_pins -of_objects $dst -filter {REF_PIN_NAME == D}]
        set q [v107_one_driver $d];set launch [get_cells -of_objects $q]
        if {![regexp {^(commands|writes|acks|lines|pixels)/(wup|rup)_reg$} $launch]} {
            error "V107 unexpected shared peer-up source: $q"
        }
        set actual_clock [get_clocks -of_objects [get_pins -of_objects $launch -filter {REF_PIN_NAME == C}]]
        global v107_gray_q
        set expected_clock [get_clocks -of_objects [get_pins -of_objects [get_cells -of_objects [lindex $v107_gray_q($fifo,$reference) 0]] -filter {REF_PIN_NAME == C}]]
        if {[llength $actual_clock] != 1 || $actual_clock ne $expected_clock} {error "V107 shared up-token source clock mismatch"}
        set c [get_pins -of_objects $launch -filter {REF_PIN_NAME == C}]
        if {[llength $c] != 1} {error "V107 missing exact peer-up launch C pin"}
        set_false_path -from $c -to $d
        puts $v107_endpoint_log "PEER_UP\t$fifo\t$source\t0\t$q\t$d\t$actual_clock"
    }
}
# The run opens/closes this trace around constraint application.
