module miter(input clk, input valid, input [5:0] idx);
wire accept, outvalid; wire [15:0] control;
jpeg_idct_transpose dut(.clk_i(clk),.rst_i(1'b0),.img_start_i(1'b0),.img_end_i(1'b0),.inport_valid_i(valid),.inport_data_i(32'b0),.inport_idx_i(idx),.outport_ready_i(1'b1),.inport_accept_o(accept),.audit_control_o(control),.outport_valid_o(outvalid),.outport_data0_o(),.outport_data1_o(),.outport_data2_o(),.outport_data3_o(),.outport_idx_o());
reg [1:0] ready;
reg wr,rd;
reg [5:0] ri;
reg [1:0] st;
reg first=1;
wire ma=~ready[wr];
always @(posedge clk) begin
 first<=0;
 if(first) begin assume({ready,wr,rd,ri,st}=={control[15:6],control[1:0]}); end
 else begin
  assert({ready,wr,rd,ri,st}=={control[15:6],control[1:0]});
  assert(ma==accept);
  assert((st==2)==outvalid);
 end
 if(valid && idx==63 && ma)begin ready[wr]<=1;wr<=~wr;end
 if(st==2 && ri==63)begin ready[rd]<=0;rd<=~rd;end
 case(st)
 0:if(ready[rd]) st<=1;
 1:st<=2;
 2:if(ri==63)st<=0;
 endcase
 if(st==2)ri<=ri+1;
end
endmodule
