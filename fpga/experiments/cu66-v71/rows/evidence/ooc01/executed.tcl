set_param general.maxThreads 2
set out [file normalize [lindex $argv 0]]
create_project -in_memory -part xc7a100tcsg324-1 cu71_rows_ooc
read_verilog -sv [file join $out cu71_tile_rows.sv]
synth_design -top cu71_tile_rows -mode out_of_context -part xc7a100tcsg324-1 -generic STRIP_BANKS=2
create_clock -period 10.0 -name core [get_ports clk]
report_utilization -hierarchical -file [file join $out utilization.rpt]
report_timing_summary -report_unconstrained -file [file join $out timing.rpt]
set f [open [file join $out inference.txt] w]
set ram [get_cells -quiet -hier -filter {REF_NAME =~ RAMB*}]
set ff [get_cells -quiet -hier -filter {REF_NAME =~ FD*}]
puts $f "BRAM_CELLS=[llength $ram] FF_CELLS=[llength $ff]"
foreach c $ram {puts $f "$c [get_property REF_NAME $c]"}
close $f
write_checkpoint -force [file join $out synthesized.dcp]
if {[llength $ram]<2||[llength $ff]>3000} {error "Storage inference/resource gate failed"}
puts "CU71_ROWS_BRAM_INFERENCE_PASS_NOT_BOARD_TIMING"
