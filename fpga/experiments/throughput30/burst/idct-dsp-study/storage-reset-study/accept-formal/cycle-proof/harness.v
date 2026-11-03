module harness(input clk);
reg reset=1;
always @(posedge clk) reset<=0;
reg [5:0] idx=0;
reg [1:0] remaining=0;
wire valid=(remaining==0) && !reset;
wire accept;
wire [15:0] control;
reg [15:0] snapshot_control=0;
reg [5:0] snapshot_idx=0;
reg [1:0] snapshot_remaining=0;
reg [8:0] cycle=0;
always @(posedge clk) begin
 if(reset) begin idx<=0;remaining<=0; end
 else if(remaining!=0) remaining<=remaining-1;
 else if(idx==63) begin idx<=0;remaining<=2;end
 else idx<=idx+1;
 cycle<=cycle+1;
 if(cycle==134) begin snapshot_control<=control;snapshot_idx<=idx;snapshot_remaining<=remaining;end
 if(!reset) assert(!valid || accept);
 if(cycle==266) assert({control,idx,remaining}=={snapshot_control,snapshot_idx,snapshot_remaining});
end
jpeg_idct_transpose dut(.clk_i(clk),.rst_i(reset),.img_start_i(1'b0),.img_end_i(1'b0),.inport_valid_i(valid),.inport_data_i(32'b0),.inport_idx_i(idx),.outport_ready_i(1'b1),.inport_accept_o(accept),.audit_control_o(control),.outport_valid_o(),.outport_data0_o(),.outport_data1_o(),.outport_data2_o(),.outport_data3_o(),.outport_idx_o());
endmodule
