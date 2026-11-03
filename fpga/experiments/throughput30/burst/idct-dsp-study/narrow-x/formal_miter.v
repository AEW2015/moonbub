module formal_miter(input clk,rst,start,stop,valid,input [15:0] a,b,c,d,input [2:0] idx);
 wire v0,v1;wire [31:0] o0,o1;wire [5:0] i0,i1;
 jpeg_idct_x ref_core(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(stop),.inport_valid_i(valid),.inport_data0_i(a),.inport_data1_i(b),.inport_data2_i(c),.inport_data3_i(d),.inport_idx_i(idx),.outport_valid_o(v0),.outport_data_o(o0),.outport_idx_o(i0));
 jpeg_idct_x_narrow test_core(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(stop),.inport_valid_i(valid),.inport_data0_i(a),.inport_data1_i(b),.inport_data2_i(c),.inport_data3_i(d),.inport_idx_i(idx),.outport_valid_o(v1),.outport_data_o(o1),.outport_idx_o(i1));
 always @* begin assert(v0==v1);assert(o0==o1);assert(i0==i1);end
endmodule
