# Prepared by scripts/cu66-v107/build.py into a new external directory.
# vivado -mode batch -source run.tcl -tclargs BUILD_DIRECTORY
if {[llength $argv] != 1} {error "expected one prepared BUILD_DIRECTORY"}
set build [file normalize [lindex $argv 0]]
source [file join $build inputs.tcl]
file mkdir [file join $build results]
set_param general.maxThreads 2
set f [open [file join $build results part-query.txt] w]
puts $f "version=[version -short]"
set matches [get_parts -quiet $part]
puts $f "part=$part count=[llength $matches]"
close $f
if {[llength $matches]!=1} {error "V107_EXACT_PART_UNAVAILABLE: $part"}
create_project -in_memory -part $part
set_property target_language Verilog [current_project]
# UG835 2026.1 read_verilog accepts neither -include_dirs nor -define.
# These are source-fileset properties, set before reading the SystemVerilog.
set_property include_dirs $include_dirs [current_fileset]
set_property verilog_define SYNTHESIS [current_fileset]
read_verilog -sv $rtl_sources
# Read the clock as a synthesis input, not only as a post-synthesis constraint.
read_xdc $constraint_file
synth_design -top cs88_pipeline_v91k -part $part -mode out_of_context -flatten_hierarchy rebuilt -directive Default
write_checkpoint -force [file join $build results synth.dcp]
source [file join $build report.tcl]
v107_reports synth
if {$synth_only} {puts "V107_SYNTH_ONLY_FINISHED"; exit 0}
opt_design -directive Default
place_design -directive Default
v107_reports place
route_design -directive Default
v107_reports route
write_checkpoint -force [file join $build results route.dcp]
report_route_status -file [file join $build results route-status.rpt]
write_xdc -force -exclude_physical [file join $build results effective-timing.xdc]
puts "V107_COMPONENT_ROUTE_FINISHED; no board or complete-custom-top signoff"
