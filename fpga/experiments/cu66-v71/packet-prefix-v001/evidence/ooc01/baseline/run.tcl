set_param general.maxThreads 2
create_project -in_memory -part xc7a100tcsg324-1 leaf
set_property include_dirs [list [pwd]] [current_fileset]
read_verilog -sv parser.sv
synth_design -mode out_of_context -top cu71_packet_prefix -part xc7a100tcsg324-1
create_clock -period 10 -name core [get_ports clk]
set_input_delay -clock core 1 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_output_delay -clock core 1 [get_ports -filter {DIRECTION == OUT}]
write_checkpoint -force synthesized.dcp
report_timing_summary -delay_type min_max -report_unconstrained -file timing.rpt
report_timing -delay_type max -max_paths 25 -file setup-paths.rpt
report_utilization -hierarchical -file utilization.rpt
puts "OOC_WNS [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]"
puts PREFIX_OOC_REPORTS_COMPLETE_UNPLACED_ONLY
