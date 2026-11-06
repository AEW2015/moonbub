set cp [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
open_checkpoint $cp
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "Wrong part"}
foreach type {max min} {
 set paths [get_timing_paths -delay_type $type -max_paths 1]
 if {[llength $paths]!=1||[get_property SLACK $paths]<=0} {error "Timing failure"}
}
report_drc -no_waivers -file [file join $out drc-native.rpt]
foreach violation [get_drc_violations] {
 if {[get_property SEVERITY $violation] eq "Error"} {error "Native DRC error"}
}
set_property BITSTREAM.CONFIG.USERID 0x53445231 [current_design]
set_property BITSTREAM.CONFIG.USR_ACCESS 0x53445231 [current_design]
write_debug_probes -force [file join $out moonbub-sdr1.ltx]
write_bitstream -force [file join $out moonbub-sdr1.bit]
puts "SDR1_BIT_LTX_ONLY_NO_HARDWARE"
close_design
