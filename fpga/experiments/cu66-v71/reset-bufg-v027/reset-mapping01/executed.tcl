set_param general.maxThreads 2
open_checkpoint {C:/mb70/dy71-v027-20261107-v001/constrained.dcp}
set out {C:/mb70/dy71-v027-20261107-v001/reset-mapping01}
set buf [get_cells -quiet core_reset_distribution]
if {[llength $buf]!=1 || [get_property REF_NAME $buf] ne "BUFG"} {error "Explicit reset BUFG missing"}
report_property $buf -file [file join $out buffer.rpt]
set stages [get_cells -quiet -hier -regexp {joint_core_reset_reg\[[0-3]\]}]
if {[llength $stages]!=4} {error "Wrong protected reset stage count"}
set f [open [file join $out stages.tsv] w]
foreach c $stages {
 if {[get_property ASYNC_REG $c] ne "1"} {error "Reset stage lost ASYNC_REG"}
 set ck [get_clocks -of_objects [get_pins $c/C]]
 if {[llength $ck]!=1 || abs([get_property PERIOD $ck]-10.0)>0.001} {error "Reset stage clock changed"}
 puts $f "$c	[get_property REF_NAME $c]	[get_property ASYNC_REG $c]	[get_property PERIOD $ck]"
}
close $f
report_property [get_nets -of_objects [get_pins core_reset_distribution/O]] -file [file join $out output-net.rpt]
puts V027_RESET_MAPPING_COMPLETE_NO_BIT_OR_HARDWARE
close_design
