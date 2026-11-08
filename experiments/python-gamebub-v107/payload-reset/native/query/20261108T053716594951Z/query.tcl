set build [file normalize [lindex $argv 0]]
set_param general.maxThreads 2
proc input_starts {pin} {
 set names {}
 foreach obj [all_fanin -flat -startpoints_only -to $pin] {
  if {[get_property CLASS $obj] eq "port"} {lappend names $obj}
 }
 return [lsort -unique $names]
}
file mkdir [file join $build results]
foreach variant {original candidate} {
 open_checkpoint /frozen/results/$variant/synth.dcp
 set f [open [file join $build results ${variant}.tsv] w]
 puts $f "cell\treset_ground\treset_ports\tce_ports\tce_register_starts"
 set payload [get_cells -hierarchical -regexp {(^|.*/)(coefficients_reg\[[0-9]+\]|chroma_reg|scale_code_reg\[[0-9]+\])}]
 if {[llength $payload]!=1027} {error "expected1027"}
 foreach c [lsort $payload] {
  set reset [get_pins $c/R];set ce [get_pins $c/CE]
  set ground 0
  foreach p [get_pins -of_objects [get_nets -of_objects $reset] -filter {DIRECTION == OUT}] {if {[get_property REF_NAME [get_cells -of_objects $p]] eq "GND"} {set ground 1}}
  set regstarts {}
  foreach p [all_fanin -flat -startpoints_only -to $ce] {if {[get_property CLASS $p] eq "pin"} {lappend regstarts $p}}
  puts $f [join [list $c $ground [input_starts $reset] [input_starts $ce] [lsort -unique $regstarts]] \t]
 }
 close $f
 close_design
}
puts DEQUANT_EXACT_FANIN_QUERY_PASS
