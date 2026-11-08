// Fixed profile: scale_code 0/1/2 denotes 8/16/32; 3 is invalid.
// Eight coefficient multiplies per active clock; packed raster order, index0 LSB.
module dequant_probe (
    input logic clk, rst, abort_i,
    input logic in_valid,
    output logic in_ready,
    input logic [31:0] in_id,
    input logic [1023:0] in_coefficients,
    input logic in_chroma,
    input logic [1:0] in_scale_code,
    output logic out_valid,
    input logic out_ready,
    output logic [31:0] out_id,
    output logic [1279:0] out_dequantized,
    output logic out_error
, output logic mismatch);
logic old_in_ready;
logic old_out_valid;
logic [31:0] old_out_id;
logic [1279:0] old_out_dequantized;
logic old_out_error;
dequant_original original(.clk(clk),.rst(rst),.abort_i(abort_i),.in_valid(in_valid),.in_ready(old_in_ready),.in_id(in_id),.in_coefficients(in_coefficients),.in_chroma(in_chroma),.in_scale_code(in_scale_code),.out_valid(old_out_valid),.out_ready(out_ready),.out_id(old_out_id),.out_dequantized(old_out_dequantized),.out_error(old_out_error));
dequant_candidate candidate(.clk(clk),.rst(rst),.abort_i(abort_i),.in_valid(in_valid),.in_ready(in_ready),.in_id(in_id),.in_coefficients(in_coefficients),.in_chroma(in_chroma),.in_scale_code(in_scale_code),.out_valid(out_valid),.out_ready(out_ready),.out_id(out_id),.out_dequantized(out_dequantized),.out_error(out_error));
assign mismatch=(old_in_ready!=in_ready) || (old_out_valid!=out_valid) || (old_out_id!=out_id) || (old_out_dequantized!=out_dequantized) || (old_out_error!=out_error);
endmodule
