module operand_miter(input check,clk,rst,start,stop,valid,input [15:0] a,b,c,d,input [2:0] idx);
 wire [351:0] x,y;
 jpeg_idct_x g(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(stop),.inport_valid_i(valid),.inport_data0_i(a),.inport_data1_i(b),.inport_data2_i(c),.inport_data3_i(d),.inport_idx_i(idx),.proof_operand_state(x));
 jpeg_idct_x_narrow t(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(stop),.inport_valid_i(valid),.inport_data0_i(a),.inport_data1_i(b),.inport_data2_i(c),.inport_data3_i(d),.inport_idx_i(idx),.proof_operand_state(y));
 always @* if(check) begin assert(x==y); assert(x[351:337]=={15{x[336]}}); end
endmodule
