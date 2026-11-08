if {[llength $argv]!=1} {error "expected build directory"}
set build [file normalize [lindex $argv 0]]
source [file join $build inputs.tcl]
file mkdir [file join $build results]
set_param general.maxThreads 2
set f [open [file join $build results tool-part.txt] w]
puts $f "version=[version -short]"
set parts [get_parts -quiet $part]
puts $f "part=$part matches=[llength $parts]"
close $f
if {[llength $parts]!=1} {error "exact part unavailable"}
source [file join $build report.tcl]
foreach variant $variants {
    create_project -in_memory -part $part
    set_property target_language Verilog [current_project]
    set_property verilog_define SYNTHESIS [current_fileset]
    read_verilog -sv [file join $build snapshot $variant cu66_idct8x8.sv]
    read_xdc [file join $build component.xdc]
    synth_design -top cu66_idct8x8 -part $part -mode out_of_context -flatten_hierarchy rebuilt -directive Default
    write_checkpoint -force [file join $build results ${variant}-synth.dcp]
    unit_reports $variant
    close_project
    puts "V106_IDCT_UNIT_VARIANT_FINISHED=$variant"
}
puts "V106_SYNTH_ONLY_FINISHED; isolated IDCT units only; no placement/routing/board signoff"
