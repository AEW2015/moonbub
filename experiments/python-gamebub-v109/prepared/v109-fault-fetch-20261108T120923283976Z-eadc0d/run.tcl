# Each trial starts from the same immutable, qualified synthesis checkpoint.
# A clean repeat instead executes the identical RuntimeOptimized RTL synthesis.
if {[llength $argv] != 1} {error "expected prepared BUILD_DIRECTORY"}
set build [file normalize [lindex $argv 0]]
source [file join $build inputs.tcl]
file mkdir [file join $build results]
set_param general.maxThreads 2
if {[version -short] ne "2026.1" || ![string match *6511674* [version]]} {error "unqualified Vivado version/build"}
proc v109_phase {name} {
    global build
    set f [open [file join $build results phase.txt] w]
    puts $f $name
    close $f
    puts "V109_PHASE $name"
}
if {$start_mode eq "checkpoint"} {
    v109_phase READ_QUALIFIED_SYNTHESIS_CHECKPOINT
    open_checkpoint /parent/synth.dcp
} elseif {$start_mode eq "rtl"} {
    v109_phase CLEAN_RTL_SYNTHESIS
    create_project -in_memory -part $part
    set_property target_language Verilog [current_project]
    set_property include_dirs $include_dirs [current_fileset]
    set_property verilog_define SYNTHESIS [current_fileset]
    read_verilog -sv $rtl_sources
    # The fixed clock is a synthesis input, not an after-the-fact timing edit.
    read_xdc $constraint_file
    synth_design -top cs88_pipeline_v91k -part $part -mode out_of_context -flatten_hierarchy rebuilt -directive RuntimeOptimized
    write_checkpoint -force [file join $build results synth.dcp]
} else {error "unrecognized start mode"}
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "part changed"}
set clocks [get_clocks]
if {[llength $clocks] != 1 || [get_property NAME $clocks] ne "component_clk" || abs([get_property PERIOD $clocks]-10.0)>0.0001} {error "single fixed 10ns clock changed"}
set wave [get_property WAVEFORM $clocks]
if {[llength $wave]!=2 || abs([lindex $wave 0])>0.0001 || abs([lindex $wave 1]-5.0)>0.0001} {error "clock waveform changed"}
set f [open [file join $build results settings.tsv] w]
puts $f "key\tvalue"
foreach {k v} [list tool [version -short] tool_full [string map [list "\n" " "] [version]] part [get_property PART [current_design]] clock $clocks period_ns [get_property PERIOD $clocks] max_threads [get_param general.maxThreads] start_mode $start_mode trial_id $trial_id opt_directive $opt_directive place_directive $place_directive physical_directive $phys_directive route_directive $route_directive] {puts $f "$k\t$v"}
close $f
write_xdc -force -exclude_physical [file join $build results before-effective-timing.xdc]
source [file join $build report.tcl]
if {$start_mode eq "rtl"} {v107_reports synth}
v109_phase OPT_DESIGN
opt_design -directive $opt_directive
v109_phase PLACE_DESIGN
place_design -directive $place_directive
v107_reports place
if {$phys_directive ne "NONE"} {
    v109_phase PRE_ROUTE_PHYS_OPT
    phys_opt_design -directive $phys_directive
    v107_reports pre_route_phys
}
v109_phase ROUTE_DESIGN
route_design -directive $route_directive
v107_reports route
write_checkpoint -force [file join $build results route.dcp]
report_route_status -file [file join $build results route-status.rpt]
write_xdc -force -exclude_physical [file join $build results effective-timing.xdc]
v109_phase ROUTE_COMPLETE
puts "V109_COMPONENT_ROUTE_FINISHED; no board or complete-custom-top signoff"
