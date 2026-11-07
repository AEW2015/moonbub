# Run only from a fresh external build directory prepared by physical.py.
# vivado -mode batch -source snapshot/.../build.tcl -tclargs BUILD_DIR
if {[llength $argv] != 1} { error "expected fresh prepared BUILD_DIR" }
set build_dir [file normalize [lindex $argv 0]]
source [file join $build_dir frozen_inputs.tcl]
set_param general.maxThreads 2
set version_file [open [file join $build_dir tool-version.txt] w]
puts $version_file [version]
close $version_file
set parts [get_parts -quiet $part]
set f [open [file join $build_dir part-preflight.txt] w]
puts $f "requested_part=$part"
puts $f "matching_parts=$parts"
puts $f "target_count=[llength $parts]"
puts $f "series7_count=[llength [get_parts -quiet xc7*]]"
close $f
if {[llength $parts] != 1} { error "V100_TARGET_PART_UNAVAILABLE: $part" }
create_project -in_memory -part $part
set_property target_language Verilog [current_project]
set_property default_lib xil_defaultlib [current_project]
set_property verilog_define SYNTHESIS [current_fileset]
read_verilog -sv -include_dirs $include_dirs -define SYNTHESIS $rtl_sources
set f [open [file join $build_dir synthesis-started.txt] w]
puts $f "synth_design begins"
close $f
synth_design -top $top -part $part -mode out_of_context -flatten_hierarchy rebuilt -directive Default
read_xdc $constraint_file
file mkdir [file join $build_dir reports]
set report_status [open [file join $build_dir report-status.tsv] w]
puts $report_status "stage\treport\tstatus\tdetail"
proc optional_report {stage name command} {
    global report_status build_dir
    set file [file join $build_dir reports ${stage}-${name}.rpt]
    if {[catch {uplevel 1 [concat $command [list -file $file]]} detail]} {
        puts $report_status "$stage\t$name\tUNAVAILABLE\t[string map [list \n { } \t { }] $detail]"
    } else { puts $report_status "$stage\t$name\tOK\t" }
    flush $report_status
}
proc stage_reports {stage} {
    global build_dir
    # Required reports fail the flow if unavailable; optional version-dependent
    # reports record their own failure and never become silent evidence gaps.
    report_utilization -hierarchical -file [file join $build_dir reports ${stage}-utilization.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 20 -file [file join $build_dir reports ${stage}-timing-summary.rpt]
    report_timing -delay_type max -max_paths 50 -path_type full_clock_expanded -file [file join $build_dir reports ${stage}-paths.rpt]
    report_clocks -file [file join $build_dir reports ${stage}-clocks.rpt]
    check_timing -verbose -file [file join $build_dir reports ${stage}-check-timing.rpt]
    report_drc -file [file join $build_dir reports ${stage}-drc.rpt]
    report_methodology -file [file join $build_dir reports ${stage}-methodology.rpt]
    optional_report $stage high-fanout {report_high_fanout_nets -timing -max_nets 50}
    optional_report $stage ram {report_ram_utilization -include_lutram}
    optional_report $stage clock-utilization {report_clock_utilization}
    set f [open [file join $build_dir reports ${stage}-primitives.tsv] w]
    puts $f "hierarchy\tprimitive\tprimitive_type"
    foreach cell [lsort [get_cells -hierarchical -filter {IS_PRIMITIVE == 1}]] {
        puts $f "$cell\t[get_property REF_NAME $cell]\t[get_property PRIMITIVE_TYPE $cell]"
    }
    close $f
    set f [open [file join $build_dir reports ${stage}-dsp48e1.tsv] w]
    puts $f "hierarchy\tprimitive"
    foreach cell [lsort [get_cells -hierarchical -filter {REF_NAME == DSP48E1}]] {
        puts $f "$cell\t[get_property REF_NAME $cell]"
    }
    close $f
    set f [open [file join $build_dir reports ${stage}-metrics.tsv] w]
    puts $f "metric\tvalue"
    puts $f "part\t[get_property PART [current_design]]"
    foreach key {LUT FF DSP BRAM SRL} pattern {{LUT*} {FD*} {DSP48E1} {RAMB*} {SRL*}} {
        set expression "IS_PRIMITIVE == 1 && REF_NAME =~ $pattern"
        puts $f "$key\t[llength [get_cells -hierarchical -filter $expression]]"
    }
    set paths [get_timing_paths -quiet -delay_type max -max_paths 1]
    if {[llength $paths]} { puts $f "worst_setup_slack_ns\t[get_property SLACK [lindex $paths 0]]" }
    close $f
    write_checkpoint -force [file join $build_dir ${stage}.dcp]
}
stage_reports synth
set f [open [file join $build_dir implementation-started.txt] w]
puts $f "opt_design begins"
close $f
opt_design -directive Default
place_design -directive Default
stage_reports place
route_design -directive Default
stage_reports route
report_route_status -file [file join $build_dir reports route-status.rpt]
write_xdc -force [file join $build_dir effective-constraints.xdc]
close $report_status
set f [open [file join $build_dir flow-complete.txt] w]
puts $f "COMPONENT_ROUTE_COMPLETE; no board or full-top qualification"
close $f
