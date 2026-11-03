module state_miter(input check,clk,rst,start,stop,valid,input [31:0] a,b,c,d,input [2:0] idx,input [31:0] p0,p1,p2,p3,p4);
 wire [1053:0] x,y;wire [31:0] ox,oy;wire vx,vy;wire [5:0] ix,iy;
 jpeg_idct_y g(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(stop),.inport_valid_i(valid),.inport_data0_i(a),.inport_data1_i(b),.inport_data2_i(c),.inport_data3_i(d),.inport_idx_i(idx),.proof_product0(p0),.proof_product1(p1),.proof_product2(p2),.proof_product3(p3),.proof_product4(p4),.proof_state(x),.outport_data_o(ox),.outport_valid_o(vx),.outport_idx_o(ix));
 jpeg_idct_y_coeff t(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(stop),.inport_valid_i(valid),.inport_data0_i(a),.inport_data1_i(b),.inport_data2_i(c),.inport_data3_i(d),.inport_idx_i(idx),.proof_product0(p0),.proof_product1(p1),.proof_product2(p2),.proof_product3(p3),.proof_product4(p4),.proof_state(y),.outport_data_o(oy),.outport_valid_o(vy),.outport_idx_o(iy));
 always @* if(check) begin assert(x==y);assert(ox==oy);assert(vx==vy);assert(ix==iy);end
endmodule
