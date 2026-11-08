if {[llength $argv] != 1} {error "expected prepared BUILD_DIRECTORY"}
set build [file normalize [lindex $argv 0]]
source [file join $build inputs.tcl]
file mkdir [file join $build results]
set_param general.maxThreads 2
set match [get_parts -quiet xc7a100tcsg324-1]
if {[llength $match] != 1} {error "exact xc7a100tcsg324-1 part unavailable"}
create_project -in_memory -part xc7a100tcsg324-1
set_property target_language Verilog [current_project]
set_property verilog_define SYNTHESIS [current_fileset]
read_verilog -sv $rtl_sources
read_xdc [file join $build unit-clocks.xdc]
synth_design -top v107_cdc_fabric -part xc7a100tcsg324-1 -mode out_of_context -flatten_hierarchy rebuilt -directive Default
write_checkpoint -force [file join $build results synth-before-cdc.dcp]
# Retain mapped names even if a strict hierarchy match fails.
set f [open [file join $build results mapped-registers.tsv] w]
puts $f "instance\tprimitive\tASYNC_REG"
foreach c [lsort [get_cells -hierarchical -filter {IS_SEQUENTIAL == 1}]] {
    puts $f "$c\t[get_property REF_NAME $c]\t[get_property ASYNC_REG $c]"
}
close $f
source [file join $build gray-constraints.tcl]
set constraint_status [open [file join $build results cdc-constraint-status.txt] w]
if {[catch {
    v107_constrain_fifo commands 5.000 10.000
    v107_constrain_fifo writes 10.000 10.000
    v107_constrain_fifo acks 10.000 10.000
    v107_constrain_fifo lines 16.667 10.000
    v107_constrain_fifo pixels 10.000 16.667
} detail]} {
    puts $constraint_status "FAIL: $detail";close $constraint_status
    error "V107_CDC_EXACT_CONSTRAINT_MATCH_FAILED: $detail"
}
puts $constraint_status "PASS: five FIFOs; ten four-bit Gray bundles; ten peer-up first stages; exact endpoint/launch-clock checks"
close $constraint_status
write_checkpoint -force [file join $build results synth.dcp]
source [file join $build report.tcl]
v107_cdc_reports synth
opt_design -directive Default
place_design -directive Default
v107_cdc_reports place
route_design -directive Default
v107_cdc_reports route
write_checkpoint -force [file join $build results route.dcp]
report_route_status -file [file join $build results route-status.rpt]
write_xdc -force -exclude_physical [file join $build results effective-timing.xdc]
puts "V107_CDC_UNIT_ROUTE_FINISHED; synthetic unit clocks; parent/hardware signoff open"
