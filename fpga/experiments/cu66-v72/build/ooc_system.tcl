# Exact-target OOC preflight for the v72 hardware source list.
# The explicit list mirrors system/sources.json after excluding simulation
# wrapper and SDRAM model; no SIMULATION define is applied.
set here [file dirname [file normalize [info script]]]
set repo [file normalize [file join $here ../../../..]]
set part xc7a100tcsg324-1
if {[llength [get_parts -quiet $part]] != 1} {
    puts stderr "UNAVAILABLE_EXACT_PART: $part is not installed"
    exit 2
}
set strip 1
if {$argc > 0} { set strip [lindex $argv 0] }
if {$strip ni {0 1}} { error "USE_STRIP must be 0 or 1" }
create_project -in_memory -part $part cu72_ooc
set_property include_dirs [list \
    [file join $repo fpga/experiments/cu66-v70/memory] \
    [file join $repo fpga/experiments/cu66-v69/packet] \
    [file join $repo fpga/experiments/cu66-v69/inverse]] [current_fileset]
foreach name {
    fpga/experiments/cu66-v72/system/cu72_system.sv
    fpga/experiments/cu66-v70/receiver/cu70_receiver.sv
    fpga/experiments/cu66-v72/memory/cu72_tile_memory.sv
    fpga/experiments/cu66-v72/memory/cu72_word_bridge.sv
    fpga/experiments/cu66-v72/memory/cu72_memory_system.sv
    fpga/experiments/cu66-v72/memory/cu72_sdram_controller.sv
    fpga/experiments/cu66-v70/display/cu70_painter.sv
    fpga/experiments/cu66-v72/display/cu72_painter_burst.sv
    fpga/experiments/cu66-v71/display/cu71_scanout.sv
    fpga/experiments/cu66-v70/display/cu70_lcd_lines.sv
    fpga/experiments/cu66-v69/packet/cu66_packet_control.sv
    fpga/experiments/cu66-v69/banks/cu66_frame_bank_control.sv
    fpga/experiments/cu66-v69/integration/cu66_base_pipeline.sv
    fpga/experiments/cu66-v69/inverse/cu66_expand_tiles.sv
    fpga/experiments/cu66-v69/inverse/cu66_dequant.sv
    fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv
    fpga/experiments/cu66-v69/inverse/cu66_reconstruct_tile.sv
    fpga/experiments/cu66-v69/entropy/cu66_ab38_decoder.sv
    fpga/experiments/cu66-v69/rows/cu66_tile_rows.sv
    fpga/experiments/cu66-v69/rows/cu66_rows_sha256.sv
    fpga/experiments/cu66-v69/hash/cu66_sha256_bytes.sv
} {
    read_verilog -sv [file join $repo $name]
}
synth_design -top cu72_system -part $part -mode out_of_context -generic USE_STRIP=$strip
create_clock -name memory100 -period 10.000 [get_ports clk]
create_clock -name read100 -period 10.000 -waveform {7.750 2.750} [get_ports read_clk]
create_clock -name panel -period 34.058 [get_ports pixel_clk]
set_clock_groups -asynchronous -group [get_clocks {memory100 read100}] -group [get_clocks panel]
# OOC assumptions only; no PLL or board/pad timing qualification.
report_utilization -hierarchical -file utilization-synth.rpt
report_timing_summary -report_unconstrained -file timing-synth.rpt
report_cdc -details -file cdc-synth.rpt
write_checkpoint -force synthesized.dcp
opt_design
place_design
phys_opt_design
route_design
report_utilization -hierarchical -file utilization-routed.rpt
report_timing_summary -report_unconstrained -file timing-routed.rpt
report_cdc -details -file cdc-routed.rpt
report_drc -file drc-routed.rpt
write_checkpoint -force routed.dcp
puts "OOC_FLOW_COMPLETED: inspect reports and unconstrained interfaces; not a board/timing PASS"
