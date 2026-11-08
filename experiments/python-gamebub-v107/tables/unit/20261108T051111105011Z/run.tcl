set build [file normalize [lindex $argv 0]]
file mkdir [file join $build results]
set_param general.maxThreads 2
create_project -in_memory -part xc7a100tcsg324-1
set_property verilog_define SYNTHESIS [current_fileset]
read_verilog -sv [list [file join $build candidate.sv] [file join $build unit_wrapper.sv]]
read_xdc [file join $build unit.xdc]
synth_design -top cu66_tables_unit_v107 -part xc7a100tcsg324-1 -mode out_of_context -flatten_hierarchy rebuilt -directive Default
write_checkpoint -force [file join $build results synth.dcp]
write_verilog -force -mode funcsim [file join $build results mapped.v]
report_utilization -hierarchical -file [file join $build results utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $build results timing.rpt]
set f [open [file join $build results ram-modes.tsv] w]
set properties {REF_NAME RAM_MODE READ_WIDTH_A READ_WIDTH_B WRITE_WIDTH_A WRITE_WIDTH_B WRITE_MODE_A WRITE_MODE_B DOA_REG DOB_REG}
puts $f "cell\t[join $properties \t]"
foreach c [get_cells -hierarchical -filter {REF_NAME =~ RAMB*}] {
 set row [list $c]
 foreach p $properties {lappend row [get_property $p $c]}
 puts $f [join $row \t]
}
close $f
puts TABLES_MAPPING_COMPLETE
