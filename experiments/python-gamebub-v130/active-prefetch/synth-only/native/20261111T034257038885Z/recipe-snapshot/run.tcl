# V120 fresh-RTL Default synthesis. The prepared input declares 8 or 10 ns.
# Omission of -directive invokes documented default; no retiming option is added.
if {[llength $argv] != 1} {error "expected prepared BUILD_DIRECTORY"}
set build [file normalize [lindex $argv 0]]
source [file join $build inputs.tcl]
file mkdir [file join $build results]
set_param general.maxThreads 2
if {[version -short] ne "2026.1" || ![string match *6511674* [version]]} {error "unqualified Vivado version/build"}
proc v116_phase {name} {
    global build
    set f [open [file join $build results phase.txt] w]
    puts $f $name
    close $f
    puts "V120_PHASE $name"
}
if {$start_mode ne "rtl"} {error "Default comparison requires fresh RTL"}
v116_phase CLEAN_RTL_SYNTHESIS
create_project -in_memory -part $part
set_property target_language Verilog [current_project]
set_property include_dirs $include_dirs [current_fileset]
set_property verilog_define SYNTHESIS [current_fileset]
read_verilog -sv $rtl_sources
# Fixed clock registered before fresh synthesis, never a post-route override.
read_xdc $constraint_file
synth_design -top cs88_pipeline_v91k -part $part -mode out_of_context -flatten_hierarchy rebuilt
write_checkpoint -force [file join $build results synth.dcp]
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "part changed"}
set clocks [get_clocks]
if {[llength $clocks] != 1 || [get_property NAME $clocks] ne "component_clk" || abs([get_property PERIOD $clocks]-$expected_period_ns)>0.0001} {error "declared fixed clock changed"}
set wave [get_property WAVEFORM $clocks]
if {[llength $wave]!=2 || abs([lindex $wave 0])>0.0001 || abs([lindex $wave 1]-$expected_period_ns/2.0)>0.0001} {error "clock waveform changed"}
set f [open [file join $build results settings.tsv] w]
puts $f "key\tvalue"
foreach {k v} [list tool [version -short] tool_full [string map [list "\n" " "] [version]] part [get_property PART [current_design]] clock $clocks period_ns [get_property PERIOD $clocks] max_threads [get_param general.maxThreads] synth_directive default synth_directive_cli omitted start_mode $start_mode trial_id $trial_id opt_directive $opt_directive place_directive $place_directive physical_directive $phys_directive route_directive $route_directive] {puts $f "$k\t$v"}
close $f
write_xdc -force -exclude_physical [file join $build results before-effective-timing.xdc]
source [file join $build report.tcl]
if {$start_mode eq "rtl"} {v120_reports synth}
# Read-only active-cell mapping inventory. No source, property or timing edits.
set f [open [file join $build results active-cell-inventory.tsv] w]
puts $f "kind\tinstance\tprimitive"
foreach c [lsort [get_cells -quiet -hierarchical -filter {NAME =~ *active_cell* || NAME =~ *active_scan_value*}]] {
    puts $f "cell\t$c\t[get_property REF_NAME $c]"
}
set readers [get_cells -quiet -hierarchical -filter {NAME =~ *active_scan_value_reg*}]
foreach c $readers {
    set dp [get_pins -quiet -of_objects $c -filter {REF_PIN_NAME == D}]
    if {[llength $dp]} {
        foreach p [lsort [all_fanin -flat -startpoints_only $dp]] {
            set sc [get_cells -quiet -of_objects $p]
            if {[llength $sc]} {puts $f "fanin\t$sc\t[get_property REF_NAME $sc]"}
        }
    }
}
close $f
v116_phase SYNTH_COMPLETE
puts "V130_ACTIVE_SYNTH_ONLY_FINISHED; no route, hardware or signoff"
