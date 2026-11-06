set_param general.maxThreads 2
set_property include_dirs {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/direct-ooc01} [current_fileset]
read_verilog -sv {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/direct-ooc01/cu71_direct_scanout.sv}
read_verilog -sv {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/direct-ooc01/cu71_cache_dma.sv}
read_verilog -sv {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/direct-ooc01/cu71_direct_cache.sv}
read_verilog -sv {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/direct-ooc01/cu71_yuv_pixel_pipe.sv}
read_verilog -sv {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/direct-ooc01/cu71_lcd_lines_direct.sv}
synth_design -top cu71_direct_scanout -part xc7a100tcsg324-1 -mode out_of_context
create_clock -name mem_clk -period 10.000 [get_ports mem_clk]
create_clock -name pixel_clk -period 34.060 [get_ports pixel_clk]
report_utilization -hierarchical -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/direct-ooc01/utilization.rpt}
report_timing_summary -delay_type min_max -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/direct-ooc01/synthesized-timing.rpt}
report_timing -max_paths 10 -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/direct-ooc01/synthesized-paths.rpt}
write_checkpoint -force {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/direct-ooc01/synthesized.dcp}
set f [open {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/direct-ooc01/primitive-counts.json} w]
set lut [llength [get_cells -hier -filter {REF_NAME =~ LUT*}]]
set ff [llength [get_cells -hier -filter {REF_NAME =~ FD*}]]
set rb18 [llength [get_cells -hier -filter {REF_NAME =~ RAMB18*}]]
set rb36 [llength [get_cells -hier -filter {REF_NAME =~ RAMB36*}]]
set dsp [llength [get_cells -hier -filter {REF_NAME =~ DSP*}]]
puts $f "{\"LUT\":$lut,\"FF\":$ff,\"RAMB18\":$rb18,\"RAMB36\":$rb36,\"DSP\":$dsp}"
close $f
puts "CU71_CACHE_SYNTH_COMPLETE LUT=$lut FF=$ff RAMB18=$rb18 RAMB36=$rb36 DSP=$dsp"
