# Read-only post-route inspection; run only after current implementation exits.
set_param general.maxThreads 4
set out [file normalize [lindex $argv 0]]
if {[file exists $out]} {error "unique output directory required"}
file mkdir $out
open_checkpoint C:/moon/builds/stb1-ce-v001/routed.dcp
set ce [get_pins -quiet -hier -filter {NAME == "control_plane/hud_ticket_reg[4]/CE"}]
if {[llength $ce]!=1} {error "exact ticket CE missing"}
set net [get_nets -of_objects $ce]
set pin [get_pins -leaf -of_objects $net -filter {DIRECTION == OUT}]
set cell [get_cells -of_objects $pin]
set f [open [file join $out target.tsv] w]
puts $f "endpoint\t$ce\nnet\t$net\ndriver\t$pin\nref\t[get_property REF_NAME $cell]\nloads\t[llength [get_pins -leaf -of_objects $net -filter {DIRECTION == IN}]]"
close $f
report_timing -delay_type max -to $ce -max_paths 20 -file [file join $out ce-setup.rpt]
report_timing -delay_type min -to $ce -max_paths 10 -file [file join $out ce-hold.rpt]
set starts [all_fanin -flat -startpoints_only -to $ce]
set f [open [file join $out ce-startpoints.tsv] w]
set metadata_count 0
foreach s $starts {
 puts $f $s
 if {[regexp {control_plane/(hud_gen|hud_ref|hud_fid|hud_bank)_reg} $s]} {incr metadata_count}
}
close $f
set f [open [file join $out cone-summary.tsv] w];puts $f "startpoints\t[llength $starts]\nmatched_hud_metadata_startpoints\t$metadata_count";close $f
set launch {}
foreach c [get_cells -quiet -hier -filter {NAME =~ control_plane/hud_gen_reg* || NAME =~ control_plane/hud_ref_reg* || NAME =~ control_plane/hud_fid_reg* || NAME =~ control_plane/hud_bank_reg*}] {
 foreach q [get_pins -quiet -of_objects $c -filter {REF_PIN_NAME == Q}] {lappend launch $q}
}
if {[llength $launch]} {report_timing -delay_type max -from $launch -to $ce -max_paths 10 -file [file join $out hud-metadata-to-ce.rpt]}
set f [open [file join $out read-checkpoint-help.txt] w];puts $f [help read_checkpoint -verbose];close $f
set f [open [file join $out report-incremental-reuse-help.txt] w];puts $f [help report_incremental_reuse -verbose];close $f
puts READONLY_POSTROUTE_CE_CONE_COMPLETE
close_design
