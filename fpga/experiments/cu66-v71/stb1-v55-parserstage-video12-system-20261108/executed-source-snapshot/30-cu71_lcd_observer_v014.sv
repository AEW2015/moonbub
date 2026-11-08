`timescale 1ns/1ps
`default_nettype none
// Laboratory observation and registered panel boundary. No video-memory master.
// The caller admits a diagnostic only while the custom owner is quiescent.
module cu71_lcd_observer_v014(
 input wire mem_clk,mem_reset,pixel_clk,pixel_reset_n,
 input wire bus_write,input wire[11:0]bus_address,input wire[31:0]bus_wdata,
 input wire[11:0]bus_read_address,output reg[31:0]bus_rdata,
 output wire bus_selected,input wire owner_quiet,input wire[31:0]front_frame_id,
 input wire[9:0]in_x,in_y,input wire in_hsync,in_vsync,in_de,
 input wire[23:0]in_rgb,
 output wire out_hsync,out_vsync,out_de,output wire[23:0]out_rgb
);
 // Separate namespace; no existing DY71 operation or mailbox is repurposed.
 assign bus_selected=bus_read_address>=12'h380&&bus_read_address<=12'h3ac;
 reg requested_pattern=0,request_token=0,pending=0,snapshot_valid=0,invalidated=0;
 reg[31:0]snapshot_frame=0,snapshot_sequence=0,denied=0;
 reg[95:0]snapshot_mem=0;
 (* ASYNC_REG="TRUE" *)reg[1:0]ack_sync=0,applied_sync=0;
 reg ack_seen=0;
 (* ASYNC_REG="TRUE" *)reg[1:0]request_sync=0,pattern_sync=0;
 reg request_seen=0,ack_token=0,collect=0,wait_frame=0,applied_pattern=0;
 reg[3:0]mask=0;
 // Held from ACK launch until the next request. Capture in the memory domain
 // uses old stage two of ACK (earliest third edge); exact max-delay bound is
 // supplied with the board integration. This is a bundled payload, not a FIFO.
 (* DONT_TOUCH="TRUE" *)reg[95:0]snapshot_pixel=0;
 wire frame_start=in_de&&in_x==0&&in_y==0;
 wire effective_pattern=frame_start?pattern_sync[1]:applied_pattern;
 reg[23:0]calibration;
 always @*begin
  // Portrait x is native canvas y; portrait y-40 is native canvas x.
  // Borders remain black. Large neutral and primary patches distinguish a
  // color-conversion/memory error from the downstream panel interface.
  calibration=24'd0;
  if(in_y>=40&&in_y<760)begin
   if(in_x<240)begin
    if(in_y<160)calibration=24'hffffff;
    else if(in_y<280)calibration=24'h808080;
    else if(in_y<400)calibration=24'hff0000;
    else if(in_y<520)calibration=24'h00ff00;
    else if(in_y<640)calibration=24'h0000ff;
    else calibration=24'h000000;
   end else calibration={in_y[7:0],in_y[7:0],in_y[7:0]};
  end
 end
 wire[23:0]selected_rgb=effective_pattern?calibration:in_rgb;
 // One matched register stage for the complete RGB/HS/VS/DE tuple. RGB has
 // configuration initialization and no datapath reset; DE suppresses publish
 // while the paired pixel-domain reset is asserted.
 (* IOB="TRUE" *)reg[23:0]rgb_out=0;
 (* IOB="TRUE" *)reg hs_out=0,vs_out=0,de_out=0;
 assign out_rgb=rgb_out;assign out_hsync=hs_out;assign out_vsync=vs_out;assign out_de=de_out;
 always @(posedge pixel_clk)begin
  rgb_out<=selected_rgb;
  if(!pixel_reset_n)begin hs_out<=0;vs_out<=0;de_out<=0;end
  else begin hs_out<=in_hsync;vs_out<=in_vsync;de_out<=in_de;end
 end
 reg[3:0]hit;
 always @*begin
  hit=0;
  if(in_de)begin
   if(in_x==0&&in_y==40)hit[0]=1;
   if(in_x==60&&in_y==72)hit[1]=1;
   if(in_x==220&&in_y==400)hit[2]=1;
   if(in_x==400&&in_y==640)hit[3]=1;
  end
 end
 always @(posedge pixel_clk)begin
  if(!pixel_reset_n)begin
   request_sync<=0;pattern_sync<=0;request_seen<=0;ack_token<=0;
   collect<=0;wait_frame<=0;mask<=0;applied_pattern<=0;
  end else begin
   request_sync<={request_sync[0],request_token};pattern_sync<={pattern_sync[0],requested_pattern};
   if(frame_start)applied_pattern<=pattern_sync[1];
   if(request_sync[1]!=request_seen)begin
    request_seen<=request_sync[1];wait_frame<=1;collect<=0;mask<=0;
   end else begin
    if(wait_frame&&frame_start)begin wait_frame<=0;collect<=1;mask<=0;end
    // A skipped point cannot combine samples from different raster frames.
    if(collect&&frame_start)mask<=0;
    if(collect&&|hit)begin
     if(hit[0])snapshot_pixel[23:0]<=selected_rgb;
     if(hit[1])snapshot_pixel[47:24]<=selected_rgb;
     if(hit[2])snapshot_pixel[71:48]<=selected_rgb;
     if(hit[3])snapshot_pixel[95:72]<=selected_rgb;
     mask<=mask|hit;
     if((mask|hit)==4'hf)begin ack_token<=request_seen;collect<=0;end
    end
   end
  end
 end
 always @(posedge mem_clk)begin
  if(mem_reset)begin
   requested_pattern<=0;request_token<=0;pending<=0;snapshot_valid<=0;invalidated<=0;
   snapshot_frame<=0;snapshot_sequence<=0;denied<=0;ack_sync<=0;ack_seen<=0;applied_sync<=0;
  end else begin
   ack_sync<={ack_sync[0],ack_token};applied_sync<={applied_sync[0],applied_pattern};
   // An owner restart invalidates observation, but does not cancel an owned
   // crossing early or permit request-token reuse before its ACK drains.
   if(!owner_quiet)begin snapshot_valid<=0;if(pending)invalidated<=1;end
   if(pending&&ack_sync[1]!=ack_seen)begin
    ack_seen<=ack_sync[1];snapshot_mem<=snapshot_pixel;pending<=0;
    snapshot_valid<=owner_quiet&&!invalidated&&front_frame_id==snapshot_frame;
    snapshot_sequence<=snapshot_sequence+1'b1;
   end
   if(bus_write&&bus_address==12'h380)begin
    if(owner_quiet&&!pending&&bus_wdata<=1)requested_pattern<=bus_wdata[0];
    else denied<=denied+1'b1;
   end
   if(bus_write&&bus_address==12'h384)begin
    if(owner_quiet&&!pending&&bus_wdata==1)begin
     request_token<=~request_token;pending<=1;snapshot_valid<=0;invalidated<=0;snapshot_frame<=front_frame_id;
    end else denied<=denied+1'b1;
   end
  end
 end
 always @*begin
  bus_rdata=0;
  case(bus_read_address)
   12'h380:bus_rdata=32'h4c443134; // LD14 extension identity, not a new codec profile
   12'h384:bus_rdata={27'd0,owner_quiet,snapshot_valid,pending,applied_sync[1],requested_pattern};
   12'h388:bus_rdata=snapshot_sequence;
   12'h38c:bus_rdata=snapshot_frame;
   12'h390:bus_rdata={8'd0,snapshot_mem[23:0]};
   12'h394:bus_rdata={8'd0,snapshot_mem[47:24]};
   12'h398:bus_rdata={8'd0,snapshot_mem[71:48]};
   12'h39c:bus_rdata={8'd0,snapshot_mem[95:72]};
   12'h3a0:bus_rdata=denied;
   12'h3a4:bus_rdata=32'h00010000;
   12'h3a8:bus_rdata=32'h00000003; // pattern + pixel snapshot; no canonical peek
   12'h3ac:bus_rdata=32'h0000000e; // full-board diagnostic revision 14
   default:bus_rdata=0;
  endcase
 end
endmodule
`default_nettype wire
