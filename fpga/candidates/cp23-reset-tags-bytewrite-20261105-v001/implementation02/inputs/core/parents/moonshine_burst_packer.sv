`timescale 1ns/1ps
`default_nettype none
// Experimental one-group 16-bit pixel to aligned BL8 masked write packer.
// Addresses are 16-bit words. Each source pixel owns a whole 16-bit word.
// DQM bits [2*i] and [2*i+1] inhibit low/high byte of output beat i.
// force_flush is level-sensitive; a stalled flush remains valid if the input
// deasserts it. A pending group never accepts a pixel from another group.
module moonshine_burst_packer(
 input wire clk,reset,
 input wire pixel_valid,output wire pixel_ready,
 input wire [23:0] pixel_address,input wire [15:0] pixel_data,
 input wire force_flush,input wire discard,output wire empty,
 output wire burst_valid,input wire burst_ready,
 output wire [23:0] burst_address,output wire [127:0] burst_data,
 output wire [15:0] burst_mask
);
 reg active,flushing;reg[23:0]base;reg[127:0]data;reg[15:0]mask;
 wire same_group=(pixel_address[23:3]==base[23:3]);
 wire full=(mask==0);
 wire mismatch=pixel_valid && active && !same_group;
 assign empty=!active;
 assign burst_valid=!discard && active && (flushing || force_flush || full || mismatch);
 assign pixel_ready=!discard && !force_flush && !flushing && (!active || (same_group && !full));
 assign burst_address=base;assign burst_data=data;assign burst_mask=mask;
 always @(posedge clk)begin
  if(reset || discard)begin active<=0;flushing<=0;base<=0;data<=0;mask<=16'hffff;end
  else begin
   if(burst_valid && burst_ready)begin active<=0;flushing<=0;mask<=16'hffff;end
   else if(burst_valid)flushing<=1;
   if(pixel_valid && pixel_ready)begin
    if(!active)begin active<=1;base<={pixel_address[23:3],3'b000};mask<=16'hffff;end
    data[pixel_address[2:0]*16+:16]<=pixel_data;
    mask[pixel_address[2:0]*2+:2]<=0;
   end
  end
 end
endmodule
`default_nettype wire
