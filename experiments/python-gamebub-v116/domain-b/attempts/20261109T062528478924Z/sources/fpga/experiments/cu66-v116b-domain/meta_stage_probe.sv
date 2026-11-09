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
, output logic [10:0] probe_quant_cell, output logic mismatch, output logic [63:0] pair_edges);
initial pair_edges=0;
logic  old_in_ready;
logic  old_out_valid;
logic [31:0]  old_out_epoch;
logic [31:0]  old_out_child_epoch;
logic [1:0]  old_out_plane;
logic [1:0]  old_out_qscale;
logic [15:0]  old_out_block;
logic [12:0]  old_out_tile;
logic [10:0]  old_out_qcell;
logic [5:0]  old_out_index;
logic signed [15:0]  old_out_value;
logic  old_output_done;
logic  old_occupied;
logic  old_out_metadata_bad;
logic  old_out_domain_bad;
domain_original original(.clk(clk),.reset(reset),.start(start),.cancel(cancel),.input_done(input_done),.in_valid(in_valid),.in_ready(old_in_ready),.in_epoch(in_epoch),.in_child_epoch(in_child_epoch),.in_plane(in_plane),.in_qscale(in_qscale),.in_block(in_block),.in_tile(in_tile),.in_qcell(in_qcell),.in_index(in_index),.in_value(in_value),.out_valid(old_out_valid),.out_ready(out_ready),.out_epoch(old_out_epoch),.out_child_epoch(old_out_child_epoch),.out_plane(old_out_plane),.out_qscale(old_out_qscale),.out_block(old_out_block),.out_tile(old_out_tile),.out_qcell(old_out_qcell),.out_index(old_out_index),.out_value(old_out_value),.output_done(old_output_done),.occupied(old_occupied),.out_metadata_bad(old_out_metadata_bad),.out_domain_bad(old_out_domain_bad));
domain_candidate dut(.clk(clk),.reset(reset),.start(start),.cancel(cancel),.input_done(input_done),.in_valid(in_valid),.in_ready(in_ready),.in_epoch(in_epoch),.in_child_epoch(in_child_epoch),.in_plane(in_plane),.in_qscale(in_qscale),.in_block(in_block),.in_tile(in_tile),.in_qcell(in_qcell),.in_index(in_index),.in_value(in_value),.out_valid(out_valid),.out_ready(out_ready),.out_epoch(out_epoch),.out_child_epoch(out_child_epoch),.out_plane(out_plane),.out_qscale(out_qscale),.out_block(out_block),.out_tile(out_tile),.out_qcell(out_qcell),.out_index(out_index),.out_value(out_value),.output_done(output_done),.occupied(occupied),.out_metadata_bad(out_metadata_bad),.out_domain_bad(out_domain_bad));
assign probe_quant_cell=dut.quant_cell(in_plane,in_tile);
assign mismatch=((old_in_ready!=in_ready) || (old_out_valid!=out_valid) || (old_out_epoch!=out_epoch) || (old_out_child_epoch!=out_child_epoch) || (old_out_plane!=out_plane) || (old_out_qscale!=out_qscale) || (old_out_block!=out_block) || (old_out_tile!=out_tile) || (old_out_qcell!=out_qcell) || (old_out_index!=out_index) || (old_out_value!=out_value) || (old_output_done!=output_done) || (old_occupied!=occupied) || (old_out_metadata_bad!=out_metadata_bad) || (old_out_domain_bad!=out_domain_bad)) || original.quant_cell(in_plane,in_tile)!=probe_quant_cell;
always @(posedge clk or negedge clk)assert(!mismatch) else $fatal(1,"V116B every-edge full-public comparison");
always_ff @(posedge clk)pair_edges<=pair_edges+1;
endmodule
