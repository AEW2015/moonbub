# Read-only synthesized/parser inspection. No optimization or property changes.
if {$argc != 2} {error "usage: checkpoint output_directory"}
set checkpoint [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
if {![file isfile $checkpoint]} {error "checkpoint missing"}
if {[file exists $out]} {error "unique output required"}
file mkdir $out
open_checkpoint $checkpoint
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "wrong part"}
set parser [get_cells -quiet system_core/receiver/parser]
if {[llength $parser] != 1} {error "exact parser hierarchy missing/ambiguous"}
if {[get_property REF_NAME $parser] ne "cu71_packet_rxstage_v001"} {error "wrong parser module"}
set clock [get_clocks -quiet raw100]
if {[llength $clock] != 1 || abs([get_property PERIOD $clock]-10.0)>0.0001} {error "raw100 clock missing/changed"}
proc require_nonempty {objects context} {
 if {![llength $objects]} {error "$context: empty collection is not evidence"}
}
proc endpoints {cells pin} {
 return [get_pins -quiet -of_objects $cells -filter "REF_PIN_NAME == $pin"]
}
set prefix {system_core/receiver/parser/}
set refcells {};set plane0 {};set plane1 {};set plane2 {};set statecells {};set headercells {};set innerheadercells {};set seqcells {}
foreach c [get_cells -quiet -hier -filter {NAME =~ system_core/receiver/parser/*}] {
 set n [get_property NAME $c]
 if {[get_property -quiet IS_SEQUENTIAL $c] eq "1"} {lappend seqcells $c}
 if {[regexp {^system_core/receiver/parser/metadata_reference_tag_reg\[[0-9]+\]$} $n]} {lappend refcells $c}
 if {[regexp {^system_core/receiver/parser/metadata_plane_bytes_reg\[([012])\]\[[0-9]+\]$} $n -> plane]} {lappend plane$plane $c}
 if {[regexp {^system_core/receiver/parser/(state_reg|FSM_sequential_state_reg)\[[0-9]+\]$} $n]} {lappend statecells $c}
 if {[regexp {^system_core/receiver/parser/inner_header_reg\[([0-9]+)\](\[[0-9]+\])?$} $n -> byte] && $byte<=39} {lappend headercells $c;lappend innerheadercells $c}
 if {[regexp {^system_core/receiver/parser/metadata_(key|frame_id|reference_id|reference_tag)_reg(\[[0-9]+\])?$} $n]} {lappend headercells $c}
}
require_nonempty $refcells metadata_reference_tag_registers
require_nonempty $statecells parser_state_registers
require_nonempty $headercells header_validation_registers
require_nonempty $innerheadercells inner_header_bytes0_to39_registers
set refq [endpoints $refcells Q];require_nonempty $refq metadata_reference_tag_Q
set stateinputs [get_pins -quiet -of_objects $statecells -filter {REF_PIN_NAME == D || REF_PIN_NAME == CE}]
require_nonempty $stateinputs state_D_or_CE
set headerq [endpoints $headercells Q];require_nonempty $headerq header_validation_Q
set f [open [file join $out identity.tsv] w]
puts $f "checkpoint\t$checkpoint\npart\t[get_property PART [current_design]]\nparser_REF_NAME\t[get_property REF_NAME $parser]\nraw100_period\t[get_property PERIOD $clock]\nreference_tag_register_count\t[llength $refcells]\ninner_header_bytes0_to39_register_count\t[llength $innerheadercells]\nparser_sequential_cell_count\t[llength $seqcells]\nstate_register_count\t[llength $statecells]\nheader_validation_launch_Q_count\t[llength $headerq]"
close $f
set f [open [file join $out parser-state-registers.tsv] w]
foreach c [lsort $statecells] {puts $f "$c\t[get_property REF_NAME $c]"}
close $f
set f [open [file join $out parser-sequential-registers.tsv] w]
foreach c [lsort $seqcells] {puts $f "$c\t[get_property REF_NAME $c]"}
close $f
set f [open [file join $out plane-summary.tsv] w]
puts $f "plane\tregisters\tCEpins\tfanin_startpoints\tref_tag_startpoints\tref_Q_to_CE_maxpaths50"
for {set plane 0} {$plane<3} {incr plane} {
 set cells [set plane$plane];require_nonempty $cells plane${plane}_byte_registers
 set ce [endpoints $cells CE];require_nonempty $ce plane${plane}_CE
 set starts [all_fanin -flat -startpoints_only -to $ce];require_nonempty $starts plane${plane}_CE_fanin
 set refs 0
 set sf [open [file join $out plane${plane}-ce-startpoints.tsv] w]
 foreach s [lsort -unique $starts] {
  puts $sf $s
  if {[regexp {^system_core/receiver/parser/metadata_reference_tag_reg\[} $s]} {incr refs}
 }
 close $sf
 set paths [get_timing_paths -quiet -delay_type max -from $refq -to $ce -max_paths 50]
 puts $f "$plane\t[llength $cells]\t[llength $ce]\t[llength $starts]\t$refs\t[llength $paths]"
 report_timing -delay_type max -to $ce -max_paths 20 -file [file join $out plane${plane}-ce-setup.rpt]
 report_timing -delay_type max -from $refq -to $ce -max_paths 50 -file [file join $out ref-tag-to-plane${plane}-ce.rpt]
}
close $f
# CHECK_INNER code6 fields are bytes0..39 plus the metadata comparison registers.
# This is a structural launch selection, not claiming one net equals the full predicate.
set headerpaths [get_timing_paths -quiet -delay_type max -from $headerq -to $stateinputs -max_paths 50]
require_nonempty $headerpaths header_validation_to_state_paths
set refstatepaths [get_timing_paths -quiet -delay_type max -from $refq -to $stateinputs -max_paths 20]
require_nonempty $refstatepaths reference_tag_validation_to_state_paths
set f [open [file join $out header-to-state-summary.tsv] w];puts $f "header_Q\t[llength $headerq]\nstate_input_pins\t[llength $stateinputs]\nmaxpaths50_found\t[llength $headerpaths]\nref_tag_maxpaths20_found\t[llength $refstatepaths]";close $f
report_timing -delay_type max -from $headerq -to $stateinputs -max_paths 50 -file [file join $out header-to-state-setup.rpt]
report_timing -delay_type max -from $refq -to $stateinputs -max_paths 20 -file [file join $out ref-tag-to-state-setup.rpt]
report_timing -delay_type max -max_paths 50 -file [file join $out global-setup50.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out synthesized-timing-summary.rpt]
set ticketce [get_pins -quiet -hier -filter {NAME == "control_plane/hud_ticket_reg[4]/CE"}]
if {[llength $ticketce] != 1} {error "exact hud_ticket4 CE missing/ambiguous"}
set hudstarts [all_fanin -flat -startpoints_only -to $ticketce];require_nonempty $hudstarts hud_ticket_CE_fanin
set metadata_count 0
set f [open [file join $out hud-ticket-ce-startpoints.tsv] w]
foreach s [lsort -unique $hudstarts] {
 puts $f $s
 if {[regexp {control_plane/(hud_gen|hud_ref|hud_fid|hud_bank)_reg} $s]} {incr metadata_count}
}
close $f
set net [get_nets -quiet -of_objects $ticketce];require_nonempty $net hud_ticket_CE_net
set drivers [get_pins -quiet -of_objects $net -filter {DIRECTION == OUT}];require_nonempty $drivers hud_ticket_CE_driver
set f [open [file join $out hud-ticket-ce-summary.tsv] w]
puts $f "fanin_startpoints\t[llength $hudstarts]\nHUD_metadata_startpoints\t$metadata_count\nnet\t$net\ndriver\t$drivers\nloads\t[llength [get_pins -quiet -of_objects $net -filter {DIRECTION == IN}]]"
close $f
report_timing -delay_type max -to $ticketce -max_paths 20 -file [file join $out hud-ticket-ce-setup.rpt]
report_timing -delay_type min -to $ticketce -max_paths 10 -file [file join $out hud-ticket-ce-hold.rpt]
report_clocks -file [file join $out clocks.rpt]
report_exceptions -coverage -file [file join $out exceptions.rpt]
puts PARSER_SYNTH_CONE_READONLY_COMPLETE_NO_ROUTED_OR_HARDWARE_CLAIM
close_design
