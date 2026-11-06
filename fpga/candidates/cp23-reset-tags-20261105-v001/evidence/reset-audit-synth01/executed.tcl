# Read-only checkpoint audit. No RTL/constraint change, image or hardware access.
set cp [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
file mkdir $out
set_param general.maxThreads 2
open_checkpoint $cp
set root [get_cells -quiet -hier -regexp {^job_reset_chain_reg\[3\]$}]
if {[llength $root]!=1} {error "Expected one job-reset synchronizer output"}
set q [get_pins -of_objects $root -filter {REF_PIN_NAME == Q}]
if {[llength $q]!=1} {error "Expected one job-reset output pin"}
set net [get_nets -segments -of_objects $q]
set loads [get_pins -leaf -of_objects $net -filter {DIRECTION == IN}]
if {[llength $loads]==0} {error "No reset loads found; do not interpret this as reset removal"}
set f [open [file join $out job-reset-loads.tsv] w]
puts $f "pin\tprimitive\tcontrol_pin"
set resetPins 0
set enablePins 0
foreach pin [lsort $loads] {
 set cell [get_cells -of_objects $pin]
 set kind [get_property REF_PIN_NAME $pin]
 puts $f "$pin\t[get_property REF_NAME $cell]\t$kind"
 if {$kind in {R S CLR PRE}} {incr resetPins}
 if {$kind eq "CE"} {incr enablePins}
}
close $f
set f [open [file join $out reset-summary.txt] w]
puts $f "checkpoint=$cp"
puts $f "job_reset_direct_loads=[llength $loads]"
puts $f "job_reset_direct_reset_pins=$resetPins"
puts $f "job_reset_direct_enable_pins=$enablePins"
set tags [get_cells -quiet -hier -regexp {^diagnostic/core/key/outer/(bh|hh)_reg\[[0-9]+\]$}]
puts $f "outer_tag_registers=[llength $tags]"
foreach pinName {R CE} {
 set attached [get_pins -quiet -of_objects $tags -filter "REF_PIN_NAME == $pinName"]
 set drivers [get_nets -quiet -of_objects $attached]
 puts $f "outer_tag_${pinName}_nets=$drivers"
}
close $f
report_control_sets -verbose -file [file join $out control-sets.rpt]
report_high_fanout_nets -max_nets 30 -timing -file [file join $out high-fanout.rpt]
report_utilization -file [file join $out utilization.rpt]
puts "RESET_AUDIT_READ_ONLY_COMPLETE"
close_design
