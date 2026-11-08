// V107: one registered coefficient token, with an ordered end-of-input fence.
module meta_stage_probe (
    input logic clk, reset, start, cancel,
    input logic input_done,
    input logic in_valid,
    output logic in_ready,
    input logic [31:0] in_epoch, in_child_epoch,
    input logic [1:0] in_plane, in_qscale,
    input logic [15:0] in_block,
    input logic [12:0] in_tile,
    input logic [10:0] in_qcell,
    input logic [5:0] in_index,
    input logic signed [15:0] in_value,
    output logic out_valid,
    input logic out_ready,
    output logic [31:0] out_epoch, out_child_epoch,
    output logic [1:0] out_plane, out_qscale,
    output logic [15:0] out_block,
    output logic [12:0] out_tile,
    output logic [10:0] out_qcell,
    output logic [5:0] out_index,
    output logic signed [15:0] out_value,
    output logic output_done, occupied,
    output logic out_metadata_bad, out_domain_bad
, output logic [10:0] probe_quant_cell);
cu66_coefficient_elastic dut(.clk(clk),.reset(reset),.start(start),.cancel(cancel),.input_done(input_done),.in_valid(in_valid),.in_ready(in_ready),.in_epoch(in_epoch),.in_child_epoch(in_child_epoch),.in_plane(in_plane),.in_qscale(in_qscale),.in_block(in_block),.in_tile(in_tile),.in_qcell(in_qcell),.in_index(in_index),.in_value(in_value),.out_valid(out_valid),.out_ready(out_ready),.out_epoch(out_epoch),.out_child_epoch(out_child_epoch),.out_plane(out_plane),.out_qscale(out_qscale),.out_block(out_block),.out_tile(out_tile),.out_qcell(out_qcell),.out_index(out_index),.out_value(out_value),.output_done(output_done),.occupied(occupied),.out_metadata_bad(out_metadata_bad),.out_domain_bad(out_domain_bad));
assign probe_quant_cell=dut.quant_cell(in_plane,in_tile);
endmodule
