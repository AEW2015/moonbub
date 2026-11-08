set build [file normalize [lindex $argv 0]]
file mkdir [file join $build results]
set_param general.maxThreads 2
open_checkpoint /parent/route.dcp
report_clocks -file [file join $build results clocks.rpt]
set cell [get_cells -quiet coefficients/child/scratch/error4]
if {[llength $cell]!=1 || [get_property REF_NAME $cell] ne "DSP48E1"} {error "exact scratch/error4 DSP absent"}
set start [get_pins -quiet coefficients/child/scratch/error4/CLK]
if {[llength $start]!=1 || [get_property REF_PIN_NAME $start] ne "CLK"} {error "exact DSP CLK startpoint absent"}
set clock [get_clocks -of_objects $start]
if {[llength $clock]!=1 || abs([get_property PERIOD $clock]-10)>0.001} {error "existing10ns clock changed"}
set f [open [file join $build results dsp.tsv] w]
puts $f "cell\tprimitive\tclock\tperiod\tAREG\tBREG\tMREG\tPREG"
puts $f "$cell\t[get_property REF_NAME $cell]\t$clock\t[get_property PERIOD $clock]\t[get_property AREG $cell]\t[get_property BREG $cell]\t[get_property MREG $cell]\t[get_property PREG $cell]"
close $f
report_timing -delay_type max -from $start -max_paths 5 -path_type full_clock_expanded -file [file join $build results dsp-control-routed.rpt]
set paths [get_timing_paths -delay_type max -from $start -max_paths 5]
if {[llength $paths]<1} {error "exact DSP CLK timing source matched no paths"}
set f [open [file join $build results dsp-paths.tsv] w]
puts $f "source\tendpoint\tslack\tdatapath\tlogic_levels"
foreach path $paths {
 puts $f "[get_property STARTPOINT_PIN $path]\t[get_property ENDPOINT_PIN $path]\t[get_property SLACK $path]\t[get_property DATAPATH_DELAY $path]\t[get_property LOGIC_LEVELS $path]"
}
close $f
puts V107_READONLY_DSP_PROBE_COMPLETE
