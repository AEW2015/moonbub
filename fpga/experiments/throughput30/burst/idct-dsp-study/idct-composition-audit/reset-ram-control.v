// Negative control: same zero-initialized RAMs, unequal first-cycle writes,
// both reset inputs asserted. Demonstrates reset does not suppress writes.
module reset_ram_control(input clk,input rst,output mismatch);
 wire [31:0] a,b;
 jpeg_idct_transpose_ram left(.clk0_i(clk),.rst0_i(rst),.addr0_i(5'd0),.data0_i(32'd1),.wr0_i(1'b1),.clk1_i(clk),.rst1_i(rst),.addr1_i(5'd0),.data1_i(32'd0),.wr1_i(1'b0),.data0_o(a),.data1_o());
 jpeg_idct_transpose_ram right(.clk0_i(clk),.rst0_i(rst),.addr0_i(5'd0),.data0_i(32'd2),.wr0_i(1'b1),.clk1_i(clk),.rst1_i(rst),.addr1_i(5'd0),.data1_i(32'd0),.wr1_i(1'b0),.data0_o(b),.data1_o());
 assign mismatch=(a!=b);
endmodule
