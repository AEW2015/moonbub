set_param general.maxThreads 2
set out [file normalize [lindex $argv 0]]
create_project -in_memory -part xc7a100tcsg324-1 idct_indexed
read_verilog -sv [file join $out cu71_idct_indexed.sv]
synth_design -mode out_of_context -top cu71_idct_indexed -part xc7a100tcsg324-1
create_clock -period 10 -name core [get_ports clk]
set_input_delay -clock core 1 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_output_delay -clock core 1 [get_ports -filter {DIRECTION == OUT}]
write_checkpoint -force [file join $out synthesized.dcp]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing.rpt]
report_timing -delay_type max -max_paths 20 -file [file join $out setup-paths.rpt]
report_utilization -hierarchical -file [file join $out utilization.rpt]
puts IDCT_INDEXED_LEAF_REPORTS_ONLY_NO_BIT_OR_HARDWARE
