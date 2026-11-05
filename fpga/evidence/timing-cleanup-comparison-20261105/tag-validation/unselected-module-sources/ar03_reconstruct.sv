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
 // Capture lookup outputs before prediction addition and saturation. The
 // complete reservation includes cropped samples and the physical final byte.
 reg pixel_valid,pixel_visible,pixel_last,pixel_final;
 reg signed[31:0]pixel_residual;reg[7:0]pixel_prediction;reg[5:0]pixel_index;
 wire pixel_ready=!pixel_valid||!pixel_visible||out_ready;
 wire signed [32:0] sum=$signed({pixel_residual[31],pixel_residual})+$signed({25'b0,pixel_prediction});
 assign out_sample=sum<0 ? 8'd0 : sum>255 ? 8'd255 : sum[7:0];
 assign start_ready=!active && inv_start_ready && !reset && !abort;
 assign in_ready=active && !geometry_error && inv_in_ready;
 assign out_valid=active && !geometry_error && pixel_valid && pixel_visible && !reset && !abort;
 assign inv_ready=active && !geometry_error && pixel_ready && !reset && !abort;
 assign out_index=pixel_index;
 assign out_last=pixel_last;
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
 // Match accepted prediction data to its coefficient using one private
 // reservation. Reset/abort invalidate the reservation and service outputs;
 // one prior write may retire privately, before any later fresh block starts.
 reg prediction_write_valid;reg[5:0]prediction_write_index;reg[7:0]prediction_write_data;
 always @(posedge clk)begin
  if(reset||abort)prediction_write_valid<=0;
  else begin
   prediction_write_valid<=in_valid&&in_ready;
   if(in_valid&&in_ready)begin prediction_write_index<=load_index;prediction_write_data<=in_prediction;end
  end
 end
 always @(posedge clk)if(prediction_write_valid)prediction[prediction_write_index]<=prediction_write_data;
 always @(posedge clk)begin
  if(reset||abort)pixel_valid<=0;
  else if(pixel_ready)begin
   pixel_valid<=active&&!geometry_error&&inv_valid;
   if(active&&!geometry_error&&inv_valid)begin
    pixel_residual<=residual;pixel_prediction<=prediction[index];pixel_index<=index;
    pixel_visible<=visible;pixel_final<=inv_last;
    pixel_last<=({1'b0,index[5:3]}==rows-1'b1)&&({1'b0,index[2:0]}==cols-1'b1);
   end
  end
 end
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
   if(in_valid && in_ready) begin load_index<=load_index+1'b1;end
   if((pixel_valid && pixel_ready && pixel_final) || (error_valid && error_ready)) begin active<=0;geometry_error<=0;end
  end
 end
endmodule
