set_param general.maxThreads 2
set_property include_dirs {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02} [current_fileset]
read_verilog -sv {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/cu71_direct_scanout_syncsafe.sv}
read_verilog -sv {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/cu71_cache_dma.sv}
read_verilog -sv {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/cu71_direct_cache.sv}
read_verilog -sv {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/cu71_yuv_pixel_pipe.sv}
read_verilog -sv {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/cu71_lcd_lines_syncsafe.sv}
synth_design -top cu71_direct_scanout_syncsafe -part xc7a100tcsg324-1 -mode out_of_context
create_clock -name mem_clk -period 10.000 [get_ports mem_clk]
create_clock -name pixel_clk -period 34.057649667 [get_ports pixel_clk]
write_checkpoint -force {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/synthesized-unconstrained.dcp}
report_cdc -details -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/cdc-before.rpt}
source {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/executed-cdc-constraints.tcl}
set f [open {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/first-stage-fanout.txt} w]
foreach rel {lcd/request_sync0_reg lcd/request_sync1_reg lcd/frame_sync_reg lcd/done_sync0_reg lcd/done_sync1_reg lcd/valid_sync_reg} {
 set first [direct_exact_reg [format {%s[0]} $rel]]
 set endpoints [all_fanout -flat -endpoints_only -from [direct_pins $first Q]]
 puts $f "$first ENDPOINTS $endpoints"
 if {[llength $endpoints]!=1} {error "DIRECT SYNCSAFE first stage has functional fanout: $first"}
}
close $f
report_cdc -details -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/cdc-after.rpt}
report_exceptions -coverage -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/exceptions.rpt}
report_bus_skew -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/bus-skew.rpt}
write_xdc -force {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/applied-leaf-only.xdc}
report_utilization -hierarchical -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/utilization.rpt}
report_timing_summary -delay_type min_max -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/synthesized-timing.rpt}
report_timing -max_paths 10 -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/synthesized-paths.rpt}
report_timing -from [get_clocks mem_clk] -to [get_clocks mem_clk] -max_paths 20 -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/memory-paths.rpt}
write_checkpoint -force {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/synthesized.dcp}
set f [open {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/syncsafe-ooc02/primitive-counts.json} w]
set lut [llength [get_cells -hier -filter {REF_NAME =~ LUT*}]]
set ff [llength [get_cells -hier -filter {REF_NAME =~ FD*}]]
set rb18 [llength [get_cells -hier -filter {REF_NAME =~ RAMB18*}]]
set rb36 [llength [get_cells -hier -filter {REF_NAME =~ RAMB36*}]]
set dsp [llength [get_cells -hier -filter {REF_NAME =~ DSP*}]]
puts $f "{\"LUT\":$lut,\"FF\":$ff,\"RAMB18\":$rb18,\"RAMB36\":$rb36,\"DSP\":$dsp}"
close $f
puts "CU71_CACHE_SYNTH_COMPLETE LUT=$lut FF=$ff RAMB18=$rb18 RAMB36=$rb36 DSP=$dsp"
