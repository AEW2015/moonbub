set_param general.maxThreads 2
set out [file normalize [lindex $argv 0]]
create_project -in_memory -part xc7a100tcsg324-1 cu71_tile_address_ooc
set_property include_dirs $out [current_fileset]
read_verilog -sv [file join $out cu71_tile_memory_address_pipe.sv]
synth_design -top cu71_tile_memory_address_pipe -mode out_of_context -part xc7a100tcsg324-1
create_clock -period 10.0 -name core [get_ports clk]
set inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_input_delay -clock core -max 1.0 $inputs
set_input_delay -clock core -min 0.0 $inputs
set_output_delay -clock core -max 1.0 [get_ports -filter {DIRECTION == OUT}]
set_output_delay -clock core -min 0.0 [get_ports -filter {DIRECTION == OUT}]
report_utilization -hierarchical -file [file join $out utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing.rpt]
report_timing -delay_type max -max_paths 30 -file [file join $out setup-paths.rpt]
write_checkpoint -force [file join $out synthesized.dcp]
puts CU71_TILE_ADDRESS_OOC_SYNTH_NOT_BOARD_TIMING
