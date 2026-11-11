# Read-only inspection of one already-routed component checkpoint.
# No implementation, clock/constraint, or checkpoint-write commands.
if {[llength $argv] != 2} {error "expected read-only ROUTE_DCP and fresh OUTPUT_DIR"}
set checkpoint [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
if {![file isfile $checkpoint] || ![file isdirectory $out]} {error "missing input or output"}
set_param general.maxThreads 2
open_checkpoint $checkpoint
set clocks [get_clocks -quiet component_clk]
if {[llength $clocks]!=1 || abs([get_property PERIOD $clocks]-8.0)>0.000001} {error "expected 8 ns component clock"}
set src_cells [lsort [get_cells -quiet -hierarchical -filter {NAME =~ *base_kill_valid_reg* && REF_NAME =~ FD*}]]
set dst_cells [lsort [get_cells -quiet -hierarchical -filter {NAME =~ *coefficients/admission/memory_reg* && REF_NAME =~ RAMB*}]]
set src_pins [lsort [get_pins -quiet -of_objects $src_cells -filter {REF_PIN_NAME == Q}]]
set dst_pins [lsort [get_pins -quiet -of_objects $dst_cells -filter {REF_PIN_NAME == ENBWREN}]]
set f [open [file join $out inventory.tsv] w]
puts $f "kind\tname\tref\tlocation"
foreach c $src_cells {puts $f "SOURCE_CELL\t$c\t[get_property REF_NAME $c]\t[get_property LOC $c]"}
foreach c $dst_cells {puts $f "DEST_CELL\t$c\t[get_property REF_NAME $c]\t[get_property LOC $c]"}
foreach p $src_pins {puts $f "SOURCE_PIN\t$p\tQ\t-"}
foreach p $dst_pins {puts $f "DEST_PIN\t$p\tENBWREN\t-"}
close $f
set f [open [file join $out paths.tsv] w]
puts $f "source\tdestination\tstatus\tslack_ns\tdata_delay_ns\tlogic_levels"
foreach src $src_pins {
    foreach dst $dst_pins {
        if {[catch {set paths [get_timing_paths -quiet -from $src -to $dst -delay_type max -max_paths 1 -nworst 1]} why]} {
            puts $f "$src\t$dst\tQUERY_ERROR\t-\t-\t-"
        } elseif {[llength $paths]==0} {
            puts $f "$src\t$dst\tNO_TIMED_PATH\t-\t-\t-"
        } else {
            set p [lindex $paths 0]
            puts $f "$src\t$dst\tPATH\t[get_property SLACK $p]\t[get_property DATAPATH_DELAY $p]\t[get_property LOGIC_LEVELS $p]"
        }
    }
}
close $f
set f [open [file join $out status.txt] w]
puts $f "checkpoint=$checkpoint"
puts $f "tool=[version]"
puts $f "clock_period_ns=[get_property PERIOD $clocks]"
puts $f "source_cells=[llength $src_cells]"
puts $f "source_pins=[llength $src_pins]"
puts $f "destination_cells=[llength $dst_cells]"
puts $f "destination_pins=[llength $dst_pins]"
puts $f "empty_selection=[expr {[llength $src_pins]==0 || [llength $dst_pins]==0}]"
puts $f "V130_TARGETED_CHECKPOINT_REPORT_COMPLETE"
close $f
puts "V130_TARGETED_CHECKPOINT_REPORT_COMPLETE"
