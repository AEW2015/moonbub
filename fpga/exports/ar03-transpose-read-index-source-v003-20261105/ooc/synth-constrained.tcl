if {$argc != 1} {error "Supply BANKS=1 or2"}
set banks [lindex $argv 0]
if {$banks ni {1 2}} {error "Invalid bank count"}
set root [file dirname [file normalize [info script]]]
set_param general.maxThreads 4
create_project -in_memory -part xc7a100tcsg324-1
read_verilog -sv [list [file join $root rtl ar03_yuv_transpose.sv] [file join $root rtl ar03_yuv_transpose_single.sv] [file join $root rtl ar03_yuv_transpose_double.sv]]
read_xdc [file join $root ooc-clock.xdc]
synth_design -mode out_of_context -top ar03_yuv_transpose -part xc7a100tcsg324-1 -generic BANKS=$banks
report_utilization -file utilization.rpt
report_timing_summary -delay_type min_max -max_paths 10 -file timing-estimated.rpt
report_timing -delay_type max -max_paths 10 -path_type full -file setup-paths-estimated.rpt
report_drc -file drc.rpt
write_checkpoint -force synthesized.dcp
puts "OOC_BANKS=$banks RAMB36=[llength [get_cells -hier -filter {REF_NAME == RAMB36E1}]] RAMB18=[llength [get_cells -hier -filter {REF_NAME == RAMB18E1}]] DSP=[llength [get_cells -hier -filter {REF_NAME == DSP48E1}]]"
puts "OOC_SYNTHESIS_COMPLETE_NOT_BOARD_QUALIFICATION=1"
