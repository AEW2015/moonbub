set_param general.maxThreads 2
set out [file normalize [lindex $argv 0]]
create_project -in_memory -part xc7a100tcsg324-1 cu71_sha_ooc
read_verilog -sv [file join $out cu71_sha256_bytes_lookahead.sv]
synth_design -top cu71_sha256_bytes_lookahead -mode out_of_context -part xc7a100tcsg324-1 -generic BUFFER_BLOCKS=1
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
puts CU71_SHA_SYNTH_DIAGNOSTIC_NOT_ROUTED_TIMING
