module harness(input clk,input eob,input downstream_ready,input coeff_valid,input [5:0] coeff_idx,input [15:0] coeff_data);
reg [1:0] phase=0;
always @(posedge clk) if(phase!=2) phase<=phase+1;
wire rst=phase==0, start=phase==1;
wire iv;wire [15:0] d0,d1,d2,d3;wire [2:0] ii;wire xv;wire [5:0] xi;
jpeg_idct_ram input_buffer(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(1'b0),.inport_valid_i(coeff_valid),.inport_data_i(coeff_data),.inport_idx_i(coeff_idx),.inport_eob_i(eob),.inport_accept_o(),.outport_valid_o(iv),.outport_data0_o(d0),.outport_data1_o(d1),.outport_data2_o(d2),.outport_data3_o(d3),.outport_idx_o(ii),.outport_ready_i(downstream_ready));
jpeg_idct_x x(.clk_i(clk),.rst_i(rst),.img_start_i(start),.inport_valid_i(iv),.inport_data0_i(d0),.inport_data1_i(d1),.inport_data2_i(d2),.inport_data3_i(d3),.inport_idx_i(ii),.outport_valid_o(xv),.outport_data_o(),.outport_idx_o(xi));
reg [5:0] expected=0;reg [1:0] cooldown=0;
always @(posedge clk) begin
 if(rst||start)begin expected<=0;cooldown<=0;end
 else begin
  if(cooldown!=0)begin assert(!xv);cooldown<=cooldown-1;end
  if(expected!=0) assert(xv);
  if(xv)begin
   assert(xi==expected);
   expected<=expected+1;
   if(expected==63)cooldown<=2;
  end
 end
end
endmodule
