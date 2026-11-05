// Private, single-block reconstruction service. Not a host CSR or wire ABI.
module ar03_reconstruct (
 input wire clk, reset, abort,
 input wire start_valid, output wire start_ready,
 input wire [31:0] start_owner,start_block,start_epoch,
 input wire [7:0] start_bank,input wire [1:0] start_plane,
 input wire [15:0] start_x,start_y,
 input wire [3:0] start_rows,start_cols,
 input wire in_valid, output wire in_ready,
 input wire signed [31:0] in_coefficient,
 input wire [7:0] in_prediction, input wire in_last,
 output wire out_valid, input wire out_ready, output wire [7:0] out_sample,
 output wire [31:0] out_owner,out_block,out_epoch,
 output wire [7:0] out_bank,output wire [1:0] out_plane,
 output wire [15:0] out_x,out_y,
 output wire [5:0] out_index, output wire out_last,
 output wire error_valid,input wire error_ready,output wire [1:0] error_code
);
 reg active,geometry_error;
 reg [31:0] owner,block_id,epoch;
 reg [7:0] bank;reg [1:0] plane;
 reg [15:0] x,y;
 reg [3:0] rows,cols;
 reg [5:0] load_index;
 reg [7:0] prediction[0:63];
 wire inv_start_ready,inv_in_ready,inv_valid,inv_ready,inv_last,inv_error;
 wire [1:0] inv_error_code;
 wire signed [31:0] residual;
 wire [5:0] index;
 wire geometry_ok=start_rows>=1 && start_rows<=8 && start_cols>=1 && start_cols<=8 && start_plane<3;
 wire admit=start_valid && start_ready;
 wire visible=({1'b0,index[5:3]}<rows) && ({1'b0,index[2:0]}<cols);
 // The inverse's accepted range fits int32, but adding prediction needs an
 // explicitly signed widened sum; clipping precedes any narrowing to uint8.
 wire signed [32:0] sum=$signed({residual[31],residual})+$signed({25'b0,prediction[index]});
 assign out_sample=sum<0 ? 8'd0 : sum>255 ? 8'd255 : sum[7:0];
 assign start_ready=!active && inv_start_ready && !reset && !abort;
 assign in_ready=active && !geometry_error && inv_in_ready;
 assign out_valid=active && !geometry_error && inv_valid && visible;
 assign inv_ready=active && (visible ? out_ready : 1'b1);
 assign out_index=index;
 assign out_last=({1'b0,index[5:3]}==rows-1'b1) && ({1'b0,index[2:0]}==cols-1'b1);
 assign out_owner=owner;assign out_block=block_id;assign out_epoch=epoch;
 assign out_bank=bank;assign out_plane=plane;assign out_x=x;assign out_y=y;
 assign error_valid=active && (geometry_error || inv_error) && !reset && !abort;
 assign error_code=geometry_error ? 2'd3 : inv_error_code;
 ar03_inverse inverse(
  .clk(clk),.reset(reset),.abort(abort),
  .start_valid(admit && geometry_ok),.start_ready(inv_start_ready),
  .start_owner(start_owner),.start_block(start_block),
  .in_valid(in_valid && active && !geometry_error),.in_ready(inv_in_ready),
  .in_data(in_coefficient),.in_last(in_last),
  .out_valid(inv_valid),.out_ready(inv_ready),.out_data(residual),
  .out_owner(),.out_block(),.out_index(index),.out_last(inv_last),
  .error_valid(inv_error),.error_ready(error_ready),.error_code(inv_error_code),.classification());
 always @(posedge clk) begin
  if(reset || abort) begin
   active<=0;geometry_error<=0;load_index<=0;owner<=0;block_id<=0;epoch<=0;
   bank<=0;plane<=0;x<=0;y<=0;rows<=0;cols<=0;
  end else begin
   if(admit) begin
    active<=1;geometry_error<=!geometry_ok;load_index<=0;
    owner<=start_owner;block_id<=start_block;epoch<=start_epoch;
    bank<=start_bank;plane<=start_plane;x<=start_x;y<=start_y;rows<=start_rows;cols<=start_cols;
   end
   if(in_valid && in_ready) begin prediction[load_index]<=in_prediction;load_index<=load_index+1'b1;end
   if((inv_valid && inv_ready && inv_last) || (error_valid && error_ready)) begin active<=0;geometry_error<=0;end
  end
 end
endmodule
