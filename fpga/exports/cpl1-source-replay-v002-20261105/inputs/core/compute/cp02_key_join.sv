// Experimental private seam: CP02 -> externally supplied exact quantizer ->
// verified reconstruction adapter with KEY prediction128. No GM01 map parser.
module cp02_key_join #(parameter MAX_BYTES=65536,MAX_BLOCKS=8192)(
 input wire clk,reset,abort,
 input wire start_valid,output wire start_ready,
 input wire [31:0] start_owner,start_epoch,start_block_base,start_bytes,start_blocks,
 input wire [15:0] start_width,input wire [1:0] start_plane,
 input wire in_valid,output wire in_ready,input wire [7:0] in_byte,input wire in_last,
 // One descriptor per raster block; quantizer factor follows current coeff index.
 input wire tile_valid,output wire tile_ready,input wire [7:0] tile_bank,
 input wire [15:0] tile_x,tile_y,input wire [3:0] tile_rows,tile_cols,
 input wire [7:0] quant_factor,
 output wire [31:0] coefficient_block,output wire [5:0] coefficient_index,
 output wire out_valid,input wire out_ready,output wire [7:0] out_sample,
 output wire [31:0] out_owner,out_epoch,out_block,output wire [1:0] out_plane,
 output wire [7:0] out_bank,output wire [15:0] out_x,out_y,
 output wire [5:0] out_index,output wire out_last,
 output wire done_valid,input wire done_ready,
 output wire error_valid,input wire error_ready,output wire [4:0] error_code
);
 wire cv,cr,cl,cpl,cd,ce,rs,ri,re;wire [3:0] cc;
 wire [1:0] rc,cp;wire signed [15:0] coefficient;
 wire [31:0] co,ep,cb;wire [5:0] ci;
 reg block_live,recover,slot_valid,slot_last,raw_closed;
 reg signed [24:0] scaled_slot;
 wire local_abort=abort||recover;
 wire error_now=ce||re;
 wire enabled=!reset && !local_abort && !error_now;
 wire slot_pop=slot_valid && block_live && ri && enabled;
 wire slot_ready=!slot_valid || slot_pop;
 wire raw_push=cv && cr;
 wire recon_start=!block_live && !slot_valid && cv && ci==0 && tile_valid && enabled;
 wire reconstructed_valid;
 wire signed [24:0] product=$signed(coefficient)*$signed({1'b0,quant_factor});
 // Product and last belong to the accepted decoder coefficient. In particular,
 // a held last product must not follow the next block's live quantizer index.
 always @(posedge clk)if(raw_push)scaled_slot<=product;
 cp02_decoder #(.MAX_BYTES(MAX_BYTES),.MAX_BLOCKS(MAX_BLOCKS)) decoder(
  .clk(clk),.reset(reset),.abort(local_abort),.start_valid(start_valid),.start_ready(start_ready),
  .start_owner(start_owner),.start_epoch(start_epoch),.start_block_base(start_block_base),.start_bytes(start_bytes),.start_blocks(start_blocks),.start_width(start_width),.start_plane(start_plane),
  .in_valid(in_valid),.in_ready(in_ready),.in_byte(in_byte),.in_last(in_last),
  .out_valid(cv),.out_ready(cr),.out_coefficient(coefficient),.out_owner(co),.out_epoch(ep),.out_block(cb),.out_plane(cp),.out_index(ci),.out_last(cl),.out_plane_last(cpl),
  .done_valid(cd),.done_ready(done_ready && rs && !block_live && !slot_valid && enabled),.error_valid(ce),.error_ready(error_ready),.error_code(cc));
 ar03_reconstruct reconstruction(
  .clk(clk),.reset(reset),.abort(local_abort),.start_valid(recon_start),.start_ready(rs),
  .start_owner(co),.start_block(cb),.start_epoch(ep),.start_bank(tile_bank),.start_plane(cp),
  .start_x(tile_x),.start_y(tile_y),.start_rows(tile_rows),.start_cols(tile_cols),
  .in_valid(slot_valid && block_live && enabled),.in_ready(ri),.in_coefficient({{7{scaled_slot[24]}},scaled_slot}),.in_prediction(8'd128),.in_last(slot_last),
  .out_valid(reconstructed_valid),.out_ready(out_ready && enabled),.out_sample(out_sample),.out_owner(out_owner),.out_block(out_block),.out_epoch(out_epoch),.out_bank(out_bank),.out_plane(out_plane),
  .out_x(out_x),.out_y(out_y),.out_index(out_index),.out_last(out_last),.error_valid(re),.error_ready(error_ready),.error_code(rc));
 assign tile_ready=!block_live && !slot_valid && cv && ci==0 && rs && enabled;
 assign cr=block_live && !raw_closed && slot_ready && enabled;
 assign out_valid=reconstructed_valid && enabled;
 assign coefficient_block=cb;assign coefficient_index=ci;
 assign error_valid=ce||re;
 assign error_code=ce?{1'b0,cc}:{3'b100,rc};
 assign done_valid=cd && rs && !block_live && !slot_valid && enabled;
 always @(posedge clk)begin
  if(reset || local_abort)begin block_live<=0;recover<=0;slot_valid<=0;slot_last<=0;raw_closed<=1;end
  else begin
   recover<=error_valid&&error_ready;
   if(slot_pop)slot_valid<=0;
   if(raw_push)begin slot_valid<=1;slot_last<=cl;if(cl)raw_closed<=1;end
   if(tile_valid&&tile_ready)begin block_live<=1;raw_closed<=0;end
   // The block's input lifetime ends on inverse acceptance, not decoder ACK.
   // raw_closed prevents replacing a held last slot with next-block coeff0.
   if(slot_pop&&slot_last)block_live<=0;
  end
 end
endmodule
