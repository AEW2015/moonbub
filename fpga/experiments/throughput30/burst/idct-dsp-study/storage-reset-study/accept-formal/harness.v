module harness(input clk);
parameter GAP=2;
reg reset=1;
always @(posedge clk) reset<=0;
reg [5:0] idx=0;
reg [7:0] remaining=0;
wire valid=(remaining==0) && !reset;
wire accept;
always @(posedge clk) begin
 if(reset) begin idx<=0;remaining<=0;end
 else if(remaining!=0) remaining<=remaining-1;
 else if(idx==63) begin idx<=0; remaining<=GAP;end
 else idx<=idx+1;
 if(!reset) assert(!valid || accept);
end
jpeg_idct_transpose dut(.clk_i(clk),.rst_i(reset),.img_start_i(1'b0),.img_end_i(1'b0),.inport_valid_i(valid),.inport_data_i(32'b0),.inport_idx_i(idx),.outport_ready_i(1'b1),.inport_accept_o(accept),.outport_valid_o(),.outport_data0_o(),.outport_data1_o(),.outport_data2_o(),.outport_data3_o(),.outport_idx_o());
endmodule
