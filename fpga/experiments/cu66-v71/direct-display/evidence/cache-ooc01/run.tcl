set_param general.maxThreads 2
read_verilog -sv {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/cache-ooc01/cu71_direct_cache.sv}
read_verilog -sv {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/cache-ooc01/cu71_yuv_pixel_pipe.sv}
read_verilog -sv {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/cache-ooc01/cu71_cache_pixel_test.sv}
synth_design -top cu71_cache_pixel_test -part xc7a100tcsg324-1 -mode out_of_context
create_clock -name clk -period 10.000 [get_ports clk]
report_utilization -hierarchical -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/cache-ooc01/utilization.rpt}
report_timing_summary -delay_type min_max -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/cache-ooc01/synthesized-timing.rpt}
report_timing -max_paths 10 -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/cache-ooc01/synthesized-paths.rpt}
write_checkpoint -force {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/cache-ooc01/synthesized.dcp}
set f [open {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/cache-ooc01/primitive-counts.json} w]
set lut [llength [get_cells -hier -filter {REF_NAME =~ LUT*}]]
set ff [llength [get_cells -hier -filter {REF_NAME =~ FD*}]]
set rb18 [llength [get_cells -hier -filter {REF_NAME =~ RAMB18*}]]
set rb36 [llength [get_cells -hier -filter {REF_NAME =~ RAMB36*}]]
set dsp [llength [get_cells -hier -filter {REF_NAME =~ DSP*}]]
puts $f "{\"LUT\":$lut,\"FF\":$ff,\"RAMB18\":$rb18,\"RAMB36\":$rb36,\"DSP\":$dsp}"
close $f
puts "CU71_CACHE_SYNTH_COMPLETE LUT=$lut FF=$ff RAMB18=$rb18 RAMB36=$rb36 DSP=$dsp"
