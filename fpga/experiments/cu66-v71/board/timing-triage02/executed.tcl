set_param general.maxThreads 2
set image [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
open_checkpoint $image
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "Wrong part"}
set reset_expression {(^|/)(joint_(core|spi|pixel)_reset_reg|rst100_reg|rst200_reg|rstpixel_reg|platform_reset_ref_reg)(\[|$)}
set f [open [file join $out excluded-source-pins.txt] w]
set all_sources [all_registers -output_pins]
set nonreset_sources {};set functional_sources {}
foreach pin $all_sources {
 set cell [get_cells -of_objects $pin]
 set name [get_property NAME $cell]
 set reset [regexp $reset_expression $name]
 set tile [string match {system_core/memory/tiles/*} $name]
 if {$reset} {puts $f "RESET_SOURCE $pin"} else {lappend nonreset_sources $pin}
 if {!$reset&&!$tile} {lappend functional_sources $pin}
 if {$tile} {puts $f "TILE_SOURCE $pin"}
}
close $f
# External inputs remain in functional path scope. This is report selection,
# not set_false_path or any other design/exception change.
set functional_sources [concat $functional_sources [all_inputs]]
set nonreset_sources [concat $nonreset_sources [all_inputs]]
set all_endpoints [get_cells -hier -filter {IS_SEQUENTIAL}]
set functional_endpoints {}
foreach cell $all_endpoints {
 if {![string match {system_core/memory/tiles/*} [get_property NAME $cell]]} {lappend functional_endpoints $cell}
}
set functional_endpoints [concat $functional_endpoints [all_outputs]]
set groups {
 entropy {^system_core/receiver/base/entropy/.*}
 dequant {^system_core/receiver/base/dequant/.*}
 IDCT {^system_core/receiver/base/inverse/.*}
 reconstruct {^system_core/receiver/base/reconstruct/.*}
 canonical_SHA {^system_core/receiver/base/canonical/.*}
 CSR_control {^control_plane/.*}
 QSPI_CDC {^(endpoint/.*|bridge/.*|transport_gray_.*|transport_lost_words_.*)}
 line_scanout {^system_core/scanout/.*}
}
set summary [open [file join $out paths.tsv] w]
puts $summary "scope\tordinal\tslack_ns\tstartpoint\tendpoint\tlogic_levels\tdata_ns\tlogic_ns\troute_ns\ttouches_tile_cells\treset_source"
set scopes [open [file join $out scopes.tsv] w]
puts $scopes "scope\tendpoint_count\tsource_count\treturned_paths\tcell_type_summary_scope"
proc prop {object key} {
 if {[lsearch -exact [list_property $object] $key]<0} {return UNAVAILABLE}
 return [get_property $key $object]
}
proc dump_paths {label targets sources} {
 global summary scopes out reset_expression
 if {[llength $targets]==0} {error "No targets for $label"}
 if {$sources eq "ALL"} {
  set paths [get_timing_paths -to $targets -delay_type max -max_paths 100 -nworst 5 -sort_by slack]
  set nsource ALL
 } else {
  if {[llength $sources]==0} {error "No sources for $label"}
  set paths [get_timing_paths -from $sources -to $targets -delay_type max -max_paths 100 -nworst 5 -sort_by slack]
  set nsource [llength $sources]
 }
 puts $scopes [join [list $label [llength $targets] $nsource [llength $paths] {Source/endpoint selection; 100 sampled paths max,5 per endpoint; intermediate tile presence flagged independently}] "\t"]
 if {[llength $paths]} {report_timing -of_objects $paths -file [file join $out ${label}.rpt]}
 set n 0;set best_clean {}
 foreach path $paths {
  set source [prop $path STARTPOINT_PIN];set endpoint [prop $path ENDPOINT_PIN]
  set tile_count 0
  foreach cell [get_cells -of_objects $path] {
   if {[string match {system_core/memory/tiles/*} [get_property NAME $cell]]} {incr tile_count}
  }
  set reset [regexp $reset_expression $source]
  puts $summary [join [list $label $n [prop $path SLACK] $source $endpoint [prop $path LOGIC_LEVELS] [prop $path DATAPATH_DELAY] [prop $path LOGIC_DELAY] [prop $path NET_DELAY] $tile_count $reset] "\t"]
  if {$n==0} {report_property -all $path -file [file join $out ${label}-worst-properties.rpt]}
  if {$best_clean eq {} && $tile_count==0 && !$reset} {set best_clean $path}
  incr n
 }
 if {$best_clean ne {}} {report_timing -of_objects $best_clean -file [file join $out ${label}-first-no-tile-or-reset.rpt]}
 flush $summary;flush $scopes
}
dump_paths global_inclusive [concat $all_endpoints [all_outputs]] ALL
dump_paths global_excluded_endpoints_sources $functional_endpoints $functional_sources
dict for {name expression} $groups {
 set cells [get_cells -quiet -hier -regexp $expression -filter {IS_SEQUENTIAL}]
 dump_paths ${name}_inclusive $cells ALL
 dump_paths ${name}_no_reset_source_or_tile_source $cells $functional_sources
}
close $summary;close $scopes
report_clocks -file [file join $out clocks.rpt]
write_xdc -force -exclude_physical [file join $out timing-unchanged.xdc]
report_exceptions -coverage -file [file join $out exceptions.rpt]
puts CU71_READONLY_TIMING_TRIAGE_COMPLETE_NO_DESIGN_OR_EXCEPTION_CHANGES
close_design
