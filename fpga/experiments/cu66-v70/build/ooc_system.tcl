# Exact-target OOC staging only. External memory/panel/control I/O still need
# board-specific integration and constraints before any hardware signoff.
set here [file dirname [file normalize [info script]]]
set repo [file normalize [file join $here ../../../..]]
set part xc7a100tcsg324-1
if {[llength [get_parts -quiet $part]] != 1} {
    puts stderr "UNAVAILABLE: exact target part $part is not installed"
    exit 2
}
set strip 0
if {$argc > 0} { set strip [lindex $argv 0] }
if {$strip ni {0 1}} { error "USE_STRIP must be 0 or 1" }
create_project -in_memory -part $part cu70_ooc
set_property include_dirs [list [file join $repo fpga/experiments/cu66-v70/memory] [file join $repo fpga/experiments/cu66-v69/packet] [file join $repo fpga/experiments/cu66-v69/inverse]] [current_fileset]
foreach name {
    fpga/experiments/cu66-v70/system/cu70_system.sv
    fpga/experiments/cu66-v70/receiver/cu70_receiver.sv
    fpga/experiments/cu66-v70/memory/cu70_tile_memory.sv
    fpga/experiments/cu66-v70/memory/cu70_word_bridge.sv
    fpga/experiments/cu66-v70/memory/cu70_memory_system.sv
    fpga/experiments/cu66-v70/memory/cu70_sdram_controller.sv
    fpga/experiments/cu66-v70/display/cu70_painter.sv
    fpga/experiments/cu66-v70/display/cu70_painter_strip.sv
    fpga/experiments/cu66-v70/display/cu70_scanout.sv
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
} { read_verilog -sv [file join $repo $name] }
synth_design -top cu70_system -part $part -mode out_of_context -generic USE_STRIP=$strip
create_clock -name memory100 -period 10.000 [get_ports clk]
create_clock -name read100 -period 10.000 -waveform {7.750 2.750} [get_ports read_clk]
create_clock -name panel -period 34.057650 [get_ports pixel_clk]
set_clock_groups -asynchronous -group [get_clocks {memory100 read100}] -group [get_clocks panel]
# Memory/read phase and panel frequency are OOC assumptions from existing RTL,
# not a synthesized PLL or a board/pad timing qualification. Preserve all
# unconstrained interface paths in reports; do not invent external delays.
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
