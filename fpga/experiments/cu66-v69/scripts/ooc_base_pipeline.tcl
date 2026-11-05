# Run in a NEW output directory after installing the exact device support.
# Non-project source flow; no attached hardware or persistent project mutation.
set here [file dirname [file normalize [info script]]]
set rtl [file dirname $here]
set part xc7a100tcsg324-1
if {[llength [get_parts -quiet $part]] != 1} {
    puts stderr "UNAVAILABLE: exact target part $part is not installed"
    exit 2
}
create_project -in_memory -part $part cu66_v69_ooc
set_property source_mgmt_mode None [current_project]
set_property include_dirs [list [file join $rtl inverse]] [current_fileset]
foreach name {
    entropy/cu66_ab38_decoder.sv inverse/cu66_expand_tiles.sv
    inverse/cu66_dequant.sv inverse/cu66_idct8x8.sv
    inverse/cu66_reconstruct_tile.sv rows/cu66_tile_rows.sv
    rows/cu66_rows_sha256.sv hash/cu66_sha256_bytes.sv
    integration/cu66_base_pipeline.sv
} { read_verilog -sv [file join $rtl $name] }
synth_design -top cu66_base_pipeline -part $part -mode out_of_context
create_clock -name core -period 10.000 [get_ports clk]
# OOC core timing only. Interface timing and actual memory-controller integration
# must be constrained in the board build before any end-to-end Fmax claim.
report_utilization -hierarchical -file utilization-synth.rpt
report_timing_summary -file timing-synth.rpt
write_checkpoint -force synthesized.dcp
opt_design
place_design
phys_opt_design
route_design
report_utilization -hierarchical -file utilization-routed.rpt
report_timing_summary -report_unconstrained -file timing-routed.rpt
report_drc -file drc-routed.rpt
report_methodology -file methodology-routed.rpt
write_checkpoint -force routed.dcp
puts "OOC_FLOW_COMPLETED: review reports; this marker is not a timing/board PASS"
