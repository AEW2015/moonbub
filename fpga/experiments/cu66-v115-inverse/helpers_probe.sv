module helpers_probe(
 input logic clk,rst,dq_abort,id_abort,
 input logic dq_in_valid, output logic dq_in_ready,
 input logic [31:0] dq_in_id, input logic [1023:0] dq_coeff,
 input logic dq_chroma,input logic [1:0] dq_scale,
 output logic dq_out_valid,input logic dq_out_ready,
 output logic [31:0] dq_out_id,output logic [1279:0] dq_out_tile,
 output logic dq_out_error,output logic [1:0] dq_phase,output logic [2:0] dq_group,
 input logic id_in_valid,output logic id_in_ready,
 input logic [31:0] id_in_id,input logic [1279:0] id_in_tile,
 output logic id_out_valid,input logic id_out_ready,
 output logic [31:0] id_out_id,output logic [1535:0] id_out_tile,
 output logic id_out_error,output logic [3:0] id_phase,
 output logic [31:0] id_active_cycles,
 input logic [19:0] domain_value,output logic domain_bad
);
 cu66_dequant dq(.clk(clk),.rst(rst),.abort_i(dq_abort),.in_valid(dq_in_valid),.in_ready(dq_in_ready),
  .in_id(dq_in_id),.in_coefficients(dq_coeff),.in_chroma(dq_chroma),.in_scale_code(dq_scale),
  .out_valid(dq_out_valid),.out_ready(dq_out_ready),.out_id(dq_out_id),.out_dequantized(dq_out_tile),.out_error(dq_out_error));
 cu66_idct8x8 idct(.clk(clk),.rst(rst),.abort_frame(id_abort),.in_valid(id_in_valid),.in_ready(id_in_ready),
  .in_id(id_in_id),.in_tile(id_in_tile),.out_valid(id_out_valid),.out_ready(id_out_ready),
  .out_id(id_out_id),.out_tile(id_out_tile),.out_error(id_out_error),.active_cycles(id_active_cycles));
 assign dq_phase=dq.state;assign dq_group=dq.group_index;assign id_phase=idct.state;
 assign domain_bad=idct.outside_domain(domain_value);
endmodule
